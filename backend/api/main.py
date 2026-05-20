from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import expenses, budgets, import_pdf, import_csv, whatsapp, reports, auth

app = FastAPI(title="Expense Tracker API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/auth",     tags=["auth"])
app.include_router(expenses.router,    prefix="/expenses", tags=["expenses"])
app.include_router(budgets.router,     prefix="/budgets",  tags=["budgets"])
app.include_router(import_pdf.router,  prefix="/import",   tags=["import"])
app.include_router(import_csv.router,  prefix="/import",   tags=["import"])
app.include_router(whatsapp.router,    prefix="/whatsapp", tags=["whatsapp"])
app.include_router(reports.router,     prefix="/reports",  tags=["reports"])


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
