from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("Browser")

@mcp.tool()
async def scan_page_elements(url: str) -> str:
    """Open browser with Playwright and scan all interactive elements on the page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        elements = await page.evaluate("""
            () => {
                const items = [];
                const selectors = [
                    'input', 'button', 'a', 'select',
                    'textarea', '[data-testid]', '[placeholder]'
                ];

                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            items.push({
                                tag:         el.tagName.toLowerCase(),
                                id:          el.id || null,
                                name:        el.name || null,
                                type:        el.type || null,
                                text:        el.innerText?.trim().substring(0, 50) || null,
                                placeholder: el.placeholder || null,
                                dataTestId:  el.dataset.testid || null,
                                className:   el.className || null,
                                ariaLabel:   el.getAttribute('aria-label') || null,
                                href:        el.href || null,
                            });
                        }
                    });
                });

                // remove duplicates
                const seen = new Set();
                return items.filter(el => {
                    const key = JSON.stringify(el);
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
            }
        """)

        await browser.close()

        result = f"Found {len(elements)} elements on {url}:\n\n"
        for i, el in enumerate(elements, 1):
            result += f"{i}. Tag: {el['tag']}"
            if el['id']:          result += f" | id='{el['id']}'"
            if el['name']:        result += f" | name='{el['name']}'"
            if el['type']:        result += f" | type='{el['type']}'"
            if el['text']:        result += f" | text='{el['text']}'"
            if el['placeholder']: result += f" | placeholder='{el['placeholder']}'"
            if el['dataTestId']:  result += f" | data-testid='{el['dataTestId']}'"
            if el['ariaLabel']:   result += f" | aria-label='{el['ariaLabel']}'"
            result += "\n"

        return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
