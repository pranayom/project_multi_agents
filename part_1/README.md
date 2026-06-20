# Part 1 Code: Control Plane Pattern

This folder supports Part 1 of the Substack series:

**Building Production-Grade Multi-Agent Systems, Part 1: The Control Plane Pattern**

The code is intentionally framework-free. It demonstrates the architecture:

- Narrow specialist agents.
- Typed handoffs.
- Durable workflow state outside agents.
- A state machine controlled by the platform.
- A policy gate that prevents unsafe side effects such as `issue_payment`.

Run:

```bash
python part_1/run_claim_triage.py
```

The claim can be triaged, but payment cannot be issued directly by an agent. The control plane gates that side effect and routes it to human approval.
