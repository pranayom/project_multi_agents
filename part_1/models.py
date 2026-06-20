from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    DEGRADED = "degraded"


class WorkflowStatus(str, Enum):
    INTAKE = "intake"
    RUNNING_AGENTS = "running_agents"
    DECISION_PENDING = "decision_pending"
    HUMAN_REVIEW = "human_review"
    SAFE_FALLBACK = "safe_fallback"
    COMPLETED = "completed"


@dataclass(frozen=True)
class ClaimInput:
    claim_id: str
    policy_id: str
    customer_id: str
    amount_usd: int
    loss_description: str
    uploaded_document_text: str


@dataclass(frozen=True)
class AgentTask:
    workflow_id: str
    task_id: str
    agent_name: str
    input_version: str
    timeout_ms: int
    max_retries: int
    max_tool_calls: int
    max_output_tokens: int
    payload: dict


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    agent_name: str
    status: AgentStatus
    confidence: float
    output_version: str
    evidence_refs: list[str]
    data: dict = field(default_factory=dict)
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class WorkflowState:
    workflow_id: str
    claim: ClaimInput
    status: WorkflowStatus = WorkflowStatus.INTAKE
    task_results: dict[str, AgentResult] = field(default_factory=dict)
    policy_gate_result: str | None = None
    proposed_action: str | None = None
    final_action: str | None = None
