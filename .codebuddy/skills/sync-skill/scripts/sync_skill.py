#!/usr/bin/env python3
"""
Sync Skill - Bidirectional directory synchronization with Git branch support.

Reads a JSON config file specifying two directories (each with an optional
Git branch) and synchronizes all content between them.

Config locations searched (in order):
  1. <skill-dir>/.sync-skill.json  (next to this script)
  2. $CLAUDE_PROJECT_DIR/.sync-skill.json
  3. ./.sync-skill.json (current working directory)
  4. ~/.codebuddy/sync-skill-config.json

Config format (JSON):
{
  "side_a": {
    "path": "/absolute/path/to/directory-a",
    "branch": "main"
  },
  "side_b": {
    "path": "/absolute/path/to/directory-b",
    "branch": ""
  },
  "exclude": [".git", "node_modules", "__pycache__"]
}

- "branch" set to a non-empty string  => the directory is treated as a Git
  repository; the script will checkout that branch before syncing and
  commit + push after syncing.
- "branch" empty string or omitted     => the directory is treated as a
  plain (non-Git) directory; only file-level sync is performed.

Sync behavior (bidirectional, no deletion propagation):
  - Files that exist only on one side are copied to the other side.
  - Files that exist on both sides: the newer version (by mtime) wins.
  - Files are never automatically deleted (prevents data loss).
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def find_config():
    """Search standard locations for the sync config file."""
    skill_dir = Path(__file__).resolve().parent.parent  # scripts/ -> skill root
    candidates = [
        skill_dir / ".sync-skill.json",
        Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / ".sync-skill.json",
        Path.cwd() / ".sync-skill.json",
        Path.home() / ".codebuddy" / "sync-skill-config.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_config(config_path):
    """Load and validate the sync configuration."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    for side in ("side_a", "side_b"):
        if side not in config:
            raise ValueError(f"Missing '{side}' in config")
        if "path" not in config[side] or not config[side]["path"]:
            raise ValueError(f"Missing or empty 'path' in {side}")

    return config


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def is_git_repo(path):
    """Return True if *path* is inside a Git working tree."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def git_checkout_branch(path, branch):
    """Checkout *branch* in the repo at *path*, creating it if necessary."""
    # Does the branch already exist (local or remote)?
    verify = subprocess.run(
        ["git", "rev-parse", "--verify", branch],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    if verify.returncode != 0:
        # Check if it exists on origin
        verify_remote = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/remotes/origin/{branch}"],
            cwd=str(path),
            capture_output=True,
            text=True,
        )
        if verify_remote.returncode == 0:
            print(f"  Tracking existing remote branch '{branch}'...")
            subprocess.run(
                ["git", "checkout", "-B", branch, f"origin/{branch}"],
                cwd=str(path),
                check=True,
            )
        else:
            print(f"  Creating new branch '{branch}'...")
            subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=str(path),
                check=True,
            )
    else:
        print(f"  Checking out branch '{branch}'...")
        subprocess.run(
            ["git", "checkout", branch],
            cwd=str(path),
            check=True,
        )

    # Pull latest (best-effort — may fail if no upstream is set)
    print(f"  Pulling latest for '{branch}'...")
    pull = subprocess.run(
        ["git", "pull", "origin", branch],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    if pull.returncode != 0:
        print(f"  (pull skipped: {pull.stderr.strip() or pull.stdout.strip()})")


def git_commit_and_push(path, branch):
    """Stage, commit and push any changes in the repo at *path*."""
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        print(f"  No changes to commit on '{branch}'")
        return

    subprocess.run(["git", "add", "-A"], cwd=str(path), check=True)

    msg = f"sync-skill: synchronized content at {datetime.now():%Y-%m-%d %H:%M:%S}"
    subprocess.run(["git", "commit", "-m", msg], cwd=str(path), check=True)

    print(f"  Pushing to '{branch}'...")
    push = subprocess.run(
        ["git", "push", "origin", branch],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        print(f"  (push failed: {push.stderr.strip()})")
    else:
        print(f"  Committed and pushed to '{branch}'")


# ---------------------------------------------------------------------------
# File sync
# ---------------------------------------------------------------------------

def _should_exclude(rel_path, exclude_patterns):
    """True if any component of *rel_path* matches an exclude pattern."""
    parts = Path(rel_path).parts
    return any(p in parts for p in exclude_patterns)


def sync_direction(src, dst, exclude_patterns):
    """
    Copy files from *src* to *dst* where the src copy is newer or the file
    is missing in *dst*.  Returns True if any file was copied.
    """
    changed = False
    if not src.exists():
        return False

    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if _should_exclude(rel, exclude_patterns):
            continue

        dst_item = dst / rel

        if item.is_dir():
            dst_item.mkdir(parents=True, exist_ok=True)
            continue

        if not item.is_file():
            continue

        if not dst_item.exists():
            dst_item.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst_item)
            print(f"  + {rel}  (new)")
            changed = True
        else:
            if item.stat().st_mtime > dst_item.stat().st_mtime:
                shutil.copy2(item, dst_item)
                print(f"  ~ {rel}  (updated)")
                changed = True

    return changed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    config_path = find_config()
    if not config_path:
        print("Error: No sync config file found.")
        print("Searched:")
        print("  <skill-dir>/.sync-skill.json")
        print("  $CLAUDE_PROJECT_DIR/.sync-skill.json")
        print("  ./.sync-skill.json")
        print("  ~/.codebuddy/sync-skill-config.json")
        sys.exit(1)

    print(f"Config: {config_path}")

    try:
        config = load_config(config_path)
    except Exception as exc:
        print(f"Error loading config: {exc}")
        sys.exit(1)

    side_a = config["side_a"]
    side_b = config["side_b"]
    exclude = config.get("exclude", [".git"])

    path_a = Path(side_a["path"]).resolve()
    path_b = Path(side_b["path"]).resolve()
    branch_a = (side_a.get("branch") or "").strip()
    branch_b = (side_b.get("branch") or "").strip()

    label_a = f"branch '{branch_a}'" if branch_a else "non-Git"
    label_b = f"branch '{branch_b}'" if branch_b else "non-Git"
    print(f"\nSide A: {path_a}  ({label_a})")
    print(f"Side B: {path_b}  ({label_b})")

    # Validate paths
    for label, p in (("A", path_a), ("B", path_b)):
        if not p.exists():
            print(f"\nError: Side {label} path does not exist: {p}")
            sys.exit(1)

    # Git: checkout branches
    for label, path, branch in (("A", path_a, branch_a), ("B", path_b, branch_b)):
        if not branch:
            continue
        if not is_git_repo(path):
            print(f"\nError: Side {label} has branch '{branch}' configured "
                  f"but is not a Git repository: {path}")
            sys.exit(1)
        print(f"\n--- Side {label}: Git checkout ---")
        git_checkout_branch(path, branch)

    # Bidirectional file sync
    print("\n--- Sync A -> B ---")
    c1 = sync_direction(path_a, path_b, exclude)
    print("\n--- Sync B -> A ---")
    c2 = sync_direction(path_b, path_a, exclude)

    # Git: commit + push
    for label, path, branch in (("A", path_a, branch_a), ("B", path_b, branch_b)):
        if not branch:
            continue
        print(f"\n--- Side {label}: Git commit ---")
        git_commit_and_push(path, branch)

    if not (c1 or c2):
        print("\nDirectories are already in sync — no file changes needed.")
    else:
        print("\nSync completed successfully.")


if __name__ == "__main__":
    main()
