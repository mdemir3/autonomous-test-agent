from typing import Any, Optional, Union

from crewai import Agent, Task, Crew, Process
from crewai import BaseLLM
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# ── Custom Ollama LLM (no LiteLLM) ───────────────────────────────────────────

class OllamaLLM(BaseLLM):
    """CrewAI-compatible LLM using LangChain ChatOllama (works without LiteLLM)."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        temperature: Optional[float] = 0.2,
        **kwargs: Any,
    ) -> None:
        # Strip ollama/ prefix if present
        model_name = model.split("/")[-1] if "/" in model else model
        super().__init__(model=model_name, temperature=temperature, **kwargs)
        self._chat = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=temperature or 0.2,
        )

    def _to_lc_messages(
        self, messages: Union[str, list]
    ) -> list[BaseMessage]:
        if isinstance(messages, str):
            return [HumanMessage(content=messages)]
        out: list[BaseMessage] = []
        for m in messages:
            role = (m.get("role") or "user").lower()
            content = m.get("content") or ""
            if role == "system":
                out.append(SystemMessage(content=content))
            elif role == "assistant":
                out.append(AIMessage(content=content))
            else:
                out.append(HumanMessage(content=content))
        return out

    def call(
        self,
        messages: Union[str, list],
        tools: Optional[list] = None,
        callbacks: Optional[list] = None,
        available_functions: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        lc_messages = self._to_lc_messages(messages)
        response = self._chat.invoke(lc_messages)
        return response.content if hasattr(response, "content") else str(response)

    def get_context_window_size(self) -> int:
        return 8192

    def supports_function_calling(self) -> bool:
        return False


# ── LLM ─────────────────────────────────────────────────────────────────────
llm = OllamaLLM(
    model="llama3",
    base_url="http://localhost:11434",
    temperature=0.2,
)

# ── AGENTS ───────────────────────────────────────────────────────────────────

browser_scanner = Agent(
    role="Browser Scanner",
    goal="Scan web pages and extract all interactive elements clearly",
    backstory="""You are a senior automation engineer expert at 
    inspecting web pages. You identify every button, input, link, 
    dropdown and interactive element on a page. You return structured, 
    clean data about each element.
    IMPORTANT: Return ONLY the code. No explanations, 
no markdown fences, no 'Here is...' text. Just raw code.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

locator_writer = Agent(
    role="Locator Writer",
    goal="Write clean, reliable Playwright locators from scanned elements",
    backstory="""You are a Playwright expert who writes rock-solid locators. 
    You follow this priority order:
    1. data-testid (most stable)
    2. id
    3. placeholder
    4. aria-label
    5. css selector
    6. xpath (last resort)
    You write locators in Page Object Model style as a Python class.
    IMPORTANT: Return ONLY the code. No explanations, 
    no markdown fences, no 'Here is...' text. Just raw code.
    """,
    llm=llm,
    verbose=True,
    allow_delegation=False
)

