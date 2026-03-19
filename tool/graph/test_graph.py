from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, TypedDict
from urllib.parse import urlparse

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph


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


@dataclass(frozen=True)
class GraphConfig:
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"


def _llm(cfg: GraphConfig) -> ChatOllama:
    # LangChain Ollama expects bare model name, not "ollama/<model>"
    return ChatOllama(model=cfg.ollama_model, base_url=cfg.ollama_base_url, temperature=0)


def _invoke(llm: ChatOllama, system: str, human: str) -> str:
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
    return clean_output(getattr(resp, "content", str(resp)))


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


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
    USERNAME_FIELD = "input[name='username']"
    PASSWORD_FIELD = "input[name='password']"

    # Buttons
    LOGIN_BUTTON = "button[type='submit']"

    # Messages
    ERROR_MESSAGE = ".error-message"

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
- Use tags: @positive @negative @edge_case @smoke.

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

    g = StateGraph(GenState)
    g.add_node("init", init_node)
    g.add_node("scan", scan_node)
    g.add_node("locators", locators_node)
    g.add_node("test_cases", test_cases_node)
    g.add_node("feature", feature_node)
    g.add_node("steps", steps_node)

    g.set_entry_point("init")
    g.add_edge("init", "scan")
    g.add_edge("scan", "locators")
    g.add_edge("locators", "test_cases")
    g.add_edge("test_cases", "feature")
    g.add_edge("feature", "steps")
    g.add_edge("steps", END)

    return g.compile()


def run_graph(url: str, requirements: str, cfg: GraphConfig | None = None) -> Dict[str, Any]:
    cfg = cfg or GraphConfig()
    graph = build_graph(cfg)
    state: GenState = {"url": url, "requirements": requirements}
    return graph.invoke(state)

