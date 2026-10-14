#!/usr/bin/env python3
"""
Antigravity IDE Conversation Index Auto-Repair & Recency Sorter
===============================================================
Scans all conversation .db files in ~/.gemini/antigravity-ide/conversations/
and ensures state.vscdb's trajectorySummaries index is completely synchronized
and sorted:
  1. Restores missing conversation entries to trajectorySummaries.
  2. Updates existing entries with latest user interaction timestamps (t_user),
     latest step timestamps (t_mod), and actual step counts from their database.
  3. Sorts all conversations in the index by **most recent interaction time descending**
     (latest active conversation at index 0 / top of the list), ensuring that
     conversations chatted in recently (even if originally created months ago)
     appear at the very front of the conversation list.

Must be run while the IDE is NOT running (otherwise the IDE's in-memory
state will overwrite changes on next persist), unless --list or --dry-run is specified.

CLI Flags:
  --list, -l      Display the sorted conversation list (read-only, works while IDE runs)
  --dry-run, -n   Simulate repair and check what would change without modifying state.vscdb
  --force, -f     Modify state.vscdb even if IDE process is detected (use with caution)

Exit codes:
  0 = success (entries added/updated/sorted or already up to date)
  1 = error
  2 = IDE is still running, refused to modify
"""

import sqlite3
import base64
import os
import sys
import json
import subprocess
import shutil
import argparse
import datetime

# --- Paths ---
STATE_DB = os.path.expanduser(
    "~/.config/Antigravity IDE/User/globalStorage/state.vscdb"
)
CONV_DIR = os.path.expanduser("~/.gemini/antigravity-ide/conversations")
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
KEY = "antigravityUnifiedStateSync.trajectorySummaries"


# --- Protobuf helpers ---
def read_varint(data, i):
    v = 0
    shift = 0
    while True:
        b = data[i]
        i += 1
        v |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return v, i


def decode_proto(data):
    i = 0
    res = []
    while i < len(data):
        key, i = read_varint(data, i)
        tag = key >> 3
        wire = key & 7
        if wire == 0:
            v, i = read_varint(data, i)
            res.append((tag, wire, v))
        elif wire == 2:
            length, i = read_varint(data, i)
            res.append((tag, wire, data[i : i + length]))
            i += length
        elif wire == 1:
            res.append((tag, wire, data[i : i + 8]))
            i += 8
        elif wire == 5:
            res.append((tag, wire, data[i : i + 4]))
            i += 4
        else:
            break
    return res


def encode_varint(v):
    res = []
    while v > 0x7F:
        res.append((v & 0x7F) | 0x80)
        v >>= 7
    res.append(v & 0x7F)
    return bytes(res)


def encode_field(tag, wire, val):
    key = (tag << 3) | wire
    if wire == 0:
        return encode_varint(key) + encode_varint(val)
    elif wire == 2:
        return encode_varint(key) + encode_varint(len(val)) + val
    raise NotImplementedError(f"wire type {wire}")


def parse_ts_parts(raw_bytes):
    """Return (seconds, nanos) from a Google Protobuf Timestamp byte string."""
    if not raw_bytes:
        return 0, 0
    sec, nano = 0, 0
    for tag, wire, val in decode_proto(raw_bytes):
        if tag == 1:
            sec = val
        elif tag == 2:
            nano = val
    return sec, nano


