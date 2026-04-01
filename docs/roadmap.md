# Roadmap

This roadmap reflects the current shipped functionality in `main` and the next logical steps for AION.

## Current status

AION already supports:

- Python-focused repository and file scanning
- Repository context extraction via static analysis
- `semgrep --config p/python` as the fast first pass
- Anthropic and OpenAI providers for contextual analysis
- AI-generated file targeting via markers, Git history, or explicit `--ai-generated`
- Rich terminal output and JSON output
- Deterministic remediation planning for selected high-confidence Python issues
- Patch artifact generation through `aion repair`
- Standalone artifact verification through `aion verify`
- A local `scan -> repair -> verify` incident loop through `aion run-incident`

## First autonomy release boundary

The current autonomy release is intentionally conservative.

What it does now:

- detects incidents
- plans deterministic remediation
- generates patch artifacts
- verifies artifacts locally

What it does **not** do yet:

- modify production files in place
- auto-commit or auto-open pull requests
- perform repository-wide autonomous remediation workflows
- support non-Python remediation

## Deterministic repair coverage today

Current built-in deterministic repair paths cover:

- raw sqlite f-string queries
- hardcoded secrets
- missing auth decorators

## Phased Roadmap

### Phase 0 — Trusted Foundation

- Upgrade scan results from "reports" to structured **incident objects**.
- Establish a unified JSON schema so scan → repair → verify stages can be chained reliably.
- Add fixtures that express the full chain: *vulnerability sample → expected patch → expected verification result*.
- **Success criterion:** the repository can represent a complete incident lifecycle, not just print findings.

### Phase 1 — Automatic Repair Closed Loop

- Prioritise template-based (deterministic) repairs for well-understood issue classes.
- Use the LLM only as a fallback when no template covers the pattern.
- Auto-run after every patch: syntax validation, semgrep re-scan, and the minimal relevant test set.
- **Success criterion:** for Python security issues covered by fixtures, AION automatically produces a patch and passes verification end-to-end.

### Phase 2 — Self-Verification and Learning

- Record every repair attempt: input, patch, verification outcome, and failure reason.
- Build a *repair eval* that measures success rate, regression rate, and false-repair rate.
- Distil rule templates and prompt strategies from failure samples.
- **Success criterion:** evaluation covers not only "vulnerability detected" but also "repair correct".

### Phase 3 — Pre-production Autonomy

- Add an orchestrator prototype that consumes an event queue and drives the scan/repair/verify pipeline.
- Support staging/sandbox repositories: apply patches automatically and run full verification.
- Introduce policy gating: configure which issue categories allow automatic repair and which are suggestion-only.
- **Success criterion:** the full incident-to-patch-conclusion loop completes without manual step-by-step intervention.

### Phase 4 — Production Online Self-Healing

- Ingest runtime attack and anomaly signals as incident triggers.
- Introduce a policy engine with release gates, canary rollout, and automatic rollback.
- Prioritise hot-fix actions (config / gateway / WAF / feature-flag changes) over in-place code replacement.
- **Success criterion:** after an attack is detected, the system autonomously blocks, repairs, verifies, and rolls back — all within defined policy constraints.

## Guiding principle

AION is moving toward self-evolving code, but every phase prioritises safety, determinism, and reviewability over aggressive automation.
