# Serial narrow prototype acceptance. Wide exports remain an archived reference.
# A failed gate stops dependent publication. Native generation runs once.
# These commands are mandatory: absent implementations/apps are errors.
validate:
    python3 -m unittest discover -s hardware/enclosure -p 'test_*.py' -v
    python3 designs/stacked/run.py test
    python3 hardware/enclosure/electrical.py check
    just cad cad-check print-check demo-check
    python3 -m unittest discover -s site -p 'test_*.py' -v
    python3 site/sample.py
    node site/energy.mjs --check
    python3 site/build.py --output .build/compass-pages
    python3 site/verify.py local --directory .build/compass-pages
