import * as T from "three";
import { createScene } from "./scene.js";

const $ = (id) => document.getElementById(id);
const query = new URLSearchParams(location.search);
const fields = new Map();
const status = $("status");
const canvas = $("canvas");
let variants,
  scene,
  serial = 0,
  firstPose = query.get("pose");
const cache = new Map();
const loader = new T.TextureLoader();
function url(path) {
  return "./outputs/" + path.split("/").map(encodeURIComponent).join("/");
}
function element(tag, text) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  return node;
}
function field(group, id, title, options, value) {
  const label = element("label", title);
  const input = element(Array.isArray(options) ? "select" : "input");
  input.id = id;
  if (Array.isArray(options)) {
    for (const item of options) {
      const [key, label] = Array.isArray(item) ? item : [item, item];
      input.add(new Option(label, key));
    }
  } else {
    input.type = options.type || "number";
    Object.assign(input, options);
  }
  label.append(input);
  $(group).append(label);
  bind(input, value);
}
function bind(input, fallback) {
  const raw = query.get(input.id);
  if (input.type === "checkbox")
    input.checked = raw === null ? fallback : raw === "1";
  else {
    input.value = raw ?? fallback;
    if (input.value === "" || !input.validity.valid) input.value = fallback;
  }
  fields.set(input.id, input);
  input.addEventListener("change", () => {
    if (input.checkValidity() && input.value !== "") refresh();
    else input.reportValidity();
  });
}
function settings() {
  return Object.fromEntries(
    [...fields].map(([key, input]) => [
      key,
      input.type === "checkbox"
        ? input.checked
        : input.type === "number"
          ? input.valueAsNumber
          : input.value,
    ]),
  );
}
function sync() {
  const params = new URLSearchParams();
  for (const [k, v] of Object.entries(settings()))
    params.set(k, typeof v === "boolean" ? Number(v) : v);
  const pose = firstPose || scene?.pose();
  if (pose) params.set("pose", pose);
  history.replaceState(null, "", "?" + params);
}
function load(path, colour) {
  if (!path) return Promise.resolve(null);
  const key = colour + path;
  if (!cache.has(key))
    cache.set(
      key,
      loader
        .loadAsync(url(path))
        .then((tex) => {
          tex.colorSpace = colour ? T.SRGBColorSpace : T.NoColorSpace;
          return tex;
        })
        .catch((error) => {
          cache.delete(key);
          throw error;
        }),
    );
  return cache.get(key);
}
function describe(v, index) {
  const article = element("article");
  article.append(
    element("h2", (index ? "B" : "A") + " · " + v.name),
    element(
      "p",
      [
        v.experiment,
        v.algorithm,
        v.dither,
        v.palette.length + " colours",
        v.resolution.join(" × "),
      ].join(" · "),
    ),
  );
  const source = element("a", "Source image");
  source.href = url(v.source);
  const record = element("a", "Experiment record");
  record.href = url(v.record);
  article.append(
    source,
    " · ",
    record,
    element("p", v.normal ? "Tangent-space normal map" : "Albedo only"),
  );
  for (const rgb of v.palette) {
    const hex = "#" + rgb.map((c) => c.toString(16).padStart(2, "0")).join("");
    const swatch = element("span");
    swatch.className = "swatch";
    swatch.style.background = hex;
    swatch.title = hex;
    swatch.setAttribute("aria-label", hex);
    article.append(swatch);
  }
  const details = element("details");
  details.append(
    element("summary", "Parameters and measurements"),
    element(
      "pre",
      JSON.stringify({ config: v.config, metrics: v.metrics }, null, 2),
    ),
  );
  article.append(details);
  return article;
}
async function refresh() {
  const token = ++serial,
    s = settings();
  const list = (s.compare ? [s.a, s.b] : [s.a]).map((id) =>
    variants.find((v) => v.id === id),
  );
  const flat = s.view === "Flat";
  $("b").parentElement.hidden = !s.compare;
  $("flatControls").hidden = !flat;
  $("spatial").hidden = flat;
  $("reset").hidden = flat;
  $("flat").hidden = !flat;
  canvas.hidden = flat;
  $("stage").classList.toggle("split", s.compare);
  $("details").replaceChildren(...list.map(describe));
  $("hint").textContent = flat
    ? "Unlit albedo · integer CSS-pixel zoom"
    : s.camera === "Orbit"
      ? "Drag to orbit · scroll to zoom · right-drag to pan"
      : "Click the viewport to look around · WASD to move · Esc to release";
  status.textContent = "";
  sync();
  if (flat) {
    $("flat").replaceChildren(
      ...list.map((v) => {
        const wrapper = element("div"),
          img = element("img");
        img.alt = v.name;
        img.src = url(v.albedo);
        img.width = v.resolution[0] * Number(s.zoom);
        img.height = v.resolution[1] * Number(s.zoom);
        wrapper.append(img);
        return wrapper;
      }),
    );
    return;
  }
  try {
    if (!scene) scene = createScene(canvas, sync);
    const pairs = await Promise.all(
      list.map(async (variant) => {
        const [map, normal] = await Promise.all([
          load(variant.albedo, true),
          load(variant.normal, false),
        ]);
        return { map, normal, variant };
      }),
    );
    if (token !== serial) return;
    scene.apply(s, pairs);
    if (firstPose) {
      scene.restore(firstPose);
      firstPose = null;
    }
    sync();
  } catch (error) {
    if (token === serial)
      status.textContent =
        "3D preview unavailable. Try Flat view. " + error.message;
  }
}
async function start() {
  const response = await fetch("./outputs/manifest.json");
  if (!response.ok) throw Error("Manifest HTTP " + response.status);
  ({ variants } = await response.json());
  if (!variants?.length) throw Error("No published variants.");
  const options = variants.map((v) => [v.id, v.experiment + " / " + v.name]);
  field("variants", "a", "Variant A", options, options[0][0]);
  field("variants", "b", "Variant B", options, (options[1] || options[0])[0]);
  bind($("view"), "3D");
  bind($("compare"), false);
  field(
    "geometryControls",
    "geometry",
    "Geometry",
    ["Slab", "Floor", "Wall", "Cube", "Room"],
    "Slab",
  );
  field(
    "geometryControls",
    "camera",
    "Camera",
    ["Orbit", "First person"],
    "Orbit",
  );
  field(
    "sampling",
    "scale",
    "Metres per texel",
    { min: 0.0001, max: 10, step: "any", required: true },
    0.01,
  );
  field(
    "sampling",
    "tiling",
    "UV tiling multiplier",
    { min: 0.01, max: 128, step: "any", required: true },
    1,
  );
  field("sampling", "filter", "Filter", ["Nearest", "Linear"], "Nearest");
  field("sampling", "mips", "Mipmapping", { type: "checkbox" }, false);
  for (const [id, label, min, max, defaultValue] of [
    ["ambient", "Ambient intensity", 0, 10, 1],
    ["sun", "Directional intensity", 0, 10, 2],
    ["azimuth", "Azimuth (degrees)", -180, 180, 45],
    ["elevation", "Elevation (degrees)", -90, 90, 50],
  ])
    field(
      "lights",
      id,
      label,
      { min, max, step: "any", required: true },
      defaultValue,
    );
  field("flatControls", "zoom", "Flat zoom", ["1", "2", "4", "8", "16"], "4");
  $("reset").onclick = () => {
    scene?.reset();
    sync();
  };
  $("share").onclick = async () => {
    sync();
    try {
      await navigator.clipboard.writeText(location.href);
      status.textContent = "View link copied.";
    } catch {
      status.textContent = "Copy the current address to share this view.";
    }
  };
  await refresh();
}
start().catch((error) => {
  status.textContent = "Could not load experiments. " + error.message;
});
