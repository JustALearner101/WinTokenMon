"""
Universal local AI token reader for Windows
Supports: Antigravity CLI, Claude Code, Cursor IDE, Codex CLI, GitHub Copilot CLI
"""

import datetime
import glob
import json
import os
import sqlite3
import time
from typing import Any


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
        self.last_total_tokens: int | None = None

    def scan_antigravity(self) -> list[dict]:
        entries = []
        pattern = os.path.join(self.home, ".gemini", "antigravity-cli", "conversations", "*.db")
        dbs = glob.glob(pattern)
        for db in dbs:
            try:
                st = os.stat(db)
                cached = self.file_cache.get(db)
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
                self.file_cache[db] = (st.st_mtime, st.st_size, db_entries)
                entries.extend(db_entries)
            except Exception:
                pass
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
                cached = self.file_cache.get(path)
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

                self.file_cache[path] = (st.st_mtime, final_pos, file_entries)
                entries.extend(file_entries)
            except Exception:
                pass
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
                cached = self.file_cache.get(db)
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
                self.file_cache[db] = (st.st_mtime, st.st_size, db_entries)
                entries.extend(db_entries)
            except Exception:
                pass
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
                cached = self.file_cache.get(path)
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

                self.file_cache[path] = (st.st_mtime, final_pos, file_entries)
                entries.extend(file_entries)
            except Exception:
                pass
        return entries

    def scan_copilot(self) -> list[dict]:
        entries = []
        copilot_db = os.path.join(self.home, ".copilot", "session-store.db")
        if not os.path.exists(copilot_db):
            return entries

        try:
            st = os.stat(copilot_db)
            cached = self.file_cache.get(copilot_db)
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
            self.file_cache[copilot_db] = (st.st_mtime, st.st_size, db_entries)
            entries.extend(db_entries)
        except Exception:
            pass
        return entries

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

            json_files = glob.glob(os.path.join(koma_dir, "**", "*.json"), recursive=True) + glob.glob(
                os.path.join(koma_dir, "**", "*.jsonl"), recursive=True
            )

            for path in json_files:
                try:
                    st = os.stat(path)
                    cached = self.file_cache.get(path)
                    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
                        entries.extend(cached[2])
                        continue

                    file_entries = []
                    filename = os.path.basename(path)

                    if path.endswith(".jsonl"):
                        if cached and st.st_size > cached[1]:
                            file_entries = list(cached[2])
                            seek_pos = cached[1]
                        else:
                            file_entries = []
                            seek_pos = 0

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
                                    in_tok = (
                                        usage.get("input_tokens", 0)
                                        or usage.get("prompt_tokens", 0)
                                        or 0
                                    )
                                    out_tok = (
                                        usage.get("output_tokens", 0)
                                        or usage.get("completion_tokens", 0)
                                        or 0
                                    )
                                    cache_tok = (
                                        usage.get("cache_read_input_tokens", 0)
                                        or usage.get("cached_tokens", 0)
                                        or 0
                                    )
                                    tot = in_tok + out_tok + cache_tok
                                    if tot > 0:
                                        ts = (
                                            _parse_flexible_date(
                                                data.get("timestamp") or data.get("created_at")
                                            )
                                            or st.st_mtime
                                        )
                                        file_entries.append(
                                            {
                                                "id": f"koma|{filename}|{turn}|{tot}",
                                                "ts": ts,
                                                "tokens": tot,
                                                "input": in_tok,
                                                "output": out_tok,
                                                "cache": cache_tok,
                                                "source": "koma",
                                            }
                                        )
                                        turn += 1
                                except Exception:
                                    continue
                            final_pos = f.tell()

                        self.file_cache[path] = (st.st_mtime, final_pos, file_entries)
                        entries.extend(file_entries)
                    else:
                        # Standard JSON
                        with open(path, encoding="utf-8", errors="ignore") as f:
                            try:
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
                                    in_tok = (
                                        usage.get("input_tokens", 0)
                                        or usage.get("prompt_tokens", 0)
                                        or 0
                                    )
                                    out_tok = (
                                        usage.get("output_tokens", 0)
                                        or usage.get("completion_tokens", 0)
                                        or 0
                                    )
                                    cache_tok = (
                                        usage.get("cache_read_input_tokens", 0)
                                        or usage.get("cached_tokens", 0)
                                        or 0
                                    )
                                    tot = in_tok + out_tok + cache_tok
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
                                                "input": in_tok,
                                                "output": out_tok,
                                                "cache": cache_tok,
                                                "source": "koma",
                                            }
                                        )
                            except Exception:
                                pass
                        self.file_cache[path] = (st.st_mtime, st.st_size, file_entries)
                        entries.extend(file_entries)
                except Exception:
                    pass
        return entries

    def get_summary(self) -> tuple[TokenUsageSummary, int]:
        """Returns current TokenUsageSummary across all AI tools and delta_tokens burned since last sweep."""
        raw_entries = (
            self.scan_antigravity()
            + self.scan_claude()
            + self.scan_cursor()
            + self.scan_codex()
            + self.scan_copilot()
            + self.scan_koma()
        )

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

        return summary, delta
