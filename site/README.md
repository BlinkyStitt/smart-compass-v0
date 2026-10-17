# Smart compass on GitHub Pages

The site compares the canonical wide and narrow rainbow MP4s, explains the
hardware, and shows native CAD size and assembly images. It uses plain HTML,
CSS and JavaScript. The build needs Python 3.9+, Git LFS, FFmpeg and FFprobe.

```sh
python3 site/build.py --output /path/to/compass-pages
python3 -m http.server 8080 --bind 127.0.0.1 --directory /path/to/compass-pages
```

Rebuild changed enclosure outputs with their owning commands before building
the site. `build.py` checks each MP4's dimensions, duration and decoding. It also
checks spatial rainbow rotation on the board and outside ring in the four
rainbow clips. It rejects missing LFS media. Asset
filenames include their content hash so revised clips cannot reuse stale URLs.
The front comparison uses the 250 mm wide and 200 mm narrow native CAD renders
at the same scale, with dimension lines.

The `GitHub Pages` workflow builds on pull requests, and deploys on pushes to
`master` or a manual run from `master`. Repository Pages must use GitHub Actions
as its source. The build fetches only the LFS media needed by the site.

Both primary videos loop. Play both aligns their times, Pause both stops paired
playback, and Restart together resets both to frame zero. Individual video
controls and direct MP4 links remain available. Visitors who request reduced
motion start with paused videos.

The silver PETG comparison stays collapsed by default. It uses the same paired
player as the primary comparison, with separate Play/Pause/Restart controls.
Opening it starts both silver clips unless reduced motion is enabled. Closing
it pauses both clips. At 620 CSS pixels and below, both comparisons show the
full-width Wide video, then the full-width Narrow video. The Wide description
and Narrow description stack below both videos. Wider layouts use two columns
for the videos and descriptions.

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
useful brightness at that cap remains unverified. The design target is four hours.
