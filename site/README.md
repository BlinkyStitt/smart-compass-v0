# Smart compass on GitHub Pages

The site compares the canonical Wide and Narrow rainbows and three paired
rainbows with moving dark regions, explains the hardware, and shows native CAD
size and assembly images. It uses plain HTML, CSS and JavaScript. The build needs
Python 3.9+, Git LFS, FFmpeg, FFprobe, Godot 4 and Node 20+. Browser verification
requires the locked Playwright driver and its Chromium installation.

```sh
python3 site/build.py --output /path/to/compass-pages
python3 -m http.server 8080 --bind 127.0.0.1 --directory /path/to/compass-pages
```

Rebuild changed enclosure outputs with their owning commands before building
the site. `build.py` checks each MP4's dimensions, duration and decoding. It also
checks spatial rainbow rotation on the board and outside ring in the four
canonical rainbow clips. It rejects missing LFS media. Asset
filenames include their content hash so revised clips cannot reuse stale URLs.
The front comparison uses the 250 mm wide and 200 mm narrow native CAD renders
at the same scale, with dimension lines.

The `GitHub Pages` workflow builds on pull requests, and deploys on pushes to
`master` or a manual run from `master`. Repository Pages must use GitHub Actions
as its source. The build fetches all LFS inputs so both native freshness inventories can be verified.
The workflow also requires the electrical gate, which currently rejects the
unqualified removable-cell candidate; this checkpoint is not deployable.

After a successful deployment, the workflow sends one ntfy notification linking
to the deployed site, commit and workflow attempt. Configure these repository
Actions variables and secret:

- Variable `NTFY_URL`: `https://ntfy.stytt.com`
- Variable `NTFY_TOPIC`: `deploy`
- Secret `NTFY_TOKEN`: the existing ntfy bearer token with publish access

Pull requests and failed, skipped or cancelled deployments send no success
notification. The POST has a 15-second timeout and is not retried or redirected.
Missing configuration, HTTP errors and transport failures produce a sanitized
Actions warning and job summary without failing the deployment. Credentials and
request/response bodies are not logged. An accepted POST does not prove delivery
to subscribers; verify the deployed page and ntfy receipt separately after an
authorized deployment.

Both primary videos loop. Play both aligns their times, Pause both stops paired
playback, and Restart together resets both to frame zero. Default startup aligns
both at zero. Each start explicitly loads the clips and keeps both paused until
they have playable buffered data at the shared position (`readyState >=
HAVE_FUTURE_DATA`) and any alignment seek has finished; full downloads are not
required. Both play requests are then issued together. The loading message stays
until both starts succeed. A loading error or rejected start pauses both and
restores the controls for retry; direct MP4 links provide a fallback. During
playback, drift greater than 100 ms is corrected. Inline videos hide
the browser player controls. Direct MP4 links remain available. Visitors who
request reduced motion start with paused videos.

The silver PETG comparison stays collapsed by default. It uses the same paired
player as the primary comparison, with separate Play/Pause/Restart controls.
Opening it starts both silver clips through the same readiness gate unless
reduced motion is enabled. Closing it cancels pending startup and pauses both
clips; reopening starts a fresh attempt. Its playback is independent of the
primary pair. The primary Wide and Narrow videos stay side by side,
including at 320 CSS pixels. At 620 CSS pixels and below, the silver comparison
stacks its full-width videos, and both comparisons stack their labeled
descriptions below the videos. Wider layouts use two columns for the videos
and descriptions.

With Playwright and its Chromium browser installed, check the built, locally
served page's responsive layout and playback with:

```sh
node site/test_layout.cjs http://127.0.0.1:8080
```

The Narrow silver loop uses its native geometry and camera path with the Wide
model's silver material coefficients for its rings and reflected ring light.
Regenerate it after rebuilding changed Narrow sources with their owning command:

```sh
python3 site/render_silver.py --frames /Volumes/Sabrent4TB/agent-work/smart-compass-v0/silver-frames
```

