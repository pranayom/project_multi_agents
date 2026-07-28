from time import time

from models import AuditEvent, WorkflowState


def emit_audit_event(
    state: WorkflowState,
    event_type: str,
    task_id: str | None = None,
    agent_name: str | None = None,
    tool_name: str | None = None,
    policy_decision: str | None = None,
    metadata: dict | None = None,
) -> None:
    event = AuditEvent(
        workflow_id=state.workflow_id,
        task_id=task_id,
        agent_name=agent_name,
        event_type=event_type,
        tool_name=tool_name,
        policy_decision=policy_decision,
        timestamp_ms=int(time() * 1000),
        metadata=metadata or {},
    )
    state.audit_events.append(event)
