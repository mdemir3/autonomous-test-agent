# AI Test Agent

A small Python project that uses **LangGraph** + **LangChain** chat models to generate BDD-style test artifacts from a URL and free-text requirements: locators, test cases, a **Behave** `.feature` file, and Playwright-based step definitions under `output/`.

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) for installing dependencies
- **LLM backend** (pick one):
  - **[Ollama](https://ollama.com/)** locally (default) — `http://localhost:11434`, model `llama3` (or change `GraphConfig` in `tool/graph/test_graph.py`)
  - **OpenAI** — API key + optional model name (see below)
  - **Anthropic (Claude)** — API key + optional model name (see below)

## Setup

From the project root:

```bash
uv sync
```

For **OpenAI** or **Claude**, install the matching integrations (optional extras):

```bash
uv sync --extra openai          # ChatGPT / OpenAI API
uv sync --extra anthropic       # Claude
# or both:
uv sync --extra cloud
```

Install Playwright browsers (one-time):

```bash
uv run playwright install chromium
```

## Run the generator

```bash
uv run python main.py
```

You will be prompted for:

1. **URL** to test (empty input falls back to the practice test login demo URL in `main.py`).
2. **Requirements** — describe what to validate; finish with a blank line after at least one line of text.

Artifacts are written under `output/`, named from the last path segment of the URL, for example:

| File | Purpose |
|------|---------|
| `output/<page>_locators.py` | Locator constants for Playwright |
| `output/<page>_test_cases.md` | Human-readable test cases |
| `output/<page>.feature` | Gherkin / Behave feature |
| `output/steps/<page>_steps.py` | Behave step definitions |

The LangGraph pipeline ends with a **`behave --dry-run` check** on the generated feature. If validation still fails after automatic repair attempts, `main.py` prints the Behave output under **“Behave dry-run still failing after auto-repair.”**

## Run Behave

`behave.ini` points Behave at the `output/` tree:

```ini
[behave]
paths = output
```

Dry-run (no browser execution):

```bash
uv run python -m behave output --dry-run
```

Run a single feature:

```bash
uv run python -m behave output/<page>.feature
```

## Healer (optional)

Locator healing logic lives in `tool/graph/healer.py` (`run_healer_sync`). It uses your MCP helpers in `mcp_servers/mcp_healer.py` plus the configured chat model (Ollama / OpenAI / Claude — same `LLM_PROVIDER` as above) to suggest replacement selectors. Wire it from your own entrypoint or call it from Python:

```python
from tool.graph.healer import run_healer_sync
run_healer_sync("https://example.com/login", "output/your_locators.py")
```

## Project layout (high level)

- `main.py` — CLI entry; calls `run_graph` from `tool.graph.test_graph`
- `tool/graph/test_graph.py` — LangGraph workflow (scan → locators → test cases → feature → steps → validate)
- `tool/graph/healer.py` — Self-healing flow for locators
- `mcp_servers/` — MCP-related helpers used by the healer
- `output/` — Generated files (safe to regenerate; do not commit secrets)

## Configuration

### LLM provider (Ollama vs OpenAI vs Claude)

The project picks a chat model in `tool/graph/llm_factory.py` using the **`LLM_PROVIDER`** environment variable:

| `LLM_PROVIDER` | What you need |
|----------------|---------------|
| `ollama` (default) | Ollama running; optional: tune `ollama_model` / `ollama_base_url` via `GraphConfig` / `HealerConfig` in code |
| `openai` | `OPENAI_API_KEY`; optional `OPENAI_MODEL` (default `gpt-4o-mini`) |
| `anthropic` (or `claude`) | `ANTHROPIC_API_KEY`; optional `ANTHROPIC_MODEL` (default `claude-3-5-sonnet-20241022`) |

**Examples — OpenAI**

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
# optional:
export OPENAI_MODEL=gpt-4o-mini
uv run python main.py
```

**Examples — Anthropic Claude**

```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
# optional:
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
uv run python main.py
```

**Default — Ollama (no env needed)**

```bash
uv run python main.py
```

The same provider applies to the generator (`tool/graph/test_graph.py`) and the healer (`tool/graph/healer.py`).

If you see an import error mentioning `langchain-openai` or `langchain-anthropic`, run the matching `uv sync --extra ...` command from the setup section above.

### Ollama tuning in code

`GraphConfig` / `HealerConfig` still control **Ollama-only** settings: `ollama_model` (default `llama3`) and `ollama_base_url` (default `http://localhost:11434`). They are ignored when `LLM_PROVIDER` is `openai` or `anthropic`.
