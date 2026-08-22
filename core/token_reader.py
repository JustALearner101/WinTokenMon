"""
Universal local AI token reader for Windows
Supports: Antigravity CLI, Claude Code, Cursor IDE, Codex CLI, GitHub Copilot CLI,
Koma, Aider, Windsurf (Cascade), Roo Code, and Cline (VS Code)
"""

import datetime
import glob
import json
import os
import re
import sqlite3
import threading
import time
from typing import Any

from .applog import log_once


def _read_varint(data: bytes, offset: int) -> tuple[int | None, int]:
    res = 0
    shift = 0
    while offset < len(data):
        b = data[offset]
        offset += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            return res, offset
        shift += 7
    return None, offset


def _walk_fields(data: bytes) -> list[tuple[int, int, Any]]:
    offset = 0
    fields = []
    while offset < len(data):
        key, offset = _read_varint(data, offset)
        if key is None:
            break
        field_num = key >> 3
        wire_type = key & 0x7
        if wire_type == 0:  # varint
            val, offset = _read_varint(data, offset)
            if val is None:
                break
            fields.append((field_num, 0, val))
        elif wire_type == 1:  # 64-bit
            offset += 8
        elif wire_type == 2:  # length-delimited
            length, offset = _read_varint(data, offset)
            if length is None or offset + length > len(data):
                break
            payload = data[offset : offset + length]
            offset += length
            fields.append((field_num, 2, payload))
        elif wire_type == 5:  # 32-bit
            offset += 4
        else:
            break
    return fields


def _parse_antigravity_blob(blob: bytes) -> dict | None:
    fields = _walk_fields(blob)
    chat_model = None
    for fnum, wtype, payload in fields:
        if fnum == 1 and wtype == 2:
            chat_model = payload
            break
    if not chat_model:
        return None

    cm_fields = _walk_fields(chat_model)
    usage = None
    created_at = None
    model_name = "unknown"
    for fnum, wtype, val in cm_fields:
        if fnum == 4 and wtype == 2:
            usage = val
        elif fnum == 9 and wtype == 2:  # start metadata
            start_fields = _walk_fields(val)
            for sf_num, sf_type, sf_val in start_fields:
                if sf_num == 4 and sf_type == 2:
                    ts_fields = _walk_fields(sf_val)
                    for tf_num, tf_type, tf_val in ts_fields:
                        if tf_num == 1 and tf_type == 0:
                            created_at = tf_val
        elif fnum == 19 and wtype == 2:
            try:
                model_name = val.decode("utf-8", errors="ignore")
            except Exception:
                pass

    if not usage:
        return None
    u_fields = _walk_fields(usage)
    tokens = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
    for fnum, wtype, val in u_fields:
        if fnum == 2 and wtype == 0:
            tokens["input"] = val if val <= 1_000_000_000 else 0
        elif fnum == 3 and wtype == 0:
            tokens["output"] = val if val <= 1_000_000_000 else 0
        elif fnum == 4 and wtype == 0:
            tokens["cache_write"] = val if val <= 1_000_000_000 else 0
        elif fnum == 5 and wtype == 0:
            tokens["cache_read"] = val if val <= 1_000_000_000 else 0
    return {"created_at": created_at, "model": model_name, "tokens": tokens}


def _parse_flexible_date(val: Any) -> float | None:
    """Parses ISO-8601 string, epoch seconds, or epoch milliseconds into timestamp float."""
    if not val:
        return None
    if isinstance(val, (int, float)):
        if val > 100_000_000_000:
            return float(val) / 1000.0
        return float(val)
    if isinstance(val, str):
        val_clean = val.strip()
        try:
            iso_str = val_clean.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(iso_str)
            return dt.timestamp()
        except Exception:
            pass
        try:
            num = float(val_clean)
            if num > 100_000_000_000:
                return num / 1000.0
            return num
        except Exception:
            pass
    return None


