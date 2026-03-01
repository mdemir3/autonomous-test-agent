from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("FileWriter")

@mcp.tool()
async def save_file(filename: str, content: str) -> str:
    """Save content to a file in the output directory."""
    os.makedirs("output/steps", exist_ok=True)

    if filename.endswith("_steps.py") or "steps" in filename:
        filepath = f"output/steps/{filename}"
    else:
        filepath = f"output/{filename}"

    with open(filepath, "w") as f:
        f.write(content)

    return f"✅ File saved: {filepath}"

@mcp.tool()
async def read_file(filename: str) -> str:
    """Read a file from the output directory."""
    filepath = f"output/{filename}"
    if not os.path.exists(filepath):
        return f"❌ File not found: {filepath}"
    with open(filepath, "r") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
