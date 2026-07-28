import asyncio

from models import AgentResult, AgentStatus, AgentTask


async def run_with_budget(agent_fn, task: AgentTask) -> AgentResult:
    for attempt in range(task.max_retries + 1):
        try:
            return await asyncio.wait_for(
                agent_fn(task),
                timeout=task.timeout_ms / 1000,
            )
        except TimeoutError:
            if attempt == task.max_retries:
                return AgentResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    status=AgentStatus.TIMED_OUT,
                    confidence=0.0,
                    output_version="none",
                    evidence_refs=[],
                    failure_reason="timeout_budget_exceeded",
                    data={"attempts": attempt + 1},
                )

    raise RuntimeError("unreachable")
