import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP for live data from the last 12-16 hours.

Time: 8:30am HKT. Output exactly 3 plain paragraphs, no headers, no bullets, no bold, no formatting. Max 200 words total.

Para 1 (US): Only mention stocks or indices with moves >5%. Lead with the single most important story regardless of move size if it is a major catalyst (deal, earnings, guidance). For deals, one clause: what happened + why it matters to the stock. For earnings or data releases today, one clause: company name + release time in HKT + what a miss/beat means for the book. Only include household-name companies (Walmart, Amazon, Apple, Samsung, Alibaba, Meta, Google, Microsoft, Netflix, Tesla, Nvidia, JPMorgan, Goldman Sachs, Bank of America, Visa, Mastercard, Nike, Disney, Coca-Cola, PepsiCo, McDonald's, Starbucks, TSMC, Tencent, Meituan, PDD, JD, Baidu, NIO, BYD, SoftBank, Sony, Toyota, HSBC, Shell, BP, ExxonMobil, Uber, Airbnb, Spotify, Palantir, AMD, Intel, Qualcomm, Broadcom, Oracle, Salesforce, SAP). Skip anything outside this list. Include VIX only if >25. No more than 3 sentences total.

Para 2 (HK/China): Only mention names with moves >5%. Skip if market is closed — state closure reason in one clause only. One China AI story if material and market-moving.

Para 3: Start with "Key risk today:" — one sentence on the single biggest thing that could move the book.

Rules: skip any move <5% entirely, no index levels unless >5% move, no vague language, never say "markets were" or "investors reacted", attribute every claim to a named source, no EPS numbers, always include HKT time for any scheduled data release or earnings."""
USER_TRIGGER = f"Output. Timestamp: {TIMESTAMP}"


def generate_brief():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": USER_TRIGGER}],
                system=SYSTEM_PROMPT
            )
            text_blocks = [block.text for block in message.content if block.type == "text"]
            if text_blocks:
                return "\n\n".join(text_blocks[1:]) if len(text_blocks) > 1 else text_blocks[0]
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
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}
        r = requests.post(url, json=payload)
        if not r.ok:
            payload["parse_mode"] = ""
            requests.post(url, json=payload)


if __name__ == "__main__":
    brief = generate_brief()
    send_telegram(brief)
    print(f"Sent at {TIMESTAMP}")
