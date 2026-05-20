"""
Parse free-text WhatsApp messages into structured expense data.

Supported formats:
  "Zomato 450"                → {type: expense, description: Zomato, amount: 450}
  "petrol 800 transport"      → {type: expense, description: petrol, amount: 800, category: Transport}
  "zomato 450 food note here" → description=zomato, amount=450, category=food, note=note here
  "balance"                   → {type: balance}
  "report"                    → {type: report}
"""
import re
from api.services.categorizer import CATEGORIES_LOWER


def parse_whatsapp_message(text: str) -> dict | None:
    t = text.strip().lower()

    if t in ("balance", "bal", "summary"):
        return {"type": "balance"}
    if t in ("report", "monthly", "summary report"):
        return {"type": "report"}

    # Pattern: DESCRIPTION AMOUNT [CATEGORY] [NOTE]
    m = re.match(
        r"^(.+?)\s+([\d,]+(?:\.\d+)?)\s*(?:([a-z &]+?))?$",
        t,
        re.IGNORECASE,
    )
    if not m:
        return None

    description = m.group(1).strip().title()
    try:
        amount = float(m.group(2).replace(",", ""))
    except ValueError:
        return None

    category = None
    if m.group(3):
        hint = m.group(3).strip().lower()
        for cat in CATEGORIES_LOWER:
            if hint in cat or cat in hint:
                category = cat.title()
                break

    return {
        "type":        "expense",
        "description": description,
        "amount":      amount,
        "category":    category,
    }
