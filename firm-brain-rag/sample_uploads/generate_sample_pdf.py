"""
Generates a realistic sample PDF (bold section titles via font styling, no
literal markdown '#' characters) for testing/demoing the Firm Brain upload
feature -- a new fictional company not already in data/, so uploading it and
querying immediately demonstrates the live add-to-knowledge-base flow.

Usage:
    python generate_sample_pdf.py
"""
import os

from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))


def build_memo_pdf(path: str):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def heading(text):
        pdf.set_font("Helvetica", "B", 16)
        pdf.ln(4)
        pdf.multi_cell(0, 9, text)
        pdf.ln(1)

    def body(text):
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, text)
        pdf.ln(2)

    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 12, "Investment Memo: Setu Pay")
    pdf.ln(2)

    heading("Summary")
    body(
        "Setu Pay is a payments infrastructure company enabling cross-border B2B "
        "transactions between US and Indian companies, cutting settlement time from "
        "5-7 days to under 24 hours. Founders are two ex-PayPal engineers, one based "
        "in Bangalore and one in New York -- a clean US-India corridor team."
    )

    heading("Traction")
    body(
        "12 paying customers as of this memo, $45,000 USD in monthly recurring "
        "revenue, growing roughly 20% month over month for the last three months. "
        "Customers are mid-size Indian IT services firms billing US clients."
    )

    heading("Team")
    body(
        "8 people total, 5 in Bangalore, 3 in New York. Both founders have 5+ years "
        "of payments infrastructure experience at PayPal, including work on "
        "cross-border settlement rails."
    )

    heading("Market")
    body(
        "Cross-border B2B payments between the US and India are estimated at "
        "roughly $30B annually in services-sector invoicing alone, with settlement "
        "delay and FX friction as the primary complaints from mid-size firms on "
        "both sides."
    )

    heading("Risks")
    body(
        "Regulatory complexity operating across two jurisdictions' payment "
        "licensing regimes, competitive pressure from larger payment processors "
        "entering the corridor, and a long enterprise sales cycle typical of "
        "fintech infrastructure deals."
    )

    heading("Recommendation")
    body(
        "Worth a founder call given the strong payments-infra team background, "
        "believable early enterprise traction, and clear US-India corridor fit. "
        "Key open question: regulatory licensing status in both jurisdictions."
    )

    pdf.output(path)


if __name__ == "__main__":
    out_path = os.path.join(HERE, "setu_pay_memo.pdf")
    build_memo_pdf(out_path)
    print(f"wrote {out_path}")
