import asyncio

from agents import (
    customer_drafting_agent,
    decision_aggregator,
    document_extraction_agent,
    fraud_screening_agent,
    policy_lookup_agent,
)
from control_plane import (
    complete_workflow,
    evaluate_policy_gate,
    record_agent_result,
    route_gated_outcome,
    start_workflow,
)
from models import AgentTask, ClaimInput, WorkflowState
from runtime import run_with_budget


def make_task(workflow_id: str, agent_name: str, claim: ClaimInput | WorkflowState) -> AgentTask:
    if isinstance(claim, WorkflowState):
        payload = {
            "claim_id": claim.claim.claim_id,
            "proposed_action": claim.proposed_action,
            "policy_gate_result": claim.policy_gate_result,
        }
    else:
        payload = {
            "claim_id": claim.claim_id,
            "policy_id": claim.policy_id,
            "customer_id": claim.customer_id,
            "amount_usd": claim.amount_usd,
            "loss_description": claim.loss_description,
            "uploaded_document_text": claim.uploaded_document_text,
        }

    return AgentTask(
        workflow_id=workflow_id,
        task_id=f"{workflow_id}:{agent_name}",
        agent_name=agent_name,
        input_version="claim-input-v2",
        timeout_ms=2_000,
        max_retries=1,
        max_tool_calls=3,
        max_output_tokens=500,
        payload=payload,
    )


async def triage_claim(claim: ClaimInput) -> WorkflowState:
    state = WorkflowState(workflow_id=f"wf-{claim.claim_id}", claim=claim)
    start_workflow(state)

    tasks = [
        make_task(state.workflow_id, "document_extraction", claim),
        make_task(state.workflow_id, "policy_lookup", claim),
        make_task(state.workflow_id, "fraud_screening", claim),
    ]

    extraction, policy, fraud = await asyncio.gather(
        run_with_budget(document_extraction_agent, tasks[0]),
        run_with_budget(policy_lookup_agent, tasks[1]),
        run_with_budget(fraud_screening_agent, tasks[2]),
    )

    for result in [extraction, policy, fraud]:
        record_agent_result(state, result)

    state.proposed_action = decision_aggregator(state.task_results)
    evaluate_policy_gate(state)

    if route_gated_outcome(state):
        return state

    draft_task = make_task(state.workflow_id, "customer_drafting", state)
    draft = await run_with_budget(customer_drafting_agent, draft_task)
    record_agent_result(state, draft)

    complete_workflow(state)
    return state
