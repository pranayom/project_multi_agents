import asyncio
from pprint import pprint

from evaluation import evaluate_agent_results, evaluate_workflow
from models import ClaimInput
from orchestrator import triage_claim


async def main() -> None:
    claim = ClaimInput(
        claim_id="CLM-1001",
        policy_id="POL-42",
        customer_id="CUST-9",
        amount_usd=1200,
        loss_description="Water damage from a burst pipe.",
        uploaded_document_text="Customer uploaded contractor invoice and photos.",
    )

    final_state = await triage_claim(claim)

    pprint(
        {
            "workflow_id": final_state.workflow_id,
            "status": final_state.status.value,
            "proposed_action": final_state.proposed_action,
            "policy_gate_result": final_state.policy_gate_result,
            "final_action": final_state.final_action,
            "audit_event_count": len(final_state.audit_events),
            "agent_eval": evaluate_agent_results(final_state),
            "workflow_eval": evaluate_workflow(final_state),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
