#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./manual-tests/run-manual-tests.sh [case-1|case-2|case-3|case-4|all]

Environment variables:
  PYTHON_EXE   Python executable to use (default: python)
EOF
}

CASE="${1:-all}"

if [[ -n "${PYTHON_EXE:-}" ]]; then
  PYTHON_EXE="$PYTHON_EXE"
elif command -v python.exe >/dev/null 2>&1; then
  PYTHON_EXE="python.exe"
elif command -v py.exe >/dev/null 2>&1; then
  PYTHON_EXE="py.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_EXE="python"
elif command -v py >/dev/null 2>&1; then
  PYTHON_EXE="py"
else
  echo "No Python launcher found in PATH for bash. Set PYTHON_EXE explicitly." >&2
  exit 1
fi

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
REPO_ROOT="$(cd "$SCRIPT_ROOT/.." && pwd)"
TEMPLATES_ROOT="$SCRIPT_ROOT/templates"
WORK_ROOT="$SCRIPT_ROOT/work"
ARTIFACTS_ROOT="$SCRIPT_ROOT/artifacts"

ensure_dir() {
  mkdir -p "$1"
}

to_windows_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -aw "$1"
  else
    "$PYTHON_EXE" - "$1" <<'PY'
import re
import sys

raw_path = sys.argv[1].replace('\\', '/')
match = re.match(r'^/mnt/([a-zA-Z])/(.*)$', raw_path)
if match:
    drive = match.group(1).upper() + ':'
    rest = '\\' + match.group(2).replace('/', '\\')
    print(drive + rest)
else:
    print(raw_path)
PY
  fi | tr -d '\r'
}

python_path_arg() {
  local path="$1"
  case "$PYTHON_EXE" in
    *.exe|py.exe|python.exe)
      to_windows_path "$path"
      ;;
    *)
      printf '%s\n' "$path"
      ;;
  esac
}

python_module_search_path() {
  python_path_arg "$REPO_ROOT/src"
}

file_url() {
  "$PYTHON_EXE" - "$(python_path_arg "$1")" <<'PY' | tr -d '\r'
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve().as_uri())
PY
}

write_utf8_no_bom() {
  local path="$1"
  local content="$2"
  "$PYTHON_EXE" - "$(python_path_arg "$path")" "$content" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(sys.argv[2], encoding="utf-8", newline="\n")
PY
}

invoke_openplate() {
  local case_id="$1"
  local log_name="$2"
  local expected_codes_csv="$3"
  local stdin_payload="${4:-}"
  shift 4

  local artifact_dir="$ARTIFACTS_ROOT/$case_id"
  ensure_dir "$artifact_dir"
  local log_path="$artifact_dir/$log_name"
  local stdin_file=""
  local exit_code

  if [[ -n "$stdin_payload" ]]; then
    stdin_file="$artifact_dir/${log_name}.stdin"
    printf '%s\n' "$stdin_payload" > "$stdin_file"
  fi

  set +e
  if [[ -n "$stdin_file" ]]; then
    env PYTHONPATH="$(python_module_search_path)" "$PYTHON_EXE" -m openplate "$@" < "$stdin_file" 2>&1 | tee "$log_path" >/dev/null
  else
    env PYTHONPATH="$(python_module_search_path)" "$PYTHON_EXE" -m openplate "$@" 2>&1 | tee "$log_path" >/dev/null
  fi
  exit_code=${PIPESTATUS[0]}
  set -e

  local expected_match=1
  IFS=',' read -r -a expected_codes <<< "$expected_codes_csv"
  for expected_code in "${expected_codes[@]}"; do
    if [[ "$exit_code" == "$expected_code" ]]; then
      expected_match=0
      break
    fi
  done

  if [[ $expected_match -ne 0 ]]; then
    echo "Command failed for $case_id ($log_name) with exit code $exit_code. See $log_path" >&2
    exit 1
  fi

  printf '%s\n' "$log_path"
}

assert_path_exists() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    echo "Expected path does not exist: $path" >&2
    exit 1
  fi
}

