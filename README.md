# Research project: Procedural generation of high-quality low-resolution textures

## Run the laboratory

On the managed Debian 13 x86-64 image, use Python 3.12 and uv from the project root.

```bash
bash setup.sh
source activate.sh
python -m pytest -q
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python src/study.py configs/concrete.json
python src/smoke.py runs/trial-001 --count 128 --seed 42
```

Open [the comparison gallery](reports/index.html) offline. The study refreshes the fixed gallery and results in `outputs/concrete/`. The batch smoke runner requires a new output directory and produces two PNGs per sample, JSON, CSV and an HTML report. Activation configures native headers, libraries, headless plotting and writable caches. The native lock targets Debian 13 amd64. The Python requirements lock includes transitive dependencies and package hashes.

## Interactive material viewer

Run `npm ci` with Node 22 or newer, then `npm run dev` from the checkout. Open `http://localhost:5173/`. Run `npm run build` again after changing results or viewer files, then refresh the browser. The build uses Python 3's standard library and copies the locked Three.js modules into `dist/`. Serve that directory over HTTP. All asset URLs are relative to the site, including under a repository subdirectory.

Choose variant A, or enable **Compare** and choose B. The two panes share one camera, geometry and light rig. Drag to orbit, scroll to zoom, or select **First person**, click the viewport and use WASD and the mouse. Escape releases the pointer. Reset camera restores the geometry's starting view. **Copy view link** includes both variants, view and lighting settings, sampling controls, and camera position and target.

One world unit is one metre. At UV tiling 1, a 64-texel-wide texture at 0.01 metres per texel repeats every 0.64 metres. Raising tiling to 2 halves that distance. **Flat** shows the original albedo at integer CSS-pixel zoom, independent of the material and lights. The experiment panel links the source PNG and full result record. Hover over palette chips for hex values.

### Publishing results

In repository **Settings → Pages → Build and deployment**, select **GitHub Actions**. Review branches build on pull requests. After merge, each push to `main` builds the static site and deploys it at `https://lopsidedlapwing.github.io/texture-lab/`. The workflow also supports manual dispatch from `main`.

Run `python src/study.py configs/concrete.json` in the activated lab and commit the completed results under `outputs/`. The CLI writes to a directory named for the config stem and refreshes `outputs/manifest.json`. The Pages build regenerates this index from every nested `results.json`, so adding a study needs no viewer edits. Temporary smoke batches under `runs/` stay local.

Each results file has a `config` object and a `rows` array. Each row has a unique `name`, RGB byte triplets in `palette`, and preferably explicit `algorithm` and `dither`. Legacy rows use method-weight-dither filenames. Albedo defaults to `<name>.png`, source to `source.png`, and an optional normal to `<name>-normal.png`. Override with row fields `albedo`, `source` and `normal` relative to the result directory. Use equal-sized, aligned albedo and tangent-space +Y normal PNGs. Keep experiment paths and variant names stable for shared links.

### Colour and engine comparison

Albedo is interpreted as sRGB; normal channels are linear data. The renderer computes lighting in linear space and encodes output as sRGB. Tone mapping, post-processing, shadows, screen-space dithering and multisample antialiasing are off. The material is fully rough and nonmetallic. Nearest filtering and disabled mipmaps expose texels by default. Optional nearest mip sampling selects a single level; linear mip sampling blends levels. Flat view is the unlit colour reference.

Godot comparisons depend on renderer, texture import settings, normal orientation, UV density, light energy, exposure, environment lighting and tone mapper. Match those settings and disable texture compression when evaluating palette colours. Browser-generated mip levels, Godot import-time mip generation and GPU compression can produce different distant colours. The room is an inward-facing box, and first-person movement has no collision. The viewer requires WebGL 2 for 3D and a browser supporting ES modules and import maps. Flat zoom is measured in CSS pixels; display scaling can change the physical pixel ratio.

The following brief records the project goals. The first checkpoint uses a procedural source. Reference screenshots were absent from the initial checkout.

## Objective

Investigate, implement, and experimentally evaluate methods for creating high-quality pixel-art-style textures for 3D games, using concrete slabs as the initial test subject.

**This is an open-ended experimental research task, not a request to produce a single texture or implement one predetermined algorithm.**

The goal is to establish a practical, reproducible workflow that produces textures with the visual qualities of professionally authored low-resolution 3D game materials.

I am particularly interested in the texturing of games such as White Knuckle, Fortune's Run, Brush Burial and Queen's Domain. Reference screenshots from White Knuckle are provided in `references/`.

