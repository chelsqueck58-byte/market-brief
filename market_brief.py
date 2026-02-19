import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP for live data from the last 12-16 hours. Do all searches silently. Output only 3 paragraphs. No narration. No preamble. No blank lines.

HARD RULES:
- Only mention a stock if move is >5%. Exceptions: deal announcements, earnings today, Fed decisions.
- No blank lines anywhere. No line breaks within a paragraph.
- No market colour. No "stocks rose", "sentiment improved", "traders weighed".
- Max 200 words total.
- HKT time required for every scheduled release.
- No EPS numbers. No market cap. No valuation metrics.
- No CEO names unless critical to story.
- Deals: one sentence only. What happened plus why it matters to the stock.
- Para 1: max 3 sentences total.
- Para 2: max 1 sentence. If closed, state region plus reason in under 6 words.
- Para 3: exactly 1 sentence starting with Key risk today:
- No special characters. No dashes, asterisks, brackets, underscores.
- Only these names allowed: Walmart, Amazon, Apple, Samsung, Alibaba, Meta, Google, Microsoft, Netflix, Tesla, Nvidia, JPMorgan, Goldman Sachs, Bank of America, Visa, Mastercard, Nike, Disney, Coca-Cola, PepsiCo, McDonalds, Starbucks, TSMC, Tencent, Meituan, PDD, JD, Baidu, NIO, BYD, SoftBank, Sony, Toyota, HSBC, Shell, BP, ExxonMobil, Uber, Airbnb, Spotify, Palantir, AMD, Intel, Qualcomm, Broadcom, Oracle, Salesforce, SAP.

Para 1 US: Lead with single biggest catalyst. Earnings: name plus HKT time plus what a miss means for the book.
Para 2 HK and China: moves over 5% only. One sentence maximum.
Para 3: Key risk today: one sentence."""

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
                return "\n".join(lines)
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


if __name__ == "__
