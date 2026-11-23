"""Source identity for the Rev A fit, print package, and site download."""

import hashlib
import io
import json
import math
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
CARRIER = ROOT / "designs/carrier"
BASELINE = ROOT / "designs/stacked/exports"
ARCHIVE_NAME = "rev-a-print.zip"
MANIFEST_NAME = "package-manifest.json"
FIT_SAMPLES = {
    "FitBatterySeatPositive": "BatteryCradle",
    "FitBatterySeatNegative": "BatteryCradle",
    "FitUSBPort": "RearCover",
}


def digest(path):
    data = path.read_bytes()
    if data.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        raise ValueError(f"Materialize the Git LFS file before packaging: {path}")
    return hashlib.sha256(data).hexdigest()


def fit_inputs():
    """Check the native inputs and the exports consumed by the carrier."""
    manifest = json.loads((BASELINE.parent / "exports-manifest.json").read_text())
    retained = ("stacked-fibonacci.FCStd", "parts.json", "loom-check.json", "EGLStencil.stl",
                "InnerDiffuser.stl", "SideDiffuser.stl")
    exports = [(BASELINE / name).relative_to(ROOT).as_posix() for name in retained]
    expected = {
        name: value for name, value in manifest["inputs"].items()
        if name.startswith(("hardware/enclosure/", "designs/stacked/"))
    }
    expected.update({name: manifest["exports"][name] for name in exports})
    for name, value in expected.items():
        if digest(ROOT / name) != value:
            raise ValueError(f"Rev A baseline differs from its native manifest: {name}")
    for path in sorted(CARRIER.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".json", ".kicad_pcb", ".kicad_sch", ".kicad_mod", ".FCMacro", ".md"}:
            if not path.name.startswith("test_") and path.name != "print_package.py":
                expected[path.relative_to(ROOT).as_posix()] = digest(path)
    return expected


def package_inputs():
    return {**fit_inputs(), "designs/carrier/print_package.py": digest(CARRIER / "print_package.py")}


def verify_archive(data):
    """Require the complete, current kit before publishing it."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest = json.loads(archive.read(MANIFEST_NAME))
        if manifest["revision"] != "Rev A" or manifest["inputs"] != package_inputs():
            raise ValueError("Rev A print archive is stale. Rebuild the fit and print package.")
        files = manifest["files"]
        if sorted(archive.namelist()) != sorted([*files, MANIFEST_NAME]):
            raise ValueError("Rev A print archive file list differs from its manifest")
        for name, expected in files.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError(f"Rev A print archive checksum differs: {name}")
        from layout import PRINT_PARTS

        inventory = json.loads(archive.read("parts.json"))
        sliced = json.loads(archive.read("slicer-check.json"))
        fit = json.loads(archive.read("routed-fit.json"))
        if fit.get("inputs") != fit_inputs():
            raise ValueError("Rev A fit report has stale inputs")
        parts = inventory["print_parts"]
        samples = inventory["fit_samples"]
        if (len(parts) != len(PRINT_PARTS)
                or {row["file"]: row["source_part"] for row in parts}
                != {name + ".stl": name for name in PRINT_PARTS}
                or inventory["stl_files"] != [row["file"] for row in parts]):
            raise ValueError("Rev A archive must contain all 12 installed print parts")
        if (len(samples) != len(FIT_SAMPLES)
                or {row["file"]: row["source_part"] for row in samples}
                != {name + ".stl": parent for name, parent in FIT_SAMPLES.items()}):
            raise ValueError("Rev A archive must contain all three interface test pieces")
        projects = {}
        for row in parts + samples:
            if hashlib.sha256(archive.read(row["file"])).hexdigest() != row["sha256"]:
                raise ValueError("Rev A STL differs from its inventory: " + row["file"])
            materials = ("glow", "silver") if row["source_part"] in {"InnerDiffuser", "SideDiffuser"} else ("opaque-petg",)
            for material in materials:
                name = Path(row["file"]).stem + ("-silver" if material == "silver" else "") + ".3mf"
                projects[name] = (material, row["sha256"])
        rows = sliced["projects"]
        if len(rows) != len(projects) or {row["project"] for row in rows} != set(projects):
            raise ValueError("Rev A archive must contain all 17 sliced projects")
        for row in rows:
            if (row["material"], row["source_stl_sha256"]) != projects[row["project"]]:
                raise ValueError("Rev A slicer material or source differs: " + row["project"])
            if not math.isfinite(row["toolpath_mass_g"]) or row["toolpath_mass_g"] <= 0:
                raise ValueError("Rev A sliced filament mass must be positive and finite")
        expected = {row["file"] for row in parts + samples} | set(projects) | {
            "parts.json", "slicer-check.json", "routed-fit.json", "README.md",
        }
        if set(files) != expected:
            raise ValueError("Rev A archive must contain exactly its declared print files and guides")
        return inventory, sliced
