from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from tool.graph.llm_factory import build_chat_llm


@dataclass(frozen=True)
class HealerConfig:
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"


def _clean(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return text.strip().strip('"\'`').strip()


def _llm(cfg: HealerConfig):
    return build_chat_llm(
        ollama_model=cfg.ollama_model,
        ollama_base_url=cfg.ollama_base_url,
    )


async def run_healer(url: str, locators_file: str = "output/locators.py", cfg: HealerConfig | None = None):
    """
    Self-heal broken locators without CrewAI.
    Uses the existing MCP helper functions, and an Ollama chat model to choose the best selector.
    """
    import asyncio
    import sys

    cfg = cfg or HealerConfig()
    llm = _llm(cfg)

    sys.path.append(".")
    from mcp_servers.mcp_healer import (
        find_broken_locators,
        scan_page_for_healing,
        update_locator,
        verify_locators_on_page,
    )

    print("\n🔍 Starting Self-Healing...")
    print(f"   URL: {url}")
    print(f"   Locators file: {locators_file}\n")

    locators_content = await find_broken_locators(locators_file)
    print(f"📄 Current locators:\n{locators_content}\n")

    verification = await verify_locators_on_page(url, locators_file)
    print(f"🔎 Verification results:\n{verification}\n")

    broken_pattern = r"❌ BROKEN: (\\w+) = \\'([^\\']+)\\'"
    broken_locators = re.findall(broken_pattern, verification)
    if not broken_locators:
        print("✅ All locators are working! No healing needed.")
        return

    for locator_name, broken_selector in broken_locators:
        print(f"\n🔧 Healing: {locator_name} = '{broken_selector}'")
        candidates = await scan_page_for_healing(url, locator_name)

        system = (
            "You are an expert automation engineer specializing in stable selectors. "
            "Return ONLY the new selector string, nothing else."
        )
        human = f"""
The locator '{locator_name}' with selector '{broken_selector}' is broken.

Here are all available elements on the page:
{candidates}

Pick the most stable selector using priority:
data-testid > id > name > placeholder > aria-label > css class > xpath

Output example: input[name='username']
""".strip()
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
        new_selector = _clean(getattr(resp, "content", str(resp)))
        print(f"   🤖 AI suggests: '{new_selector}'")

        fix_result = await update_locator(locators_file, locator_name, new_selector)
        print(f"   {fix_result}")

    print("\n🔄 Running final verification after healing...\n")
    final_check = await verify_locators_on_page(url, locators_file)
    print(final_check)
    print("\n✅ Self-healing complete!")


def run_healer_sync(url: str, locators_file: str = "output/locators.py", cfg: HealerConfig | None = None):
    import asyncio

    return asyncio.run(run_healer(url, locators_file, cfg))