# --- IDE process check ---
def is_ide_running():
    """Check if any antigravity-ide main process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "antigravity-ide/antigravity-ide$"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        try:
            result = subprocess.run(
                ["lsof", STATE_DB], capture_output=True, text=True
            )
            return "antigravity" in result.stdout.lower()
        except FileNotFoundError:
            return False


# --- Title extraction ---
def extract_title(cid):
    """Try to extract a human-readable title for a conversation."""
    transcript_path = os.path.join(
        BRAIN_DIR, cid, ".system_generated/logs/transcript.jsonl"
    )
    if os.path.exists(transcript_path):
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    obj = json.loads(line)
                    if obj.get("type") == "USER_INPUT":
                        content = obj.get("content", "").strip()
                        if content.startswith("<USER_REQUEST>"):
                            content = content[14:].strip()
                        if "</USER_REQUEST>" in content:
                            content = content[: content.index("</USER_REQUEST>")].strip()
                        lines = content.split("\n")
                        clean_lines = []
                        for lt in lines:
                            stripped = lt.strip()
                            if stripped and not stripped.startswith("@["):
                                clean_lines.append(stripped)
                        title = " ".join(clean_lines)[:80] if clean_lines else content[:80]
                        if title:
                            return title
        except (json.JSONDecodeError, IOError):
            pass
    return f"Conversation {cid[:8]}"


# --- Build or refresh single conversation summary ---
def inspect_conversation_db(cid, existing_fields=None, default_workspace_bytes=None):
    """
    Read metadata from ~/.gemini/antigravity-ide/conversations/{cid}.db and construct
    or update summary fields. Returns dict with parsed info or None on failure.
    """
    db_path = os.path.join(CONV_DIR, f"{cid}.db")
    if not os.path.exists(db_path):
        return None

    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.cursor()

        cur.execute("SELECT count(*) FROM steps")
        step_count = cur.fetchone()[0]
        if step_count == 0:
            con.close()
            return None

        cur.execute("SELECT trajectory_id, trajectory_type FROM trajectory_meta")
        row = cur.fetchone()
        if not row:
            con.close()
            return None
        trajectory_id, traj_type = row

        cur.execute("SELECT metadata FROM steps WHERE idx=0")
        m0 = cur.fetchone()
        if not m0:
            con.close()
            return None
        t_create = [p[2] for p in decode_proto(m0[0]) if p[0] == 1][0]

        cur.execute("SELECT metadata FROM steps WHERE idx=(SELECT max(idx) FROM steps)")
        m_last = cur.fetchone()[0]
        t_mod = [p[2] for p in decode_proto(m_last) if p[0] == 1][0]

        # Extract latest user interaction step
        cur.execute("SELECT idx, metadata FROM steps WHERE step_type=14 ORDER BY idx DESC LIMIT 1")
        user_step = cur.fetchone()
        if user_step:
            last_user_idx = user_step[0]
            t_user = [p[2] for p in decode_proto(user_step[1]) if p[0] == 1][0]
        else:
            last_user_idx = 0
            t_user = t_mod

        cur.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
        blob_row = cur.fetchone()
        if blob_row:
            filtered_blob = b"".join(
                encode_field(t, w, v)
                for t, w, v in decode_proto(blob_row[0])
                if t != 15
            )
        else:
            filtered_blob = b""

        con.close()

        # Determine title: preserve existing title if customized, otherwise extract
        title = None
        if existing_fields and 1 in existing_fields:
            ex_title = existing_fields[1].decode("utf-8", errors="ignore").strip()
            if ex_title and not ex_title.startswith("Conversation "):
                title = ex_title
        if not title:
            title = extract_title(cid)

        # Workspace bytes
        if existing_fields and 9 in existing_fields and existing_fields[9]:
            workspace_bytes = existing_fields[9]
        else:
            workspace_bytes = default_workspace_bytes or b""

        status = existing_fields.get(5, 1) if existing_fields else 1
        annotations = existing_fields.get(15, b"") if existing_fields else b""

        t_user_sec, t_user_nano = parse_ts_parts(t_user)
        t_mod_sec, t_mod_nano = parse_ts_parts(t_mod)
        t_create_sec, _ = parse_ts_parts(t_create)

        # Recent interaction timestamp:
        # A conversation is active when either user spoke or model responded.
        # Primary sort metric is latest interaction (max of user input and model output).
        sort_time_sec = max(t_user_sec, t_mod_sec)
        sort_key = (sort_time_sec, t_user_sec, t_mod_sec)

        summary_fields = [
            encode_field(1, 2, title.encode("utf-8")),
            encode_field(2, 0, step_count),
            encode_field(3, 2, t_mod),
            encode_field(4, 2, trajectory_id.encode("utf-8")),
            encode_field(5, 0, status),
            encode_field(7, 2, t_create),
            encode_field(9, 2, workspace_bytes),
            encode_field(10, 2, t_user),
            encode_field(15, 2, annotations),
            encode_field(16, 0, last_user_idx),
            encode_field(17, 2, filtered_blob),
            encode_field(22, 0, traj_type),
        ]
        summary_bytes = b"".join(summary_fields)
        summary_b64 = base64.b64encode(summary_bytes)

        sub2 = encode_field(1, 2, summary_b64)
        entry_bytes = (
            encode_field(1, 2, cid.encode("utf-8"))
            + encode_field(2, 2, sub2)
        )
        entry_tuple = (1, 2, entry_bytes)

        return {
            "cid": cid,
            "title": title,
            "step_count": step_count,
            "t_user_sec": t_user_sec,
            "t_mod_sec": t_mod_sec,
            "t_create_sec": t_create_sec,
            "sort_key": sort_key,
            "entry_tuple": entry_tuple,
        }

    except Exception as e:
        print(f"  ERROR processing {cid[:8]}: {e}", file=sys.stderr)
        return None


# --- Main ---
def main():
    parser = argparse.ArgumentParser(
        description="Antigravity IDE Conversation Index Auto-Repair & Recency Sorter"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all conversations sorted by recent interaction"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Simulate repair and check what would change"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force execution even if IDE process is running"
    )
    args = parser.parse_args()

    if not os.path.exists(STATE_DB):
        print(f"ERROR: state.vscdb not found at {STATE_DB}", file=sys.stderr)
        return 1

    if not os.path.exists(CONV_DIR):
        print(f"No conversations directory found at {CONV_DIR}, nothing to do.")
        return 0

    ide_running = is_ide_running()
    if ide_running and not (args.list or args.dry_run or args.force):
        print(
            "ERROR: Antigravity IDE is currently running.\n"
            "Please close ALL IDE windows first, then re-run this script.\n"
            "(Use --list / -l to view sorted conversation list safely without modifying state.vscdb,\n"
            " or --force / -f if you really want to force write despite IDE running.)",
            file=sys.stderr,
        )
        return 2

    con = sqlite3.connect(STATE_DB)
    cur = con.cursor()
    cur.execute(f'SELECT value FROM ItemTable WHERE key="{KEY}"')
    row = cur.fetchone()
    if not row:
        print("ERROR: trajectorySummaries key not found in state.vscdb", file=sys.stderr)
        con.close()
        return 1

    parsed = decode_proto(base64.b64decode(row[0]))

    orig_cids = []
    existing_meta = {}
    default_workspace_bytes = None

    for entry in parsed:
        sub = decode_proto(entry[2])
        cid = sub[0][2].decode("latin1")
        orig_cids.append(cid)
        sub2 = decode_proto(sub[1][2])
        raw_summary = base64.b64decode(sub2[0][2])
        s_fields = {p[0]: p[2] for p in decode_proto(raw_summary)}
        existing_meta[cid] = s_fields
        if 9 in s_fields and not default_workspace_bytes:
            default_workspace_bytes = s_fields[9]

    all_cids = set(existing_meta.keys())
    for fname in os.listdir(CONV_DIR):
        if fname.endswith(".db"):
            all_cids.add(fname[:-3])

    processed = []
    added_list = []
    updated_list = []
    unchanged_count = 0

    for cid in all_cids:
        info = inspect_conversation_db(
            cid,
            existing_fields=existing_meta.get(cid),
            default_workspace_bytes=default_workspace_bytes,
        )
        if not info:
            continue

        action = "unchanged"
        if cid not in existing_meta:
            action = "added"
            added_list.append(info)
        else:
            old_sc = existing_meta[cid].get(2, 0)
            old_u_sec, _ = parse_ts_parts(existing_meta[cid].get(10))
            old_m_sec, _ = parse_ts_parts(existing_meta[cid].get(3))
            if (
                info["step_count"] != old_sc
                or info["t_user_sec"] != old_u_sec
                or info["t_mod_sec"] != old_m_sec
            ):
                action = "updated"
                updated_list.append(info)
            else:
                unchanged_count += 1

        info["action"] = action
        processed.append(info)

    # Sort all conversations: MOST RECENT INTERACTION FIRST
    processed.sort(key=lambda x: x["sort_key"], reverse=True)

    sorted_cids = [x["cid"] for x in processed]
    order_changed = sorted_cids != orig_cids

    if args.list:
        print(f"=== Antigravity IDE Conversations (Total: {len(processed)}, Sorted by Recent Interaction) ===")
        print(f"{'#':>3} | {'CID':<8} | {'Last Interaction':<16} | {'Created':<16} | {'Steps':>5} | Title")
        print("-" * 88)
        for idx, info in enumerate(processed):
            st = max(info["t_user_sec"], info["t_mod_sec"])
            dt_s = datetime.datetime.fromtimestamp(st).strftime("%Y-%m-%d %H:%M") if st else "N/A"
            dt_c = datetime.datetime.fromtimestamp(info["t_create_sec"]).strftime("%Y-%m-%d %H:%M") if info["t_create_sec"] else "N/A"
            print(f"{idx:3d} | {info['cid'][:8]} | {dt_s:<16} | {dt_c:<16} | {info['step_count']:5d} | {info['title'][:40]}")
        con.close()
        return 0

    needs_write = len(added_list) > 0 or len(updated_list) > 0 or order_changed

    if not needs_write:
        print(f"OK: All {len(processed)} conversation(s) indexed, up-to-date, and sorted by recent interaction.")
        con.close()
        return 0

    print("=== Conversation Index Sync & Recency Sort ===")
    if added_list:
        print(f"  + Restored {len(added_list)} missing conversation(s):")
        for x in added_list[:5]:
            print(f"      + {x['cid'][:8]} : {x['title'][:50]}")
        if len(added_list) > 5:
            print(f"      ... and {len(added_list) - 5} more")

    if updated_list:
        print(f"  * Refreshed {len(updated_list)} conversation(s) with newer interactions:")
        for x in updated_list[:5]:
            dt = datetime.datetime.fromtimestamp(max(x["t_user_sec"], x["t_mod_sec"])).strftime("%m-%d %H:%M")
            print(f"      * {x['cid'][:8]} : {x['title'][:40]} (active: {dt})")
        if len(updated_list) > 5:
            print(f"      ... and {len(updated_list) - 5} more")

    if order_changed:
        print(f"  -> Re-sorted all {len(processed)} conversation(s) by latest interaction time (descending).")

    if args.dry_run:
        print("\n[Dry Run] No changes written to state.vscdb.")
        con.close()
        return 0

    # Build new protobuf
    all_entries = [x["entry_tuple"] for x in processed]
    full_raw = b"".join(encode_field(t, w, v) for t, w, v in all_entries)
    full_b64 = base64.b64encode(full_raw).decode("ascii")

    # Roundtrip test
    test_parsed = decode_proto(base64.b64decode(full_b64))
    assert len(test_parsed) == len(processed), "Protobuf roundtrip verification failed!"

    # Backup and write
    shutil.copy2(STATE_DB, f"{STATE_DB}.backup")
    cur.execute(f'UPDATE ItemTable SET value=? WHERE key="{KEY}"', (full_b64,))
    con.commit()
    con.close()

    print(f"\nRepaired & Sorted successfully!")
    print(f"Total indexed: {len(processed)} conversations (latest active conversation at top).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
