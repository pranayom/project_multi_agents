import asyncio

from models import AgentIdentity, ToolCall
from policies import HIGH_IMPACT_SIDE_EFFECTS, authorize_tool_call


TOOL_PARAM_REQUIREMENTS = {
    "document.parse": {"document_text"},
    "policy.retrieve": {"policy_id"},
    "coverage.lookup": {"policy_id", "amount_usd"},
    "fraud.score": {"claim_id", "amount_usd"},
    "risk_features.read": {"claim_id"},
    "template.read": {"template_name"},
    "draft.create": {"template_name", "claim_id"},
    "payment.issue": {"claim_id", "amount_usd", "customer_id"},
}


def validate_tool_call(identity: AgentIdentity, call: ToolCall) -> None:
    if identity.is_expired():
        raise PermissionError("agent identity token has expired")

    if identity.agent_role != call.agent_name:
        raise PermissionError("agent identity does not match requested tool caller")

    if not authorize_tool_call(call):
        raise PermissionError(f"{call.agent_name} cannot call {call.tool_name}")

    required = TOOL_PARAM_REQUIREMENTS.get(call.tool_name)
    if required is None:
        raise ValueError(f"unknown tool: {call.tool_name}")

    missing = required - call.params.keys()
    if missing:
        raise ValueError(f"{call.tool_name} missing params: {sorted(missing)}")

    if call.tool_name in HIGH_IMPACT_SIDE_EFFECTS:
        raise PermissionError(f"{call.tool_name} requires control-plane approval")


async def execute_tool(identity: AgentIdentity, call: ToolCall) -> dict:
    """Mock MCP-inspired boundary for external tool/API calls.

    In production, this adapter could call MCP servers, internal APIs, or
    service-specific gateways. The control point is the same: authorize,
    validate, scope, and audit tool access outside the model.
    """
    validate_tool_call(identity, call)

    delay_ms = call.params.get("_delay_ms", 0)
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)

    if call.tool_name == "policy.retrieve":
        return {"policy_id": call.params["policy_id"], "coverage_limit_usd": 5000}

    if call.tool_name == "coverage.lookup":
        return {
            "covered": call.params["amount_usd"] <= 5000,
            "coverage_limit_usd": 5000,
        }

    if call.tool_name == "fraud.score":
        return {"risk_score": 0.15 if call.params["amount_usd"] < 3000 else 0.72}

    if call.tool_name == "document.parse":
        text = call.params["document_text"]
        return {"has_required_documents": "invoice" in text.lower()}

    return {"ok": True}
