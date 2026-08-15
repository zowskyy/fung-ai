#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GODOT="${GODOT_BIN:-godot}"
PROJECT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ARTIFACTS="$SCRIPT_DIR/artifacts"

mkdir -p "$ARTIFACTS"

"$GODOT" --headless --path "$PROJECT" --import --log-file "$ARTIFACTS/import.log"
"$GODOT" --headless --path "$PROJECT" --script res://addons/scene_animator/tests/parse_check.gd --log-file "$ARTIFACTS/parse-check.log"
"$GODOT" --headless --path "$PROJECT" --script res://addons/scene_animator/tests/run_scene_animator_tests.gd --log-file "$ARTIFACTS/runtime-tests.log"
