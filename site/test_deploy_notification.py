"""Exercise the workflow's notification code without contacting ntfy."""
from contextlib import nullcontext, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pages.yml"
SCRIPT = compile(
    textwrap.dedent(WORKFLOW.read_text().split("python3 - <<'PY'\n", 1)[1])
    .rsplit("\nPY", 1)[0],
    str(WORKFLOW),
    "exec",
)


class DeploymentNotificationTests(unittest.TestCase):
    def setUp(self):
        self.environment = {
            "NTFY_URL": "https://ntfy.example.test",
            "NTFY_TOPIC": "deploy",
            "NTFY_TOKEN": "private-test-token",
            "DEPLOYMENT_URL": "https://example.test/smart-compass/",
            "GITHUB_SERVER_URL": "https://github.example.test",
            "GITHUB_REPOSITORY": "owner/smart-compass-v0",
            "GITHUB_SHA": "a" * 40,
            "GITHUB_RUN_ID": "1234",
            "GITHUB_RUN_ATTEMPT": "2",
        }

    def run_notification(self, *, error=None, status=200, missing=None, summary_error=None):
        environment = dict(self.environment)
        if missing:
            environment[missing] = "  "
        opener = MagicMock()
        opener.open.side_effect = error
        opener.open.return_value.__enter__.return_value.status = status
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory) / "summary.md"
            environment["GITHUB_STEP_SUMMARY"] = str(summary)
            with (
                patch.dict(os.environ, environment, clear=True),
                patch("urllib.request.build_opener", return_value=opener) as factory,
                redirect_stdout(output),
                patch.object(Path, "open", side_effect=summary_error)
                if summary_error else nullcontext(),
            ):
                # No SystemExit or exception: failures must preserve deployment success.
                exec(SCRIPT, {})
            summary_text = summary.read_text() if summary.exists() else ""
        return opener, factory, output.getvalue(), summary_text

    def assert_sanitized_failure(self, output, summary):
        self.assertIn("::warning::ntfy:", output)
        self.assertIn("## Deployment notification", summary)
        self.assertNotIn("Sent:", summary)
        for value in self.environment.values():
            self.assertNotIn(value, output + summary)
        self.assertNotIn("sensitive response body", output + summary)

    def test_success_posts_one_authenticated_json_request_with_all_links(self):
        opener, _, output, summary = self.run_notification()
        opener.open.assert_called_once()
        request = opener.open.call_args.args[0]
        self.assertEqual(opener.open.call_args.kwargs, {"timeout": 15})
        self.assertEqual(request.full_url, self.environment["NTFY_URL"])
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(request.get_header("Authorization"), "Bearer private-test-token")
        base = "https://github.example.test/owner/smart-compass-v0"
        self.assertEqual(json.loads(request.data), {
            "topic": "deploy",
            "title": "Smart Compass deployed",
            "priority": 3,
            "tags": ["white_check_mark"],
            "click": self.environment["DEPLOYMENT_URL"],
            "message": (
                "owner/smart-compass-v0 deployed successfully.\n"
                f"Commit: {base}/commit/{'a' * 40}\n"
                "Website: https://example.test/smart-compass/\n"
                f"Workflow: {base}/actions/runs/1234/attempts/2"
            ),
        })
        self.assertEqual(output, "")
        self.assertIn("Sent: deployment notification accepted by ntfy.", summary)
        self.assertNotIn(self.environment["NTFY_TOKEN"], summary)

    def test_missing_configuration_warns_without_making_a_request(self):
        for key in ("NTFY_URL", "NTFY_TOPIC", "NTFY_TOKEN", "DEPLOYMENT_URL"):
            with self.subTest(key=key):
                opener, _, output, summary = self.run_notification(missing=key)
                opener.open.assert_not_called()
                self.assert_sanitized_failure(output, summary)
                self.assertIn("configuration is missing", summary)

    def test_http_errors_warn_without_retrying_or_exposing_response_details(self):
        for status in (302, 401, 429, 500):
            with self.subTest(status=status):
                error = HTTPError(
                    self.environment["NTFY_URL"], status,
                    "private-test-token: sensitive response body", {}, None,
                )
                opener, _, output, summary = self.run_notification(error=error)
                opener.open.assert_called_once()
                self.assert_sanitized_failure(output, summary)
                self.assertIn("HTTP error", summary)

    def test_transport_timeout_and_invalid_configuration_are_nonfatal(self):
        for error in (
            URLError("private-test-token: sensitive response body"),
            TimeoutError("private-test-token"),
            ValueError("private-test-token"),
        ):
            with self.subTest(error=type(error).__name__):
                opener, _, output, summary = self.run_notification(error=error)
                opener.open.assert_called_once()
                self.assert_sanitized_failure(output, summary)
                self.assertIn("configuration or transport error", summary)

    def test_non_success_status_is_not_reported_as_sent(self):
        opener, _, output, summary = self.run_notification(status=503)
        opener.open.assert_called_once()
        self.assert_sanitized_failure(output, summary)

    def test_summary_write_failure_is_nonfatal_and_does_not_retry_delivery(self):
        opener, _, output, summary = self.run_notification(
            summary_error=PermissionError("private-test-token: sensitive response body"),
        )
        opener.open.assert_called_once()
        self.assertEqual(summary, "")
        self.assertEqual(
            output,
            "::warning::ntfy: Could not write the notification job summary.\n",
        )

    def test_redirects_are_disabled_to_keep_one_request_and_protect_credentials(self):
        _, factory, _, _ = self.run_notification()
        handler = factory.call_args.args[0]
        self.assertIsNone(handler.redirect_request(
            None, None, 302, "Found", {}, "https://another.example.test",
        ))
