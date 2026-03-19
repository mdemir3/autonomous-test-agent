import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
from tool.graph.test_graph import run_graph

def main():
    print("\n🤖 AI Automation Test Generator")
    print("=" * 50)

    url = input("\n🌐 Enter the URL to test: ").strip()
    if not url:
        url = "https://practicetestautomation.com/practice-test-login/"  # default demo site

    print("\n📋 Enter requirements (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        else:
            lines.append(line)

    requirements = "\n".join(lines)
    if not requirements:
        requirements = print("⚠️  No requirements entered. Please describe the page.")
    

    print("\n🚀 Starting AI agents...\n")
    result = run_graph(url, requirements)

    print("\n✅ Done! Check the output/ folder:")
    print("  📄 output/locators.py")
    print("  📄 output/test_cases.md")
    print("  📄 output/login.feature")
    print("  📄 output/steps/login_steps.py")

def heal():
    from tool.graph.healer import run_healer_sync

    print("\n── HEAL MODE ───────────────────────────────")

    url = input("\n🌐 Enter the URL to verify locators against: ").strip()
    if not url:
        print("⚠️  No URL entered.")
        return

    locators_file = input(
        "📄 Locators file path (press Enter for default 'output/locators.py'): "
    ).strip()

    if not locators_file:
        locators_file = "output/locators.py"

    run_healer_sync(url, locators_file)


if __name__ == "__main__":
    main()

