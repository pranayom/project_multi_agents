from models import AgentResult, AgentStatus, AgentTask


def document_extraction_agent(task: AgentTask) -> AgentResult:
    text = task.payload["uploaded_document_text"]
    has_receipt = "receipt" in text.lower() or "invoice" in text.lower()

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED if has_receipt else AgentStatus.DEGRADED,
        confidence=0.92 if has_receipt else 0.55,
        output_version="document-extraction-v1",
        evidence_refs=["uploaded_document:claim_packet"],
        data={"has_required_documents": has_receipt},
        failure_reason=None if has_receipt else "missing_receipt_or_invoice",
    )


def policy_lookup_agent(task: AgentTask) -> AgentResult:
    amount = task.payload["amount_usd"]
    covered = amount <= 5000

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED,
        confidence=0.88,
        output_version="policy-lookup-v1",
        evidence_refs=[f"policy:{task.payload['policy_id']}:coverage_limit"],
        data={"covered": covered, "coverage_limit_usd": 5000},
    )


def fraud_screening_agent(task: AgentTask) -> AgentResult:
    amount = task.payload["amount_usd"]
    risk_score = 0.15 if amount < 3000 else 0.72

    return AgentResult(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=AgentStatus.SUCCEEDED,
        confidence=0.86,
        output_version="fraud-screening-v1",
        evidence_refs=["fraud_features:amount_velocity"],
        data={"risk_score": risk_score},
    )


def decision_aggregator(results: dict[str, AgentResult]) -> str:
    extraction = results["document_extraction"].data
    policy = results["policy_lookup"].data
    fraud = results["fraud_screening"].data

    if not extraction["has_required_documents"]:
        return "request_missing_documents"

    if not policy["covered"]:
        return "deny_claim"

    if fraud["risk_score"] >= 0.70:
        return "human_review_fraud_risk"

    return "issue_payment"