def _parse_token_number(val: str) -> int | None:
    """Parses '1,234', '5.4k', '2m' style token counts into plain integers."""
    val = val.strip().replace(",", "").lower()
    if not val:
        return None
    mult = 1
    if val.endswith("k"):
        mult, val = 1000, val[:-1]
    elif val.endswith("m"):
        mult, val = 1_000_000, val[:-1]
    try:
        return int(float(val) * mult)
    except Exception:
        return None


_AIDER_TOKENS_RE = re.compile(
    r"tokens?:\s*([\d.,]+\s*[km]?)\s*sent\s*,?\s*([\d.,]+\s*[km]?)\s*received",
    re.IGNORECASE,
)
_AIDER_FALLBACK_RE = re.compile(r"tokens?:\s*([\d.,]+[km]?)", re.IGNORECASE)


class TokenUsageSummary:
    def __init__(self):
        self.today_tokens: int = 0
        self.today_input: int = 0
        self.today_output: int = 0
        self.today_cache: int = 0
        self.rolling_5h_tokens: int = 0
        self.weekly_tokens: int = 0
        self.lifetime_tokens: int = 0
        self.by_source: dict[str, int] = {}
        self.by_source_today: dict[str, int] = {}
        self.last_scanned: float = time.time()


class WindowsTokenReader:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.appdata = os.environ.get("APPDATA", os.path.join(self.home, "AppData", "Roaming"))
        self.localappdata = os.environ.get(
            "LOCALAPPDATA", os.path.join(self.home, "AppData", "Local")
        )
        self.file_cache: dict[
            str, tuple[float, int, list[dict]]
        ] = {}  # path -> (mtime, size, entries)
        self._cache_lock = threading.Lock()
        self.last_total_tokens: int | None = None
        self.enabled_sources: set[str] | None = None  # None = all sources enabled

    def _cache_get(self, path: str) -> tuple[float, int, list[dict]] | None:
        with self._cache_lock:
            return self.file_cache.get(path)

    def _cache_set(self, path: str, value: tuple[float, int, list[dict]]):
        with self._cache_lock:
            self.file_cache[path] = value

    def scan_antigravity(self) -> list[dict]:
        entries = []
        pattern = os.path.join(self.home, ".gemini", "antigravity-cli", "conversations", "*.db")
        dbs = glob.glob(pattern)
        for db in dbs:
            try:
                st = os.stat(db)
                cached = self._cache_get(db)
                if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                    entries.extend(cached[2])
                    continue

                db_entries = []
                conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                c = conn.cursor()
                c.execute("SELECT idx, data FROM gen_metadata WHERE data IS NOT NULL")
                conv_id = os.path.splitext(os.path.basename(db))[0]
                for idx, blob in c.fetchall():
                    res = _parse_antigravity_blob(blob)
                    if res:
                        total = sum(res["tokens"].values())
                        if total > 0:
                            db_entries.append(
                                {
                                    "id": f"antigravity|{conv_id}|{idx}",
                                    "ts": res["created_at"] or st.st_mtime,
                                    "tokens": total,
                                    "input": res["tokens"]["input"],
                                    "output": res["tokens"]["output"],
                                    "cache": res["tokens"]["cache_read"]
                                    + res["tokens"]["cache_write"],
                                    "source": "antigravity",
                                }
                            )
                conn.close()
                self._cache_set(db, (st.st_mtime, st.st_size, db_entries))
                entries.extend(db_entries)
            except Exception as exc:
                log_once("scan.antigravity", f"{exc}")
        return entries

    def scan_claude(self) -> list[dict]:
        entries = []
        projects_dir = os.path.join(self.home, ".claude", "projects")
        if not os.path.exists(projects_dir):
            return entries

        jsonl_files = glob.glob(os.path.join(projects_dir, "**", "*.jsonl"), recursive=True)
        for path in jsonl_files:
            try:
                st = os.stat(path)
                cached = self._cache_get(path)
                if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                    entries.extend(cached[2])
                    continue

                if cached and st.st_size > cached[1]:
                    file_entries = list(cached[2])
                    seek_pos = cached[1]
                else:
                    file_entries = []
                    seek_pos = 0

                with open(path, encoding="utf-8", errors="ignore") as f:
                    if seek_pos > 0:
                        f.seek(seek_pos)
                    for line in f:
                        if not line.strip() or "usage" not in line or "assistant" not in line:
                            continue
                        try:
                            data = json.loads(line)
                            if data.get("type") != "assistant":
                                continue
                            msg = data.get("message", {})
                            usage = msg.get("usage", {})
                            if usage:
                                inp = usage.get("input_tokens", 0) or 0
                                out = usage.get("output_tokens", 0) or 0
                                cw = usage.get("cache_creation_input_tokens", 0) or 0
                                cr = usage.get("cache_read_input_tokens", 0) or 0
                                tot = inp + out + cw + cr
                                if tot > 0:
                                    msg_id = msg.get("id", "")
                                    req_id = data.get("requestId", "")
                                    entry_id = (
                                        f"claude|{msg_id}|{req_id}"
                                        if (msg_id or req_id)
                                        else f"claude|{path}|{time.time()}"
                                    )

                                    ts_str = data.get("timestamp")
                                    ts = _parse_flexible_date(ts_str) or st.st_mtime

                                    file_entries.append(
                                        {
                                            "id": entry_id,
                                            "ts": ts,
                                            "tokens": tot,
                                            "input": inp,
                                            "output": out,
                                            "cache": cw + cr,
                                            "source": "claude",
                                        }
                                    )
                        except Exception:
                            continue
                    final_pos = f.tell()

                self._cache_set(path, (st.st_mtime, final_pos, file_entries))
                entries.extend(file_entries)
            except Exception as exc:
                log_once("scan.claude", f"{exc}")
        return entries

    def scan_cursor(self) -> list[dict]:
        entries = []
        possible_roots = [
            os.path.join(self.appdata, "Cursor", "User", "globalStorage", "state.vscdb"),
            os.path.join(self.appdata, "Cursor Nightly", "User", "globalStorage", "state.vscdb"),
            os.path.join(self.appdata, "Cursor", "User", "workspaceStorage"),
        ]

        db_paths = []
        for r in possible_roots:
            if os.path.isfile(r):
                db_paths.append(r)
            elif os.path.isdir(r):
                db_paths.extend(glob.glob(os.path.join(r, "**", "state.vscdb"), recursive=True))

        for db in db_paths:
            try:
                st = os.stat(db)
                cached = self._cache_get(db)
                if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                    entries.extend(cached[2])
                    continue

                db_entries = []
                conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                c = conn.cursor()

                c.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='cursorDiskKV'"
                )
                if c.fetchone():
                    # 1. Parse bubbleId:* entries
                    c.execute("SELECT key, value FROM cursorDiskKV WHERE key GLOB 'bubbleId:*'")
                    for key, val in c.fetchall():
                        if isinstance(val, bytes):
                            val = val.decode("utf-8", errors="ignore")
                        try:
                            obj = json.loads(val)
                            tok_count = obj.get("tokenCount", {})
                            inp = tok_count.get("inputTokens", 0) or 0
                            out = tok_count.get("outputTokens", 0) or 0
                            tot = inp + out
                            if tot > 0:
                                dt = _parse_flexible_date(obj.get("createdAt")) or st.st_mtime
                                db_entries.append(
                                    {
                                        "id": f"cursor|{key}",
                                        "ts": dt,
                                        "tokens": tot,
                                        "input": inp,
                                        "output": out,
                                        "cache": 0,
                                        "source": "cursor",
                                    }
                                )
                        except Exception:
                            continue

                    # 2. Parse composerData:* entries
                    c.execute("SELECT key, value FROM cursorDiskKV WHERE key GLOB 'composerData:*'")
                    for key, val in c.fetchall():
                        if isinstance(val, bytes):
                            val = val.decode("utf-8", errors="ignore")
                        try:
                            obj = json.loads(val)
                            composer_ts = _parse_flexible_date(obj.get("createdAt")) or st.st_mtime
                            conv = obj.get("conversation", [])
                            for bubble in conv:
                                tok_count = bubble.get("tokenCount", {})
                                inp = tok_count.get("inputTokens", 0) or 0
                                out = tok_count.get("outputTokens", 0) or 0
                                tot = inp + out
                                if tot > 0:
                                    bubble_id = bubble.get("bubbleId") or f"{key}_{len(db_entries)}"
                                    bubble_ts = (
                                        _parse_flexible_date(bubble.get("createdAt")) or composer_ts
                                    )
                                    db_entries.append(
                                        {
                                            "id": f"cursor|bubble|{bubble_id}",
                                            "ts": bubble_ts,
                                            "tokens": tot,
                                            "input": inp,
                                            "output": out,
                                            "cache": 0,
                                            "source": "cursor",
                                        }
                                    )
                        except Exception:
                            continue

                conn.close()
                self._cache_set(db, (st.st_mtime, st.st_size, db_entries))
                entries.extend(db_entries)
            except Exception as exc:
                log_once("scan.cursor", f"{exc}")
        return entries

    def scan_codex(self) -> list[dict]:
        entries = []
        codex_dir = os.path.join(self.home, ".codex", "sessions")
        if not os.path.exists(codex_dir):
            return entries

        jsonl_files = glob.glob(os.path.join(codex_dir, "**", "rollout-*.jsonl"), recursive=True)
        for path in jsonl_files:
            try:
                st = os.stat(path)
                cached = self._cache_get(path)
                if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                    entries.extend(cached[2])
                    continue

                if cached and st.st_size > cached[1]:
                    file_entries = list(cached[2])
                    seek_pos = cached[1]
                else:
                    file_entries = []
                    seek_pos = 0

                filename = os.path.basename(path)
                turn = len(file_entries)
                with open(path, encoding="utf-8", errors="ignore") as f:
                    if seek_pos > 0:
                        f.seek(seek_pos)
                    for line in f:
                        if "token_count" not in line:
                            continue
                        try:
                            data = json.loads(line)
                            payload = data.get("payload", {}) or data.get("event_msg", {}).get(
                                "payload", {}
                            )
                            if payload.get("type") == "token_count":
                                info = payload.get("info", {})
                                last = info.get("last_token_usage", {})
                                if last:
                                    inp_total = last.get("input_tokens", 0) or 0
                                    cached_inp = last.get("cached_input_tokens", 0) or 0
                                    out = last.get("output_tokens", 0) or 0
                                    cw = last.get("cache_write_input_tokens", 0) or 0

                                    inp = max(0, inp_total - cached_inp)
                                    cr = cached_inp
                                    tot = inp + out + cw + cr
                                    if tot > 0:
                                        ts = (
                                            _parse_flexible_date(data.get("timestamp"))
                                            or st.st_mtime
                                        )
                                        file_entries.append(
                                            {
                                                "id": f"codex|{filename}|{turn}|{tot}",
                                                "ts": ts,
                                                "tokens": tot,
                                                "input": inp,
                                                "output": out,
                                                "cache": cw + cr,
                                                "source": "codex",
                                            }
                                        )
                                        turn += 1
                        except Exception:
                            continue
                    final_pos = f.tell()

                self._cache_set(path, (st.st_mtime, final_pos, file_entries))
                entries.extend(file_entries)
            except Exception as exc:
                log_once("scan.codex", f"{exc}")
        return entries

    def scan_copilot(self) -> list[dict]:
        entries = []
        copilot_db = os.path.join(self.home, ".copilot", "session-store.db")
        if not os.path.exists(copilot_db):
            return entries

        try:
            st = os.stat(copilot_db)
            cached = self._cache_get(copilot_db)
            if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                return cached[2]

            db_entries = []
            conn = sqlite3.connect(f"file:{copilot_db}?mode=ro", uri=True)
            c = conn.cursor()

            c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='assistant_usage_events'"
            )
            if c.fetchone():
                c.execute("""
                    SELECT id, model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, created_at
                    FROM assistant_usage_events
                """)
                for row_id, _model, in_tok, out_tok, cr, cw, created_at in c.fetchall():
                    in_tok = in_tok or 0
                    out_tok = out_tok or 0
                    cr = cr or 0
                    cw = cw or 0
                    actual_inp = max(0, in_tok - cr - cw)
                    tot = actual_inp + out_tok + cr + cw
                    if tot > 0:
                        ts = _parse_flexible_date(created_at) or st.st_mtime
                        db_entries.append(
                            {
                                "id": f"copilot|{row_id}",
                                "ts": ts,
                                "tokens": tot,
                                "input": actual_inp,
                                "output": out_tok,
                                "cache": cr + cw,
                                "source": "copilot",
                            }
                        )
            conn.close()
            self._cache_set(copilot_db, (st.st_mtime, st.st_size, db_entries))
            entries.extend(db_entries)
        except Exception as exc:
            log_once("scan.copilot", f"{exc}")
        return entries

    @staticmethod
    def _koma_usage(obj: dict) -> tuple[int, int, int]:
        """Extracts (input, output, cache) from a Koma usage object with key fallbacks."""
        inp = obj.get("input_tokens", 0) or obj.get("prompt_tokens", 0) or 0
        out = obj.get("output_tokens", 0) or obj.get("completion_tokens", 0) or 0
        cache = obj.get("cache_read_input_tokens", 0) or obj.get("cached_tokens", 0) or 0
        return inp, out, cache

    def _scan_koma_jsonl(self, path: str, st: os.stat_result, cached) -> list[dict]:
        """Incrementally parses new lines of a Koma .jsonl session log."""
        if cached and st.st_size > cached[1]:
            file_entries = list(cached[2])
            seek_pos = cached[1]
        else:
            file_entries = []
            seek_pos = 0

        filename = os.path.basename(path)
        turn = len(file_entries)
        with open(path, encoding="utf-8", errors="ignore") as f:
            if seek_pos > 0:
                f.seek(seek_pos)
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    usage = data.get("usage") or data.get("token_usage") or data
                    inp, out, cache = self._koma_usage(usage)
                    tot = inp + out + cache
                    if tot > 0:
                        ts = (
                            _parse_flexible_date(data.get("timestamp") or data.get("created_at"))
                            or st.st_mtime
                        )
                        file_entries.append(
                            {
                                "id": f"koma|{filename}|{turn}|{tot}",
                                "ts": ts,
                                "tokens": tot,
                                "input": inp,
                                "output": out,
                                "cache": cache,
                                "source": "koma",
                            }
                        )
                        turn += 1
                except Exception:
                    continue
            final_pos = f.tell()

        self._cache_set(path, (st.st_mtime, final_pos, file_entries))
        return file_entries

    def _scan_koma_json(self, path: str, st: os.stat_result) -> list[dict]:
        """Parses a single Koma .json session/ledger file."""
        file_entries = []
        filename = os.path.basename(path)
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                items = (
                    data
                    if isinstance(data, list)
                    else data.get("messages", [])
                    or data.get("turns", [])
                    or data.get("sessions", [])
                    or [data]
                )
                for idx, item in enumerate(items):
                    usage = (
                        item.get("usage")
                        or item.get("token_usage")
                        or item.get("stats", {})
                        or item
                    )
                    inp, out, cache = self._koma_usage(usage)
                    tot = inp + out + cache
                    if tot > 0:
                        ts = (
                            _parse_flexible_date(
                                item.get("timestamp")
                                or item.get("created_at")
                                or data.get("created_at")
                            )
                            or st.st_mtime
                        )
                        file_entries.append(
                            {
                                "id": f"koma|{filename}|{idx}|{tot}",
                                "ts": ts,
                                "tokens": tot,
                                "input": inp,
                                "output": out,
                                "cache": cache,
                                "source": "koma",
                            }
                        )
        except Exception as exc:
            log_once("scan.koma_json", f"{exc}")
        self._cache_set(path, (st.st_mtime, st.st_size, file_entries))
        return file_entries

    def scan_koma(self) -> list[dict]:
        """Scans Koma (aula-id/koma) AI agent sessions and token ledgers."""
        entries = []
        possible_dirs = [
            os.path.join(self.home, ".koma", "sessions"),
            os.path.join(self.home, ".koma", "ledger"),
            os.path.expandvars(r"%LOCALAPPDATA%\koma\sessions"),
            os.path.expandvars(r"%APPDATA%\koma\sessions"),
        ]

        for koma_dir in possible_dirs:
            if not os.path.exists(koma_dir):
                continue

            json_files = glob.glob(
                os.path.join(koma_dir, "**", "*.json"), recursive=True
            ) + glob.glob(os.path.join(koma_dir, "**", "*.jsonl"), recursive=True)

            for path in json_files:
                try:
                    st = os.stat(path)
                    cached = self._cache_get(path)
                    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                        entries.extend(cached[2])
                    elif path.endswith(".jsonl"):
                        entries.extend(self._scan_koma_jsonl(path, st, cached))
                    else:
                        entries.extend(self._scan_koma_json(path, st))
                except Exception:
                    pass
        return entries

    def scan_aider(self) -> list[dict]:
        """Scans Aider markdown chat history (~/.aider.chat.history.md) for token usage lines."""
        entries = []
        hist_path = os.path.join(self.home, ".aider.chat.history.md")
        if not os.path.exists(hist_path):
            return entries

        try:
            st = os.stat(hist_path)
            cached = self._cache_get(hist_path)
            if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                return cached[2]

            if cached and st.st_size > cached[1]:
                entries = list(cached[2])
                seek_pos = cached[1]
            else:
                entries = []
                seek_pos = 0

            ts = st.st_mtime
            turn = len(entries)
            with open(hist_path, encoding="utf-8", errors="ignore") as f:
                if seek_pos > 0:
                    f.seek(seek_pos)
                for line in f:
                    low = line.lower()
                    # Track session date headers for accurate timestamps
                    if "aider chat started at" in low or "aider v" in low and "started" in low:
                        date_str = line.split("at", 1)[1].strip() if " at " in low else ""
                        try:
                            dt = datetime.datetime.strptime(
                                date_str.split(".")[0].strip(), "%Y-%m-%d %H:%M:%S"
                            )
                            ts = dt.timestamp()
                        except Exception:
                            pass
                        continue

                    m = _AIDER_TOKENS_RE.search(low)
                    inp = out = None
                    if m:
                        inp = _parse_token_number(m.group(1))
                        out = _parse_token_number(m.group(2))
                    else:
                        fb = _AIDER_FALLBACK_RE.search(low)
                        if fb:
                            out = _parse_token_number(fb.group(1))
                    if not (inp or out):
                        continue
                    tot = (inp or 0) + (out or 0)
                    if tot > 0:
                        entries.append(
                            {
                                "id": f"aider|{hist_path}|{turn}|{tot}",
                                "ts": ts,
                                "tokens": tot,
                                "input": inp or 0,
                                "output": out or 0,
                                "cache": 0,
                                "source": "aider",
                            }
                        )
                        turn += 1
                final_pos = f.tell()

            self._cache_set(hist_path, (st.st_mtime, final_pos, entries))
        except Exception as exc:
            log_once("scan.aider", f"{exc}")
        return entries

    @staticmethod
    def _collect_usage_objects(obj: Any, found: list[tuple[int, int, int]]):
        """Recursively collects usage tuples (input, output, cache) from nested JSON blobs."""
        if isinstance(obj, dict):
            inp = (
                obj.get("inputTokens")
                or obj.get("input_tokens")
                or obj.get("promptTokens")
                or obj.get("prompt_tokens")
                or obj.get("tokensIn")
                or 0
            )
            out = (
                obj.get("outputTokens")
                or obj.get("output_tokens")
                or obj.get("completionTokens")
                or obj.get("completion_tokens")
                or obj.get("tokensOut")
                or 0
            )
            cache_fields = (
                obj.get("cacheReads"),
                obj.get("cache_read_input_tokens"),
                obj.get("cached_tokens"),
                obj.get("cacheReadInputTokens"),
                obj.get("cacheWrites"),
                obj.get("cache_creation_input_tokens"),
                obj.get("cacheWriteInputTokens"),
            )
            cache = sum(int(v or 0) for v in cache_fields if isinstance(v, (int, float)))
            if isinstance(inp, (int, float)) or isinstance(out, (int, float)):
                i, o, c = int(inp or 0), int(out or 0), cache
                if i + o + c > 0:
                    found.append((i, o, c))
            for v in obj.values():
                WindowsTokenReader._collect_usage_objects(v, found)
        elif isinstance(obj, list):
            for v in obj:
                WindowsTokenReader._collect_usage_objects(v, found)

    def _scan_vscdb(self, db: str, source: str) -> list[dict]:
        """Generic non-locking scanner for VS Code-style state.vscdb databases."""
        entries = []
        conv_id = os.path.basename(os.path.dirname(db))
        try:
            st = os.stat(db)
            cached = self._cache_get(db)
            if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                return cached[2]

            db_entries = []
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1)
            c = conn.cursor()
            c.execute("SELECT key, value FROM ItemTable")
            rows = c.fetchall()
            conn.close()

            for key, val in rows:
                if isinstance(val, bytes):
                    val = val.decode("utf-8", errors="ignore")
                try:
                    obj = json.loads(val)
                except Exception:
                    continue
                found: list[tuple[int, int, int]] = []
                self._collect_usage_objects(obj, found)
                for idx, (inp, out, cache) in enumerate(found):
                    tot = inp + out + cache
                    db_entries.append(
                        {
                            "id": f"{source}|{conv_id}|{key}|{idx}",
                            "ts": st.st_mtime,
                            "tokens": tot,
                            "input": inp,
                            "output": out,
                            "cache": cache,
                            "source": source,
                        }
                    )
            self._cache_set(db, (st.st_mtime, st.st_size, db_entries))
            entries.extend(db_entries)
        except Exception as exc:
            log_once("scan.vscdb", f"{exc}")
        return entries

    def scan_windsurf(self) -> list[dict]:
        """Scans Windsurf (Cascade) workspace storage SQLite DBs with a 24h mtime pre-filter."""
        entries = []
        ws_root = os.path.join(self.appdata, "Windsurf", "User", "workspaceStorage")
        if not os.path.isdir(ws_root):
            return entries

        now = time.time()
        for folder_name in os.listdir(ws_root):
            folder_path = os.path.join(ws_root, folder_name)
            db = os.path.join(folder_path, "state.vscdb")
            if not os.path.isfile(db):
                continue
            try:
                # Fast filter: skip project folders untouched in the last 24 hours
                if now - os.path.getmtime(folder_path) > 86400:
                    continue
            except Exception:
                continue
            entries.extend(self._scan_vscdb(db, "windsurf"))
        return entries

    def scan_cline_and_roo(self) -> list[dict]:
        """Scans Cline & Roo Code JSON session logs from VS Code globalStorage task folders."""
        entries = []
        roots = [
            (
                "cline",
                os.path.join(
                    self.appdata, "Code", "User", "globalStorage", "saoudrizwan.claude-dev"
                ),
            ),
            (
                "roo",
                os.path.join(
                    self.appdata, "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline"
                ),
            ),
            (
                "cline",
                os.path.join(
                    self.appdata,
                    "Code - Insiders",
                    "User",
                    "globalStorage",
                    "saoudrizwan.claude-dev",
                ),
            ),
            (
                "roo",
                os.path.join(
                    self.appdata,
                    "Code - Insiders",
                    "User",
                    "globalStorage",
                    "rooveterinaryinc.roo-cline",
                ),
            ),
        ]
        for source, root in roots:
            tasks_dir = os.path.join(root, "tasks")
            if not os.path.isdir(tasks_dir):
                continue

            json_files = glob.glob(os.path.join(tasks_dir, "**", "*.json"), recursive=True)
            for path in json_files:
                basename = os.path.basename(path).lower()
                # Only parse conversation histories; skip checkpoints/metadata noise
                if "api_conversation_history" not in basename and "ui_messages" not in basename:
                    continue
                try:
                    st = os.stat(path)
                    cached = self._cache_get(path)
                    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                        entries.extend(cached[2])
                        continue

                    file_entries = []
                    # Task folder names are epoch-milliseconds timestamps
                    base_ts = st.st_mtime
                    try:
                        base_ts = float(os.path.basename(os.path.dirname(path))) / 1000.0
                    except Exception:
                        pass

                    with open(path, encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)

                    items = data if isinstance(data, list) else [data]
                    found: list[tuple[int, int, int]] = []
                    self._collect_usage_objects(items, found)
                    for idx, (inp, out, cache) in enumerate(found):
                        tot = inp + out + cache
                        file_entries.append(
                            {
                                "id": f"{source}|{path}|{idx}",
                                "ts": base_ts,
                                "tokens": tot,
                                "input": inp,
                                "output": out,
                                "cache": cache,
                                "source": source,
                            }
                        )
                    self._cache_set(path, (st.st_mtime, st.st_size, file_entries))
                    entries.extend(file_entries)
                except Exception as exc:
                    log_once("scan.cline_roo", f"{exc}")
        return entries

    def get_summary(self) -> tuple[TokenUsageSummary, int]:
        """Returns current TokenUsageSummary across all AI tools and delta_tokens burned since last sweep."""
        enabled = self.enabled_sources

        def _on(src: str) -> bool:
            return enabled is None or src in enabled

        raw_entries: list[dict] = []
        if _on("antigravity"):
            raw_entries += self.scan_antigravity()
        if _on("claude"):
            raw_entries += self.scan_claude()
        if _on("cursor"):
            raw_entries += self.scan_cursor()
        if _on("codex"):
            raw_entries += self.scan_codex()
        if _on("copilot"):
            raw_entries += self.scan_copilot()
        if _on("koma"):
            raw_entries += self.scan_koma()
        if _on("aider"):
            raw_entries += self.scan_aider()
        if _on("windsurf"):
            raw_entries += self.scan_windsurf()
        if _on("cline") or _on("roo"):
            cline_roo = self.scan_cline_and_roo()
            if enabled is not None:
                cline_roo = [e for e in cline_roo if e["source"] in enabled]
            raw_entries += cline_roo

        dedup_map: dict[str, dict] = {}
        for e in raw_entries:
            eid = e.get("id") or f"{e['source']}_{e['ts']}_{e['tokens']}"
            if eid not in dedup_map or e["tokens"] > dedup_map[eid]["tokens"]:
                dedup_map[eid] = e

        all_entries = list(dedup_map.values())
        summary = TokenUsageSummary()

        now = time.time()
        today_start = datetime.datetime.combine(
            datetime.date.today(), datetime.time.min
        ).timestamp()
        five_hours_ago = now - (5 * 3600)
        seven_days_ago = now - (7 * 86400)

        total_lifetime = 0
        by_source: dict[str, int] = {}

        for e in all_entries:
            ts = e["ts"]
            tok = e["tokens"]
            src = e.get("source", "other")
            total_lifetime += tok
            by_source[src] = by_source.get(src, 0) + tok

            if ts >= today_start:
                summary.today_tokens += tok
                summary.today_input += e["input"]
                summary.today_output += e["output"]
                summary.today_cache += e["cache"]
                summary.by_source_today[src] = summary.by_source_today.get(src, 0) + tok

            if ts >= five_hours_ago:
                summary.rolling_5h_tokens += tok

            if ts >= seven_days_ago:
                summary.weekly_tokens += tok

        summary.lifetime_tokens = total_lifetime
        summary.by_source = by_source

        delta = 0
        if self.last_total_tokens is not None:
            if total_lifetime > self.last_total_tokens:
                delta = total_lifetime - self.last_total_tokens
        else:
            delta = 0  # First initialization
        self.last_total_tokens = total_lifetime

        # Prune cache entries for deleted files; cap size to keep memory bounded
        with self._cache_lock:
            if len(self.file_cache) > 256:
                missing = [p for p in self.file_cache if not os.path.exists(p)]
                for p in missing:
                    del self.file_cache[p]
                while len(self.file_cache) > 512:
                    self.file_cache.pop(next(iter(self.file_cache)))

        return summary, delta
