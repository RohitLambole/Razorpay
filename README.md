Quickstart (FastAPI backend)

Create Supabase project and run supplied SQL schema (supabase_schema.sql).
Set environment variables in Render (use values from .env.example).
Install deps: pip install -r requirements.txt
Run locally for smoke test: uvicorn main:app --reload
Deploy on Render: create a web service pointing to main.py module and set PYTHONPATH as needed.