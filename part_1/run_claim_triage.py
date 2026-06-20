from pprint import pprint

from models import ClaimInput
from orchestrator import triage_claim


if __name__ == "__main__":
    claim = ClaimInput(
        claim_id="CLM-1001",
        policy_id="POL-42",
        customer_id="CUST-9",
        amount_usd=1200,
        loss_description="Water damage from a burst pipe.",
        uploaded_document_text="Customer uploaded contractor invoice and photos.",
    )

    final_state = triage_claim(claim)

    pprint(
        {
            "workflow_id": final_state.workflow_id,
            "status": final_state.status.value,
            "proposed_action": final_state.proposed_action,
            "policy_gate_result": final_state.policy_gate_result,
            "final_action": final_state.final_action,
        }
    )
