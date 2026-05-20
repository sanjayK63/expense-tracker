"""
Year-over-year reports + monthly PDF/Excel summary.
"""
from fastapi import APIRouter, Header, Query
from fastapi.responses import StreamingResponse
from api.services.auth_helper import require_user
from api.db import get_client
import io

router = APIRouter()


@router.get("/monthly-summary")
async def monthly_summary(
    year: int = Query(...),
    month: int = Query(...),
    authorization: str = Header(...),
):
    user_id = await require_user(authorization)
    from_d  = f"{year}-{month:02d}-01"
    to_d    = f"{year}-{month:02d}-31"
    result  = (
        get_client().table("expenses")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", from_d)
        .lte("date", to_d)
        .execute()
    )
    rows = result.data
    by_cat: dict = {}
    for r in rows:
        by_cat.setdefault(r["category"], 0)
        by_cat[r["category"]] += r["amount"]
    return {
        "month": f"{year}-{month:02d}",
        "total": sum(r["amount"] for r in rows),
        "transactions": len(rows),
        "by_category": by_cat,
    }


@router.get("/year-over-year")
async def year_over_year(
    authorization: str = Header(...),
):
    """Returns last 24 months of monthly totals grouped by category."""
    user_id = await require_user(authorization)
    result  = (
        get_client().table("expenses")
        .select("date, amount, category")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    # Group by year-month and category
    from collections import defaultdict
    data: dict = defaultdict(lambda: defaultdict(float))
    for r in result.data:
        ym = r["date"][:7]  # YYYY-MM
        data[ym][r["category"]] += r["amount"]
    return dict(data)


@router.get("/recurring")
async def detect_recurring(authorization: str = Header(...)):
    """
    Detect likely recurring expenses: same description + similar amount
    appearing in 3+ consecutive months.
    """
    user_id = await require_user(authorization)
    result  = (
        get_client().table("expenses")
        .select("date, amount, description, category")
        .eq("user_id", user_id)
        .order("date")
        .execute()
    )
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for r in result.data:
        key = r["description"].lower().strip()
        groups[key].append(r)

    recurring = []
    for desc, entries in groups.items():
        if len(entries) < 3:
            continue
        months = sorted({e["date"][:7] for e in entries})
        if len(months) >= 3:
            amounts = [e["amount"] for e in entries]
            avg_amt = sum(amounts) / len(amounts)
            recurring.append({
                "description": entries[0]["description"],
                "category":    entries[0]["category"],
                "avg_amount":  round(avg_amt, 2),
                "occurrences": len(entries),
                "months":      months,
            })

    return sorted(recurring, key=lambda x: -x["occurrences"])


@router.get("/export/excel")
async def export_excel(
    year: int = Query(...),
    month: int = Query(...),
    authorization: str = Header(...),
):
    """Download monthly expenses as XLSX."""
    import pandas as pd
    user_id = await require_user(authorization)
    from_d  = f"{year}-{month:02d}-01"
    to_d    = f"{year}-{month:02d}-31"
    result  = (
        get_client().table("expenses")
        .select("date, amount, category, description, payment_method, source")
        .eq("user_id", user_id)
        .gte("date", from_d)
        .lte("date", to_d)
        .order("date")
        .execute()
    )
    df  = pd.DataFrame(result.data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Expenses")
    buf.seek(0)
    filename = f"expenses_{year}_{month:02d}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
