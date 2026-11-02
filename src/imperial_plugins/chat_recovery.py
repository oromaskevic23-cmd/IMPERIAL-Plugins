"""IMPERIAL Chat History Recovery — 10 offline NCA search specializations.

Founding Architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
Original implementation contributors: see Git history and AUTHORS.md.

Only an explicitly supplied ChatGPT export is read. This module does NOT have
API access to ChatGPT chats, memories, account, Val Town or private documents.
Search agents are ten deterministic role-based search passes, NOT 10 LLMs.
SQLite stores REDACTED excerpts in a local non-encrypted file. No network.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_EXPORT_BYTES = 80 * 1024 * 1024
MAX_MESSAGE_CHARS = 12000
MAX_MESSAGES = 250000
MAX_RESULTS = 30
SCHEMA = "imperial.plugins.chat-recovery.v1"
AGENTS = (
    ("NCA-REC-01", "architecture", ("архитект", "architecture", "federation", "федерац", "core")),
    ("NCA-REC-02", "modules", ("модул", "module", "репозитор", "repository", "component")),
    ("NCA-REC-03", "documents", ("документ", "document", "readme", "spec", "файл")),
    ("NCA-REC-04", "decisions", ("решен", "decision", "утверж", "approve", "канон")),
    ("NCA-REC-05", "timeline", ("дата", "date", "checkpoint", "история", "timeline")),
    ("NCA-REC-06", "orchestration", ("hanter", "astra", "orion", "nca", "оркестрат")),
    ("NCA-REC-07", "providers", ("val town", "val.run", "supabase", "server", "сервер")),
    ("NCA-REC-08", "security", ("guardian", "passport", "audit", "zero trust", "cyber")),
    ("NCA-REC-09", "engineering", ("constructor", "velion", "сборк", "test", "commit")),
    ("NCA-REC-10", "recovery", ("восстанов", "recover", "ошиб", "резерв", "backup")),
)
_REDACT = (
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"
                r".*?-----END (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----",
                re.I | re.S), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?<![A-Za-z0-9_])(?:sk-(?:proj-|test-|live-)?[A-Za-z0-9_-]{15,}|"
                r"github_pat_[A-Za-z0-9_]{40,}|gh[pousr]_[A-Za-z0-9]{30,}|"
                r"xox[baprs]-[A-Za-z0-9-]{15,}|AKIA[0-9A-Z]{16})(?![A-Za-z0-9_])"),
     "[REDACTED_CREDENTIAL]"),
    (re.compile(r"(?<!\d)\d{8,12}:[A-Za-z0-9_-]{30,}(?![A-Za-z0-9_-])"),
     "[REDACTED_BOT_TOKEN]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
     "[REDACTED_JWT]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "[REDACTED_EMAIL]"),
)
_TIME_RE = re.compile(r"^\d{4}-\d\d-\d\d$")
_VALID_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,150}$")
_VAL_TOWN = re.compile(r"\bval[\s-]*town\b|\bval\.run\b", re.I)


class RecoveryError(ValueError):
    """Fail-closed invalid export, query, source or index."""


def _check_input(source: Path) -> bytes:
    if source.is_symlink() or not source.is_file():
        raise RecoveryError("SOURCE_NOT_A_REGULAR_FILE")
    info = source.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_EXPORT_BYTES:
        raise RecoveryError("EXPORT_SIZE_DENIED")
    with source.open("rb") as f:
        content = f.read(MAX_EXPORT_BYTES + 1)
    if len(content) != info.st_size:
        raise RecoveryError("EXPORT_MUTATED_OR_TOO_LARGE")
    return content


def _safe_id(value: Any) -> str | None:
    return value if isinstance(value, str) and _VALID_ID.fullmatch(value) else None


def _time(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not 0 < value < 4102444800:
        return None
    return int(value)


def _redact(value: str) -> str:
    for pattern, substitute in _REDACT:
        value = pattern.sub(substitute, value)
    return value


def _text(node: dict) -> str:
    msg = node.get("message")
    if not isinstance(msg, dict):
        return ""
    author = msg.get("author")
    if not isinstance(author, dict) or author.get("role") not in ("user", "assistant"):
        return ""
    content = msg.get("content")
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts", [])
    if not isinstance(parts, list):
        return ""
    # Non-text images, binary and tool data are intentionally NOT indexed.
    return "\n".join(p for p in parts if isinstance(p, str))[:MAX_MESSAGE_CHARS]


def _active_nodes(convo: dict) -> set[str] | None:
    mapping = convo.get("mapping")
    current = convo.get("current_node")
    if not isinstance(mapping, dict) or not isinstance(current, str) or current not in mapping:
        return None  # Unknown active branch, explicitly reported.
    visited: set[str] = set()
    while current and current not in visited:
        visited.add(current)
        node = mapping.get(current)
        if not isinstance(node, dict):
            break
        parent = node.get("parent")
        current = parent if isinstance(parent, str) and parent in mapping else ""
    return visited


def _date_limit(date_string: str) -> int:
    if not isinstance(date_string, str) or not _TIME_RE.fullmatch(date_string):
        raise RecoveryError("EXPLICIT_UTC_DATE_REQUIRED")
    try:
        return int(datetime.fromisoformat(date_string).replace(
            tzinfo=timezone.utc).timestamp())
    except ValueError as exc:
        raise RecoveryError("INVALID_DATE") from exc


def _open_db(target: Path) -> sqlite3.Connection:
    if target.exists() or target.is_symlink():
        raise RecoveryError("INDEX_ALREADY_EXISTS_REFUSE_OVERWRITE")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise RecoveryError("INDEX_PARENT_UNSAFE")
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    return sqlite3.connect(str(target))


def build_index(source: str | Path, index: str | Path) -> dict:
    """Build a private REDACTED SQLite FTS5 index from a user-provided export.

    No credential import, network, cloud sync or automatic access to other chats.
    """
    raw = _check_input(Path(source))
    try:
        conversations = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise RecoveryError("INVALID_CHATGPT_EXPORT_JSON") from exc
    if not isinstance(conversations, list):
        raise RecoveryError("EXPECTED_CONVERSATIONS_ARRAY")
    conn = _open_db(Path(index))
    count, unknown_branches, redacted_count = 0, 0, 0
    try:
        conn.execute("""CREATE TABLE messages (
            rowid INTEGER PRIMARY KEY, conversation_id TEXT NOT NULL,
            message_id TEXT NOT NULL, title TEXT NOT NULL,
            role TEXT NOT NULL, created_at INTEGER NOT NULL,
            branch_status TEXT NOT NULL, content TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            UNIQUE(conversation_id,message_id))""")
        conn.execute("CREATE VIRTUAL TABLE messages_fts USING fts5(title,content,tokenize='unicode61')")
        conn.execute("CREATE INDEX messages_time ON messages(created_at)")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        for convo in conversations:
            if not isinstance(convo, dict):
                continue
            cid = _safe_id(convo.get("id"))
            mapping = convo.get("mapping")
            if cid is None or not isinstance(mapping, dict):
                continue
            title = _redact(str(convo.get("title") or "Untitled"))[:300]
            active = _active_nodes(convo)
            if active is None:
                unknown_branches += 1
            fallback_time = _time(convo.get("create_time"))
            for mid, node in mapping.items():
                if not isinstance(node, dict) or _safe_id(mid) is None:
                    continue
                body = _text(node)
                if not body.strip():
                    continue
                msg = node["message"]
                timestamp = _time(msg.get("create_time")) or fallback_time
                if timestamp is None:
                    continue  # Never guess chronology for "before Val Town".
                sanitized = _redact(body)
                redacted_count += int(sanitized != body)
                branch = ("UNKNOWN" if active is None else
                          "ACTIVE" if mid in active else "ALTERNATE")
                role = msg["author"]["role"]
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO messages "
                    "(conversation_id,message_id,title,role,created_at,"
                    "branch_status,content,content_sha256) VALUES(?,?,?,?,?,?,?,?)",
                    (cid, mid, title, role, timestamp, branch, sanitized,
                     hashlib.sha256(sanitized.encode("utf-8")).hexdigest())
                )
                if cursor.rowcount:
                    rowid = cursor.lastrowid
                    conn.execute("INSERT INTO messages_fts(rowid,title,content) VALUES(?,?,?)",
                                 (rowid, title, sanitized))
                    count += 1
                    if count > MAX_MESSAGES:
                        raise RecoveryError("EXPORT_MESSAGE_LIMIT")
        manifest_sha = hashlib.sha256(raw).hexdigest()
        for key, value in (
            ("schema", SCHEMA), ("export_sha256", manifest_sha),
            ("message_count", str(count)), ("unknown_branch_conversations", str(unknown_branches)),
            ("redacted_message_count", str(redacted_count)),
            ("production_authorized", "false"),
        ):
            conn.execute("INSERT INTO meta(key,value) VALUES(?,?)", (key, value))
        conn.commit()
    except Exception:
        conn.close()
        Path(index).unlink(missing_ok=True)
        raise
    finally:
        try: conn.close()
        except Exception: pass
    return {"schema": SCHEMA, "messages_indexed": count,
            "unknown_branch_conversations": unknown_branches,
            "messages_with_redactions": redacted_count,
            "export_sha256": manifest_sha, "agents_defined": 10,
            "cloud_account_access": False, "index_encrypted": False}


def _read_index(index: str | Path) -> sqlite3.Connection:
    target = Path(index)
    if target.is_symlink() or not target.is_file():
        raise RecoveryError("INDEX_NOT_A_REGULAR_FILE")
    if target.stat().st_size > 250 * 1024 * 1024:
        raise RecoveryError("INDEX_TOO_LARGE")
    # ro prevents accidental writes; this is NOT SQL encryption.
    conn = sqlite3.connect(f"file:{target.resolve().as_posix()}?mode=ro", uri=True)
    try:
        version = conn.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        if not version or version[0] != SCHEMA:
            raise RecoveryError("INDEX_SCHEMA_MISMATCH")
    except Exception:
        conn.close()
        raise
    return conn


def recover(index: str | Path, query: str, *, before: str | None = None,
            before_val_town: bool = False, include_alternates: bool = False,
            limit: int = 10) -> dict:
    """Ten deterministic specialist search passes with grounded source refs."""
    if not isinstance(query, str) or not query.strip() or len(query) > 300:
        raise RecoveryError("SEARCH_QUERY_REQUIRED")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise RecoveryError("INVALID_RESULT_LIMIT")
    if before is not None and before_val_town:
        raise RecoveryError("AMBIGUOUS_CUTOFF_MODE")
    conn = _read_index(index)
    try:
        cutoff_method = "NONE"
        cutoff = None
        if before is not None:
            cutoff = _date_limit(before)
            cutoff_method = "OWNER_EXPLICIT_UTC_DATE"
        elif before_val_town:
            rows = conn.execute("SELECT created_at,content FROM messages "
                                "WHERE role='user' ORDER BY created_at").fetchall()
            hints = [stamp for stamp, text in rows if _VAL_TOWN.search(text)]
            if not hints:
                raise RecoveryError("NO_VAL_TOWN_MENTION_FOUND_SET_EXPLICIT_CUTOFF")
            cutoff = min(hints)
            cutoff_method = "HEURISTIC_FIRST_USER_MENTION_NOT_ACTUAL_PLATFORM_START"
        terms = re.findall(r"[\w-]{2,}", query.casefold(), re.UNICODE)[:12]
        if not terms:
            raise RecoveryError("SEARCH_TERMS_MISSING")
        # Each user term is quoted, preventing MATCH operator injection.
        fts_query = " OR ".join('"' + x.replace('"', '""') + '"' for x in terms)
        where = ["messages_fts MATCH ?"]
        args: list[Any] = [fts_query]
        if cutoff is not None:
            where.append("m.created_at < ?")
            args.append(cutoff)
        if not include_alternates:
            where.append("m.branch_status != 'ALTERNATE'")
        sql = ("SELECT m.conversation_id,m.message_id,m.title,m.role,m.created_at,"
               "m.branch_status,m.content,m.content_sha256,bm25(messages_fts) "
               "FROM messages_fts JOIN messages m ON m.rowid=messages_fts.rowid "
               "WHERE " + " AND ".join(where) + " ORDER BY bm25(messages_fts) LIMIT 150")
        rows = conn.execute(sql, args).fetchall()
        fused: dict[str, dict] = {}
        per_agent: list[dict] = []
        for agent_id, specialization, vocabulary in AGENTS:
            ranked = []
            for cid, mid, title, role, created_at, branch, body, digest, score in rows:
                haystack = (title + " " + body).casefold()
                bonus = sum(1 for keyword in vocabulary if keyword in haystack)
                role_score = float(-score) + bonus * 0.25
                ranked.append((role_score,cid,mid,title,role,created_at,branch,body,digest))
            ranked.sort(key=lambda r: (-r[0], r[5],r[1],r[2]))
            picks = ranked[:min(limit,5)]
            per_agent.append({"agent_id":agent_id,"specialization":specialization,
                              "candidates":len(picks),"simulated_search_only":True})
            for _,cid,mid,title,role,created_at,branch,body,digest in picks:
                key = cid + "/" + mid
                if key not in fused:
                    fused[key] = {
                        "source_ref": "chatgpt-export:" + cid + "/" + mid,
                        "conversation_title": title,
                        "created_at_utc": datetime.fromtimestamp(
                            created_at,timezone.utc).isoformat(),
                        "role": role, "branch_status": branch,
                        "excerpt": body[:600], "text_sha256": digest,
                        "matched_by": [],
                    }
                fused[key]["matched_by"].append(agent_id)
        results = sorted(fused.values(), key=lambda z:(
            -len(z["matched_by"]), z["created_at_utc"],z["source_ref"]
        ))[:limit]
        return {
            "schema": SCHEMA, "query": query,
            "cutoff_utc_exclusive": (
                datetime.fromtimestamp(cutoff,timezone.utc).isoformat()
                if cutoff is not None else None),
            "cutoff_method": cutoff_method,
            "cutoff_requires_owner_confirmation": cutoff_method.startswith("HEURISTIC"),
            "matches": len(results), "results": results,
            "agents": per_agent, "real_nca_workers_executed": 0,
            "llm_calls": 0, "remote_chat_access": False,
            "source_type": "USER_SUPPLIED_CHATGPT_EXPORT_ONLY",
            "production_authorized": False,
        }
    finally:
        conn.close()