assert_path_missing() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "Expected path to be missing: $path" >&2
    exit 1
  fi
}

assert_file_contains() {
  local path="$1"
  local expected_text="$2"
  assert_path_exists "$path"
  if ! grep -Fq -- "$expected_text" "$path"; then
    echo "Expected '$expected_text' in $path" >&2
    exit 1
  fi
}

assert_file_not_contains() {
  local path="$1"
  local unexpected_text="$2"
  assert_path_exists "$path"
  if grep -Fq -- "$unexpected_text" "$path"; then
    echo "Did not expect '$unexpected_text' in $path" >&2
    exit 1
  fi
}

reset_case_folders() {
  local case_id="$1"
  rm -rf "$WORK_ROOT/$case_id" "$ARTIFACTS_ROOT/$case_id"
  ensure_dir "$WORK_ROOT/$case_id"
  ensure_dir "$ARTIFACTS_ROOT/$case_id"
}

initialize_git_repo() {
  local repo_path="$1"
  (
    cd "$repo_path"
    git init >/dev/null 2>&1
    git branch -M main >/dev/null 2>&1
    git config user.email 'manual-tests@example.com'
    git config user.name 'OpenPlate Manual Tests'
    git add .
    git commit -m 'fixture init' >/dev/null 2>&1
  )
}

new_local_catalog_repo() {
  local case_id="$1"
  local case_work="$WORK_ROOT/$case_id"
  local repo_path="$case_work/local-catalog"

  cp -R "$TEMPLATES_ROOT/local-catalog" "$repo_path"

  local repo_url_without_ref
  repo_url_without_ref="$(file_url "$repo_path")"
  local worker_source_url="${repo_url_without_ref}?path=prompt-worker-template#main"
  local prompt_root_config="$repo_path/prompt-root-template/openplate.template.yaml"

  "$PYTHON_EXE" - "$(python_path_arg "$prompt_root_config")" "$worker_source_url" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
path.write_text(
    path.read_text(encoding="utf-8").replace("__PROMPT_WORKER_URL__", sys.argv[2]),
    encoding="utf-8",
)
PY

  initialize_git_repo "$repo_path"
  printf '%s\n' "$repo_path"
}

write_summary() {
  local case_id="$1"
  shift
  local summary_path="$ARTIFACTS_ROOT/$case_id/summary.txt"
  printf '%s\n' "$@" > "$summary_path"
}

build_case3_file_import_json() {
  local verbose_path="$1"
  local file_import_path="$2"
  "$PYTHON_EXE" - "$(python_path_arg "$verbose_path")" "$(python_path_arg "$file_import_path")" <<'PY'
import json
import sys
from pathlib import Path

verbose_document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root_node = next(node for node in verbose_document if "service_name" in node["answers"])
document = [
    {
        "node-id": root_node["node-id"],
        "answers": {
            "service_name": "json-file-service",
            "include_worker": "true",
            "hidden_name": "json-hidden",
            "extra_answer": "ignored-value",
        },
        "info": root_node.get("info"),
    },
    {
        "node-id": "deadbee",
        "answers": {"stray": "value"},
        "info": {"template": "ignored-template", "dest_folder": "ignored-folder"},
    },
]
Path(sys.argv[2]).write_text(json.dumps(document, indent=2), encoding="utf-8")
PY
}

build_case3_stdin_import_json() {
  local compact_path="$1"
  local stdin_import_path="$2"
  "$PYTHON_EXE" - "$(python_path_arg "$compact_path")" "$(python_path_arg "$stdin_import_path")" <<'PY'
import json
import sys
from pathlib import Path

compact_document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root_node = next(node for node in compact_document if "service_name" in node["answers"])
document = [
    {
        "node-id": root_node["node-id"],
        "answers": {
            "service_name": "json-stdin-service",
            "include_worker": "false",
        },
    }
]
Path(sys.argv[2]).write_text(json.dumps(document, indent=2), encoding="utf-8")
PY
}