The exploded assembly uses the demo's full explosion and reassembly motion with
the current Wide CAD model and a grey background. It loops in 24 seconds. The
poster shows the fully separated assembly. Regenerate the tracked clip with
Godot and FFmpeg, using a new external-drive directory for the PNG frames:

```sh
python3 site/render_assembly.py --frames /Volumes/Sabrent4TB/agent-work/smart-compass-v0/assembly-frames
```

The renderer checks CAD freshness through the demo's normal startup gate.

Both wearing-scale stills add the same soft front light to the mannequin so its
pose stays visible. The fill light affects only the mannequin. The pendant and
night scene keep their original lighting. Regenerate these images with:

```sh
python3 site/render_worn.py
```

This command checks both designs' CAD freshness and uses their native Godot
scenes with the same camera, pose and pendant dimensions.

The main weight number includes the pendant, battery and necklace. Each card also
shows pendant mass with its included battery mass. The page identifies the current
LiPo fit candidate and its screw-fastened access; field-swappable cells still need
a compartment revision. The wide mass comes from the generated installed
inventory. `estimates.py` applies that inventory's density and uncertainty model to
the narrow CAD materials and strip lengths, and transfers the electronics, harness
and fitting allowances provisionally. The narrow design has no final fitting BOM.
Runtime uses the documented 37 Wh pack, 85% efficiency and 1.25 A total at 5 V. It
is an energy calculation before reserve, aging, temperature and cutoff losses;
useful brightness and peak demand remain unverified. These legacy pouch values
do not describe the selected protected-cell revision or set a current cap.


Three paired comparisons immediately before Silver PETG show Rainbow • dark
sectors, dark spirals and dark diagonals on the same posed mannequin. Each
starts collapsed and paused, with generated posters, Wide/Narrow labels,
independent synchronized controls and direct MP4 links. Opening starts both
clips unless reduced motion is enabled; closing pauses both. The layout stacks
at 620 CSS pixels, like Silver PETG.

Regenerate native exports with `just cad` followed by
`python3 designs/stacked/run.py build` before building this site. The six
`infinity-rainbow-dark-*.mp4` assets live in their designs' exports and use LFS;
the Pages workflow fetches them. The build verifies 1280 × 720, 384 frames,
16 seconds, 24 fps, full decoding, moving mask identity and loop joins. The four
canonical rainbow clips retain their separate strict rotation checks. All eleven
movies get content-hashed URLs and generated posters. Stored glow may remain
visible during black LED intent; these renders establish no electrical savings
or battery runtime.
## Publication integrity

`build.py` first checks electrical qualification and both native manifests. It hashes their complete input and
export sets, site sources, inventory and battery/electrical review definitions.
Missing LFS content, stale geometry and changes during a build fail publication.
Every consumed byte is checked against the captured input hash; clip checks and
posters use the copied clip. `build-info.json` records input and output hashes.

Output is built in a private sibling directory under a per-output process lock.
Only a complete artifact replaces the prior directory. A persisted journal
restores the previous complete artifact after interruption, including process
death between the directory renames. Arbitrary existing directories and symlinks
are refused. Choose a fresh output path for an older artifact without the new
publication inventory; the builder preserves it rather than guessing ownership.

`python3 -m unittest discover -s site` exercises real publication failures,
source changes, concurrent processes, and process death before/after installing
the new directory. These tests do not replace browser checks or establish physical results.

SKI-1230 remains incomplete: the cell compartment, independent mass ledgers,
qualified electrical model and complete Pages release remain undelivered.
The calculator and browser verifier operate as a separate, explicitly
unqualified parameter study. Existing rendered geometry and the 37 Wh site
calculation remain explicitly legacy pouch evidence. The selected one-cell
reference is **2.448 h (display 2.45 h)** from the selected protected XTAR
INR21700-50E: 3.6 V × 5.0 Ah = 18 Wh, at 6.25 W and assumed 85% efficiency,
before reserve/other losses. This replaces the historical Efest reference,
not the legacy geometry or mass model. See the
[battery decision](../hardware/enclosure/battery-options.md).

## Reproducible electrical study

Run from the root:

