"""
Standalone CLI entry point.

Usage:
    python run_cli.py sample_decks/kavach_ai.pdf
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.graph import run_screening
from agent.parser import extract_text

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_cli.py <path_to_pitch_deck.pdf>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"[error] File not found: {pdf_path}")
        sys.exit(1)

    print(f"\n=== Deal Screening Agent ===")
    print(f"Deck: {pdf_path}\n")
    print("[parse] Extracting raw text from PDF...")
    raw_text, used_ocr = extract_text(pdf_path)
    print(f"[parse] Extracted {len(raw_text)} characters" + (" (used OCR fallback)" if used_ocr else "") + "\n")
    if len(raw_text.strip()) < 100:
        print("[parse] Warning: very little text extracted -- memo below will be low-confidence.\n")

    print("--- reasoning trace ---")
    final_memo = None
    for event in run_screening(raw_text):
        if event["type"] == "log":
            data_str = f"  {event['data']}" if "data" in event else ""
            print(f"[{event['step']}] {event['detail']}{data_str}")
        elif event["type"] == "result":
            final_memo = event["memo"]

    print("\n--- screening memo ---\n")
    print(final_memo)
    print()

    out_dir = os.path.join(HERE, "output")
    os.makedirs(out_dir, exist_ok=True)
    out_name = os.path.splitext(os.path.basename(pdf_path))[0] + "_memo.md"
    out_path = os.path.join(out_dir, out_name)
    with open(out_path, "w") as f:
        f.write(final_memo)
    print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
