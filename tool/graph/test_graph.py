from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, TypedDict
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
import subprocess
import sys

from tool.graph.llm_factory import build_chat_llm


def extract_page_name(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").split("/")[-1]
    page_name = path if path else parsed.netloc.split(".")[0]
    return page_name.lower().replace("-", "_").replace(" ", "_")


def clean_output(content: str) -> str:
    content = re.sub(r"```[\w]*\n", "", content)
    content = re.sub(r"```", "", content)
    content = re.sub(r"^Here is.*:\s*\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^This code.*\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^The following.*\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^Below is.*\n", "", content, flags=re.MULTILINE)
    return content.strip()


class GenState(TypedDict, total=False):
    url: str
    requirements: str
    page_name: str
    class_name: str
    scan: str
    locators: str
    test_cases: str
    feature: str
    steps: str
    validation_error: str


@dataclass(frozen=True)
class GraphConfig:
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"


def _llm(cfg: GraphConfig):
    return build_chat_llm(
        ollama_model=cfg.ollama_model,
        ollama_base_url=cfg.ollama_base_url,
    )


def _invoke(llm, system: str, human: str) -> str:
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
    return clean_output(getattr(resp, "content", str(resp)))


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _behave_dry_run(feature_path: str) -> tuple[bool, str]:
    """Run behave --dry-run and return (ok, output)."""
    try:
        p = subprocess.run(
            [sys.executable, "-m", "behave", feature_path, "--dry-run"],
            check=False,
            capture_output=True,
            text=True,
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode == 0, out
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _needs_repair(behave_output: str) -> bool:
    markers = [
        "ParserError:",
        "AmbiguousStep",
        "ImportError:",
        "undefined",
        "UNDEFINED",
    ]
    return any(m in behave_output for m in markers)


def build_graph(cfg: GraphConfig) -> Any:
    llm = _llm(cfg)

    def init_node(state: GenState) -> GenState:
        page_name = extract_page_name(state["url"])
        class_name = page_name.title().replace("_", "") + "PageLocators"
        return {**state, "page_name": page_name, "class_name": class_name}

    def scan_node(state: GenState) -> GenState:
        system = (
            "You are a senior automation engineer. Return ONLY plain text. No markdown, no code fences."
        )
        human = f"""
The page URL is: {state['url']}
Page name: {state['page_name']}

List all interactive elements you would expect on this page based on these requirements:
{state['requirements']}

For each element provide:
- Element name (descriptive)
- Expected HTML tag
- Expected id, name, or data-testid
- Type (if input)
- Purpose
""".strip()
        return {**state, "scan": _invoke(llm, system, human)}

    def locators_node(state: GenState) -> GenState:
        system = (
            "You are a Playwright expert who writes rock-solid locators in a Python class. "
            "Return ONLY Python code (the class). No markdown fences, no explanations."
        )
        human = f"""
Based on the elements list below, write a Python locators file.

Elements:
{state['scan']}

Format it exactly like this:

class {state['class_name']}:
    # Inputs
    PRIMARY_INPUT = "css-or-other-stable-selector"
    SECONDARY_INPUT = "css-or-other-stable-selector"

    # Buttons
    PRIMARY_ACTION_BUTTON = "css-or-other-stable-selector"

    # Messages
    FEEDBACK_MESSAGE = "css-or-other-stable-selector"

Rules:
- The class name MUST be exactly: {state['class_name']} (do not rename it).
- Prefer data-testid > id > placeholder > aria-label > css > xpath.
- Use Playwright locator strings.
- Group by element type with comments.
""".strip()
        content = _invoke(llm, system, human)
        out_path = f"output/{state['page_name']}_locators.py"
        _write(out_path, content)
        return {**state, "locators": content}

    def test_cases_node(state: GenState) -> GenState:
        system = (
            "You are a senior QA engineer. Return ONLY plain text test cases. No markdown fences."
        )
        human = f"""
Write detailed test cases for this page.
URL: {state['url']}
Requirements:
{state['requirements']}

For each test case include:
- TC ID (TC_001, TC_002 etc)
- Title
- Preconditions
- Test Steps (numbered)
- Expected Result
- Test Type (Positive/Negative/Edge Case)

Cover happy path, negative scenarios, edge cases, and boundaries.
""".strip()
        content = _invoke(llm, system, human)
        out_path = f"output/{state['page_name']}_test_cases.md"
        _write(out_path, content)
        return {**state, "test_cases": content}

    def feature_node(state: GenState) -> GenState:
        system = (
            "You are a BDD expert. Return ONLY raw Gherkin feature content. No markdown fences, no explanations."
        )
        human = f"""
Convert these test cases into a Behave-compatible Gherkin feature for the {state['page_name']} page.

Rules:
- Output MUST be valid Gherkin with EXACTLY ONE 'Feature:' header in the whole file.
- Use a Background with: Given the user is on the {state['page_name'].replace('_', ' ')} page
- Use Given for setup, When for actions, Then for assertions (don't mix keywords).
- Keep step text identical across scenarios so step definitions can be reused (avoid paraphrasing).
- For Scenario Outline: use <placeholders> in the FEATURE text (e.g. \"<error>\").
- Every Scenario Outline MUST have an 'Examples:' block indented under it (not at feature level).
- Do not repeat 'Feature:' before scenarios.
- Do NOT put tags directly above Background (Background cannot be tagged).
- Do NOT include 'Examples:' unless the scenario is a Scenario Outline.
- Use tags: @positive @negative @edge_case @smoke.
- Do NOT use {{param}} or unquoted placeholders in the feature; use "<param>" only.

Test cases:
{state['test_cases']}
""".strip()
        content = _invoke(llm, system, human)
        # Guardrail: some models accidentally repeat "Feature:" blocks.
        # Keep only the first "Feature:" header and remove subsequent duplicates.
        lines = content.splitlines()
        feature_seen = False
        cleaned_lines: list[str] = []
        for line in lines:
            if line.strip().startswith("Feature:"):
                if feature_seen:
                    continue
                feature_seen = True
            cleaned_lines.append(line)
        content = "\n".join(cleaned_lines).strip() + "\n"

        # Guardrail: Background cannot be tagged. If a tag line appears immediately
        # before the Background keyword, drop that tag line.
        lines = content.splitlines()
        fixed: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("@"):
                # look ahead to next non-empty line
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and lines[j].lstrip().startswith("Background:"):
                    i += 1
                    continue
            fixed.append(line)
            i += 1
        content = "\n".join(fixed).strip() + "\n"

        # Guardrail: remove stray Examples blocks not under a Scenario Outline.
        # (If the model outputs Examples at feature level, it will break parsing.)
        out_lines: list[str] = []
        in_stray_examples = False
        for line in content.splitlines():
            if re.match(r"^\s*Examples:\s*$", line):
                # Start ignoring unless a Scenario Outline appeared recently in output.
                # This is a blunt guardrail; the validator/repair node handles complex cases.
                in_stray_examples = True
                continue
            if in_stray_examples:
                if line.strip().startswith("|") or line.strip() == "":
                    continue
                # stop skipping when a non-table, non-empty line appears
                in_stray_examples = False
            if not in_stray_examples:
                out_lines.append(line)
        content = "\n".join(out_lines).strip() + "\n"

        out_path = f"output/{state['page_name']}.feature"
        _write(out_path, content)
        return {**state, "feature": content}

    def steps_node(state: GenState) -> GenState:
        system = (
            "You are a Python automation expert. Return ONLY Python code. No markdown fences, no explanations."
        )
        human = f"""
Write Behave step definitions in Python using Playwright for this feature file.

CRITICAL (or steps will be undefined):
0) Do NOT define the same step text twice (Behave will throw AmbiguousStep).
1) If the feature says Given/When/Then, the decorator MUST be @given/@when/@then for that exact step sentence.
2) For Scenario Outline parameters: the feature uses <param> but the step PATTERN must use curly braces, e.g. \"{{param}}\".
   Example: @then('an error message \"{{error}}\" should be displayed') and def step(context, error): ...
3) Implement EVERY distinct step sentence from the feature, including valid values like \"Password123\", success Thens, and longer Thens.
4) Do not use context.parametrize. Use function parameters from the step pattern.
5) Imports must work regardless of current working directory.
6) Import the locator class EXACTLY as written in the locators file: {state['class_name']}.
7) Use Playwright API on context.page with locator strings from L, e.g.:
   context.page.fill(L.USERNAME_FIELD, value)
   context.page.click(L.LOGIN_BUTTON)
   expect(context.page.locator(L.ERROR_MESSAGE)).to_have_text("...")
8) NEVER use: `from behave import async_setup` (invalid in behave 1.3.3).
9) NEVER import page/context objects from Playwright. Use the Behave `context` argument only.

Use this exact file skeleton (fill in ALL step defs below it):

import os
import sys
from behave import given, when, then
from playwright.sync_api import sync_playwright, expect

_out = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _out not in sys.path:
    sys.path.insert(0, _out)
from {state['page_name']}_locators import {state['class_name']} as L

def before_scenario(context, scenario):
    context._playwright = sync_playwright().start()
    context.browser = context._playwright.chromium.launch(headless=True)
    context.page = context.browser.new_page()

def after_scenario(context, scenario):
    context.browser.close()
    context._playwright.stop()

@given('the user is on the {state['page_name'].replace("_", " ")} page')
def step_open_page(context):
    context.page.goto('{state['url']}')

Feature file content:
{state['feature']}
""".strip()
        content = _invoke(llm, system, human)
        out_path = f"output/steps/{state['page_name']}_steps.py"
        _write(out_path, content)
        return {**state, "steps": content}

    def validate_and_repair_node(state: GenState) -> GenState:
        feature_path = f"output/{state['page_name']}.feature"

        # Try a few times: generation models sometimes need 1-2 iterations to converge.
        last_out = ""
        for _attempt in range(3):
            ok, out = _behave_dry_run(feature_path)
            last_out = out
            if ok and not _needs_repair(out):
                return {**state, "validation_error": ""}

            # Ask the model to rewrite BOTH files using the dry-run output as ground truth.
            system = (
                "You fix Behave projects. Return ONLY raw file contents exactly as requested."
            )
            human = f"""
Behave dry-run failed. Fix the GENERATED FILES so that:
- The feature is valid Gherkin (single Feature:, Background not tagged, Examples only under Scenario Outline).
- Steps file loads without errors (imports + no duplicate step decorators) and covers every step sentence.
- Step decorators keyword must match feature keyword (Given/When/Then).
- Scenario Outline params: feature uses <param>, step patterns use \"{{param}}\".
- Steps must import locators: from {state['page_name']}_locators import {state['class_name']} as L
- Steps must use context.page with L constants (strings), not L.some_locator_object.
- The steps file MUST start with all required imports: behave decorators + Playwright expect + sync_playwright.
- Do not use `from behave import async_setup`.
- Do not import `context` or `page` from Playwright.

Dry-run output:
{out}

Current feature file:
{state['feature']}

Current steps file:
{state.get('steps','')}

Return EXACTLY TWO SECTIONS in this order, with these headers on their own lines:
===FEATURE===
<fixed gherkin>
===STEPS===
<fixed python>
""".strip()
            fixed = _invoke(llm, system, human)
            if "===FEATURE===" in fixed and "===STEPS===" in fixed:
                feat = (
                    fixed.split("===FEATURE===")[1]
                    .split("===STEPS===")[0]
                    .strip()
                    + "\n"
                )
                steps = fixed.split("===STEPS===")[1].strip() + "\n"
                _write(feature_path, feat)
                _write(f"output/steps/{state['page_name']}_steps.py", steps)
                state = {**state, "feature": feat, "steps": steps}
                continue

            # If the model didn't follow the format, don't overwrite files; just break.
            break

        return {**state, "validation_error": last_out}

    g = StateGraph(GenState)
    g.add_node("init", init_node)
    g.add_node("scan", scan_node)
    g.add_node("locators", locators_node)
    g.add_node("test_cases", test_cases_node)
    g.add_node("feature", feature_node)
    g.add_node("steps", steps_node)
    g.add_node("validate", validate_and_repair_node)

    g.set_entry_point("init")
    g.add_edge("init", "scan")
    g.add_edge("scan", "locators")
    g.add_edge("locators", "test_cases")
    g.add_edge("test_cases", "feature")
    g.add_edge("feature", "steps")
    g.add_edge("steps", "validate")
    g.add_edge("validate", END)

    return g.compile()


def run_graph(url: str, requirements: str, cfg: GraphConfig | None = None) -> Dict[str, Any]:
    cfg = cfg or GraphConfig()
    graph = build_graph(cfg)
    state: GenState = {"url": url, "requirements": requirements}
    return graph.invoke(state)

