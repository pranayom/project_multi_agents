from time import time

from models import AgentIdentity, AgentResult, AgentStatus, AgentTask, ToolCall
from security import UntrustedText, contains_prompt_injection_signal
from tool_runtime import execute_tool


def make_identity(task: AgentTask) -> AgentIdentity:
    return AgentIdentity(
        agent_instance_id=f"{task.agent_name}:{task.task_id}",
        agent_role=task.agent_name,
        workflow_id=task.workflow_id,
        task_id=task.task_id,
        token_scope=(task.agent_name,),
        expires_at_epoch_ms=int(time() * 1000) + task.timeout_ms,
    )


async def document_extraction_agent(task: AgentTask) -> AgentResult:
    identity = make_identity(task)
    text = task.payload["uploaded_document_text"]

    if contains_prompt_injection_signal(text):
        return AgentResult(
            task_id=task.task_id,
            agent_name=task.agent_name,
            status=AgentStatus.DEGRADED,
            confidence=0.0,
            output_version="document-extraction-v2",
            evidence_refs=["uploaded_document:claim_packet"],
            failure_reason="prompt_injection_signal_detected",
        )

    tool_result = await execute_tool(
        identity,
        ToolCall(
            agent_name=task.agent_name,
            tool_name="document.parse",
            params={"document_text": text},
        ),
    )

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED if tool_result["has_required_documents"] else AgentStatus.DEGRADED,
        confidence=0.91 if tool_result["has_required_documents"] else 0.5,
        output_version="document-extraction-v2",
        evidence_refs=["uploaded_document:claim_packet"],
        data=tool_result,
        failure_reason=None if tool_result["has_required_documents"] else "missing_invoice",
    )


async def policy_lookup_agent(task: AgentTask) -> AgentResult:
    identity = make_identity(task)
    policy = await execute_tool(
        identity,
        ToolCall(
            agent_name=task.agent_name,
            tool_name="policy.retrieve",
            params={"policy_id": task.payload["policy_id"]},
        ),
    )
    coverage = await execute_tool(
        identity,
        ToolCall(
            agent_name=task.agent_name,
            tool_name="coverage.lookup",
            params={
                "policy_id": task.payload["policy_id"],
                "amount_usd": task.payload["amount_usd"],
            },
        ),
    )

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED,
        confidence=0.89,
        output_version="policy-lookup-v2",
        evidence_refs=[f"policy:{policy['policy_id']}:coverage_limit"],
        data=coverage,
    )


async def fraud_screening_agent(task: AgentTask) -> AgentResult:
    identity = make_identity(task)
    result = await execute_tool(
        identity,
        ToolCall(
            agent_name=task.agent_name,
            tool_name="fraud.score",
            params={
                "claim_id": task.payload["claim_id"],
                "amount_usd": task.payload["amount_usd"],
            },
        ),
    )

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED,
        confidence=0.87,
        output_version="fraud-screening-v2",
        evidence_refs=["fraud_features:amount_velocity"],
        data=result,
    )


async def customer_drafting_agent(task: AgentTask) -> AgentResult:
    context = UntrustedText(source="agent_output", content=str(task.payload))

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED,
        confidence=0.82,
        output_version="customer-drafting-v2",
        evidence_refs=["template:payment-review-required"],
        data={
            "draft": (
                "Your claim has been reviewed. A payment action requires final "
                "approval before funds are issued."
            ),
            "isolated_context_source": context.source,
        },
    )


def decision_aggregator(results: dict[str, AgentResult]) -> str:
    extraction = results["document_extraction"].data
    policy = results["policy_lookup"].data
    fraud = results["fraud_screening"].data

    if not extraction.get("has_required_documents"):
        return "request_missing_documents"

    if not policy.get("covered"):
        return "deny_claim"

    if fraud.get("risk_score", 1.0) >= 0.70:
        return "human_review_fraud_risk"

    return "issue_payment"
