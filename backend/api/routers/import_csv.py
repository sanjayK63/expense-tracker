from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException
from api.services.auth_helper import require_user
from api.db import get_client
from api.services.categorizer import detect_category
import pandas as pd
import uuid
from datetime import date

router = APIRouter()


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    account_name: str = Form(...),
    col_date: str = Form(...),
    col_amount: str = Form(...),
    col_desc: str = Form(""),
    col_category: str = Form(""),
    col_payment: str = Form(""),
    default_category: str = Form("Others"),
    authorization: str = Header(...),
):
    user_id    = await require_user(authorization)
    file_bytes = await file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "csv"

    try:
        if ext == "csv":
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        elif ext == "xlsb":
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes), engine="pyxlsb")
        else:
            df = pd.read_csv(pd.io.common.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    mapped = pd.DataFrame()
    mapped["date"]    = pd.to_datetime(df[col_date], dayfirst=True, errors="coerce",
                                       format="mixed").dt.strftime("%Y-%m-%d")
    mapped["amount"]  = pd.to_numeric(
        df[col_amount].astype(str).str.replace(",", "").str.replace("₹", ""),
        errors="coerce",
    ).abs()
    mapped["description"]    = df[col_desc]    if col_desc     else "Imported"
    mapped["category"]       = df[col_category] if col_category else default_category
    mapped["payment_method"] = df[col_payment]  if col_payment  else "UPI"

    mapped = mapped.dropna(subset=["date", "amount"])
    mapped = mapped[mapped["amount"] > 0]

    rows = []
    for _, row in mapped.iterrows():
        rows.append({
            "id":             str(uuid.uuid4()),
            "user_id":        user_id,
            "date":           row["date"],
            "amount":         float(row["amount"]),
            "category":       row["category"] if row["category"] else detect_category(str(row["description"])),
            "description":    str(row["description"]),
            "payment_method": str(row["payment_method"]),
            "source":         account_name,
        })

    return {"preview": rows[:10], "total": len(rows), "rows": rows}
