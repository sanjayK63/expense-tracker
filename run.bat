@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Expense Dashboard...
streamlit run app.py
pause
