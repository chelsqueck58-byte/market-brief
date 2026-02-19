import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP for live data from the last 12-16 hours. Do all searches silently. Output only the 3 final paragraphs with zero narration, zero preamble, zero line breaks within paragraphs.

HARD RULES — violations mean the output is wrong:
- Never mention any stock or index move unless it is >5%. No exceptions except: deal announcements, earnings today, Fed decisions.
- Never add line breaks or blank lines within a paragraph.
- Never narrate your search process.
- Never say "markets gained", "stocks rose", "traders weighed" or any market colour.
- Each paragraph is one continuous block of text.
- Max 200 words across all 3 paragraphs.
- Always include HKT time for any scheduled release.
- No EPS numbers.
- Only household names: Walmart, Amazon, Apple, Samsung, Alibaba, Meta, Google, Microsoft, Netflix, Tesla, Nvidia, JPMorgan, Goldman Sachs, Bank of America, Visa, Mastercard, Nike, Disney, Coca-Cola, PepsiCo, McDonald's, Starbucks, TSMC, Tencent, Meituan, PDD, JD, Baidu, NIO, BYD, SoftBank, Sony, Toyota, HSBC, Shell, BP, ExxonMobil, Uber, Airbnb, Spotify, Palantir, AMD, Intel, Qualcomm, Broadcom, Oracle, Salesforce, SAP.

Time context: 8:30am HKT.

Para 1 (US): Lead with biggest catalyst. Deals: what + why it matters to the stock. Earnings today: name + HKT time + what a miss means for the book. Max 3 sentences, no line breaks.

Para 2 (HK/China): >5% moves only. If closed, one clause stating why. One China AI story only if market-moving. No line breaks.

Para 3: "Key risk today:" one sentence."""

USER_TRIGGER = f"Output. Timestamp: {TIMESTAMP}"


def generate_brief():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    for attempt in range(3):
        try:
            message = client.messages.create(
