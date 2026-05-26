from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException
from pydantic import BaseModel
from typing import Any
from api.services.auth_helper import require_user
from api.parsers.slice_cc import parse_slice_statement
from api.parsers.bob_cc import parse_bob_statement
from api.parsers.generic import parse_generic_statement
from api.services.categorizer import detect_category
from api.db import get_admin_client
import uuid

router = APIRouter()

MAX_PDF_SIZE  = 20 * 1024 * 1024   # 20 MB
MAX_IMPORT_ROWS = 5_000             # safety cap per import


@router.post("/pdf")
async def import_pdf(
    file: UploadFile = File(...),
    password: str = Form(""),
    account_name: str = Form(...),
    authorization: str = Header(...),
):
    user_id    = await require_user(authorization)
    file_bytes = await file.read(MAX_PDF_SIZE + 1)
    if len(file_bytes) > MAX_PDF_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 20 MB.")

    # Validate PDF magic bytes
    if not file_bytes.startswith(b"%PDF"):
        raise HTTPException(400, "File does not appear to be a valid PDF.")

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

    # Cap rows to prevent runaway imports
    rows = rows[:MAX_IMPORT_ROWS]
    return {
        "preview":  rows[:10],
        "total":    len(rows),
        "note":     note,
        "rows":     rows,
    }


class ConfirmBody(BaseModel):
    rows: list[dict[str, Any]]


@router.post("/pdf/confirm")
async def confirm_pdf_import(
    body: ConfirmBody,
    authorization: str = Header(...),
):
    """Bulk-insert rows returned by /import/pdf after user reviews preview."""
    user_id = await require_user(authorization)
    if not body.rows:
        raise HTTPException(400, "No rows to import")
    client = get_admin_client()
    # Enforce ownership and strip frontend-only fields
    rows = []
    for r in body.rows:
        rows.append({
            "id":             r.get("id") or str(uuid.uuid4()),
            "user_id":        user_id,
            "date":           r["date"],
            "amount":         float(r["amount"]),
            "category":       r.get("category", "Others"),
            "description":    r.get("description", ""),
            "payment_method": r.get("payment_method", "UPI"),
            "source":         r.get("source", ""),
            "type":           r.get("type", "Debit"),
        })
    result = client.table("expenses").insert(rows).execute()
    return {"imported": len(result.data)}
