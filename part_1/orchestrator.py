from agents import (
    decision_aggregator,
    document_extraction_agent,
    fraud_screening_agent,
    policy_lookup_agent,
)
from models import AgentTask, ClaimInput, WorkflowState, WorkflowStatus
from policy_gate import policy_gate
from state_machine import transition


def make_task(workflow_id: str, agent_name: str, claim: ClaimInput) -> AgentTask:
    return AgentTask(
        workflow_id=workflow_id,
        task_id=f"{workflow_id}:{agent_name}",
        agent_name=agent_name,
        input_version="claim-input-v1",
        timeout_ms=2_000,
        max_retries=1,
        max_tool_calls=3,
        max_output_tokens=500,
        payload={
            "claim_id": claim.claim_id,
            "policy_id": claim.policy_id,
            "amount_usd": claim.amount_usd,
            "loss_description": claim.loss_description,
            "uploaded_document_text": claim.uploaded_document_text,
        },
    )


def triage_claim(claim: ClaimInput) -> WorkflowState:
    state = WorkflowState(workflow_id=f"wf-{claim.claim_id}", claim=claim)
    transition(state, WorkflowStatus.RUNNING_AGENTS)

    agents = {
        "document_extraction": document_extraction_agent,
        "policy_lookup": policy_lookup_agent,
        "fraud_screening": fraud_screening_agent,
    }

    for agent_name, agent_fn in agents.items():
        task = make_task(state.workflow_id, agent_name, claim)
        state.task_results[agent_name] = agent_fn(task)

    transition(state, WorkflowStatus.DECISION_PENDING)
    state.proposed_action = decision_aggregator(state.task_results)
    state.policy_gate_result = policy_gate(state)

    if state.policy_gate_result != "safe_to_continue":
        transition(state, WorkflowStatus.HUMAN_REVIEW)
        state.final_action = "route_to_human_reviewer"
        return state

    transition(state, WorkflowStatus.COMPLETED)
    state.final_action = state.proposed_action
    return state
