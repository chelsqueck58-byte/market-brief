import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP for live data from the last 12-16 hours. Do all searches silently. Output only bullet points. No narration. No preamble. No blank lines. No paragraph headers.

HARD RULES:
- Output exactly 3 to 6 bullet points total. No more. No less.
- Each bullet must start with exactly this character: •
- Each bullet is one sentence. Max 15 words per bullet.
- No blank lines between bullets. No line breaks within a bullet.
- Rank bullets from most important to least important.
- Never mention the same company twice across all bullets.
- Only mention a stock if move is >5%. Exceptions: deal announcements, earnings today, Fed decisions.
- No market colour. No "stocks rose", "sentiment improved", "traders weighed".
- No CEO names. No options pricing. No technical levels.
- HKT time required for every scheduled release today.
- No EPS numbers. No market cap. No valuation metrics. No YTD performance.
- No special characters except the bullet. No dashes, asterisks, brackets, underscores, semicolons.
- Never mention tomorrow's data in bullets. Today only.
- Do not output a timestamp line.
- Last bullet always starts with: Key risk today:
- Only these names allowed: Walmart, Amazon, Apple, Samsung, Alibaba, Meta, Google, Microsoft, Netflix, Tesla, Nvidia, JPMorgan, Goldman Sachs, Bank of America, Visa, Mastercard, Nike, Disney, Coca-Cola, PepsiCo, McDonalds, Starbucks, TSMC, Tencent, Meituan, PDD, JD, Baidu, NIO, BYD, SoftBank, Sony, Toyota, HSBC, Shell, BP, ExxonMobil, Uber, Airbnb, Spotify, Palantir, AMD, Intel, Qualcomm, Broadcom, Oracle, Salesforce, SAP.

ORDER: US catalysts first ranked by importance. Then HK and China. Last bullet is Key risk today."""

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
