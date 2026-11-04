#!/usr/bin/env bash
# Full test run: unit tests, then integration tests against a fresh Compose stack.
#   1. start docker-compose.yaml under its own project (does not touch `make up`)
#   2. wait for the API
#   3. run backend unit tests and HTTP integration tests
#   4. tear the stack down (always, including its volume)
# Used by `make test-all` and by the CI integration job.
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT="${TEST_PROJECT:-site-issue-triage-test}"
export API_PORT="${API_PORT:-8000}"
export INTEGRATION_BASE_URL="${INTEGRATION_BASE_URL:-http://127.0.0.1:${API_PORT}}"
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.yaml)

teardown() {
  echo "==> Tearing down $PROJECT"
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap teardown EXIT

echo "==> Starting Compose stack ($PROJECT) on port $API_PORT"
"${COMPOSE[@]}" up -d --build

echo "==> Waiting for API at $INTEGRATION_BASE_URL"
for _ in $(seq 1 60); do
  if curl -fsS "$INTEGRATION_BASE_URL/api/studies" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [[ -z "${ready:-}" ]]; then
  echo "API did not become ready" >&2
  "${COMPOSE[@]}" logs
  exit 1
fi

echo "==> Unit tests"
(cd backend && uv run pytest)

echo "==> Integration tests"
(cd backend && uv run pytest ../tests/integration -m integration)

echo "==> All tests passed"
