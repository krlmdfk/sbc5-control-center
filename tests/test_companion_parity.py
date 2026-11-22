"""Offline regression tests for companion parity CI."""
import contextlib
import importlib.util
import io
import os
import pathlib
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "companion_parity", pathlib.Path(__file__).resolve().parents[1]
    / "scripts" / "check_companion_parity.py",
)
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)
URL = "https://api.github.com/repos/example/project"


def http_error(code, headers=None, reason="error"):
    return urllib.error.HTTPError(URL, code, reason, headers or {}, io.BytesIO())


class ApiTests(unittest.TestCase):
    def test_authenticated(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}), patch.object(
            parity.urllib.request, "urlopen", return_value=io.BytesIO(b'{}')
        ) as opened:
            self.assertEqual(parity.request_json(URL), {})
            self.assertEqual(opened.call_args.args[0].get_header("Authorization"), "Bearer test-token")

    def test_anonymous(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}), patch.object(
            parity.urllib.request, "urlopen", return_value=io.BytesIO(b'{}')
        ) as opened:
            parity.request_json(URL)
            self.assertIsNone(opened.call_args.args[0].get_header("Authorization"))

    def test_retry(self):
        with patch.object(parity.urllib.request, "urlopen", side_effect=[
            http_error(403, {"Retry-After": "3"}, "rate limit"),
            http_error(503),
            io.BytesIO(b'{}'),
        ]), patch.object(parity.time, "sleep") as sleep:
            self.assertEqual(parity.request_json(URL), {})
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [3, 4])

    def test_permanent_403(self):
        with patch.object(parity.urllib.request, "urlopen", side_effect=http_error(403)) as opened, patch.object(parity.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.HTTPError):
                parity.request_json(URL)
            self.assertEqual(opened.call_count, 1)
            sleep.assert_not_called()

    def test_long_limit(self):
        with patch.object(parity.urllib.request, "urlopen", side_effect=http_error(429, {"Retry-After": "3600"})) as opened, patch.object(parity.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.HTTPError):
                parity.request_json(URL)
            self.assertEqual(opened.call_count, 1)
            sleep.assert_not_called()

    def test_network_exhaustion(self):
        with patch.object(parity.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")) as opened, patch.object(parity.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.URLError):
                parity.request_json(URL)
            self.assertEqual(opened.call_count, parity.MAX_ATTEMPTS)
            self.assertEqual(sleep.call_count, parity.MAX_ATTEMPTS - 1)


class StatusTests(unittest.TestCase):
    def test_status_and_exit_code(self):
        for status, findings, failure in (
            ("PASS", [], None),
            ("DRIFT", ["different content"], None),
            ("INCOMPLETE", None, RuntimeError("API unavailable")),
        ):
            for advisory in (False, True):
                with self.subTest(status=status, advisory=advisory), tempfile.TemporaryDirectory() as tmp:
                    summary = pathlib.Path(tmp) / "summary.md"
                    args = ["check_companion_parity.py", "--role", "hacs"]
                    if advisory:
                        args.append("--advisory")
                    output = io.StringIO()
                    with patch.object(parity.sys, "argv", args), patch.object(
                        parity, "audit", return_value=findings, side_effect=failure
                    ), patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}), contextlib.redirect_stdout(output):
                        self.assertEqual(parity.main(), int(status != "PASS" and not advisory))
                    self.assertIn("Companion parity " + status, output.getvalue())
                    self.assertIn("Status: " + status, summary.read_text())


if __name__ == "__main__":
    unittest.main()
