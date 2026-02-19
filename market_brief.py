import anthropic
import requests
import os
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))
TIMESTAMP = datetime.now(HKT).strftime("%Y-%m-%d %H:%M HKT")

SYSTEM_PROMPT = """
You are a senior equity research analyst compiling a pre-market intelligence brief for a fundamental equities PM focused on US tech (Mag 7), China/HK consumer + internet, AI infrastructure, and cross-market themes.

check these sources — Specialist trade press:
- TechNode (China tech M&A, policy): https://technode.com
- SCMP (HK/China business, geopolitics): https://www.scmp.com/tech , https://www.scmp.com/business
- eFinancialCareers (banking comp, headcount): https://www.efinancialcareers.com
- GamesIndustry.biz (Tencent/NetEase gaming ecosystem): https://www.gamesindustry.biz
- Game Developer (studio layoffs, M&A): https://www.gamedeveloper.com
- VideoGamer (gaming news): https://www.videogamer.com
- CoinDesk (crypto-macro linkages only, skip noise): https://www.coindesk.com
- TheStreet (retail flow sentiment, options): https://www.thestreet.com
- FinancialContent (commodity flash crashes, volatility): https://markets.financialcontent.com
- Dao Insights (China consumer/AI marketing): https://daoinsights.com
- Global Times (China state media signals): https://www.globaltimes.cn
- Blockonomi / Techloy (China AI spending): https://blockonomi.com , https://www.techloy.com

Time: It is 8:30am HKT. Cover last 12-16 hours. Output max 100 words total . 3 paragraphs

**SOURCE PRIORITY (search these in order):**
You are a senior equity research analyst. Search Reuters, Bloomberg, CNBC, Yahoo Finance, SCMP, and HKEX filings for live data.

Rules: numbers only, no vague language, skip immaterial items, end with "Key risk:" one sentence.
"""

USER_TRIGGER = f"Output. Timestamp: {TIMESTAMP}"


def generate_brief():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search"
            }
        ],
        messages=[{"role": "user", "content": USER_TRIGGER}],
        system=SYSTEM_PROMPT
    )

    # Collect all text blocks — Claude emits: preamble → tool calls → final output
    text_blocks = [block.text for block in message.content if block.type == "text"]

    if text_blocks:
        # Skip preamble (first block), return everything after
        if len(text_blocks) > 1:
            return "\n\n".join(text_blocks[1:])
        else:
            return text_blocks[0]

    return "Error: no text returned"


def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=payload)
        if not r.ok:
            payload["parse_mode"] = ""
            requests.post(url, json=payload)


if __name__ == "__main__":
    brief = generate_brief()
    send_telegram(brief)
    print(f"Sent at {TIMESTAMP}")
