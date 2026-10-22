# Keep generated work beside this checkout, including CAD, Godot and slicer scratch.
export TMPDIR := justfile_directory() + "/.."

default:
    @just --list

# Rebuild the model, geometry exports, images and animations; check all results.
cad:
    python3 hardware/enclosure/cad.py build

# Check that the saved model, build sources and every export match.
cad-check:
    python3 hardware/enclosure/cad.py check

# Run the host geometry and build-workflow tests without FreeCAD.
cad-tests:
    python3 -m unittest discover -s hardware/enclosure -p 'test_*.py' -v

# Slice the exact delivered 3MF projects and verify their effective settings.
print-check:
    python3 hardware/enclosure/slicing.py

# Verify canonical assets, then launch the interactive optical preview.
demo:
    python3 demo/run.py launch

# Check runtime GLB import, controls, LED metadata and Metal ray optics.
demo-check:
    python3 demo/run.py check

# Measure the actual 1280 x 720 scene on this machine.
demo-benchmark:
    python3 demo/run.py benchmark

# Enable the tracked commit hook in this checkout.
install-hooks:
    git config --local core.hooksPath .githooks
    git lfs install --local

# Verify both generated designs and their runtime presentation checks.
validate:
    just cad-check
    just demo-check
    python3 designs/stacked/run.py check
    python3 designs/stacked/run.py preview-check
