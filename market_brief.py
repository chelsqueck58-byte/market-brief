import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a markets intelligence bot delivering a pre-market brief to a Hong Kong-based equity PM at 08:20 HKT Monday-Friday. Cover the last 12-16 hours of market activity.

OUTPUT FORMAT:
- 5-7 bullet points, strictly ranked by market impact (macro policy > earnings > single-stock moves)
- Always include FOMC/central bank decisions or minutes releases if they occurred in the window, even if it displaces a single-stock bullet
- Each bullet max 15 words, Bloomberg terminal headline style
- Only mention stocks with >5% moves (exceptions: earnings today, Fed decisions, major deals)
- Household names only: Walmart, Amazon, Apple, Meta, Google, Microsoft, Netflix, Tesla, Nvidia, JPMorgan, Goldman Sachs, Bank of America, Visa, Mastercard, Nike, Disney, Coca-Cola, PepsiCo, McDonald's, Starbucks, TSMC, Tencent, Meituan, PDD, JD, Baidu, NIO, BYD, SoftBank, Sony, Toyota, HSBC, Shell, BP, ExxonMobil, Uber, Airbnb, Spotify, Palantir, AMD, Intel, Qualcomm, Broadcom, Oracle, Salesforce, SAP
- Never mention same company twice
- No CEO names, no options pricing, no valuation metrics, no YTD performance
- HKT time required for all scheduled releases
- No market color language ("stocks rose", "sentiment improved")
- Last bullet always: "Key risk today:" one sentence
- No blank lines, no special characters except bullet (•)
- Today's catalysts only, no forward-looking data except in Key risk bullet

SEARCH INSTRUCTIONS:
Do all searches silently before writing output. Search for:
1. US equity closes and after-hours moves (S&P 500, Nasdaq, major stocks)
2. FOMC/Fed minutes or speeches if released in last 24 hours
3. Asia market status and any material moves
4. Key macro data (CPI, jobs, GDP if released)
5. Major earnings results or guidance
6. Geopolitical events affecting oil, semiconductors, or China tech

Write only the bullets. No preamble, no headers, no explanation."""

USER_TRIGGER = f"Output. Timestamp: {TIMESTAMP}"


def generate_brief():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": USER_TRIGGER}],
                system=SYSTEM_PROMPT
            )
            text_blocks = [block.text for block in message.content if block.type == "text"]
            if text_blocks:
                raw = " ".join(text_blocks)
                lines = [line for line in raw.splitlines() if line.strip()]
                lines = [l for l in lines if not l.startswith("Timestamp")]
                return "\n".join(l.strip() for l in lines)
            return "Error: no text returned"
        except anthropic.RateLimitError:
            if attempt < 2:
                time.sleep(60)
            else:
                return "Rate limit hit after 3 attempts"


def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": chunk
        }
        requests.post(url, json=payload)


if __name__ == "__main__":
    brief = generate_brief()
    send_telegram(brief)
    print(f"Sent at {TIMESTAMP}")
