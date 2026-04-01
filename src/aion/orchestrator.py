from __future__ import annotations

from pathlib import Path

from .models import ContextProfile, Incident, RepairSession, RunIncidentResult
from .repair import IncidentDetector, PatchGenerator, Verifier


class Orchestrator:
    def __init__(
        self,
        detector: IncidentDetector | None = None,
        generator: PatchGenerator | None = None,
        verifier: Verifier | None = None,
    ):
        self.detector = detector or IncidentDetector()
        self.generator = generator or PatchGenerator()
        self.verifier = verifier or Verifier()

    def ingest_event(self, event: dict[str, object]) -> dict[str, object]:
        return {
            "event_type": event.get("event_type", "code_scan"),
            "target_file": str(event["target_file"]),
            "metadata": dict(event.get("metadata", {})),
        }

    def plan_remediation(self, incident: Incident) -> dict[str, object]:
        return {
            "incident_id": incident.id,
            "target_file": incident.target_file,
            "strategy": incident.remediation_strategy,
            "verification_strategy": incident.verification_strategy,
        }

    def verify_patch(self, artifact):
        return self.verifier.verify(artifact)

    def run_incident(self, target: Path, context_profile: ContextProfile) -> RunIncidentResult:
        incidents = self.detector.detect(target, context_profile)
        session = RepairSession(target=str(target), incidents=incidents)
        artifact = self.generator.generate(target, incidents, context_profile)
        session.artifact = artifact
        if artifact is None:
            session.warnings.append("No deterministic remediation plan could be applied.")
            return RunIncidentResult(session=session, verification=None)
        verification = self.verifier.verify(artifact)
        return RunIncidentResult(session=session, verification=verification)
