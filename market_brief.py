import anthropic
import requests
import os
import time
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP for live data.

Time: 8:30am HKT. Cover last 12-16 hours. Output exactly 3 short paragraphs, max 100 words total.

Para 1: US markets (SPX, NDX, VIX, key mover)
Para 2: HK/China + AI/tech news
Para 3: Key catalyst today

Rules: numbers only, no vague language, skip immaterial items, end with "Key risk:" one sentence."""

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
