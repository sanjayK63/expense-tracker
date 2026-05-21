"""
Excel / CSV import with automatic column detection.
Supports: .csv  .xlsx  .xls  .xlsb
"""
from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException
from api.services.auth_helper import require_user
from api.db import get_admin_client
from api.services.categorizer import detect_category
import pandas as pd
import uuid
import io

router = APIRouter()

# ── Column name patterns (lowercase) ──────────────────────────────────────────
_DATE_HINTS   = ["date", "txn date", "transaction date", "value date", "posting date",
                 "trans date", "tran date"]
_DEBIT_HINTS  = ["debit", "withdrawal", "dr", "debit amount", "withdrawal amt",
                 "debit amt", "spend"]
_CREDIT_HINTS = ["credit", "deposit", "cr", "credit amount", "deposit amt",
                 "credit amt"]
_AMOUNT_HINTS = ["amount", "transaction amount", "txn amount", "net amount"]
_DESC_HINTS   = ["description", "narration", "particulars", "remarks",
                 "transaction details", "details", "memo", "trans description",
                 "tran description", "transaction remark"]
_CAT_HINTS    = ["category", "cat", "expense category", "expense type", "type",
                 "head", "expense head"]


def _find_col(df: pd.DataFrame, hints: list[str]) -> str | None:
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for h in hints:
        if h in cols_lower:
            return cols_lower[h]
    # partial match fallback
    for h in hints:
        for lc, orig in cols_lower.items():
            if h in lc:
                return orig
    return None


def _clean_amount(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
              .str.replace(",", "", regex=False)
              .str.replace("₹", "", regex=False)
              .str.replace(" ", "", regex=False)
              .str.strip(),
        errors="coerce",
    ).abs().fillna(0)


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    account_name: str = Form(...),
    authorization: str = Header(...),
):
    user_id    = await require_user(authorization)
    file_bytes = await file.read()
    ext        = (file.filename or "").rsplit(".", 1)[-1].lower()

    # ── Read file ──────────────────────────────────────────────────────────────
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        elif ext == "xlsb":
            df = pd.read_excel(io.BytesIO(file_bytes), engine="pyxlsb")
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    # ── Auto-detect columns ────────────────────────────────────────────────────
    col_date   = _find_col(df, _DATE_HINTS)
    col_debit  = _find_col(df, _DEBIT_HINTS)
    col_credit = _find_col(df, _CREDIT_HINTS)
    col_amount = _find_col(df, _AMOUNT_HINTS) if not col_debit else None
    col_desc   = _find_col(df, _DESC_HINTS)
    col_cat    = _find_col(df, _CAT_HINTS)

    if not col_date:
        raise HTTPException(400, f"Could not find a Date column. Columns found: {list(df.columns)}")
    if not col_debit and not col_amount:
        raise HTTPException(400, f"Could not find an Amount/Debit column. Columns found: {list(df.columns)}")

    # ── Parse dates ────────────────────────────────────────────────────────────
    dates = pd.to_datetime(df[col_date], dayfirst=True, errors="coerce",
                           format="mixed").dt.strftime("%Y-%m-%d")

    # ── Build rows ─────────────────────────────────────────────────────────────
    rows = []
    for i, row in df.iterrows():
        date_val = dates.iloc[i] if hasattr(dates, "iloc") else dates[i]
        if pd.isna(date_val) or str(date_val) == "NaT":
            continue

        desc = str(row[col_desc]).strip() if col_desc and col_desc in df.columns else "Imported"
        if desc in ("nan", "", "None"):
            desc = "Imported"

        if col_debit:
            debit  = _clean_amount(pd.Series([row[col_debit]]))[0]
            credit = _clean_amount(pd.Series([row[col_credit]]))[0] if col_credit else 0.0
            if debit > 0:
                amount, txn_type = debit, "Debit"
            elif credit > 0:
                amount, txn_type = credit, "Credit"
            else:
                continue
        else:
            amount = _clean_amount(pd.Series([row[col_amount]]))[0]
            if amount <= 0:
                continue
            txn_type = "Debit"

        # Use category from file if present, otherwise auto-detect
        file_cat = ""
        if col_cat:
            raw_cat = str(row.get(col_cat, "")).strip()
            if raw_cat and raw_cat.lower() not in ("nan", "none", ""):
                file_cat = raw_cat
        category = file_cat if file_cat else detect_category(desc)

        rows.append({
            "id":             str(uuid.uuid4()),
            "user_id":        user_id,
            "date":           str(date_val),
            "amount":         round(float(amount), 2),
            "category":       category,
            "description":    desc,
            "payment_method": "UPI",
            "source":         account_name,
            "type":           txn_type,
        })

    if not rows:
        raise HTTPException(400, "No valid rows found after parsing. Check the file format.")

    return {"rows": rows, "total": len(rows)}


@router.post("/csv/confirm")
async def confirm_csv_import(
    body: dict,
    authorization: str = Header(...),
):
    user_id = await require_user(authorization)
    rows = body.get("rows", [])
    if not rows:
        raise HTTPException(400, "No rows to import")
    client = get_admin_client()
    clean = []
    for r in rows:
        clean.append({
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
    result = client.table("expenses").insert(clean).execute()
    return {"imported": len(result.data)}
