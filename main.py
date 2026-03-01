import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sys, os
_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "tool"))
from crew.test_crew import run_crew

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
    result = run_crew(url, requirements)

    print("\n✅ Done! Check the output/ folder:")
    print("  📄 output/locators.py")
    print("  📄 output/test_cases.md")
    print("  📄 output/login.feature")
    print("  📄 output/steps/login_steps.py")

if __name__ == "__main__":
    main()
