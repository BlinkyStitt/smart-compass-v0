#!/usr/bin/env bash
set -euo pipefail

carrier=$(cd -- "$(dirname -- "$0")" && pwd)
reports=${1:?Supply a writable report directory}
mkdir -p "$reports"
cli=${KICAD_CLI:-kicad-cli}
kicad_python=${KICAD_PYTHON:-python3}

"$cli" pcb drc --refill-zones --severity-all --exit-code-violations \
  -o "$reports/carrier-a-drc.rpt" "$carrier/carrier-a.kicad_pcb"
for name in charger usb-pigtail usb-pd60 led-power; do
  board="$carrier/wall-power/$name"
  "$cli" pcb drc --refill-zones --severity-all --exit-code-violations --schematic-parity \
    -o "$reports/$name-drc.rpt" "$board.kicad_pcb"
  "$cli" sch export netlist --format kicadxml -o "$reports/$name.xml" "$board.kicad_sch"
  "$kicad_python" "$carrier/wall-power/verify_netlist.py" "$board.kicad_pcb" "$reports/$name.xml"
done
