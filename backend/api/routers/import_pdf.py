from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException
from api.services.auth_helper import require_user
from api.parsers.slice_cc import parse_slice_statement
from api.parsers.bob_cc import parse_bob_statement
from api.parsers.generic import parse_generic_statement
from api.services.categorizer import detect_category
import uuid

router = APIRouter()


@router.post("/pdf")
async def import_pdf(
    file: UploadFile = File(...),
    password: str = Form(""),
    account_name: str = Form(...),
    authorization: str = Header(...),
):
    user_id    = await require_user(authorization)
    file_bytes = await file.read()

    # Try parsers in priority order
    df, note = parse_slice_statement(file_bytes, password=password)
    if df is None:
        df, note = parse_bob_statement(file_bytes, password=password)
    if df is None:
        df, note = parse_generic_statement(file_bytes, password=password)
    if df is None:
        raise HTTPException(400, detail=note or "Could not parse this PDF format.")

    # Apply auto-categorization and build rows
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "id":             str(uuid.uuid4()),
            "user_id":        user_id,
            "date":           str(row["Date"]),
            "amount":         float(row["Amount"]),
            "category":       detect_category(str(row.get("Description", ""))),
            "description":    str(row.get("Description", "")),
            "payment_method": str(row.get("Payment Method", "UPI")),
            "source":         account_name,
            "type":           str(row.get("Type", "Debit")),
        })

    return {
        "preview":  rows[:10],
        "total":    len(rows),
        "note":     note,
        "rows":     rows,       # full payload — frontend calls POST /expenses/bulk to confirm
    }


@router.post("/pdf/confirm")
async def confirm_pdf_import(
    body: dict,
    authorization: str = Header(...),
):
    """Bulk-insert rows returned by /import/pdf after user reviews preview."""
    user_id = await require_user(authorization)
    from api.db import get_client
    rows = body.get("rows", [])
    if not rows:
        raise HTTPException(400, "No rows to import")
    for r in rows:
        r["user_id"] = user_id  # enforce ownership
    client = get_client()
    result = client.table("expenses").insert(rows).execute()
    return {"imported": len(result.data)}
