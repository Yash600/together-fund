"""
Generates 3 synthetic pitch-deck PDFs used to test the Deal Screening Agent.
Not part of the runtime app -- run once to (re)create the sample PDFs in
this folder. None of these are real companies.

Usage:
    python generate_decks.py
"""
import os

from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))


def make_deck(filename: str, slides: list[tuple[str, str]]):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for title, body in slides:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.multi_cell(0, 12, title)
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 8, body)
    pdf.output(os.path.join(HERE, filename))
    print(f"wrote {filename}")


# --- Deck 1: Kavach AI -- clean corridor fit, consistent claims ---
kavach_slides = [
    ("Kavach AI", "AI compliance and fraud-detection agents for fintech companies.\n\n"
                  "Founders: Priya Raman (ex-Razorpay risk lead, Bangalore) and Alex Chen "
                  "(ex-Stripe fraud engineering, San Francisco).\n\nSeed round: raising $2.5M."),
    ("The Problem", "Mid-size US and EU fintechs spend 200-400 engineering hours per quarter "
                     "building and maintaining manual compliance and fraud-review workflows. "
                     "Existing compliance tooling (Alloy, Sardine) is priced for enterprise "
                     "customers, leaving a gap for mid-market fintechs."),
    ("Our Product", "Kavach AI deploys an autonomous compliance agent that reviews transaction "
                     "flags, drafts SAR (Suspicious Activity Report) filings, and routes edge "
                     "cases to human reviewers with full audit trails. Agent decisions are "
                     "explainable and logged for regulator review."),
    ("Traction", "6 paying design partners (mid-size US fintechs, $2-15M ARR each).\n"
                 "$22,000 MRR, up from $9,000 three months ago.\n"
                 "Average time-to-review reduced from 4.5 hours to 40 minutes per flagged case "
                 "across design partners."),
    ("Market", "US fintech compliance software spend is estimated at $3.1B annually across "
               "banks, fintechs, and payment processors (source: internal analysis based on "
               "public compliance-vendor revenue disclosures). Mid-market segment (our target) "
               "is roughly $600M of that."),
    ("Team", "Priya Raman - 6 years at Razorpay leading fraud/risk engineering, built their "
             "internal transaction-monitoring system used across 200+ enterprise merchants.\n"
             "Alex Chen - 4 years at Stripe on the fraud engineering team, shipped 2 patents on "
             "anomaly detection.\nTeam of 7, split across Bangalore (5) and San Francisco (2)."),
    ("The Ask", "Raising $2.5M seed at a $16M post-money cap (SAFE). Use of funds: 60% "
                "engineering hires (Bangalore), 25% compliance/legal advisory, 15% GTM."),
]

# --- Deck 2: GrowthPilot AI -- inflated/inconsistent claims, off-thesis (horizontal) ---
growthpilot_slides = [
    ("GrowthPilot AI", "The AI marketing copilot for every business.\n\nRaising $4M seed.\n\n"
                        "Founders: experienced operators from the marketing tech industry."),
    ("The Problem", "Marketing teams waste time writing copy, planning campaigns, and analyzing "
                     "performance across channels."),
    ("Our Product", "GrowthPilot AI generates marketing copy, ad creative, and campaign plans "
                     "using generative AI, with one-click publishing to major ad platforms."),
    ("Traction", "500+ paying customers on our platform today.\n"
                 "$8,000 MRR and growing fast.\n"
                 "Customers love our $500/month Enterprise plan for its ROI."),
    ("Market", "The global marketing technology market is worth $120 billion and growing 15% "
               "annually. Every business that does marketing is a potential customer -- a "
               "massive TAM."),
    ("Team", "Our founding team has deep experience in marketing technology and has built "
             "successful products before."),
    ("The Ask", "Raising $4,000,000 at a $30M post-money valuation to accelerate growth."),
]

# --- Deck 3: Bhasha Health -- vertical AI fit, but India-only market (no corridor claim) ---
bhasha_slides = [
    ("Bhasha Health", "AI clinical documentation assistant for Indian hospitals, supporting "
                       "regional languages (Hindi, Tamil, Bengali, Marathi).\n\n"
                       "Raising 12,000,000 INR (~$145,000) pre-seed.\n\nFounder: Dr. Ananya Rao "
                       "(practicing physician, Bangalore)."),
    ("The Problem", "Indian doctors in public and semi-private hospitals spend an estimated "
                     "90 minutes per day on manual clinical note-taking, in a system where most "
                     "patient conversations happen in regional languages rather than English."),
    ("Our Product", "An ambient AI scribe that listens to doctor-patient conversations in "
                     "regional Indian languages and produces structured clinical notes in "
                     "English and the local language, integrated with common Indian hospital "
                     "management systems."),
    ("Traction", "3 hospital pilot sites in Bangalore and Chennai (2 private, 1 public).\n"
                 "Approximately 40 doctors using the tool daily across pilots.\n"
                 "Self-reported time savings of ~35 minutes/day per doctor in early pilot "
                 "feedback (not yet independently measured)."),
    ("Market", "India has roughly 1.3 million registered allopathic doctors. Clinical "
               "documentation tooling for the Indian regional-language context is largely "
               "unaddressed by existing (English-first, US-built) ambient scribe products."),
    ("Team", "Dr. Ananya Rao - 8 years practicing physician, public hospital experience in "
             "Bangalore, self-taught the initial prototype.\nTeam of 3, all Bangalore, no "
             "prior startup experience."),
    ("The Ask", "Raising 12,000,000 INR pre-seed to expand to 10 hospital sites and hire 2 "
                "engineers."),
]

if __name__ == "__main__":
    make_deck("kavach_ai.pdf", kavach_slides)
    make_deck("growthpilot_ai.pdf", growthpilot_slides)
    make_deck("bhasha_health.pdf", bhasha_slides)
