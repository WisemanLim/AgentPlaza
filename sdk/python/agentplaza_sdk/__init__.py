"""agentplaza-sdk — Addon 에이전트 공통 골격 (D4-03).

에이전트 작성자는 capability 핸들러만 쓴다. REST·MCP·A2A 표면은 SDK 가 agent.yaml 을 읽어 붙인다(DP4).
"""
from agentplaza_sdk.agent import Agent, CapabilityError, Context
from agentplaza_sdk.app import create_app
from agentplaza_sdk.llm import LLMClient

__all__ = ["Agent", "CapabilityError", "Context", "LLMClient", "create_app"]
__version__ = "0.1.0"
