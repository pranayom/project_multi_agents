from audit import emit_audit_event
from models import AgentResult, WorkflowState, WorkflowStatus
from policies import escalation_decision, policy_gate
from state_machine import transition


def start_workflow(state: WorkflowState) -> None:
    transition(state, WorkflowStatus.RUNNING_AGENTS)
    emit_audit_event(state, "workflow_started")


def record_agent_result(state: WorkflowState, result: AgentResult) -> None:
    state.task_results[result.agent_name] = result
    emit_audit_event(
        state,
        "agent_result_recorded",
        task_id=result.task_id,
        agent_name=result.agent_name,
        metadata={"status": result.status.value, "confidence": result.confidence},
    )


def evaluate_policy_gate(state: WorkflowState) -> str:
    transition(state, WorkflowStatus.DECISION_PENDING)
    state.policy_gate_result = policy_gate(state)
    emit_audit_event(
        state,
        "policy_gate_evaluated",
        policy_decision=state.policy_gate_result,
        metadata={"proposed_action": state.proposed_action},
    )
    return state.policy_gate_result


def route_gated_outcome(state: WorkflowState) -> bool:
    escalation = escalation_decision(state)
    emit_audit_event(state, "escalation_evaluated", metadata={"decision": escalation})

    if escalation == "no_escalation":
        return False

    transition(state, WorkflowStatus.HUMAN_REVIEW)
    state.final_action = "route_to_human_reviewer"
    return True


def complete_workflow(state: WorkflowState) -> None:
    transition(state, WorkflowStatus.COMPLETED)
    state.final_action = state.proposed_action


def move_to_safe_fallback(state: WorkflowState, reason: str) -> None:
    transition(state, WorkflowStatus.SAFE_FALLBACK)
    state.final_action = "safe_fallback"
    emit_audit_event(state, "safe_fallback_selected", metadata={"reason": reason})