clear_readonly_file() {
  local path="$1"
  if command -v attrib >/dev/null 2>&1; then
    attrib -R "$(to_windows_path "$path")" >/dev/null 2>&1 || true
  else
    chmod u+w "$path" 2>/dev/null || true
  fi
}

run_case1() {
  local case_id='case-1'
  reset_case_folders "$case_id"

  local repo_path
  repo_path="$(new_local_catalog_repo "$case_id")"
  local repo_url
  repo_url="$(file_url "$repo_path")"
  local source_with_ref="${repo_url}?path=lifecycle-template#main"
  local source_without_ref="${repo_url}?path=lifecycle-template"
  local gated_source="${repo_url}?path=version-gated-template#main"

  local case_work="$WORK_ROOT/$case_id"
  local config_path="$case_work/openplate-config.yaml"
  local project_a="$case_work/bootstrap-project"
  local project_b="$case_work/default-branch-project"
  local project_c="$case_work/version-gated-project"
  ensure_dir "$project_a"
  ensure_dir "$project_b"
  ensure_dir "$project_c"

  invoke_openplate "$case_id" '01-version.log' '0' '' --version >/dev/null
  invoke_openplate "$case_id" '02-config-set.log' '0' '' -c "$(to_windows_path "$config_path")" config set --vcs-url "$repo_url" --template-prefix '?path=local-catalog' --parameter-default 'service_name=bootstrap-default' --parameter-default 'owner_name=platform-team' --allow-template-commands >/dev/null
  invoke_openplate "$case_id" '03-config-remove-default.log' '0' '' -c "$(to_windows_path "$config_path")" config set --parameter-default 'owner_name=' >/dev/null
  local config_log
  config_log="$(invoke_openplate "$case_id" '04-config-get.log' '0' '' -c "$(to_windows_path "$config_path")" config get)"
  assert_file_contains "$config_log" 'vcs_url:'
  assert_file_contains "$config_log" 'template_prefix:'
  assert_file_contains "$config_log" 'service_name: bootstrap-default'
  assert_file_not_contains "$config_log" 'owner_name: platform-team'

  invoke_openplate "$case_id" '05-init-explicit-ref.log' '0' $'\n' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$project_a")" --dest-folder 'bootstrap/app' --no-cache "$source_with_ref" >/dev/null

  local managed_a="$project_a/scaffold/bootstrap/app/managed/service.txt"
  local docs_a="$project_a/scaffold/bootstrap/app/docs/bootstrap-default-overview.md"
  local runbook_a="$project_a/scaffold/bootstrap/app/notes/runbook.md"
  local hook_a="$project_a/hooks/init-command.txt"
  local project_config_a="$project_a/.openplate.project.yaml"
  assert_file_contains "$managed_a" 'service=bootstrap-default'
  assert_file_contains "$managed_a" 'deployment=lambda'
  assert_file_contains "$managed_a" 'instance=t3.small'
  assert_file_contains "$managed_a" 'hidden=hidden-default'
  assert_path_exists "$docs_a"
  assert_path_exists "$runbook_a"
  assert_file_contains "$hook_a" 'init command ran'
  assert_file_contains "$project_config_a" 'dest_folder: bootstrap/app'
  assert_file_contains "$project_config_a" 'no_cache: true'

  clear_readonly_file "$managed_a"
  rm -f "$managed_a"
  rm -f "$docs_a"
  rm -f "$hook_a"

  local rerun_rejected_log
  rerun_rejected_log="$(invoke_openplate "$case_id" '06-init-rerun-rejected.log' '1' '' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$project_a")" --dest-folder 'bootstrap/app' --no-cache "$source_with_ref")"
  assert_file_contains "$rerun_rejected_log" "Template already exists at destination folder 'bootstrap/app'"
  assert_path_missing "$managed_a"
  assert_path_missing "$docs_a"

  invoke_openplate "$case_id" '07-init-overwrite.log' '0' '' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$project_a")" --overwrite --dest-folder 'bootstrap/app' --no-cache "$source_with_ref" >/dev/null

  assert_file_contains "$managed_a" 'service=bootstrap-default'
  assert_file_contains "$docs_a" 'bootstrap-default'
  assert_path_missing "$hook_a"

  local template_count_a
  template_count_a="$("$PYTHON_EXE" - "$(python_path_arg "$project_config_a")" <<'PY'
