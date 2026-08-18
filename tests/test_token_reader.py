"""
Unit tests for multi-provider token reader, parsers, and caching logic.
"""

import json
import os
import sqlite3
import tempfile
import time
import unittest

from core.token_reader import TokenUsageSummary, WindowsTokenReader, _read_varint, _walk_fields


class TestTokenReader(unittest.TestCase):
    def test_token_usage_summary_totals(self):
        """Tests TokenUsageSummary fields and properties."""
        summary = TokenUsageSummary()
        summary.today_input = 1000
        summary.today_output = 500
        summary.today_cache = 200
        summary.today_tokens = 1700
        summary.rolling_5h_tokens = 1700
        summary.weekly_tokens = 5000
        summary.lifetime_tokens = 20000

        self.assertEqual(summary.today_tokens, 1700)
        self.assertEqual(summary.rolling_5h_tokens, 1700)
        self.assertEqual(summary.lifetime_tokens, 20000)

    def test_varint_and_protobuf_decoder(self):
        """Tests low-level Protobuf varint decoding used in Antigravity reader."""
        # Test varint for 300 (0xAC 0x02)
        val, offset = _read_varint(b"\xac\x02", 0)
        self.assertEqual(val, 300)
        self.assertEqual(offset, 2)

        # Construct synthetic protobuf with field 2 (varint=50), field 3 (varint=25)
        # Field 2 tag: (2 << 3) | 0 = 0x10. Value 50 = 0x32
        # Field 3 tag: (3 << 3) | 0 = 0x18. Value 25 = 0x19
        proto_bytes = b"\x10\x32\x18\x19"
        fields = _walk_fields(proto_bytes)
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0], (2, 0, 50))
        self.assertEqual(fields[1], (3, 0, 25))

    def test_claude_jsonl_parser(self):
        """Tests Claude Code JSONL log parsing with synthetic records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = os.path.join(tmpdir, ".claude", "projects", "my_project")
            os.makedirs(claude_dir, exist_ok=True)
            log_file = os.path.join(claude_dir, "session.jsonl")

            records = [
                {
                    "type": "assistant",
                    "timestamp": time.time(),
                    "message": {
                        "id": "msg_1",
                        "usage": {
                            "input_tokens": 1500,
                            "output_tokens": 300,
                            "cache_creation_input_tokens": 100,
                        },
                    },
                },
                {
                    "type": "assistant",
                    "timestamp": time.time() - 3600,
                    "message": {
                        "id": "msg_2",
                        "usage": {
                            "input_tokens": 2000,
                            "output_tokens": 400,
                            "cache_read_input_tokens": 50,
                        },
                    },
                },
            ]
            with open(log_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")

            reader = WindowsTokenReader()
            reader.home = tmpdir
            records_parsed = reader.scan_claude()
            self.assertEqual(len(records_parsed), 2)
            self.assertEqual(records_parsed[0]["input"], 1500)
            self.assertEqual(records_parsed[0]["output"], 300)
            self.assertEqual(records_parsed[1]["input"], 2000)

    def test_codex_jsonl_parser(self):
        """Tests Codex CLI rollout JSONL parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = os.path.join(tmpdir, ".codex", "sessions", "session_1")
            os.makedirs(session_dir, exist_ok=True)
            log_file = os.path.join(session_dir, "rollout-test.jsonl")

            records = [
                {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "last_token_usage": {
                                "input_tokens": 5000,
                                "output_tokens": 1200,
                                "cached_input_tokens": 800,
                            }
                        },
                    },
                }
            ]
            with open(log_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")

            reader = WindowsTokenReader()
            reader.home = tmpdir
            parsed = reader.scan_codex()
            self.assertEqual(len(parsed), 1)
            self.assertEqual(
                parsed[0]["tokens"], 6200
            )  # (5000-800 fresh input) + 1200 out + 800 cache = 6200
            self.assertEqual(parsed[0]["output"], 1200)

    def test_cursor_sqlite_parser(self):
        """Tests Cursor IDE state.vscdb parsing with synthetic cursorDiskKV table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cursor_dir = os.path.join(tmpdir, "Cursor", "User", "globalStorage")
            os.makedirs(cursor_dir, exist_ok=True)
            db_path = os.path.join(cursor_dir, "state.vscdb")

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("CREATE TABLE cursorDiskKV (key TEXT PRIMARY KEY, value TEXT)")

            # Insert synthetic bubble conversation with token usage
            bubble_val = json.dumps({"tokenCount": {"inputTokens": 4500, "outputTokens": 800}})
            cur.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", ("bubbleId:12345", bubble_val))
            conn.commit()
            conn.close()

            reader = WindowsTokenReader()
            reader.appdata = tmpdir
            parsed = reader.scan_cursor()
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["input"], 4500)
            self.assertEqual(parsed[0]["output"], 800)
            self.assertEqual(parsed[0]["tokens"], 5300)

    def test_koma_json_and_jsonl_parsers(self):
        """Tests Koma (aula-id/koma) session JSON and JSONL token parser."""
        with tempfile.TemporaryDirectory() as tmpdir:
            koma_sessions_dir = os.path.join(tmpdir, ".koma", "sessions")
            os.makedirs(koma_sessions_dir, exist_ok=True)

            # 1. Standard JSON session
            session_json = os.path.join(koma_sessions_dir, "session-1.json")
            data_json = {
                "id": "koma-sess-001",
                "created_at": time.time(),
                "turns": [
                    {
                        "turn": 1,
                        "usage": {
                            "input_tokens": 1200,
                            "output_tokens": 350,
                            "cache_read_input_tokens": 100,
                        },
                    },
                    {
                        "turn": 2,
                        "usage": {
                            "input_tokens": 2400,
                            "output_tokens": 500,
                            "cache_read_input_tokens": 200,
                        },
                    },
                ],
            }
            with open(session_json, "w", encoding="utf-8") as f:
                json.dump(data_json, f)

            # 2. JSONL ledger
            koma_ledger_dir = os.path.join(tmpdir, ".koma", "ledger")
            os.makedirs(koma_ledger_dir, exist_ok=True)
            ledger_jsonl = os.path.join(koma_ledger_dir, "daily_ledger.jsonl")
            with open(ledger_jsonl, "w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "timestamp": time.time(),
                            "usage": {
                                "input_tokens": 5000,
                                "output_tokens": 1000,
                                "cached_tokens": 500,
                            },
                        }
                    )
                    + "\n"
                )

            reader = WindowsTokenReader()
            reader.home = tmpdir
            parsed = reader.scan_koma()

            self.assertEqual(len(parsed), 3)
            # Verify sources
            for entry in parsed:
                self.assertEqual(entry["source"], "koma")

            # Verify total tokens across parsed records
            total_koma_tokens = sum(e["tokens"] for e in parsed)
            # (1200 + 350 + 100) + (2400 + 500 + 200) + (5000 + 1000 + 500) = 1650 + 3100 + 6500 = 11250
            self.assertEqual(total_koma_tokens, 11250)


if __name__ == "__main__":
    unittest.main()
