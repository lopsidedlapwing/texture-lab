import * as T from "three";
import { OrbitControls } from "./vendor/OrbitControls.js";

export function createScene(canvas, changed) {
  const renderer = new T.WebGLRenderer({ canvas, antialias: false });
  renderer.outputColorSpace = T.SRGBColorSpace;
  renderer.toneMapping = T.NoToneMapping;
  renderer.setScissorTest(true);
  const scene = new T.Scene();
  scene.background = new T.Color("#303535");
  const ambient = new T.AmbientLight(0xffffff);
  const sun = new T.DirectionalLight(0xffffff);
  scene.add(ambient, sun);
  const camera = new T.PerspectiveCamera(50, 1, 0.02, 120);
  camera.rotation.order = "YXZ";
  const orbit = new OrbitControls(camera, canvas);
  orbit.minDistance = 0.1;
  orbit.maxDistance = 50;
  orbit.addEventListener("end", changed);
  let mesh,
    shape,
    state,
    previousTime = 0;
  const materials = [0, 1].map(
    () => new T.MeshStandardMaterial({ roughness: 1, metalness: 0 }),
  );
  const keys = new Set();
  function makeShape(name) {
    const sizes = {
      Slab: [2.4, 0.18, 1.6],
      Floor: [12, 0.08, 12],
      Wall: [5, 3, 0.12],
      Cube: [1.6, 1.6, 1.6],
      Room: [6, 3, 6],
    };
    const geometry = new T.BoxGeometry(...sizes[name]);
    const { position, normal, uv } = geometry.attributes;
    // Project each face in world metres before applying texture-specific repeats.
    for (let i = 0; i < uv.count; i++) {
      const nx = normal.getX(i),
        ny = normal.getY(i),
        nz = normal.getZ(i);
      const x = position.getX(i),
        y = position.getY(i),
        z = position.getZ(i);
      uv.setXY(i, nx ? -nx * z : nz ? nz * x : x, ny ? -ny * z : y);
    }
    if (mesh) {
      scene.remove(mesh);
      mesh.geometry.dispose();
    }
    mesh = new T.Mesh(geometry, materials[0]);
    scene.add(mesh);
    shape = name;
  }
  function reset() {
    camera.position.set(
      ...(shape === "Room"
        ? [0, 0.2, 2.4]
        : shape === "Floor"
          ? [3, 3, 4]
          : [2.6, 1.9, 3.1]),
    );
    orbit.target.set(0, 0, 0);
    orbit.update();
  }
  function apply(s, pairs) {
    state = s;
    if (shape !== s.geometry) {
      makeShape(s.geometry);
      reset();
    }
    orbit.enabled = s.camera === "Orbit";
    if (orbit.enabled && document.pointerLockElement === canvas)
      document.exitPointerLock();
    ambient.intensity = s.ambient;
    sun.intensity = s.sun;
    const a = (s.azimuth * Math.PI) / 180,
      e = (s.elevation * Math.PI) / 180;
    sun.position.set(
      Math.cos(a) * Math.cos(e),
      Math.sin(e),
      Math.sin(a) * Math.cos(e),
    );
    pairs.forEach(({ map, normal, variant }, i) => {
      for (const tex of [map, normal].filter(Boolean)) {
        tex.wrapS = tex.wrapT = T.RepeatWrapping;
        tex.repeat.set(
          s.tiling / (s.scale * variant.resolution[0]),
          s.tiling / (s.scale * variant.resolution[1]),
        );
        const near = s.filter === "Nearest";
        tex.magFilter = near ? T.NearestFilter : T.LinearFilter;
        tex.minFilter = s.mips
          ? near
            ? T.NearestMipmapNearestFilter
            : T.LinearMipmapLinearFilter
          : tex.magFilter;
        tex.generateMipmaps = s.mips;
        tex.needsUpdate = true;
      }
      Object.assign(materials[i], {
        map,
        normalMap: normal,
        side: shape === "Room" ? T.BackSide : T.FrontSide,
        needsUpdate: true,
      });
    });
  }
  function pose() {
    return [...camera.position.toArray(), ...orbit.target.toArray()]
      .map((v) => Number(v.toFixed(5)))
      .join(",");
  }
  function restore(value) {
    const p = value?.split(",").map(Number);
    if (p?.length === 6 && p.every(Number.isFinite)) {
      camera.position.fromArray(p);
      orbit.target.fromArray(p, 3);
      orbit.update();
    }
  }
  canvas.addEventListener("click", () => {
    if (state?.camera === "First person")
      canvas.requestPointerLock()?.catch(() => {});
  });
  document.addEventListener("mousemove", (ev) => {
    if (document.pointerLockElement !== canvas) return;
    camera.rotation.y -= ev.movementX * 0.002;
    camera.rotation.x = T.MathUtils.clamp(
      camera.rotation.x - ev.movementY * 0.002,
      -1.54,
      1.54,
    );
    aim();
  });
  function aim() {
    camera.getWorldDirection(orbit.target).add(camera.position);
  }
  document.addEventListener("keydown", (e) => {
    if (document.pointerLockElement === canvas) keys.add(e.code);
  });
  document.addEventListener("keyup", (e) => keys.delete(e.code));
  document.addEventListener("pointerlockchange", () => {
    keys.clear();
    changed();
  });
  window.addEventListener("blur", () => keys.clear());
  renderer.setAnimationLoop((time) => {
    const dt = Math.min(0.1, (time - previousTime) / 1000);
    previousTime = time;
    if (canvas.hidden || !mesh || !state) return;
    if (document.pointerLockElement === canvas && keys.size) {
      camera.translateZ(
        2 * dt * (Number(keys.has("KeyS")) - Number(keys.has("KeyW"))),
      );
      camera.translateX(
        2 * dt * (Number(keys.has("KeyD")) - Number(keys.has("KeyA"))),
      );
      aim();
    }
    const w = canvas.clientWidth,
      h = canvas.clientHeight;
    if (!w || !h) return;
    const ratio = Math.min(devicePixelRatio, 2);
    if (renderer.getPixelRatio() !== ratio) renderer.setPixelRatio(ratio);
    if (
      canvas.width !== Math.floor(w * ratio) ||
      canvas.height !== Math.floor(h * ratio)
    )
      renderer.setSize(w, h, false);
    const n = state.compare ? 2 : 1;
    for (let i = 0; i < n; i++) {
      const width = Math.floor(w / n);
      camera.aspect = width / h;
      camera.updateProjectionMatrix();
      renderer.setViewport(i * width, 0, width, h);
      renderer.setScissor(i * width, 0, width, h);
      mesh.material = materials[i];
      renderer.render(scene, camera);
    }
  });
  return { apply, reset, pose, restore };
}
