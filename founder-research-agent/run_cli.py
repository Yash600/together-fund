"""
Standalone CLI entry point.

Usage:
    python run_cli.py "Founder Name" "Company Name"
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.graph import run_research

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 3:
        print('Usage: python run_cli.py "Founder Name" "Company Name"')
        sys.exit(1)
    founder_name = sys.argv[1]
    company_name = sys.argv[2]

    print("\n=== Founder Research Agent ===")
    print(f"Founder: {founder_name}")
    print(f"Company: {company_name}\n")
    print("--- reasoning trace ---")

    final_brief = None
    for event in run_research(founder_name, company_name):
        if event["type"] == "log":
            data_str = f"  {event['data']}" if "data" in event else ""
            print(f"[{event['step']}] {event['detail']}{data_str}")
        elif event["type"] == "result":
            final_brief = event["brief"]

    print("\n--- research brief ---\n")
    print(final_brief)
    print()

    out_dir = os.path.join(HERE, "output")
    os.makedirs(out_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() else "_" for c in f"{founder_name}_{company_name}")
    out_path = os.path.join(out_dir, f"{safe_name}_brief.md")
    with open(out_path, "w") as f:
        f.write(final_brief)
    print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
