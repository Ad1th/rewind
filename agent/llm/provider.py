"""LLM Provider Abstraction & Deterministic Demo Provider."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

from agent.runtime.contracts import ActionProposal


class LLMProvider(ABC):
    """Abstract provider interface for LLM Planners."""

    @abstractmethod
    async def generate_proposals(
        self,
        session_id: str,
        goal_prompt: str,
        execution_history: List[Dict[str, Any]],
    ) -> List[ActionProposal]:
        """Generate structured ActionProposals based on goal prompt and execution history."""
        pass


class DeterministicDemoLLMProvider(LLMProvider):
    """Deterministic Demo Provider for choreographed hackathon demonstration scenarios.
    
    LABEL: DEMO_PROVIDER_DETERMINISTIC
    Note: All generated proposals pass through the real, un-mocked REWIND Interceptor & Sandbox Drivers.
    """

    def __init__(self, demo_scenario_proposals: Optional[List[ActionProposal]] = None) -> None:
        self.scenario_proposals = demo_scenario_proposals or []
        self._cursor = 0

    async def generate_proposals(
        self,
        session_id: str,
        goal_prompt: str,
        execution_history: List[Dict[str, Any]],
    ) -> List[ActionProposal]:
        if self._cursor >= len(self.scenario_proposals):
            return []

        proposal = self.scenario_proposals[self._cursor]
        self._cursor += 1
        return [proposal]

    def reset(self) -> None:
        self._cursor = 0