The target aesthetic includes:

- Low-resolution, clearly visible texels.
- Heavily quantised colour palettes.
- High local contrast, including genuinely bright and dark texels.
- Rich hue variation, including occasional unexpected colours.
- Dithering that creates interesting spatial patterns without overwhelming material structure.
- Recognisable materials, despite limited resolution and palette size.
- Spatially coherent stains, cracks, rust and dirt.
- Explicit surface features such as tile seams, bevels, screws and recesses.
- Fine-scale texture variation alongside larger-scale material structure.

Avoid the common failure mode of generating a nearly uniform base colour and adding small-amplitude noise or gradients. Such textures may look technically plausible but artistically bland.

## Core research questions

### 1. Palette generation

Investigate established colour quantisation algorithms, including:

- Median cut and modified median cut.
- Octree quantisation.
- K-means and weighted k-means.
- Greedy marginal-error-reduction palette selection.
- libimagequant's approach.
- Perceptual colour spaces such as Oklab and CIELAB.
- Methods that jointly optimise palettes and dithering.

The key problem is balancing colour frequency with uniqueness.

For example, if a concrete image consists of 95% grey and 5% reddish mineral flecks, allocating four palette entries to grey and one to red may produce a better texture than allocating all five to grey.

Explore objective functions based on total perceptual representation error:

E(P) = sum over pixels i of min over palette colours p of d(c_i, p)^2

Investigate marginal error reduction when adding new palette entries.

Also investigate optional weighting based on colour rarity, edge importance, local saliency, and semantic features.

Do not assume any custom algorithm will outperform established solutions. Compare against libimagequant and other appropriate baselines.

### 2. Downsampling and quantisation

Compare alternative ordering and filtering strategies:

- Downscale first, then quantise.
- Quantise at high resolution before downsampling, with a final palette projection.
- Joint or feature-preserving approaches.
- Area, nearest-neighbour, Lanczos and edge-aware downsampling.
- Possible preservation of rare colour features during reduction.

Evaluate target resolutions such as 32×32, 64×64 and 128×128.

Investigate which techniques best preserve small cracks, mineral flecks and significant brightness changes.

### 3. Dithering

Implement or integrate:

- No dithering.
- Bayer 4×4.
- Bayer 8×8.
- Floyd–Steinberg.
- Stucki.
- Atkinson.
- Blue-noise threshold dithering, if practical.

Pay particular attention to the difference between a palette optimised for nearest-colour representation and a palette optimised for the perceptual appearance of a dithered image.

Test whether wider brightness ranges combined with dithering outperform narrow palettes that minimise individual pixel errors.

Investigate how dithering affects material readability and whether it produces undesirable repeating patterns.

### 4. Material structure

Investigate how to generate visually meaningful concrete surface structure rather than uncorrelated noise.

Experiments may include:

- Multi-scale procedural noise.
- Aggregates of different sizes and colours.
- Cracks, pits, chips and surface erosion.
- Correlated variation in hue and brightness.
- Separate spatial masks for dirt, rust and staining.
- Local material replacement instead of simply tinting the underlying material.
- Variation concentrated around seams, corners and damaged areas.

Treat material structure as a separate experimental variable from quantisation and dithering.

Compare procedurally generated source images with rendered or photographic source images where appropriately licensed material is available.

### 5. Explicit geometric and semantic features

Investigate ways of incorporating details such as:

- Bevelled slab edges.
- Tile seams.
- Screw heads.
- Recesses.
- Painted markings.
- Small labels.

Compare approaches in which features are:

1. Included in the high-resolution source before reduction.
2. Added after quantisation.
3. Defined early as semantic masks but rasterised or composited late.
4. Represented partly using height and normal maps.

Avoid destroying important shapes through indiscriminate dithering or downsampling.

Explore height-derived normal maps and simple baked ambient-occlusion-like shading.

Keep actual material colour separate from baked lighting wherever possible.

### 6. Multiple spatial scales

Investigate how to combine:

- Fine texel-scale variation.
- Mid-scale cracks, stains and aggregates.
- Large-scale colour variation spanning multiple repeated tiles.

The eventual approach should work for 3D game materials, including repeated UV textures combined with world-space overlays.

For now, demonstrate these effects using static images and comparison renders rather than requiring a complete game engine integration.

## Experimental methodology

Use a hypothesis-driven, iterative process.

### Phase A: Research and baselines

Review relevant algorithms and available libraries.

Implement at least one established quantisation baseline and one custom or alternative approach.

