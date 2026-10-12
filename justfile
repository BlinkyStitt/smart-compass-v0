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

# Enable the tracked commit hook in this checkout.
install-hooks:
    git config --local core.hooksPath .githooks
