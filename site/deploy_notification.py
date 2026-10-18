"""Send one best-effort ntfy result after the Pages workflow finishes."""

import json
import os
import urllib.request


def notification(needs, commit, latest, repository, run_url):
    results = {name: job["result"] for name, job in needs.items()}
    if "cancelled" in results.values():
        return None
    deploy = needs["deploy"]
    url = deploy.get("outputs", {}).get("page_url", "")
    deployed = deploy["result"] == "success" and bool(url)
    if not deployed and commit != latest:
        return None
    failed = [name for name, result in results.items() if result == "failure"]
    if not failed and not deployed:
        return None
    lines = [
        "Site: " + ("deployed" if deployed else "not deployed"),
        f"Commit: https://github.com/{repository}/commit/{commit}",
    ]
    if deployed:
        lines.append(f"Website: {url}")
    if failed:
        lines.append("Failed jobs: " + ", ".join(failed))
    lines.append(f"Workflow: {run_url}")
    return {
        "title": "Smart compass validation/deployment failed" if failed else "Smart compass deployed",
        "message": "\n".join(lines),
        "priority": 4 if failed else 3,
        "tags": ["x" if failed else "white_check_mark"],
        "click": run_url if failed else url,
    }


def main():
    env = os.environ
    message = notification(
        json.loads(env["JOB_RESULTS"]),
        env["GITHUB_SHA"],
        env["LATEST_SHA"],
        env["GITHUB_REPOSITORY"],
        f"{env['GITHUB_SERVER_URL']}/{env['GITHUB_REPOSITORY']}/actions/runs/"
        f"{env['GITHUB_RUN_ID']}/attempts/{env['GITHUB_RUN_ATTEMPT']}",
    )
    if message is None:
        print("No deployment notification for this attempt.")
        return
    try:
        if not all(env.get(key) for key in ("NTFY_URL", "NTFY_TOPIC", "NTFY_TOKEN")):
            raise ValueError("Notification configuration is missing")
        message["topic"] = env["NTFY_TOPIC"]
        request = urllib.request.Request(
            env["NTFY_URL"],
            data=json.dumps(message).encode(),
            headers={
                "Authorization": f"Bearer {env['NTFY_TOKEN']}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=15):
            pass
        summary = "Deployment notification accepted by ntfy."
    except (OSError, ValueError):
        # Keep URLs, credentials, request bodies and response bodies out of logs.
        summary = "Deployment notification failed; deployment results are unchanged."
        print(f"::warning::{summary}")
    with open(env["GITHUB_STEP_SUMMARY"], "a") as stream:
        stream.write(summary + "\n")


if __name__ == "__main__":
    main()