Generate initial concrete textures using a fixed source image and controlled settings.

Document the methods and their limitations.

### Phase B: Controlled comparisons

Run systematic experiments varying palette size, palette-generation algorithm, target resolution, dithering method and contrast.

Avoid changing every variable simultaneously.

Generate labelled contact sheets with consistent scaling, alignment and lighting so variants are easy to compare.

Retain the original source image alongside the processed versions.

### Phase C: Analyse results

Calculate useful diagnostics, including:

- Palette colours and their frequencies.
- Perceptual colour error.
- Luminance range and distribution.
- Edge preservation.
- Spatial-frequency characteristics.
- Colour distribution in perceptual colour space.
- Dithering patterns and repetition.

Do not mistake low numerical reconstruction error for artistic quality.

A texture can achieve excellent reconstruction accuracy while looking bland, and another can achieve worse reconstruction accuracy while looking aesthetically superior.

Look for measurable properties that might help explain the differences, but do not claim that any metric fully captures artistic quality.

Inspect generated images when visual inspection is supported. Never claim to have visually evaluated an image solely because a program successfully generated it.

### Phase D: Iterative refinement

Use the experimental results to formulate hypotheses about why particular approaches succeed or fail.

Design further experiments to test those hypotheses.

Examples:

- Would expanding the luminance range increase perceived surface detail?
- Does palette optimisation disproportionately suppress rare but attractive colours?
- Does Bayer dithering preserve material structure better than error diffusion?
- Does feature-aware downsampling improve cracks and aggregate?
- Does a source generated with several independent material properties outperform one generated using RGB noise?
- Does combining two material palettes create better rust than simply tinting concrete?

Continue investigating promising directions rather than stopping immediately after the first successful output.

### Phase E: Feature integration

Once the basic surface appearance is satisfactory, add seams, edges, screws and other features.

Compare early versus late feature composition.

Generate albedo, height and normal maps suitable for eventual Godot integration.

## Research infrastructure

Create a reusable command-line experimental framework.

Experiments should be described by configuration files rather than hardcoded parameter combinations.

Use deterministic random seeds and log software versions.

For each experiment, store:

- The configuration.
- The input image or exact source reference.
- The generated palette.
- Intermediate images where informative.
- The final PNG texture.
- Metrics.
- Notes explaining the hypothesis and outcome.

Create contact sheets and a browsable HTML report, using relative image paths so it can be opened offline.

Maintain an experiment ledger containing the hypothesis, parameters, measurements, observations and resulting decision.

Use sensible naming and organise outputs so comparisons can be reproduced.

Write automated tests for image dimensions, deterministic output, palette-size limits and core quantisation behaviour.

## Research deliverables

Maintain these files:

- `README.md`: Setup and usage.
- `RESEARCH.md`: Research findings and relevant literature.
- `EXPERIMENTS.md`: Chronological experiment ledger.
- `FINDINGS.md`: Current conclusions, including failed approaches.
- `NEXT_STEPS.md`: Highest-value remaining experiments.
- `reports/index.html`: Visual comparison gallery.
- `src/`: Reusable implementation.
- `configs/`: Experimental configurations.
- `tests/`: Automated tests.
- `outputs/`: Generated images and experiment metadata.

Provide an easy way to regenerate the best candidate textures and the comparison gallery.

Avoid committing enormous numbers of redundant intermediate files. Preserve representative outputs and all configurations required for reproduction.

## Autonomy and decision-making

You have substantial discretion to choose methods and change your research direction based on findings.

Do not ask for approval at every experimental step. Make reasonable decisions, test them, and document them.

Do not optimise exclusively for the earliest working solution or the smallest amount of code.

Do not repeatedly regenerate superficially different noise textures without developing an explanation for what is being tested.

Prioritise experiments that distinguish competing hypotheses.

When a method fails, document why and use that information to improve the next experiment.

You are encouraged to read relevant research papers, examine established implementations, and challenge the assumptions in this prompt.

Do not fabricate visual observations, experimental results or citations.

## Initial work

Begin by establishing the repository structure and working experimental framework.

Then perform an initial systematic comparison of palette-generation and dithering algorithms using the same concrete source image.

Produce contact sheets and a first written assessment.

Continue to the most promising follow-up experiments as resources permit.

At the end of each substantial experimental phase, checkpoint the code, configurations, results and findings so the work can be resumed.

The ultimate success criterion is not the number of generated textures or implemented algorithms. It is whether the experiments uncover a reliable, understandable process for producing aesthetically convincing low-resolution materials.