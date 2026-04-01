from __future__ import annotations

from .models import DefenseAction, DefensePlan, Incident, OrchestrationEvent, RolloutDecision


class RuntimeDefensePlanner:
    def plan(
        self,
        event: OrchestrationEvent,
        incidents: list[Incident],
        rollout: RolloutDecision | None = None,
    ) -> DefensePlan:
        actions: list[DefenseAction] = []
        notes: list[str] = []

        highest_severity = self._highest_severity(incidents)

        if event.event_type == "runtime_alert":
            if highest_severity in {"critical", "high"}:
                actions.append(
                    DefenseAction(
                        action_type="gateway_block",
                        target=event.target_file,
                        rationale="Runtime alert on a high-severity issue should be rate-limited or blocked at the edge first.",
                        parameters={"mode": "temporary_block"},
                    )
                )
                actions.append(
                    DefenseAction(
                        action_type="waf_rule",
                        target=event.target_file,
                        rationale="Add a temporary WAF signature while the staged remediation is being validated.",
                        parameters={"scope": "endpoint"},
                    )
                )
            actions.append(
                DefenseAction(
                    action_type="code_patch",
                    target=event.target_file,
                    rationale="Follow up with the deterministic code remediation flow.",
                    parameters={"source": "aion_orchestrator"},
                )
            )
        elif event.event_type == "dependency_alert":
            actions.append(
                DefenseAction(
                    action_type="dependency_pin",
                    target=event.target_file,
                    rationale="Dependency alerts should first generate a version pin or upgrade action.",
                    parameters={"priority": highest_severity or "medium"},
                )
            )
        else:
            actions.append(
                DefenseAction(
                    action_type="code_patch",
                    target=event.target_file,
                    rationale="Code scan findings should produce a patch artifact and staged remediation path.",
                )
            )

        if any(incident.issue_type == "missing_auth_decorator" for incident in incidents):
            actions.append(
                DefenseAction(
                    action_type="feature_flag",
                    target=event.target_file,
                    rationale="Sensitive routes can be disabled behind a feature flag while auth is restored.",
                    parameters={"flag": "disable_sensitive_route"},
                )
            )

        if rollout is not None:
            if rollout.recommendation == "rollback":
                notes.append("Prefer rollback or containment actions over rollout because staged verification failed.")
            elif rollout.recommendation == "approved_for_rollout":
                notes.append("Containment actions may be removed after the staged rollout completes.")
            else:
                notes.append("Runtime containment should stay active until a human approves the rollout.")

        return DefensePlan(strategy="runtime_containment_first", actions=actions, notes=notes)

    def _highest_severity(self, incidents: list[Incident]) -> str | None:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        if not incidents:
            return None
        return sorted(incidents, key=lambda incident: order.get(incident.severity, 99))[0].severity
