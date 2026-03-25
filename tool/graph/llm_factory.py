"""Build a LangChain chat model from env (Ollama, OpenAI, or Anthropic)."""
from __future__ import annotations

import os
from typing import Any


def build_chat_llm(
    *,
    ollama_model: str = "llama3",
    ollama_base_url: str = "http://localhost:11434",
) -> Any:
    """
    Select provider with LLM_PROVIDER:
    - ollama (default): local Ollama
    - openai: needs OPENAI_API_KEY; optional OPENAI_MODEL (default gpt-4o-mini)
    - anthropic: needs ANTHROPIC_API_KEY; optional ANTHROPIC_MODEL
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider in ("openai", "gpt"):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "langchain-openai is not installed. Run: uv sync --extra openai"
            ) from e

        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai. "
                "Install: uv sync --extra openai"
            )
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            api_key=key,
        )

    if provider in ("anthropic", "claude"):
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:
            raise ImportError(
                "langchain-anthropic is not installed. Run: uv sync --extra anthropic"
            ) from e

        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic. "
                "Install: uv sync --extra anthropic"
            )
        return ChatAnthropic(
            model=os.getenv(
                "ANTHROPIC_MODEL",
                "claude-3-5-sonnet-20241022",
            ),
            temperature=0,
            api_key=key,
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=ollama_model,
        base_url=ollama_base_url,
        temperature=0,
    )
