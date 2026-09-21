#!/usr/bin/env sh
set -eu

FORCE=0
if [ "${1:-}" = "--force" ]; then
  FORCE=1
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
TARGET="$HOME/.config/jcval94-git-hooks"

EXISTING="$(git config --global --get core.hooksPath || true)"
if [ -n "$EXISTING" ] && [ "$EXISTING" != "$TARGET" ] && [ "$FORCE" -ne 1 ]; then
  echo "core.hooksPath is already set to '$EXISTING'." >&2
  echo "Re-run with --force only if you want to replace it." >&2
  exit 1
fi

mkdir -p "$TARGET"
cp "$REPO_ROOT/tools/contribution_gate.py" "$TARGET/contribution_gate.py"
cp "$REPO_ROOT/.githooks/pre-commit" "$TARGET/pre-commit"
cp "$REPO_ROOT/.githooks/pre-push" "$TARGET/pre-push"
chmod +x "$TARGET/pre-commit" "$TARGET/pre-push" "$TARGET/contribution_gate.py"

git config --global core.hooksPath "$TARGET"

echo "Installed jcval94 contribution gate globally."
echo "Hooks path: $TARGET"
"$TARGET/contribution_gate.py" status
