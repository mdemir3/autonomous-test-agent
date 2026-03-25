from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import ast
import re

mcp = FastMCP("Healer")


@mcp.tool()
async def find_broken_locators(locators_file: str) -> str:
    """Read locators.py and return all locator definitions."""
    try:
        with open(locators_file, "r") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"❌ File not found: {locators_file}"


@mcp.tool()
async def verify_locators_on_page(url: str, locators_file: str) -> str:
    """
    Open the browser, load the URL, and check which locators
    are broken (element not found on page).
    Returns a list of broken locators with details.
    """
    # Read locators file
    try:
        with open(locators_file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return f"❌ Locators file not found: {locators_file}"

    # Parse locator constants from the file
    # Matches: CONSTANT_NAME = "selector"
    pattern = r'(\w+)\s*=\s*["\']([^"\']+)["\']'
    locators = re.findall(pattern, content)

    if not locators:
        return "❌ No locators found in file"

    broken = []
    working = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            await browser.close()
            return f"❌ Could not open URL: {e}"

        for name, selector in locators:
            try:
                # Try to find element with 3 second timeout
                element = await page.wait_for_selector(
                    selector, timeout=3000, state="attached"
                )
                if element:
                    working.append(f"✅ {name} = '{selector}'")
            except Exception:
                broken.append(f"❌ BROKEN: {name} = '{selector}'")

        await browser.close()

    result = f"Checked {len(locators)} locators on {url}\n\n"
    result += f"Working ({len(working)}):\n"
    result += "\n".join(working) + "\n\n"
    result += f"Broken ({len(broken)}):\n"
    result += "\n".join(broken) if broken else "None! All locators work ✅"

    return result


@mcp.tool()
async def scan_page_for_healing(url: str, broken_locator_name: str) -> str:
    """
    Scan the full page to find all possible selectors
    that could replace a broken locator.
    Returns all candidate selectors for the AI to choose from.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            await browser.close()
            return f"❌ Could not open URL: {e}"

        # Scan all interactive elements with full attribute details
        elements = await page.evaluate("""
            () => {
                const items = [];
                const tags = ['input', 'button', 'a', 'select',
                              'textarea', '[data-testid]'];

                tags.forEach(sel => {
                    document.querySelectorAll(sel).forEach((el, idx) => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            // Build multiple selector strategies
                            const selectors = [];

                            if (el.dataset.testid)
                                selectors.push(`[data-testid='${el.dataset.testid}']`);
                            if (el.id)
                                selectors.push(`#${el.id}`);
                            if (el.name)
                                selectors.push(`[name='${el.name}']`);
                            if (el.placeholder)
                                selectors.push(`[placeholder='${el.placeholder}']`);
                            if (el.getAttribute('aria-label'))
                                selectors.push(`[aria-label='${el.getAttribute('aria-label')}']`);
                            if (el.type)
                                selectors.push(`${el.tagName.toLowerCase()}[type='${el.type}']`);
                            if (el.className && el.className.trim())
                                selectors.push(`.${el.className.trim().split(' ')[0]}`);

                            items.push({
                                tag:         el.tagName.toLowerCase(),
                                text:        el.innerText?.trim().substring(0, 40) || null,
                                type:        el.type || null,
                                placeholder: el.placeholder || null,
                                id:          el.id || null,
                                name:        el.name || null,
                                dataTestId:  el.dataset.testid || null,
                                ariaLabel:   el.getAttribute('aria-label') || null,
                                selectors:   selectors,
                            });
                        }
                    });
                });
                return items;
            }
        """)

        await browser.close()

    result = f"Found {len(elements)} elements on page for healing '{broken_locator_name}':\n\n"
    for i, el in enumerate(elements, 1):
        result += f"{i}. <{el['tag']}>"
        if el['text']:        result += f" text='{el['text']}'"
        if el['type']:        result += f" type='{el['type']}'"
        if el['placeholder']: result += f" placeholder='{el['placeholder']}'"
        if el['id']:          result += f" id='{el['id']}'"
        if el['name']:        result += f" name='{el['name']}'"
        if el['dataTestId']:  result += f" data-testid='{el['dataTestId']}'"
        result += f"\n   Selectors: {el['selectors']}\n"

    return result


@mcp.tool()
async def update_locator(
    locators_file: str,
    locator_name: str,
    new_selector: str
) -> str:
    """
    Update a specific locator in the locators.py file
    with a new working selector.
    """
    try:
        with open(locators_file, "r") as f:
            content = f.read()

        # Replace the broken locator with the new one
        pattern = rf'({locator_name}\s*=\s*)["\'][^"\']+["\']'
        new_content = re.sub(pattern, f'{locator_name} = "{new_selector}"', content)

        if new_content == content:
            return f"❌ Could not find locator '{locator_name}' in file"

        with open(locators_file, "w") as f:
            f.write(new_content)

        return f"✅ Healed: {locator_name} = '{new_selector}'"

    except Exception as e:
        return f"❌ Error updating locator: {e}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")