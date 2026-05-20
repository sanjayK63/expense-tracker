"""
WhatsApp expense bot via Twilio sandbox.

Setup:
  1. Create Twilio account at twilio.com
  2. Enable WhatsApp sandbox: console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
  3. Set webhook URL to: https://your-api.railway.app/whatsapp/webhook
  4. Add TWILIO_* env vars

Message formats accepted:
  "Zomato 450"                    → Food, ₹450
  "Zomato 450 food"               → Food, ₹450 (explicit category)
  "petrol 800 transport"          → Transport, ₹800
  "balance"                       → returns current month summary
  "report"                        → sends mini report
"""
from fastapi import APIRouter, Request, Response
from api.services.categorizer import detect_category
from api.services.whatsapp_parser import parse_whatsapp_message
from api.db import get_client
import uuid
from datetime import date

router = APIRouter()

# Map WhatsApp sender number → Supabase user_id
# In production, stored in a whatsapp_users table
PHONE_USER_MAP: dict[str, str] = {}


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Twilio sends a form-encoded POST on every incoming WhatsApp message."""
    from twilio.twiml.messaging_response import MessagingResponse

    form = await request.form()
    body   = str(form.get("Body", "")).strip()
    sender = str(form.get("From", ""))

    user_id = PHONE_USER_MAP.get(sender)

    twiml = MessagingResponse()

    if not user_id:
        twiml.message(
            "👋 Hi! I'm your Expense Bot.\n"
            "To link this number to your account, open the app and go to "
            "Settings → Link WhatsApp."
        )
        return Response(content=str(twiml), media_type="application/xml")

    parsed = parse_whatsapp_message(body)

    if parsed is None:
        twiml.message(
            "❓ I didn't understand that.\n\n"
            "Try:\n• *Zomato 450* → log expense\n• *balance* → month summary\n• *report* → mini report"
        )
        return Response(content=str(twiml), media_type="application/xml")

    if parsed["type"] == "expense":
        row = {
            "id":             str(uuid.uuid4()),
            "user_id":        user_id,
            "date":           str(date.today()),
            "amount":         parsed["amount"],
            "category":       parsed.get("category") or detect_category(parsed["description"]),
            "description":    parsed["description"],
            "payment_method": "UPI",
            "source":         "WhatsApp Bot",
        }
        get_client().table("expenses").insert(row).execute()
        twiml.message(
            f"✅ Logged ₹{parsed['amount']:,.0f} under *{row['category']}*\n"
            f"_{parsed['description']}_"
        )

    elif parsed["type"] == "balance":
        # Quick month summary
        today = date.today()
        from_d = f"{today.year}-{today.month:02d}-01"
        result = (
            get_client().table("expenses")
            .select("amount, category")
            .eq("user_id", user_id)
            .gte("date", from_d)
            .execute()
        )
        total = sum(r["amount"] for r in result.data)
        twiml.message(f"📊 *{today.strftime('%B %Y')}*\nTotal spent: ₹{total:,.2f}\nTransactions: {len(result.data)}")

    return Response(content=str(twiml), media_type="application/xml")


@router.post("/link")
async def link_whatsapp(body: dict):
    """Frontend calls this after user submits their WhatsApp number in settings."""
    phone   = body.get("phone")
    user_id = body.get("user_id")
    if phone and user_id:
        PHONE_USER_MAP[f"whatsapp:{phone}"] = user_id
        return {"status": "linked"}
    return {"status": "error", "detail": "phone and user_id required"}