import sys
import yaml
from pathlib import Path

data = yaml.safe_load(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(len(data.get('templates') or []))
PY
)"
  template_count_a="$(printf '%s' "$template_count_a" | tr -d '\r\n')"
  if [[ "$template_count_a" != "1" ]]; then
    echo "Expected exactly one tracked template after init --overwrite, found: $template_count_a" >&2
    exit 1
  fi

  invoke_openplate "$case_id" '08-init-default-branch-and-ignore.log' '0' $'branchless-service\nlambda' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$project_b")" --allow-default-branch -i '.*runbook\.md' --dest-folder 'branchless/app' "$source_without_ref" >/dev/null

  local managed_b="$project_b/scaffold/branchless/app/managed/service.txt"
  local runbook_b="$project_b/scaffold/branchless/app/notes/runbook.md"
  assert_file_contains "$managed_b" 'service=branchless-service'
  assert_path_missing "$runbook_b"

  invoke_openplate "$case_id" '09-init-ignore-tool-version.log' '0' '' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$project_c")" --ignore-tool-version "$gated_source" >/dev/null
  assert_path_exists "$project_c/gated/info.txt"

  write_summary "$case_id" \
    "Catalog repo: $repo_path" \
    "Explicit ref source: $source_with_ref" \
    "Default branch source: $source_without_ref" \
    "Version-gated source: $gated_source" \
    'Validated config persistence, file:// sources, ?path= selection, #main refs, --allow-default-branch, --dest-folder, --no-cache, --ignore, init rerun rejection, init --overwrite behavior, and --ignore-tool-version.'
}

run_case2() {
  local case_id='case-2'
  reset_case_folders "$case_id"

  local repo_path
  repo_path="$(new_local_catalog_repo "$case_id")"
  local repo_url
  repo_url="$(file_url "$repo_path")"
  local source_url="${repo_url}?path=lifecycle-template#main"

  local case_work="$WORK_ROOT/$case_id"
  local config_path="$case_work/openplate-config.yaml"
  local blocked_project="$case_work/blocked-project"
  local default_project="$case_work/default-visibility-project"
  local hidden_project="$case_work/ask-hidden-project"
  ensure_dir "$blocked_project"
  ensure_dir "$default_project"
  ensure_dir "$hidden_project"

  local blocked_log
  blocked_log="$(invoke_openplate "$case_id" '01-blocked-init-commands.log' '1' '' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$blocked_project")" "$source_url")"
  assert_file_contains "$blocked_log" 'Template init_commands require confirmation'
  assert_file_contains "$blocked_log" 'This template defines init_commands that would run later:'
  assert_file_contains "$blocked_log" '--allow-template-commands'
  assert_file_contains "$blocked_log" 'openplate config set'

  invoke_openplate "$case_id" '02-config-allow-init-commands.log' '0' '' -c "$(to_windows_path "$config_path")" config set --allow-template-commands >/dev/null

  invoke_openplate "$case_id" '03-init-with-default-hidden.log' '0' $'interactive-default\nlambda' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$default_project")" --dest-folder 'interactive/default' "$source_url" >/dev/null
  local managed_default="$default_project/scaffold/interactive/default/managed/service.txt"
  assert_file_contains "$managed_default" 'service=interactive-default'
  assert_file_contains "$managed_default" 'deployment=lambda'
  assert_file_contains "$managed_default" 'instance=t3.small'
  assert_file_contains "$managed_default" 'hidden=hidden-default'
  assert_path_exists "$default_project/hooks/init-command.txt"

  invoke_openplate "$case_id" '04-init-with-ask-hidden.log' '0' $'interactive-ec2\nec2\nm5.large\noverride-secret' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$hidden_project")" --ask-hidden --dest-folder 'interactive/hidden' "$source_url" >/dev/null
  local managed_hidden="$hidden_project/scaffold/interactive/hidden/managed/service.txt"
  assert_file_contains "$managed_hidden" 'service=interactive-ec2'
  assert_file_contains "$managed_hidden" 'deployment=ec2'
  assert_file_contains "$managed_hidden" 'instance=m5.large'
  assert_file_contains "$managed_hidden" 'hidden=override-secret'

  write_summary "$case_id" \
    "Catalog repo: $repo_path" \
    "Source: $source_url" \
    'Validated init_commands authorization failure guidance, persistent allow-template-commands config, interactive prompting, hidden defaults, and conditionally_hidden visibility with --ask-hidden.'
}

