import os
import anthropic
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_portfolio_brief(metrics: pd.DataFrame, correlation: pd.DataFrame) -> str:
    """
    Sends the metrics table and correlation matrix to Claude and gets back
    a plain-English portfolio brief — no predictions, just interpretation.
    """
    metrics_text = metrics.to_string()
    corr_text = correlation.round(2).to_string()

    prompt = f"""You are a sharp, plain-speaking investment analyst. A user has asked you to interpret
the following data about a set of UCITS ETFs available to European investors.

PERFORMANCE & RISK METRICS:
{metrics_text}

CORRELATION MATRIX (daily returns):
{corr_text}

Write a concise portfolio brief (250-350 words) covering:
1. Which ETF delivered the best risk-adjusted return and why that matters more than raw return
2. What the correlation matrix reveals about diversification — which combinations actually help
3. One honest warning about the riskiest ETF in the set
4. A single clear recommendation for a European investor who wants simple, long-term whole-market exposure

Be direct. No disclaimers, no "past performance" boilerplate, no bullet-point lists.
Write in plain paragraphs like a knowledgeable friend, not a financial advisor covering their back."""

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
