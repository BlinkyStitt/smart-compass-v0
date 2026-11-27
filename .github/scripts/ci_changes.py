"""Keep PR path filtering below the workflow so its required gate always reports."""

import json
import os
import re
import urllib.request


def path_match(path, pattern):
    """Match the supported GitHub path syntax; reject unknown syntax safely."""
    expression = ""
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if pattern[index : index + 2] == "**":
                index += 2
                if index < len(pattern) and pattern[index] == "/":
                    expression += "(?:.*/)?"
                    index += 1
                else:
                    expression += ".*"
                continue
            expression += "[^/]*"
        elif char == "?":
            expression += "[^/]"
        elif char in "[]{}+\\":
            raise ValueError("Unsupported path syntax: " + pattern)
        else:
            expression += re.escape(char)
        index += 1
    return re.fullmatch(expression, path) is not None


def matches(path, patterns):
    selected = False
    for pattern in patterns:
        negative = pattern.startswith("!")
        if path_match(path, pattern[1:] if negative else pattern):
            selected = not negative
    return selected


def needs_validation(files, includes, ignores):
    if includes and ignores:
        raise ValueError("Use either include paths or ignored paths")
    for entry in files:
        paths = [entry["filename"]]
        if entry.get("previous_filename"):
            paths.append(entry["previous_filename"])
        for path in paths:
            if path.startswith(".github/"):
                return True
            if includes and matches(path, includes):
                return True
            if not includes and not matches(path, ignores):
                return True
    return False


def changed_files(api, repo, number, count, token, opener=urllib.request.urlopen):
    result = []
    for page in range(1, 31):
        request = urllib.request.Request(
            api
            + "/repos/"
            + repo
            + "/pulls/"
            + str(number)
            + "/files?per_page=100&page="
            + str(page),
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
            },
        )
        with opener(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("Unexpected changed-file response")
        result.extend(batch)
        if len(batch) < 100:
            break
    if len(result) != count:
        raise ValueError("The changed-file list is incomplete")
    return result


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as stream:
        event = json.load(stream)
    run = True
    if os.environ["GITHUB_EVENT_NAME"] == "pull_request":
        count = event["pull_request"]["changed_files"]
        if count < 3000:
            files = changed_files(
                os.environ["GITHUB_API_URL"],
                os.environ["GITHUB_REPOSITORY"],
                event["number"],
                count,
                os.environ["GH_TOKEN"],
            )
            run = needs_validation(
                files,
                json.loads(os.environ["CI_INCLUDE_PATHS"]),
                json.loads(os.environ["CI_IGNORE_PATHS"]),
            )
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
        stream.write("run_validation=" + str(run).lower() + "\n")


if __name__ == "__main__":
    main()
