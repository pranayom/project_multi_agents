# Production-Grade Multi-Agent Systems

I wrote this repo alongside a three-article Substack series about the controls around a multi-agent workflow. The running example is insurance claim triage. An agent can recommend a $1,200 payment, but it cannot move the money. That decision passes through a policy gate and, in this example, goes to a human.

The code is plain Python with deterministic mock agents. There is no agent framework or model API to configure. I wanted the control flow to stay visible: typed handoffs, workflow state outside agent memory, platform-owned transitions, scoped tool access, audit events, execution budgets, and approval for high-impact actions.

## The articles

1. [Building Production Grade Multi-Agent Systems - Part 1](https://pranaytiwari.substack.com/p/building-production-grade-multi-agent?r=1cfec): The control plane pattern.

2. [Building Production Grade Multi-Agent Systems - Part 2a](https://pranaytiwari.substack.com/p/building-production-grade-multi-agent-c63?r=1cfec): Identity, context boundaries, and tool validation.

3. [Building Production Grade Multi-Agent Systems - Part 2b](https://pranaytiwari.substack.com/p/building-production-grade-multi-agent-c39?r=1cfec): Execution budgets, side-effect gates, and evaluation.

## How the code is organized

[`part_1/`](part_1/) follows the first article. It has specialist agents, typed task contracts, a state machine, durable workflow state, and a small policy gate around payment.

[`part_2/`](part_2/) carries the same claim through the controls discussed in Parts 2a and 2b. It adds agent identity, scoped permissions, prompt-injection checks, tool-call validation, time budgets, audit events, risk-based escalation, and workflow evaluation.

Both examples are intentionally small. They are meant to make the boundaries easy to inspect, not to pass as a production claims system.

## Run the examples

You need Python 3.10 or newer. The examples use only the standard library.

```bash
python part_1/run_claim_triage.py
python part_2/run_claim_triage.py
```

Each run starts with claim `CLM-1001` for water damage from a burst pipe. The agents triage the claim and propose an action. The workflow stops the payment action at the control plane and records that human approval is required.
