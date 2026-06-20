from models import WorkflowState, WorkflowStatus


VALID_TRANSITIONS = {
    WorkflowStatus.INTAKE: {WorkflowStatus.RUNNING_AGENTS},
    WorkflowStatus.RUNNING_AGENTS: {WorkflowStatus.DECISION_PENDING, WorkflowStatus.SAFE_FALLBACK},
    WorkflowStatus.DECISION_PENDING: {
        WorkflowStatus.HUMAN_REVIEW,
        WorkflowStatus.SAFE_FALLBACK,
        WorkflowStatus.COMPLETED,
    },
    WorkflowStatus.HUMAN_REVIEW: {WorkflowStatus.COMPLETED},
    WorkflowStatus.SAFE_FALLBACK: set(),
    WorkflowStatus.COMPLETED: set(),
}


def transition(state: WorkflowState, next_status: WorkflowStatus) -> None:
    allowed = VALID_TRANSITIONS[state.status]

    if next_status not in allowed:
        raise ValueError(f"invalid transition: {state.status.value} -> {next_status.value}")

    if next_status == WorkflowStatus.COMPLETED:
        if state.policy_gate_result != "safe_to_continue":
            raise ValueError("cannot complete unless the policy gate allows the action")

    state.status = next_status
