"""
WhatsApp expense bot via Twilio sandbox.
All incoming webhooks are signature-validated against TWILIO_AUTH_TOKEN.
The /link endpoint requires a valid Supabase JWT.
"""
from fastapi import APIRouter, Request, Response, Header, HTTPException
from api.services.categorizer import detect_category
from api.services.whatsapp_parser import parse_whatsapp_message
from api.services.auth_helper import require_user
from api.db import get_admin_client
from api.config import settings
import uuid
from datetime import date

router = APIRouter()


def _validate_twilio_signature(request: Request, form_data: dict) -> bool:
    """Validate that the webhook actually came from Twilio."""
    if not settings.twilio_auth_token:
        return True  # Skip validation if Twilio not configured (dev mode)
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(settings.twilio_auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        return validator.validate(url, form_data, signature)
    except Exception:
        return False


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Twilio sends a form-encoded POST on every incoming WhatsApp message."""
    from twilio.twiml.messaging_response import MessagingResponse

    form      = await request.form()
    form_dict = dict(form)

    # ── Security: validate Twilio signature ──────────────────────────────────
    if not _validate_twilio_signature(request, form_dict):
        return Response(status_code=403, content="Invalid signature")

    body   = str(form_dict.get("Body", "")).strip()
    sender = str(form_dict.get("From", ""))

    # Look up user from DB (not in-memory map)
    client  = get_admin_client()
    result  = client.table("whatsapp_users").select("user_id").eq("phone", sender).execute()
    user_id = result.data[0]["user_id"] if result.data else None

    twiml = MessagingResponse()

    if not user_id:
        twiml.message(
            "👋 Hi! I'm your Expense Bot.\n"
            "To link this number, open the app → Settings → Link WhatsApp."
        )
        return Response(content=str(twiml), media_type="application/xml")

    parsed = parse_whatsapp_message(body)

    if parsed is None:
        twiml.message(
            "❓ I didn't understand that.\n\n"
            "Try:\n• *Zomato 450* → log expense\n• *balance* → month summary"
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
        client.table("expenses").insert(row).execute()
        twiml.message(
            f"✅ Logged ₹{parsed['amount']:,.0f} under *{row['category']}*\n"
            f"_{parsed['description']}_"
        )

    elif parsed["type"] == "balance":
        today  = date.today()
        from_d = f"{today.year}-{today.month:02d}-01"
        res    = (
            client.table("expenses")
            .select("amount")
            .eq("user_id", user_id)
            .gte("date", from_d)
            .execute()
        )
        total = sum(r["amount"] for r in res.data)
        twiml.message(
            f"📊 *{today.strftime('%B %Y')}*\n"
            f"Total spent: ₹{total:,.2f}\nTransactions: {len(res.data)}"
        )

    return Response(content=str(twiml), media_type="application/xml")


@router.post("/link")
async def link_whatsapp(body: dict, authorization: str = Header(...)):
    """
    Authenticated endpoint — user must be logged in to link their phone.
    Stores the mapping in the whatsapp_users DB table (not in-memory).
    """
    user_id = await require_user(authorization)
    phone   = str(body.get("phone", "")).strip()
    if not phone:
        raise HTTPException(400, "phone is required")

    # Normalise to whatsapp:+91XXXXXXXXXX format
    if not phone.startswith("whatsapp:"):
        phone = f"whatsapp:{phone}"

    client = get_admin_client()
    client.table("whatsapp_users").upsert(
        {"phone": phone, "user_id": user_id},
        on_conflict="phone"
    ).execute()
    return {"status": "linked"}
