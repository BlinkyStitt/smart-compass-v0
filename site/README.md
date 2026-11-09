# Smart compass on GitHub Pages

The page shows only the narrow removable-cell prototype. Wide files remain a
pinned source archive. The page includes the rainbow, three dark patterns, silver
PETG, night lighting and player controls. Tap any image or video to open a
full-screen viewer. Close or Escape returns to the page and restores focus.

The site uses plain HTML, CSS and JavaScript. It needs Python 3.9+, Git LFS,
FFmpeg/FFprobe, Godot 4, Node 20+ and the locked Playwright driver with its matching
Chromium. Missing tools, source files or materialized LFS assets fail validation.

Run the full repository contract from the root:

```sh
just validate
```

`just cad` owns the active narrow build. It generates the native model, STEP,
GLB, print projects, fit samples, installed inventory, service guide, dimension
views and media as one atomic generation. Its long form is
`python3 designs/stacked/run.py build`. Do not run both commands to request the
same build. The wide export files must retain their recorded hashes.

After native generation, build and verify the site:

```sh
python3 -m unittest discover -s site -p 'test_*.py'
python3 site/build.py --output .build/compass-pages
python3 site/verify.py local --directory .build/compass-pages
```

The builder requires electrical and native freshness checks. It then regenerates
the actual pattern samples, checks convergence and publishes one complete local
artifact. A local artifact does not establish deployment or physical acceptance.

## Mass, dimensions and service

`estimates.py` recomputes both glow and silver variants from the narrow native
census and selected source records. Each installed part has one accounting owner.
The continuous W044 negative conductor has one complete cut and one mass owner.
The installed protected XTAR 21700 cell and the full sewn necklace enter worn
mass once. Samples, trim waste, tools, spare cells and the off-body charger do
not enter worn mass. Missing, duplicated or unowned CAD parts fail the build.

The page shows raw worn bounds, the 1133.980925 g ceiling, margin, and the separate
50 g margin target. The bounds are sums of engineering allowances. They are not
confidence intervals or measured assembly masses. The source body diameter and
depth differ from the full closed projections. Front and side dimension views
use one scale and include the fitted textile attachment targets. The free neck
span has no fixed rigid envelope.

The service package contains the actual wire cut list, fit samples, alternative
ring-material projects, service poses, continuous-clearance record, complete
inventory and source-linked instructions. Battery access retains the rear,
optics, necklace attachments and fixed loom. Rear and board maintenance require
the documented disconnection of bridging wires. All physical fit, insulation,
retention, reset timing, heat, runtime, mass and wearing tests remain unmeasured.

## Electrical model and pattern samples

```sh
python3 site/sample.py
node site/energy.mjs --check
node site/energy.mjs --reference
```

The sampler runs the shared Godot functions for both the archived wide layout
and the active narrow layout. It retains RGB/time channels as little-endian
float32 files under `.build/energy-samples`. It repeats runs byte for byte and
records scene, pattern, sampler and model hashes, pixel identities, intervals,
tool versions and convergence results. The eight-second cycle starts with 512
then 1024 steps. It halves the interval again until each average battery-input
power changes by at most max(0.1% of its preceding value, 1 mW).

`electrical-inputs.json` owns the settings and source basis. `energy.mjs` is the
pure browser/CLI calculation. Electrical brightness precedes 8-bit PWM rounding.
Optical glow, exposure and screen brightness do not enter electrical demand.
Black pixels retain idle demand. Non-LED demand, input static loss, conversion,
series-path loss and usable-energy reserve have separate owners. Series loss
is solved for each sample before averaging. The model counts each loss once.

Use the actual rainbow for runtime planning. Full-white, full-brightness
operation is outside the intended use. The requested Adafruit approximation
uses 20 mA per fully driven channel plus a separate 1 mA powered-pixel idle allowance.
The source links and their limitations are in `electrical-inputs.json`. Actual
WS2812 products differ. These coefficients are planning estimates, not supplied
component maxima. A saturated HSV rainbow averages 1.5 summed RGB channels before
rounding. The sampler calculates its demand from the shared functions and
layout; it does not apply a second fixed rainbow discount.