run_case3() {
  local case_id='case-3'
  reset_case_folders "$case_id"

  local repo_path
  repo_path="$(new_local_catalog_repo "$case_id")"
  local repo_url
  repo_url="$(file_url "$repo_path")"
  local source_url="${repo_url}?path=prompt-root-template#main"

  local case_work="$WORK_ROOT/$case_id"
  local export_project="$case_work/export-workspace"
  local file_import_project="$case_work/file-import-project"
  local stdin_import_project="$case_work/stdin-import-project"
  local config_path="$case_work/openplate-config.yaml"
  ensure_dir "$export_project"
  ensure_dir "$file_import_project"
  ensure_dir "$stdin_import_project"

  local artifact_dir="$ARTIFACTS_ROOT/$case_id"
  local compact_path="$artifact_dir/prompts-compact.json"
  local verbose_path="$artifact_dir/prompts-verbose.json"
  local file_import_path="$artifact_dir/prompts-import-file.json"
  local stdin_import_path="$artifact_dir/prompts-import-stdin.json"

  invoke_openplate "$case_id" '01-print-init-json-compact.log' '0' '' -c "$(to_windows_path "$config_path")" project --project-folder "$(to_windows_path "$export_project")" print-init-json "$source_url" >/dev/null
  cp "$artifact_dir/01-print-init-json-compact.log" "$compact_path"
  assert_path_missing "$export_project/.openplate.project.yaml"
  assert_file_not_contains "$compact_path" '"info"'

  invoke_openplate "$case_id" '02-print-init-json-verbose.log' '0' '' -c "$(to_windows_path "$config_path")" project --project-folder "$(to_windows_path "$export_project")" --ask-hidden print-init-json "$source_url" --verbose >/dev/null
  cp "$artifact_dir/02-print-init-json-verbose.log" "$verbose_path"
  assert_file_contains "$verbose_path" '"info"'
  assert_file_contains "$verbose_path" '"hidden_name"'

  build_case3_file_import_json "$verbose_path" "$file_import_path"
  build_case3_stdin_import_json "$compact_path" "$stdin_import_path"

  local file_import_log
  file_import_log="$(invoke_openplate "$case_id" '03-init-prompts-json-file.log' '0' '' -d -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$file_import_project")" --ask-hidden --dest-folder 'imported/root' "$source_url" --prompts-json-file "$(to_windows_path "$file_import_path")")"
  assert_file_contains "$file_import_log" 'Ignoring supplied prompt template because it was not processed'
  assert_file_contains "$file_import_log" 'Ignoring unused supplied prompt parameter'
  assert_file_contains "$file_import_project/generated/imported/root/managed/root.txt" 'service=json-file-service'
  assert_file_contains "$file_import_project/generated/imported/root/managed/root.txt" 'hidden=json-hidden'
  assert_file_contains "$file_import_project/generated/worker/json-file-service/managed/worker.txt" 'worker=json-file-service-worker'

  local stdin_payload
  stdin_payload="$(cat "$stdin_import_path")"
  invoke_openplate "$case_id" '04-init-prompts-json-stdin.log' '0' "$stdin_payload" -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$stdin_import_project")" --dest-folder 'stdin/root' "$source_url" --prompts-json-stdin >/dev/null
  assert_file_contains "$stdin_import_project/generated/stdin/root/managed/root.txt" 'service=json-stdin-service'
  assert_path_missing "$stdin_import_project/generated/worker/json-stdin-service/managed/worker.txt"

  write_summary "$case_id" \
    "Catalog repo: $repo_path" \
    "Source: $source_url" \
    'Validated compact and verbose prompt export, read-only export behavior, file and stdin imports, hidden prompt scope, ignored extra nodes, unused answers, sibling prompt materialization, and dest-folder-independent import identity.'
}

