from models import AgentStatus, ToolCall, WorkflowState


AGENT_TOOL_POLICY = {
    "document_extraction": {
        "allowed_tools": {"ocr.read", "document.parse"},
        "denied_tools": {"claim.update", "email.send", "payment.issue"},
    },
    "policy_lookup": {
        "allowed_tools": {"policy.retrieve", "coverage.lookup"},
        "denied_tools": {"claim.deny", "email.send", "payment.issue"},
    },
    "fraud_screening": {
        "allowed_tools": {"fraud.score", "risk_features.read"},
        "denied_tools": {"claim.deny", "email.send", "payment.issue"},
    },
    "customer_drafting": {
        "allowed_tools": {"template.read", "draft.create"},
        "denied_tools": {"claim.update", "email.send", "payment.issue"},
    },
}


HIGH_IMPACT_SIDE_EFFECTS = {
    "claim.deny",
    "email.send",
    "payment.issue",
}


def authorize_tool_call(call: ToolCall) -> bool:
    policy = AGENT_TOOL_POLICY.get(call.agent_name)
    if policy is None:
        return False

    if call.tool_name in policy["denied_tools"]:
        return False

    return call.tool_name in policy["allowed_tools"]


def classify_action_as_tool(action: str) -> str:
    return {
        "deny_claim": "claim.deny",
        "issue_payment": "payment.issue",
        "request_missing_documents": "email.send",
    }.get(action, "workflow.noop")


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

    action_tool = classify_action_as_tool(state.proposed_action or "")
    if action_tool in HIGH_IMPACT_SIDE_EFFECTS:
        return "requires_human_approval_for_side_effect"

    return "safe_to_continue"


def escalation_decision(state: WorkflowState) -> str:
    if state.policy_gate_result in {
        "human_review_missing_documents",
        "human_review_policy_unverified",
        "human_review_fraud_risk",
    }:
        return "escalate"

    if state.policy_gate_result == "requires_human_approval_for_side_effect":
        return "human_approval_required"

    return "no_escalation"
