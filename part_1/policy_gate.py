from models import AgentStatus, WorkflowState


HIGH_IMPACT_SIDE_EFFECTS = {
    "deny_claim",
    "issue_payment",
    "send_customer_email",
}


def policy_gate(state: WorkflowState) -> str:
    extraction = state.task_results.get("document_extraction")
    policy = state.task_results.get("policy_lookup")
    fraud = state.task_results.get("fraud_screening")

    if not extraction or extraction.status != AgentStatus.SUCCEEDED:
        return "human_review_missing_documents"

    if not policy or policy.status != AgentStatus.SUCCEEDED:
        return "human_review_policy_unverified"

    if fraud and fraud.data.get("risk_score", 1.0) >= 0.70:
        return "human_review_fraud_risk"

    if state.proposed_action in HIGH_IMPACT_SIDE_EFFECTS:
        return "requires_human_approval_for_side_effect"

    return "safe_to_continue"
