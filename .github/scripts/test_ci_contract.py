import io
import json
import unittest

from ci_changes import changed_files, needs_validation, path_match
from ci_gate import verify


class CIContractTests(unittest.TestCase):
    def test_path_boundaries(self):
        for path in ("a.py", "src/a.py", "src/nested/a.py"):
            self.assertTrue(path_match(path, "**/*.py"))
        self.assertFalse(path_match("src/a.py", "*.py"))
        self.assertTrue(path_match("tests/a/b", "tests/**"))
        self.assertFalse(path_match("tests2/a", "tests/**"))
        self.assertFalse(path_match("src/a.rs", "**/*.py"))

    def test_filter_decisions(self):
        includes = ["**/*.py", "tests/**", "requirements*.txt"]
        self.assertTrue(needs_validation([{"filename": "main.py"}], includes, []))
        self.assertFalse(needs_validation([{"filename": "README.md"}], includes, []))
        self.assertTrue(
            needs_validation([{"filename": ".github/scripts/ci_gate.py"}], includes, [])
        )
        self.assertTrue(
            needs_validation(
                [{"filename": "old.txt", "previous_filename": "main.py"}], includes, []
            )
        )
        self.assertFalse(needs_validation([{"filename": "docs/a.md"}], [], ["docs/**"]))
        self.assertTrue(needs_validation([{"filename": "src/a.rs"}], [], ["docs/**"]))
        self.assertFalse(
            needs_validation(
                [{"filename": "src/private/a.py"}], ["**/*.py", "!src/private/**"], []
            )
        )
        self.assertTrue(
            needs_validation(
                [{"filename": "src/private/keep.py"}],
                ["**/*.py", "!src/private/**", "src/private/keep.py"],
                [],
            )
        )

    def test_unsupported_pattern_fails_closed(self):
        with self.assertRaises(ValueError):
            path_match("file.py", "*.{py,rs}")

    def test_file_pagination(self):
        pages = [[{"filename": str(n)} for n in range(100)], [{"filename": "last.py"}]]
        calls = []

        def opener(request, timeout):
            calls.append(request.full_url)
            return io.StringIO(json.dumps(pages.pop(0)))

        result = changed_files(
            "https://api.github.com", "owner/repo", 2, 101, "token", opener
        )
        self.assertEqual(len(result), 101)
        self.assertTrue(calls[1].endswith("page=2"))

    def test_incomplete_file_list_fails_closed(self):
        def opener(request, timeout):
            return io.StringIO("[]")

        with self.assertRaises(ValueError):
            changed_files("https://api.github.com", "owner/repo", 2, 1, "token", opener)

    def test_gate_success_and_expected_skip(self):
        for flag, result in [("true", "success"), ("false", "skipped")]:
            verify(
                {
                    "ci_changes": {
                        "result": "success",
                        "outputs": {"run_validation": flag},
                    },
                    "build": {"result": result},
                },
                ["build"],
            )

    def test_gate_rejects_failure_cancellation_and_unexpected_skip(self):
        for flag, results in [
            ("true", ["failure", "cancelled", "skipped"]),
            ("false", ["failure", "cancelled", "success"]),
        ]:
            for result in results:
                with self.assertRaises(ValueError):
                    verify(
                        {
                            "ci_changes": {
                                "result": "success",
                                "outputs": {"run_validation": flag},
                            },
                            "build": {"result": result},
                        },
                        ["build"],
                    )

    def test_gate_rejects_missing_jobs_and_decisions(self):
        for needs in [
            {},
            {"ci_changes": {"result": "success"}},
            {"ci_changes": {"result": "failure"}, "build": {"result": "success"}},
            {
                "ci_changes": {"result": "success", "outputs": {"run_validation": ""}},
                "build": {"result": "success"},
            },
        ]:
            with self.assertRaises(ValueError):
                verify(needs, ["build"])


if __name__ == "__main__":
    unittest.main()
