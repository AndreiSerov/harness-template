#!/usr/bin/env bash
# Blocks `git commit`, in any form, until scripts/check passes in the tree being committed.
# It runs on every Bash call and finds the commit itself, because a settings `if` rule misses
# `git -C . commit`, `git -c a=b commit` and `sh -c "git commit"`.
# The hook's cwd field is used because CLAUDE_PROJECT_DIR stays on the main checkout
# when the session works in a worktree.
set -u

cwd=$(python3 -c '
import json, re, sys

event = json.load(sys.stdin)
command = event.get("tool_input", {}).get("command", "")
# git, then any global options with their values, then the commit subcommand.
options = r"(?:\s+-[cC]\s+\S+|\s+--?[\w-]+(?:=\S+)?)*"
if re.search(rf"\bgit{options}\s+commit(?![\w-])", command):
    print(event.get("cwd", "."))
')
[ -n "$cwd" ] || exit 0

root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -x "$root/scripts/check" ] || exit 0

if ! output=$(cd "$root" && scripts/check 2>&1); then
  printf 'Commit blocked: scripts/check failed.\n%s\n' "$(printf '%s\n' "$output" | tail -n 40)" >&2
  exit 2
fi
exit 0
