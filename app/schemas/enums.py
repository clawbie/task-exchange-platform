from enum import Enum


class ActorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"


class ExecutorConstraints(str, Enum):
    HUMAN_ONLY = "human_only"
    AGENT_ONLY = "agent_only"
    HUMAN_OR_AGENT = "human_or_agent"


class ReasoningTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BrowserRequirement(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    INTERACTIVE = "interactive"


class ComputeRequirement(str, Enum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"


class SpeedPriority(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"
