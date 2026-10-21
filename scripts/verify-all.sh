#!/usr/bin/env bash
# One-command health check for the whole project. Prints a PASS/FAIL table.
#   scripts/verify-all.sh          full run (~10 min; includes the engine test suite)
#   scripts/verify-all.sh --quick  skips the long engine test suite (~2 min)
# The Vega Virtual Device run, live AWS deploy and demo video are manual and not covered.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
QUICK=0; [ "${1:-}" = "--quick" ] && QUICK=1
WORK="$(mktemp -d "${TMPDIR:-/tmp}/nostrobe-verify.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
NAMES=(); RESULTS=(); FAILED=0

check() {  # check "description" command...
  local name="$1"; shift
  local log="$WORK/check_${#NAMES[@]}.log"
  printf '… %s\n' "$name"
  local start=$SECONDS
  if "$@" >"$log" 2>&1; then
    RESULTS+=("PASS  $(printf '%4ss' $((SECONDS - start)))  $name")
  else
    RESULTS+=("FAIL  $(printf '%4ss' $((SECONDS - start)))  $name   (details printed above)")
    FAILED=$((FAILED + 1)); echo "---- $name: last lines ----"; tail -n 15 "$log"
  fi
  NAMES+=("$name")
}
skip() { NAMES+=("$1"); RESULTS+=("SKIP         $1   ($2)"); }

end_to_end() {  # real product path: generate a hazard clip, analyze it, verify it, refuse a mismatch
  uv run --project engine nostrobe synth --suite smoke --seed 7 --output "$WORK/synth" || return 1
  uv run --project engine nostrobe analyze "$WORK/synth/HAZARD_rate_3_5.mp4" --out "$WORK/out" || return 1
  local track="$WORK/out/HAZARD_rate_3_5.broadcast.hzt.json"
  python3 - "$track" <<'PY' || return 1
import json, sys
t = json.load(open(sys.argv[1]))
fails = [e for e in t["events"] if e["severity"] == "fail"]
assert t["verifier"]["passes"], "verifier did not pass"
assert fails and abs(fails[0]["t_start"] - 1.0) < 0.05 and abs(fails[0]["t_end"] - 3.0) < 0.05, "hazard interval differs from truth 1.0-3.0 s"
assert t["veils"], "no veil was produced for a hazardous clip"
PY
  uv run --project engine nostrobe verify "$WORK/synth/HAZARD_rate_3_5.mp4" "$track" || return 1
  ! uv run --project engine nostrobe verify "$WORK/synth/HAZARD_flat.mp4" "$track"  # must refuse wrong video
}

repo_synced() {
  git fetch -q origin || { echo "could not reach GitHub"; return 1; }
  local dirty; dirty="$(git status --porcelain)"
  [ -z "$dirty" ] || { echo "uncommitted changes:"; echo "$dirty"; return 1; }
  [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "local main differs from GitHub main (push or pull needed)"; return 1; }
}

echo "No Strobe-lem verification — $(date '+%Y-%m-%d %H:%M')"
check "Install pinned dependencies (engine, contracts, TV, infra)" \
  bash -c 'npm ci --silent && uv sync --project engine --locked -q && uv sync --project infra --locked -q && (cd tv && npm ci --silent)'
check "Engine lint, format and strict types" \
  bash -c 'cd engine && uv run ruff check && uv run ruff format --check && uv run mypy --strict src'
if [ $QUICK -eq 1 ]; then skip "Engine test suite (431 tests)" "--quick"
else check "Engine test suite (431 tests)" bash -c 'cd engine && uv run pytest -q -p no:cacheprovider'; fi
check "End to end: hazard detected, veiled, verified; wrong video refused" end_to_end
check "Schema and generated TypeScript types in sync" bash -c 'npm run -s types:check && npm run -s typecheck'
check "TV app types and lint" bash -c 'cd tv && npm run -s typecheck && npm run -s lint'
check "TV app tests (cold cache)" bash -c 'cd tv && npx jest --clearCache >/dev/null && npx jest --runInBand'
if [ -f "$HOME/vega/env" ]; then
  check "TV Release build (Vega SDK)" bash -c '. "$HOME/vega/env" && cd tv && npm run -s build:release'
else skip "TV Release build (Vega SDK)" "Vega SDK not installed"; fi
check "AWS pipeline tests" bash -c 'cd infra && uv run pytest -q'
if command -v sam >/dev/null; then check "AWS SAM template valid" sam validate --lint --template-file infra/template.yaml
else skip "AWS SAM template valid" "sam CLI not installed"; fi
check "Web reference player conformance" node scripts/test-web-reader.cjs
check "TV catalog build configuration" node scripts/test-catalog-config.cjs
check "Submission copy, links, results and friction log" python3 scripts/check-submission.py
check "Git: committed and identical to GitHub main" repo_synced

echo; echo "================ SUMMARY ================"
printf '%s\n' "${RESULTS[@]}"
echo "========================================="
if [ $FAILED -eq 0 ]; then echo "ALL AUTOMATED CHECKS PASSED"; else echo "$FAILED CHECK(S) FAILED"; fi
echo "Not covered here (manual): Fire TV run on the Vega Virtual Device, live AWS deploy, demo video."
exit $FAILED
