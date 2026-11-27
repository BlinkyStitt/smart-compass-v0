"""Fail closed when expected PR validation fails, disappears, or skips."""

import json
import os


def verify(needs, expected):
    if set(needs) != set(expected) | {"ci_changes"}:
        raise ValueError("Expected validation jobs are missing or changed")
    changes = needs["ci_changes"]
    if changes["result"] != "success":
        raise ValueError("Changed-file validation did not succeed")
    flag = changes.get("outputs", {}).get("run_validation")
    if flag not in ("true", "false"):
        raise ValueError("Changed-file validation did not report a decision")
    required = "success" if flag == "true" else "skipped"
    for name in expected:
        if needs[name]["result"] != required:
            raise ValueError(name + ": " + needs[name]["result"])


if __name__ == "__main__":
    verify(
        json.loads(os.environ["CI_GATE_NEEDS"]),
        json.loads(os.environ["CI_EXPECTED_JOBS"]),
    )
