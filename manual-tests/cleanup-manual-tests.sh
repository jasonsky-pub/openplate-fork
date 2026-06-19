#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./manual-tests/cleanup-manual-tests.sh [case-1|case-2|case-3|case-4|all]
EOF
}

CASE="${1:-all}"

case "$CASE" in
  case-1|case-2|case-3|case-4|all) ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 1
    ;;
esac

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$CASE" == 'all' ]]; then
  cases_to_clean=(case-1 case-2 case-3 case-4)
else
  cases_to_clean=("$CASE")
fi

for root in "$SCRIPT_ROOT/work" "$SCRIPT_ROOT/artifacts"; do
  for case_id in "${cases_to_clean[@]}"; do
    rm -rf "$root/$case_id"
  done
done

printf 'Removed generated manual-test state for: %s\n' "$(IFS=', '; echo "${cases_to_clean[*]}")"