The selected no-reserve reference is 21.6 Wh at 6.25 W and 85% efficiency:
**2.9376 h**, displayed as 2.94 h. The historical Efest 19.24 Wh reference remains an
arithmetic regression case: 2.61664 h, displayed as 2.62 h. The page's pattern result
also includes its stated non-LED and loss assumptions. It therefore differs from
these reference cases. Higher brightness requires another load review. The 2%
default is a bench scenario, not a delivered firmware ceiling.

Runtime equals usable energy divided by average battery-input power. Zero
usable energy gives zero runtime. Positive energy with zero demand gives a
named unbounded state with `hours: null`. Invalid inputs cannot leave apparently
current results visible. If the selected pattern has a valid result but its
rainbow comparison has no constant-power equilibrium, the selected result stays
visible and the comparison is marked unavailable. Sampled frame peaks do not
establish internal PWM, radio-burst, inrush, fault or thermal limits.

## Media and browser checks

Each rainbow/dark/silver loop uses 1280 × 720 pixels, 384 frames at 24 fps and 16 seconds.
The narrow exploded assembly opens, holds and closes in a 24-second loop.
It uses an animated PNG at 12 fps, with a direct MP4 link. Reduced motion starts
with a still frame. Play/Pause animation also controls the image explicitly.
Rebuild its MP4 from the current narrow CAD with:

```sh
python3 site/render_assembly.py --frames /Volumes/Sabrent4TB/agent-work/smart-compass-v0/assembly-frames
```

Use a new frame directory for each capture. The site build rejects a still loop
or a loop that does not return to its closed pose. The build checks decoding,
spatial colour motion, dark-mask identity and loop joins. Each asset gets a
content-hashed URL. The dimension and service SVGs use the current narrow CAD.

Each player has Play and Restart controls. Failure restores retry controls and
announces the error. Closing a pattern disclosure cancels startup and pauses its
clip. Reduced motion starts paused. Direct MP4 links provide recovery. The
narrow rainbow uses the available width on phones and desktops. Full-screen
videos have native playback controls. Where native fullscreen is unavailable,
the same modal viewer fills the browser viewport.

```sh
npm ci --prefix site --ignore-scripts --no-fund
PLAYWRIGHT_BROWSERS_PATH="$PWD/.build/browser-cache" node site/node_modules/playwright/cli.js install --with-deps chromium
python3 site/verify.py local --directory .build/compass-pages
```

Use the locked Playwright version and its full Chromium headless runtime. The
verifier checks desktop/mobile layout, keyboard controls, announced errors and
results, calculator/CLI agreement, reset, stale responses, zero cases and
playback recovery. Gallery checks cover narrow-only media, phone and desktop
layouts, image/video fullscreen, touch, keyboard, focus restoration, reduced
motion, disclosure playback and decoded animated-image motion. Synthetic browser failure cases test software behavior only.
`site/verify.py study` is an isolated calculator/player test; it cannot replace
complete local artifact verification. Servers and browser contexts close on
success or failure. Missing browsers fail the check.

## Publication integrity

The build hashes the active native inputs, exports, inventory, sources and site
model. It verifies the wide archive's export bytes against its retained manifest.
It rejects pointers, missing/stale files, mixed generations and changes during a
build. Posters and movie checks consume captured copies. `build-info.json`
records the reviewed revision and each input/output hash. The artifact goes
directly to Pages without Jekyll. It contains no `.nojekyll` marker, because the
pinned upload action excludes dotfiles. A tar roundtrip checks that packaging
preserves the complete verified inventory.

A private sibling directory and per-output lock protect the previous complete
artifact. The publication journal recovers from interruption during directory
replacement and cleanup. The unit suite tests source edits, interrupted export,
concurrency, failed publication and complete-artifact recovery.

The GitHub Pages workflow builds pull requests. It deploys only an authorized
push/manual run on `master`. PR builds do not deploy or send deployment
notifications. The existing successful-deployment notification uses configured
`NTFY_URL`, `NTFY_TOPIC` and secret `NTFY_TOKEN`; it does not establish delivery
to subscribers.

After an authorized deployment, verify the complete reviewed artifact:

```sh
python3 site/verify.py live --url https://blinkystitt.github.io/smart-compass-v0/ --expected .build/compass-pages
```

The live check fetches fresh provenance and all assets, compares hashes and
values, then repeats the browser probes. Local tests and CI do not establish
live deployment or physical-device acceptance.