run_case4() {
  local case_id='case-4'
  reset_case_folders "$case_id"

  local repo_path
  repo_path="$(new_local_catalog_repo "$case_id")"
  local repo_url
  repo_url="$(file_url "$repo_path")"
  local source_url="${repo_url}?path=lifecycle-template#main"

  local case_work="$WORK_ROOT/$case_id"
  local config_path="$case_work/openplate-config.yaml"
  local project_path="$case_work/update-project"
  ensure_dir "$project_path"

  invoke_openplate "$case_id" '01-init.log' '0' $'update-demo\nlambda' -c "$(to_windows_path "$config_path")" init --project-folder "$(to_windows_path "$project_path")" --allow-template-commands --dest-folder 'update/app' "$source_url" >/dev/null

  local managed_path="$project_path/scaffold/update/app/managed/service.txt"
  local docs_path="$project_path/scaffold/update/app/docs/update-demo-overview.md"
  local runbook_path="$project_path/scaffold/update/app/notes/runbook.md"
  clear_readonly_file "$managed_path"
  printf 'drifted readonly content\n' > "$managed_path"
  printf '# drifted non-readonly file\n' > "$docs_path"
  rm -f "$runbook_path"

  local verify_fail_log
  verify_fail_log="$(invoke_openplate "$case_id" '02-verify-before-update.log' '1' '' -c "$(to_windows_path "$config_path")" project --project-folder "$(to_windows_path "$project_path")" verify)"
  assert_file_contains "$verify_fail_log" 'Running verify on folder:'

  invoke_openplate "$case_id" '03-update-missing.log' '0' $'update-demo\nlambda' -c "$(to_windows_path "$config_path")" update --project-folder "$(to_windows_path "$project_path")" --ask-again --update-missing >/dev/null
  assert_file_contains "$managed_path" 'service=update-demo'
  assert_file_contains "$runbook_path" 'Runbook for update-demo.'
  assert_file_contains "$docs_path" '# drifted non-readonly file'

  invoke_openplate "$case_id" '04-update-full.log' '0' '' -c "$(to_windows_path "$config_path")" update --project-folder "$(to_windows_path "$project_path")" --update-full >/dev/null
  assert_file_contains "$docs_path" '# update-demo'

  local verify_pass_log
  verify_pass_log="$(invoke_openplate "$case_id" '05-verify-after-update.log' '0' '' -c "$(to_windows_path "$config_path")" project --project-folder "$(to_windows_path "$project_path")" verify)"
  assert_file_contains "$verify_pass_log" 'Done!'

  local automation_verify_log
  automation_verify_log="$(invoke_openplate "$case_id" '06-verify-automation.log' '0' '' -a -c "$(to_windows_path "$config_path")" project --project-folder "$(to_windows_path "$project_path")" verify)"
  assert_file_not_contains "$automation_verify_log" 'Running verify on folder:'

  write_summary "$case_id" \
    "Catalog repo: $repo_path" \
    "Source: $source_url" \
    'Validated update, --update-missing, --update-full, --ask-again, project verify in human mode, and project verify with --automation output.'
}

ensure_dir "$WORK_ROOT"
ensure_dir "$ARTIFACTS_ROOT"

if [[ "$CASE" == 'all' ]]; then
  cases_to_run=(case-1 case-2 case-3 case-4)
else
  cases_to_run=("$CASE")
fi

for case_id in "${cases_to_run[@]}"; do
  case "$case_id" in
    case-1) run_case1 ;;
    case-2) run_case2 ;;
    case-3) run_case3 ;;
    case-4) run_case4 ;;
  esac
done

printf 'Manual test run complete for: %s\n' "$(IFS=', '; echo "${cases_to_run[*]}")"