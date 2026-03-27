from __future__ import annotations

import json
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


def _json_or_none(text: str):
    """Best-effort JSON extraction from model output."""
    cleaned = _clean(text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # Try extracting first JSON object block
    m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


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
            "You are a QA healing classifier. Decide whether this is safe to auto-heal "
            "or likely a product bug/spec drift. Return JSON only."
        )
        human = f"""
The locator '{locator_name}' with selector '{broken_selector}' is broken.

Here are all available elements on the page:
{candidates}

Rules:
- Prefer semantic match to locator intent (name/text/type/purpose), not only existence.
- If no strong semantic match exists, classify as potential_bug.
- If there is a strong match, propose the best stable selector with priority:
  data-testid > id > name > placeholder > aria-label > css class > xpath

Return strict JSON with this schema:
{{
  "decision": "safe_heal" | "potential_bug",
  "confidence": 0.0-1.0,
  "reason": "short rationale",
  "new_selector": "selector or empty string",
  "risk_note": "what could still go wrong"
}}
""".strip()
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
        parsed = _json_or_none(getattr(resp, "content", str(resp)))

        if not isinstance(parsed, dict):
            print("   ⚠️ Could not parse classifier output. Marking as potential_bug.")
            print("   decision=potential_bug confidence=0.0 reason=parse_error")
            continue

        decision = str(parsed.get("decision", "potential_bug")).strip().lower()
        confidence = parsed.get("confidence", 0.0)
        reason = str(parsed.get("reason", "")).strip()
        risk_note = str(parsed.get("risk_note", "")).strip()
        new_selector = str(parsed.get("new_selector", "")).strip()

        print(f"   🧠 decision={decision} confidence={confidence}")
        if reason:
            print(f"   reason: {reason}")
        if risk_note:
            print(f"   risk: {risk_note}")

        if decision != "safe_heal" or not new_selector:
            print("   🚫 Not auto-healing; classify as potential product bug/spec drift.")
            continue

        print(f"   🤖 applying selector: '{new_selector}'")
        fix_result = await update_locator(locators_file, locator_name, new_selector)
        print(f"   {fix_result}")

    print("\n🔄 Running final verification after healing...\n")
    final_check = await verify_locators_on_page(url, locators_file)
    print(final_check)
    print("\n✅ Self-healing complete!")


def run_healer_sync(url: str, locators_file: str = "output/locators.py", cfg: HealerConfig | None = None):
    import asyncio

    return asyncio.run(run_healer(url, locators_file, cfg))