```sh
python3 site/sample.py
node site/energy.mjs --check
node site/energy.mjs --reference
```

Godot and Node must be installed; missing tools fail. The sampler runs the real
shared functions for both native LED layouts, repeats each run byte-for-byte,
and retains all RGB/time channels as little-endian IEEE-754 float32 data under
`.build/energy-samples`. The manifest records native scene, pattern, sampler and
model hashes, `(group,index)` identities, sampling intervals, tool version and
convergence results. A changed source or sample fails the check. Each cycle is
[0,8), initially 512 then 1024 steps, with further interval halving until every
design/pattern's average input-power change is at most max(0.1%, 1 mW).

`energy.mjs` is the pure calculation shared by browser and CLI consumers.
`--evaluate` accepts JSON on stdin with `samples`, `groups` and `settings`; the
sampler's binary reader is in `sample_check.mjs`. `electrical-inputs.json` owns
the one-cell reference and explicitly unqualified study coefficients. It maps
raw channels to rounded 8-bit PWM after electrical brightness; optical shader
controls never enter the calculation. Idle demand remains at black. Non-LED
demand, converter quiescent input, constant efficiency, series loss and reserve
are counted separately. Series loss is solved at each sampled time before
averaging. Runtime is usable energy divided by average battery demand; zero
energy gives zero, while positive energy at zero demand returns a named
unbounded state with `hours: null`, never numeric infinity.

The study distinguishes sampled peaks from hardware limits. Its equal-channel
board approximation, unresolved strip stock, idle coefficients, radio/controller
duty, contact/converter losses and cutoff reserve are not qualified bounds.
These outputs must not become product predictions or lower protection ratings.
The Pages build remains blocked by the electrical gate. Physical behavior stays
unmeasured; no owner trial or human sign-off is a completion condition.

## Automated browser checks

```sh
npm ci --prefix site --ignore-scripts --no-fund
PLAYWRIGHT_BROWSERS_PATH="$PWD/.build/browser-cache" node site/node_modules/playwright/cli.js install --with-deps chromium
python3 site/sample.py
python3 site/verify.py study
```

The driver is Playwright 1.64.1 (Apache-2.0, Node >=20), pinned with integrity
hashes in `package-lock.json`. The [npm registry](https://registry.npmjs.org/playwright)
records its 2026-10-14 publication, meeting the seven-day age rule on
2026-10-31; installation reported zero advisories. Chromium is the matching
driver-managed version. The verifier selects the full Chromium new headless
runtime (`channel: 'chromium'`), including its media implementation; do not
install only the separate headless shell. See the
[Playwright browser documentation](https://playwright.dev/docs/browsers#chromium-new-headless-mode).
CI pins Godot 4.7.2 and the release asset SHA-256 from
the [official release](https://github.com/godotengine/godot-builds/releases/tag/4.7.2-stable).

The study creates a temporary localhost fixture from the actual calculator,
pattern data and three canonical MP4s. It checks 320 px/desktop layout, accessible
labels and keyboard operation, design/pattern/settings/reset, CLI agreement,
invalid/zero cases, stale responses/data, paired playback and buffering/error
recovery. A deliberately injected zero-demand model checks the unbounded state;
it does not assert that real hardware has zero demand. The server, contexts and
browser close on success or failure; a process lock prevents concurrent probes.
Missing tools and browsers fail. Study success is not complete-site acceptance.

After the electrical and native gates pass, `build.py` regenerates samples from
both checked scenes and seals their hashes with the artifact. Use:

```sh
python3 site/build.py --output .build/compass-pages
python3 site/verify.py local --directory .build/compass-pages
python3 site/verify.py live --url https://blinkystitt.github.io/smart-compass-v0/ --expected .build/compass-pages
```

The live command follows an authorized deployment; it compares the complete
reviewed provenance and every asset byte, then runs the same browser probes.
The workflow runs local verification before uploading and live verification
after deployment. At this checkpoint the electrical gate prevents reaching
either release check. The legacy cards/mass model still require the fitted
assembly migration before publication can be qualified.
