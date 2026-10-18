import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import deploy_notification


class NotificationTests(unittest.TestCase):
    def jobs(self, build="success", deploy="success", url="https://compass.example/"):
        return {
            "build": {"result": build},
            "deploy": {"result": deploy, "outputs": {"page_url": url}},
        }

    def message(self, jobs, latest="current"):
        return deploy_notification.notification(
            jobs, "current", latest, "owner/compass", "https://github.com/run/1"
        )

    def test_success_links_to_deployed_site(self):
        message = self.message(self.jobs())
        self.assertEqual(message["title"], "Smart compass deployed")
        self.assertEqual(message["click"], "https://compass.example/")
        self.assertIn("Website: https://compass.example/", message["message"])
        self.assertIn("https://github.com/owner/compass/commit/current", message["message"])

    def test_build_and_deploy_failures_link_to_workflow(self):
        for jobs, failed in (
            (self.jobs(build="failure", deploy="skipped", url=""), "build"),
            (self.jobs(deploy="failure", url=""), "deploy"),
        ):
            with self.subTest(failed=failed):
                message = self.message(jobs)
                self.assertEqual(message["priority"], 4)
                self.assertEqual(message["click"], "https://github.com/run/1")
                self.assertIn("Site: not deployed", message["message"])
                self.assertIn("Failed jobs: " + failed, message["message"])

    def test_skips_cancelled_skipped_and_superseded_failures(self):
        for jobs in (
            self.jobs(deploy="cancelled"),
            self.jobs(build="cancelled", deploy="skipped"),
            self.jobs(deploy="skipped", url=""),
            self.jobs(url=""),
        ):
            with self.subTest(jobs=jobs):
                self.assertIsNone(self.message(jobs))
        self.assertIsNone(self.message(self.jobs(deploy="failure"), latest="newer"))
        self.assertIsNotNone(self.message(self.jobs(), latest="newer"))

    def test_authenticated_delivery_and_visible_failure(self):
        for outcome in ("accepted", "network failure", "missing configuration"):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as folder:
                summary = Path(folder) / "summary"
                env = {
                    "JOB_RESULTS": json.dumps(self.jobs()),
                    "GITHUB_SHA": "current",
                    "LATEST_SHA": "current",
                    "GITHUB_REPOSITORY": "owner/compass",
                    "GITHUB_SERVER_URL": "https://github.com",
                    "GITHUB_RUN_ID": "1",
                    "GITHUB_RUN_ATTEMPT": "2",
                    "GITHUB_STEP_SUMMARY": str(summary),
                    "NTFY_URL": "https://fixture.example",
                    "NTFY_TOPIC": "deploy",
                    "NTFY_TOKEN": "synthetic",
                }
                if outcome == "missing configuration":
                    env["NTFY_TOKEN"] = ""
                send = MagicMock(return_value=MagicMock())
                if outcome == "network failure":
                    send.side_effect = OSError("private detail")
                output = io.StringIO()
                with patch.dict(os.environ, env), patch.object(
                    deploy_notification.urllib.request, "urlopen", send
                ), contextlib.redirect_stdout(output):
                    deploy_notification.main()
                if outcome == "missing configuration":
                    send.assert_not_called()
                else:
                    request = send.call_args.args[0]
                    self.assertEqual(send.call_args.kwargs["timeout"], 15)
                    self.assertEqual(request.get_header("Authorization"), "Bearer synthetic")
                    self.assertEqual(json.loads(request.data)["topic"], "deploy")
                if outcome == "accepted":
                    self.assertEqual(summary.read_text(), "Deployment notification accepted by ntfy.\n")
                else:
                    self.assertIn("Deployment notification failed", summary.read_text())
                self.assertNotIn("synthetic", output.getvalue())
                self.assertNotIn("private detail", output.getvalue())
