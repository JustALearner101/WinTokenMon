"""
Unit tests for v0.4.0 extended AI scanners (Aider, Windsurf, Roo Code, Cline)
and the Compact HUD velocity calculation.
"""

import json
import os
import sqlite3
import tempfile
import time
import unittest

from core.token_reader import WindowsTokenReader, _parse_token_number


class TestAiderParser(unittest.TestCase):
    def test_aider_markdown_parser(self):
        """Tests Aider markdown history parsing with structured token lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_path = os.path.join(tmpdir, ".aider.chat.history.md")
            with open(hist_path, "w", encoding="utf-8") as f:
                f.write("# aider chat started at 2026-08-22 10:00:00\n\n")
                f.write("#### user\nfix the bug\n\n")
                f.write("> Tokens: 5.4k sent, 345 received.\n\n")
                f.write("#### user\nadd tests\n\n")
                f.write("> Tokens: 1,200 sent, 89 received.\n")

            reader = WindowsTokenReader()
            reader.home = tmpdir
            parsed = reader.scan_aider()

            self.assertEqual(len(parsed), 2)
            self.assertEqual(parsed[0]["input"], 5400)  # k-suffix expanded
            self.assertEqual(parsed[0]["output"], 345)
            self.assertEqual(parsed[0]["tokens"], 5745)
            self.assertEqual(parsed[0]["source"], "aider")
            self.assertEqual(parsed[1]["input"], 1200)
            self.assertEqual(parsed[1]["output"], 89)

    def test_aider_fallback_regex(self):
        """Tests tolerant fallback for unknown 'Tokens: N' markdown formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_path = os.path.join(tmpdir, ".aider.chat.history.md")
            with open(hist_path, "w", encoding="utf-8") as f:
                f.write("some future format line\n")
                f.write("Tokens: 9999 total\n")

            reader = WindowsTokenReader()
            reader.home = tmpdir
            parsed = reader.scan_aider()

            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["tokens"], 9999)

    def test_aider_incremental_cache(self):
        """Tests appended lines are picked up incrementally without re-parsing old data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hist_path = os.path.join(tmpdir, ".aider.chat.history.md")
            with open(hist_path, "w", encoding="utf-8") as f:
                f.write("> Tokens: 100 sent, 50 received.\n")

            reader = WindowsTokenReader()
            reader.home = tmpdir
            first = reader.scan_aider()
            self.assertEqual(len(first), 1)

            time.sleep(0.02)
            with open(hist_path, "a", encoding="utf-8") as f:
                f.write("> Tokens: 200 sent, 60 received.\n")

            second = reader.scan_aider()
            self.assertEqual(len(second), 2)


class TestWindsurfParser(unittest.TestCase):
    def test_windsurf_sqlite_ro_query(self):
        """Tests Windsurf state.vscdb mode=ro query returns tokens without lock errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_dir = os.path.join(tmpdir, "Windsurf", "User", "workspaceStorage", "workspace-abc")
            os.makedirs(ws_dir, exist_ok=True)
            db_path = os.path.join(ws_dir, "state.vscdb")

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
            cascade_val = json.dumps(
                {
                    "tabs": [
                        {
                            "messages": [
                                {"tokenUsage": {"inputTokens": 3000, "outputTokens": 700}},
                                {"tokenUsage": {"inputTokens": 1500, "outputTokens": 250}},
                            ]
                        }
                    ]
                }
            )
            cur.execute(
                "INSERT INTO ItemTable VALUES (?, ?)",
                ("workbench.panel.aichat.view.aichat.chatdata", cascade_val),
            )
            conn.commit()
            conn.close()

            reader = WindowsTokenReader()
            reader.appdata = tmpdir
            parsed = reader.scan_windsurf()

            self.assertEqual(len(parsed), 2)
            self.assertTrue(all(e["source"] == "windsurf" for e in parsed))
            self.assertEqual(sum(e["tokens"] for e in parsed), 5450)

    def test_windsurf_stale_workspace_skipped(self):
        """Tests that workspace folders untouched for >24h are skipped by mtime filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_dir = os.path.join(tmpdir, "Windsurf", "User", "workspaceStorage", "old-workspace")
            db_dir = os.path.join(ws_dir)
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(ws_dir, "state.vscdb")

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
            cur.execute(
                "INSERT INTO ItemTable VALUES (?, ?)",
                ("chat", json.dumps({"inputTokens": 500})),
            )
            conn.commit()
            conn.close()

            # Backdate folder mtime to 3 days ago
            stale_ts = time.time() - (3 * 86400)
            os.utime(ws_dir, (stale_ts, stale_ts))

            reader = WindowsTokenReader()
            reader.appdata = tmpdir
            parsed = reader.scan_windsurf()
            self.assertEqual(len(parsed), 0)


class TestClineRooParsers(unittest.TestCase):
    def _make_task_fixture(self, root: str) -> str:
        tasks_dir = os.path.join(root, "tasks", "1755849600000")
        os.makedirs(tasks_dir, exist_ok=True)
        history = [
            {
                "role": "assistant",
                "usage": {
                    "input_tokens": 4200,
                    "output_tokens": 600,
                    "cache_creation_input_tokens": 150,
                    "cache_read_input_tokens": 900,
                },
            },
            {
                "role": "assistant",
                "usage": {"input_tokens": 2100, "output_tokens": 400},
            },
        ]
        with open(os.path.join(tasks_dir, "api_conversation_history.json"), "w") as f:
            json.dump(history, f)
        return tasks_dir

    def test_cline_json_log_parser(self):
        """Tests Cline task JSON token accumulation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cline_root = os.path.join(
                tmpdir, "Code", "User", "globalStorage", "saoudrizwan.claude-dev"
            )
            self._make_task_fixture(cline_root)

            reader = WindowsTokenReader()
            reader.appdata = tmpdir
            parsed = [e for e in reader.scan_cline_and_roo() if e["source"] == "cline"]

            self.assertEqual(len(parsed), 2)
            self.assertEqual(sum(e["tokens"] for e in parsed), 8350)

    def test_roo_json_log_parser(self):
        """Tests Roo Code task JSON token accumulation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            roo_root = os.path.join(
                tmpdir,
                "Code - Insiders",
                "User",
                "globalStorage",
                "rooveterinaryinc.roo-cline",
            )
            self._make_task_fixture(roo_root)

            reader = WindowsTokenReader()
            reader.appdata = tmpdir
            parsed = [e for e in reader.scan_cline_and_roo() if e["source"] == "roo"]

            self.assertEqual(len(parsed), 2)
            # (4200 + 600 + 150 + 900) + (2100 + 400) = 5850 + 2500
            self.assertEqual(sum(e["tokens"] for e in parsed), 8350)

    def test_enabled_sources_filter(self):
        """Tests get_summary respects enabled_sources provider toggles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cline_root = os.path.join(
                tmpdir, "Code", "User", "globalStorage", "saoudrizwan.claude-dev"
            )
            self._make_task_fixture(cline_root)

            reader = WindowsTokenReader()
            reader.home = tmpdir
            reader.appdata = tmpdir
            reader.enabled_sources = {"aider"}  # Everything else disabled
            summary, _delta = reader.get_summary()
            self.assertEqual(summary.lifetime_tokens, 0)

            reader.enabled_sources = {"cline"}
            summary, _delta = reader.get_summary()
            self.assertEqual(summary.lifetime_tokens, 8350)


class TestVelocityCalculation(unittest.TestCase):
    def test_parse_token_number(self):
        """Tests k/m suffix and comma handling in token number parser."""
        self.assertEqual(_parse_token_number("5.4k"), 5400)
        self.assertEqual(_parse_token_number("1,234"), 1234)
        self.assertEqual(_parse_token_number("2m"), 2_000_000)
        self.assertEqual(_parse_token_number("42"), 42)
        self.assertIsNone(_parse_token_number(""))
        self.assertIsNone(_parse_token_number("garbage"))

    def test_velocity_math(self):
        """Tests rolling-window tokens/min velocity math used by the Compact HUD."""
        samples = [
            (time.time() - 120, 1_000_000),
            (time.time() - 60, 1_000_000),
            (time.time(), 1_100_000),
        ]
        oldest_ts, oldest_tok = samples[0]
        now = time.time()
        elapsed_min = (now - oldest_ts) / 60.0
        velocity = max(0, samples[-1][1] - oldest_tok) / elapsed_min

        # 100k delta over ~2 minutes ≈ ~50k/min (allow timing slop)
        self.assertGreater(velocity, 30_000)
        self.assertLess(velocity, 80_000)


if __name__ == "__main__":
    unittest.main()
