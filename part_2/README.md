# Part 2 Code: Controls, Runtime Boundaries, and Evaluation

This folder supports Part 2 of the Substack series:

**Building Production-Grade Multi-Agent Systems, Part 2: Controls, Runtime Boundaries, and Evaluation**

The code remains framework-free. It demonstrates production controls around the same claim-payment workflow from Part 1:

- Least-agency tool permissions.
- Agent identity and scoped credentials.
- Tool-call validation before execution.
- Execution budgets.
- Audit logging.
- Risk-based human escalation.
- Agent-level and workflow-level evaluation.

Run:

```bash
python part_2/run_claim_triage.py
```

The sample workflow proposes `payment.issue`, but the tool runtime denies direct agent access. The control plane routes the payment action to human approval.
