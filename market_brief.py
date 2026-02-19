import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP for live data from the last 12-16 hours. Do all searches silently. Output only 3 paragraphs with zero narration, zero preamble, zero blank lines between or within paragraphs.

HARD RULES:
- Never mention any stock or index move unless it is >5%. Only exceptions: deal announcements, earnings today, Fed decisions.
- Never add line breaks or blank lines anywhere in the output.
- Never narrate your search process.
- Never use market colour: no "markets gained", "stocks rose", "traders weighed", "sentiment improved".
- Each paragraph is one continuous block of text.
- Max 200 words total across all 3 paragraphs.
- Always include HKT time for any scheduled release.
- No EPS numbers.
- No valuation metrics, no market cap figures, no CEO names unless critical.
- For deals: one sentence max, what was announced plus single most important implication.
- No special characters: no dashes, no brackets, no asterisks, no underscores, no symbols.
- Only these names: Walmart, Amazon, Apple, Samsung, Alibaba, Meta, Google, Microsoft, Netflix, Tesla, Nvidia, JPMorgan, Goldman Sachs, Bank of America, Visa, Mastercard, Nike, Disney, Coca-Cola, PepsiCo, McDonald's, Starbucks, TSMC, Tencent, Meituan, PDD, JD, Baidu, NIO, BYD, SoftBank, Sony, Toyota, HSBC, Shell, BP, ExxonMobil, Uber, Airbnb, Spotify, Palantir, AMD, Intel, Qualcomm, Broadcom, Oracle, Salesforce, SAP.

Time context: 8:30am HKT.

Para 1 (US): Lead with biggest catalyst. Deals: one sentence, what plus single most important implication. Earnings today: name plus HKT time plus what a miss means for the book. Max 3 sentences.
Para 2 (HK/China): >5% moves only. If closed state why in one clause. One China AI story only if market-moving.
Para 3: Start with Key risk today: then one sentence."""

USER_TRIGGER = f"Output. Timestamp: {TIMESTAMP}"


def generate_brief():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": USER_TRIGGER}],
                system=SYSTEM_PROMPT
            )
            text_blocks = [block.text for block in message.content if block.type == "text"]
            if text_blocks:
                raw = "\n".join(text_blocks[1:]) if len(text_blocks) > 1 else text_blocks[0]
                # Strip any blank lines Claude sneaks in
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


if __name__ == "__main__":
    brief = generate_brief()
    send_telegram(brief)
    print(f"Sent at {TIMESTAMP}")
