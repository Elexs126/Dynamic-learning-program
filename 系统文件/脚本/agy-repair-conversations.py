#!/usr/bin/env python3
"""
Antigravity IDE Conversation Index Auto-Repair
===============================================
Scans all conversation .db files in ~/.gemini/antigravity-ide/conversations/
and ensures each one has a corresponding entry in state.vscdb's
trajectorySummaries index. Restores missing entries automatically.

MUST be run while the IDE is NOT running (otherwise the IDE's in-memory
state will overwrite our changes on next persist).

Exit codes:
  0 = success (entries added or nothing to do)
  1 = error
  2 = IDE is still running, refused to modify
"""

import sqlite3, base64, os, sys, json, subprocess

# --- Paths ---
STATE_DB = os.path.expanduser(
    "~/.config/Antigravity IDE/User/globalStorage/state.vscdb"
)
CONV_DIR = os.path.expanduser("~/.gemini/antigravity-ide/conversations")
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")
KEY = "antigravityUnifiedStateSync.trajectorySummaries"


# --- Protobuf helpers ---
def read_varint(data, i):
    v = 0; shift = 0
    while True:
        b = data[i]; i += 1
        v |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return v, i

def decode_proto(data):
    i = 0; res = []
    while i < len(data):
        key, i = read_varint(data, i)
        tag = key >> 3; wire = key & 7
        if wire == 0:
            v, i = read_varint(data, i); res.append((tag, wire, v))
        elif wire == 2:
            length, i = read_varint(data, i)
            res.append((tag, wire, data[i:i+length])); i += length
        elif wire == 1:
            res.append((tag, wire, data[i:i+8])); i += 8
        elif wire == 5:
            res.append((tag, wire, data[i:i+4])); i += 4
        else: break
    return res

def encode_varint(v):
    res = []
    while v > 0x7f:
        res.append((v & 0x7f) | 0x80); v >>= 7
    res.append(v & 0x7f)
    return bytes(res)

def encode_field(tag, wire, val):
    key = (tag << 3) | wire
    if wire == 0:
        return encode_varint(key) + encode_varint(val)
    elif wire == 2:
        return encode_varint(key) + encode_varint(len(val)) + val
    raise NotImplementedError(f"wire type {wire}")


# --- IDE process check ---
def is_ide_running():
    """Check if any antigravity-ide main process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "antigravity-ide/antigravity-ide$"],
            capture_output=True, text=True
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
            with open(transcript_path) as f:
                for line in f:
                    obj = json.loads(line)
                    if obj.get("type") == "USER_INPUT":
                        content = obj.get("content", "").strip()
                        if content.startswith("<USER_REQUEST>"):
                            content = content[14:].strip()
                        if "</USER_REQUEST>" in content:
                            content = content[:content.index("</USER_REQUEST>")].strip()
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


# --- Summary entry builder ---
def build_summary_entry(cid, workspace_bytes):
    """Build a trajectorySummaries entry from a conversation .db file."""
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

        cur.execute("SELECT idx, metadata FROM steps WHERE step_type=14 ORDER BY idx DESC LIMIT 1")
        user_step = cur.fetchone()
        if user_step:
            last_user_idx = user_step[0]
            t_user = [p[2] for p in decode_proto(user_step[1]) if p[0] == 1][0]
        else:
            last_user_idx = 0
            t_user = t_create

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

        # Check for parent references (subagent conversations)
        cur.execute("SELECT count(*) FROM parent_references")
        is_subagent = cur.fetchone()[0] > 0

        con.close()

        if is_subagent:
            return None

        title = extract_title(cid)

        summary_fields = [
            encode_field(1, 2, title.encode("utf-8")),
            encode_field(2, 0, step_count),
            encode_field(3, 2, t_mod),
            encode_field(4, 2, trajectory_id.encode("utf-8")),
            encode_field(5, 0, 1),
            encode_field(7, 2, t_create),
            encode_field(9, 2, workspace_bytes),
            encode_field(10, 2, t_user),
            encode_field(15, 2, b""),
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
        return (1, 2, entry_bytes)

    except Exception as e:
        print(f"  ERROR processing {cid[:8]}: {e}", file=sys.stderr)
        return None


# --- Main ---
def main():
    if not os.path.exists(STATE_DB):
        print("ERROR: state.vscdb not found", file=sys.stderr)
        return 1

    if not os.path.exists(CONV_DIR):
        print("No conversations directory found, nothing to do.")
        return 0

    if is_ide_running():
        print(
            "ERROR: Antigravity IDE is still running.\n"
            "Please close ALL IDE windows first, then re-run this script.",
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

    existing_cids = set()
    for entry in parsed:
        sub = decode_proto(entry[2])
        cid = sub[0][2].decode("latin1")
        existing_cids.add(cid)

    workspace_bytes = None
    for entry in parsed:
        sub = decode_proto(entry[2])
        inner_b64 = decode_proto(sub[1][2])[0][2]
        inner_raw = base64.b64decode(inner_b64)
        for p in decode_proto(inner_raw):
            if p[0] == 9:
                workspace_bytes = p[2]
                break
        if workspace_bytes:
            break

    if not workspace_bytes:
        print("ERROR: No workspace template found", file=sys.stderr)
        con.close()
        return 1

    all_db_cids = set()
    for fname in os.listdir(CONV_DIR):
        if fname.endswith(".db"):
            all_db_cids.add(fname[:-3])

    missing = all_db_cids - existing_cids
    if not missing:
        print(f"OK: All {len(all_db_cids)} conversations indexed. Nothing to repair.")
        con.close()
        return 0

    print(f"Found {len(missing)} conversation(s) missing from index:")

    new_entries = list(parsed)
    added = 0

    for cid in sorted(missing):
        entry = build_summary_entry(cid, workspace_bytes)
        if entry:
            new_entries.append(entry)
            title = extract_title(cid)
            added += 1
            print(f"  + {cid[:8]} : {title[:60]}")
        else:
            print(f"  - {cid[:8]} : skipped (subagent/empty/error)")

    if added == 0:
        print("No entries needed to be added.")
        con.close()
        return 0

    full_raw = b"".join(encode_field(t, w, v) for t, w, v in new_entries)
    full_b64 = base64.b64encode(full_raw).decode("ascii")

    test_parsed = decode_proto(base64.b64decode(full_b64))
    assert len(test_parsed) == len(new_entries), "Protobuf roundtrip failed!"

    cur.execute(f'UPDATE ItemTable SET value=? WHERE key="{KEY}"', (full_b64,))
    con.commit()
    con.close()

    print(f"\nRepaired: {added} conversation(s) restored to index.")
    print(f"Total indexed: {len(new_entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
