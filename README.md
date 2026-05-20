# 💰 Expense Tracker

A smart personal finance tracker for Indian bank accounts. Parses bank statement PDFs automatically, auto-categorizes transactions, and gives you a clean monthly dashboard.

## Features

- **PDF import** — Slice CC, Bank of Baroda CC, generic table-based statements
- **CSV / Excel import** — CSV, XLSX, XLS, XLSB with column mapping
- **Auto-categorization** — keyword rules + your own custom mapping master
- **Monthly dashboard** — donut chart, budget vs actual bars, trend chart
- **Budget tracking** — per-category limits with over-budget alerts
- **Transaction history** — filter, bulk delete, export in any format
- **Account tagging** — every import batch tagged by account name for easy batch-delete

## Quick start (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Or double-click `run.bat` on Windows.

## Supported banks (PDF)

| Bank | Statement type |
|------|---------------|
| Slice | Credit card (Feb 2026+ format A & B) |
| Bank of Baroda | Credit card (merged-cell format) |
| Any bank | Generic table-based statements (auto-detected) |

> HDFC & ICICI parsers coming soon.

## Project structure

```
expense-tracker/
├── app.py               # Streamlit app (all pages)
├── requirements.txt
├── run.bat              # Windows launcher
└── data/                # Local data (gitignored)
    ├── expenses.csv
    ├── budgets.csv
    ├── custom_keywords.csv
    └── attachments/
```

## Roadmap

- [ ] Supabase backend (multi-user, persistent cloud storage)
- [ ] Google / email authentication
- [ ] React + Next.js frontend
- [ ] FastAPI microservice for PDF parsing
- [ ] WhatsApp expense bot
- [ ] Bank SMS auto-import
- [ ] Recurring expense detection
- [ ] Budget alerts (push / WhatsApp)
- [ ] HDFC + ICICI PDF parsers
- [ ] Year-over-year reports
- [ ] Mobile app (React Native)

## Tech stack

| Layer | Current | Target |
|-------|---------|--------|
| Frontend | Streamlit | Next.js + Tailwind |
| Backend | In-process | FastAPI |
| Database | CSV files | Supabase (PostgreSQL) |
| Auth | None | Supabase Auth |
| Storage | Local disk | Supabase Storage |
| Deploy | Local | Vercel + Railway |