test_case_writer = Agent(
    role="Test Case Writer",
    goal="Write comprehensive test cases covering all scenarios",
    backstory="""You are a senior QA engineer with 10 years experience. 
    You write detailed test cases covering:
    - Happy path (valid data)
    - Negative scenarios (invalid data)
    - Edge cases (empty fields, special characters)
    - Boundary conditions
    You are thorough and never miss a scenario.
    IMPORTANT: Return ONLY the code. No explanations, 
no markdown fences, no 'Here is...' text. Just raw code.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

feature_writer = Agent(
    role="BDD Feature File Writer",
    goal="Write clean Gherkin feature files from test cases",
    backstory="""You are a BDD expert. You write crystal clear 
    Given/When/Then scenarios in Gherkin syntax that even 
    non-technical stakeholders can understand. You use Scenario 
    Outline for data-driven tests and always add meaningful tags.
    IMPORTANT: Return ONLY the code. No explanations, 
no markdown fences, no 'Here is...' text. Just raw code.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

step_writer = Agent(
    role="Step Definition Writer",
    goal="Write Behave step definitions in Python for the feature file",
    backstory="""You are a Python automation expert. You write clean 
    Behave step definitions using Playwright. You use the locators 
    from the locators file and implement each Given/When/Then step 
    with proper waits and assertions.
    IMPORTANT: Return ONLY the code. No explanations, 
no markdown fences, no 'Here is...' text. Just raw code.""",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# ── TASKS ─────────────────────────────────────────────────────────────────────

def build_tasks(url: str, requirements: str):

    scan_task = Task(
        description=f"""
        The page URL is: {url}
        
        List all interactive elements you would expect on this page based on 
        these requirements: {requirements}
        
        For each element provide:
        - Element name (descriptive)
        - Expected HTML tag
        - Expected id, name, or data-testid
        - Type (if input)
        - Purpose
        
        Return a clean structured list.
        """,
        expected_output="Structured list of all page elements with attributes",
        agent=browser_scanner
    )

    locator_task = Task(
        description="""
        Based on the elements identified, write a Python locators file.
        
        Format it exactly like this:
        
        class LoginPageLocators:
            # Inputs
            USERNAME_FIELD = "input[name='username']"
            PASSWORD_FIELD = "input[name='password']"
            
            # Buttons
            LOGIN_BUTTON = "button[type='submit']"
            
            # Messages
            ERROR_MESSAGE = ".error-message"
            SUCCESS_MESSAGE = ".success-message"
        
        Use Playwright locator syntax.
        Name each constant clearly in UPPER_SNAKE_CASE.
        Group by element type with comments.
        """,
        expected_output="Complete Python locators file with Page Object Model class",
        agent=locator_writer,
        output_file="output/locators.py"
    )

    test_case_task = Task(
        description=f"""
        Write detailed test cases for this page based on:
        Requirements: {requirements}
        
        For each test case include:
        - TC ID (TC_001, TC_002 etc)
        - Title
        - Preconditions
        - Test Steps (numbered)
        - Expected Result
        - Test Type (Positive/Negative/Edge Case)
        
        Cover ALL scenarios thoroughly.
        """,
        expected_output="Complete list of test cases in structured format",
        agent=test_case_writer,
        output_file="output/test_cases.md"
    )

    feature_task = Task(
        description="""
        Convert the test cases into a proper Gherkin feature file for Behave.
        
        Follow this exact format:
        
        Feature: [Feature name]
          As a [user type]
          I want to [action]
          So that [benefit]
        
          Background:
            Given the user is on the login page
        
          @positive
          Scenario: Successful login with valid credentials
            Given the user enters valid username "student"
            And the user enters valid password "Password123"
            When the user clicks the login button
            Then the user should be redirected to the dashboard
            And the welcome message should be displayed
        
          @negative
          Scenario Outline: Login fails with invalid credentials
            Given the user enters username "<username>"
            And the user enters password "<password>"
            When the user clicks the login button
            Then an error message "<error>" should be displayed
        
            Examples:
              | username      | password      | error                    |
              | invalid_user  | secret_sauce  | Username is incorrect    |
              | standard_user | wrong_pass    | Password is incorrect    |
              |               |               | Username is required     |
        
        Use tags: @positive @negative @edge_case @smoke
        """,
        expected_output="Complete .feature file in Gherkin syntax",
        agent=feature_writer,
        output_file="output/login.feature"
    )

    step_task = Task(
        description="""
        Write Behave step definitions in Python using Playwright.
        
        Use this exact structure:
        
        from behave import given, when, then
        from playwright.sync_api import sync_playwright
        
        # Import locators
        import sys
        sys.path.append('../')
        from output.locators import LoginPageLocators as L
        
        def before_scenario(context, scenario):
            playwright = sync_playwright().start()
            context.browser = playwright.chromium.launch(headless=False)
            context.page = context.browser.new_page()
        
        def after_scenario(context, scenario):
            context.browser.close()
        
        @given('the user is on the login page')
        def step_open_login_page(context):
            context.page.goto("https://yourapp.com/login")
        
        @given('the user enters valid username "{username}"')
        def step_enter_username(context, username):
            context.page.fill(L.USERNAME_FIELD, username)
        
        # implement ALL steps from the feature file
        
        Write ALL steps. Use proper Playwright methods:
        - page.fill() for inputs
        - page.click() for buttons  
        - page.expect_url() for navigation
        - page.locator().text_content() for text checks
        - expect(page.locator()).to_be_visible() for visibility
        """,
        expected_output="Complete Behave step definitions Python file",
        agent=step_writer,
        output_file="output/steps/login_steps.py"
    )

    return [scan_task, locator_task, test_case_task, feature_task, step_task]


# ── CREW ──────────────────────────────────────────────────────────────────────

def run_crew(url: str, requirements: str):
    import os
    os.makedirs("output/steps", exist_ok=True)

    tasks = build_tasks(url, requirements)

    crew = Crew(
        agents=[
            browser_scanner,
            locator_writer,
            test_case_writer,
            feature_writer,
            step_writer
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()

    # Save each task output manually
    outputs = [task.output.raw for task in tasks if task.output]

    file_map = {
        0: None,                          # scan task - no file needed
        1: "output/locators.py",
        2: "output/test_cases.md",
        3: "output/login.feature",
        4: "output/steps/login_steps.py"
    }

    for i, filepath in file_map.items():
        if filepath and i < len(outputs) and outputs[i]:
            # strip markdown code fences if present
            content = outputs[i]
            content = content.replace("```python", "").replace("```Python", "")
            content = content.replace("```gherkin", "").replace("```", "")
            content = content.replace("```", "").strip()

            with open(filepath, "w") as f:
                f.write(content)
            print(f"✅ Saved: {filepath}")

    return result
