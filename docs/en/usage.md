# Usage

## Scan a repository

```bash
uv run aion scan ./path/to/project
```

## Scan known AI-generated files only

```bash
uv run aion scan ./path/to/project \
  --ai-generated ./path/to/project/generated_file.py
```

## Use OpenAI instead of Anthropic

```bash
uv run aion scan ./path/to/project --provider openai
```

## Emit JSON

```bash
uv run aion scan ./path/to/project --output json
```

## Verbose mode

```bash
uv run aion scan ./path/to/project --verbose
```

Repair and verification flow:

```bash
uv run aion repair ./path/to/file.py \
  --context-file ./context.json \
  --artifact-path ./artifact.json \
  --record-path ./repair-record.json

uv run aion verify --artifact-path ./artifact.json

uv run aion run-incident ./path/to/file.py \
  --context-file ./context.json \
  --record-path ./incident-record.json \
  --output json

uv run aion repair-eval ./tests/fixtures \
  --records-dir ./repair-records \
  --output json

uv run aion process-event ./event.json \
  --result-path ./orchestration.json \
  --output json

uv run aion process-event-queue ./events.json \
  --results-dir ./queue-results \
  --output json
```

The current autonomy release generates patch artifacts and verifies them locally. It does not rewrite production files in place.
`repair-eval` runs the deterministic repair pipeline across fixture cases and reports repair success rate, verification pass rate, false-fix rate, and rollback rate.
`process-event` is the staged orchestration entrypoint. It accepts an event payload, applies policy gating, and only runs approved remediations inside a sandbox workspace.
`process-event-queue` accepts a JSON array of events and reports queue-level metrics while persisting one result file per event.

Example orchestration settings in `.aion.yaml`:

```yaml
auto_repair_issue_types:
  - raw_sqlite_query
  - hardcoded_secret
auto_repair_min_confidence: 0.90
sandbox_mode: repository
sandbox_verification_commands:
  - python -m pytest tests/unit
auto_approve_verified_fixes: false
rollback_on_verification_failure: true
```

When sandbox verification commands are configured, AION runs them inside the staged workspace and records each command's exit code, stdout/stderr, and a rollout recommendation:
- `approved_for_rollout` when sandbox verification passes and auto approval is enabled
- `rollback` when verification fails and rollback-on-failure is enabled
- `needs_human_review` otherwise

Verbose mode prints the extracted context profile, Semgrep findings, fallback reasons,
and token estimates to stderr.

## Typical workflow

1. Point the tool at a repository or a generated file.
2. Let it identify candidate Python files.
3. Review warnings about AI-generated detection or missing `semgrep`.
4. Inspect context-aware findings and suggested fixes.
