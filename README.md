# Agentic Commerce — Razorpay Hackathon

Agentic Commerce is an AI-native commerce MVP that demonstrates agent-driven product discovery, intelligent quoting with approval policies, and secure payments via Razorpay. This repository contains a FastAPI backend and a React + TypeScript frontend (Vite + Tailwind). The product is designed as a demo for the Razorpay hackathon: judges can sign in to a polished demo merchant, have an agent discover products, create quotes, approve them (if required), and complete a payment link flow.

This README explains how the project is organized, how to run and test it locally, and what judges should look for during evaluation.

Quick project overview

- Backend: FastAPI application (app/) — catalog, quotes, payments, Razorpay webhook handling, Supabase persistence, LLM integration hooks.
- Frontend: React + TypeScript + Vite + Tailwind in frontend/ — polished landing page, demo auth, dashboard, catalog, quote builder, payments, and agent workspace.
- Integrations: Razorpay payment links (server-side), Supabase for persistence, optional OpenAI usage (server-side only).

Important notes for the judges

- No secrets are stored in the frontend. Razorpay and OpenAI API keys reside on the backend (use the .env.example as a guide). The frontend uses a demo auth mode for the hackathon demo flow.
- The demo merchant used in the UI is:

  `146cf105-7ad7-48f8-8cc6-77f958febf0d`

- The public backend used for the hosted demo (when available) is:

  `https://razorpay-backend-j4mc.onrender.com`

What to evaluate

- Agentic discovery: use the Agent workspace to ask for product discovery (example instruction provided in Agent UI). The agent UI uses real catalog APIs to find products and can convert suggestions into real quotes.
- Quote builder & policy: create a quote and request a discount. The backend enforces discount policy server-side:
  - ≤20% — auto-approved
  - >20% and ≤40% — requires approval (pending_approval)
  - >40% — rejected (HTTP 403)
- Approval flow: the Demo UI provides an Approve action that calls the server approve API (POST /quotes/{quote_id}/approve).
- Payment flow: create a payment via POST /payments/create. The backend returns a Razorpay payment link; the frontend opens the returned short_url. Razorpay webhooks update payment status and finalize reservations.

Repository structure (high level)

- main.py — FastAPI entrypoint
- app/ — backend application (routers, llm integration, db helpers)
- frontend/ — React app (Vite + TypeScript + Tailwind)
  - src/ — application source
  - vite.config.ts — dev server and proxy
  - .env.example — frontend env example

Environment & secrets (backend)

Copy the file `env.example` and set values (for backend only):

- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- RAZORPAY_KEY_ID
- RAZORPAY_KEY_SECRET
- RAZORPAY_WEBHOOK_SECRET
- OPENAI_API_KEY (optional; only required if you run agent LLM flows server-side)
- JWT_SIGNING_KEY (optional; authentication is demo-only in the frontend)

Do NOT commit secrets to the repository.

Running the backend locally (quick)

1. Create a Python virtual environment and install dependencies:

   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Create a Supabase project and run the SQL schema (if you want to persist data). Alternatively, some operations can be tested with lightweight local state.

3. Copy `env.example` to `.env` and set required variables.

4. Start the server:

   uvicorn main:app --reload

By default the app starts on http://127.0.0.1:8000 (unless configured otherwise).

Running the frontend locally (quick)

1. cd frontend
2. npm install
3. Copy `.env.example` to `.env.local` and optionally set:

   VITE_API_BASE_URL=https://razorpay-backend-j4mc.onrender.com
   VITE_DEFAULT_MERCHANT_ID=146cf105-7ad7-48f8-8cc6-77f958febf0d

   Notes:
   - For local development we use a Vite dev proxy so the frontend calls `/api/*` and Vite forwards to the backend origin. This avoids CORS and keeps secrets server-side.

4. Start development server:

   npm run dev

5. Open http://localhost:5173 and use the Demo Login to sign in. Navigate to App → Catalog → Agent → Quotes → Payments.

Verifying the core flows (what judges should test)

1. Catalog
   - Visit /app/catalog and confirm products load from the backend (no fake data).
2. Agent discovery → Quote creation
   - Go to /app/agent and use the guided flow to pick a product and create a quote.
   - Observe the quote status and policy application.
3. Approve a pending quote
   - If a quote is pending_approval, open its detail page and use Approve. This calls POST /quotes/{quote_id}/approve.
4. Payment
   - From Payments, paste a quote_id (created earlier) and create a payment.
   - The backend will create a Razorpay payment link and return it. Click "Continue to payment" to open Razorpay's link.
   - Use Razorpay test credentials (configured on the backend) to complete a test payment. The webhook should update the payment status and backend should finalize the quote.

Notes & known limitations

- Authentication: the frontend uses a polished demo auth for the hackathon. We structured the app so Supabase Auth or a JWT auth can be integrated cleanly later.
- Quote/payment history: the backend implements quote creation and payment creation. Full server-side listing endpoints for quotes and payments may not be present in the current MVP; the frontend stores created quotes locally for demo viewing. This is documented in the UI and README.
- LLM / Agent: The backend contains an LLM wrapper (app/llm.py) that calls OpenAI when configured. For the hackathon demo we keep OpenAI keys server-side. The frontend Agent workspace uses a guided adapter and uses real catalog/quote APIs to create actionable quotes. Any mock LLM outputs are clearly labeled as demo.

Testing checklist for judges (fast)

- Start backend (uvicorn main:app --reload)
- Start frontend (cd frontend && npm install && npm run dev)
- Sign in to the demo merchant via UI (Demo Login)
- Open Agent → ask to find products → create a quote
- Approve the quote if pending
- Create payment and follow Razorpay link
- Watch webhook-backed settlement and quote finalization

Support / Contact

If you have questions during the hackathon or want me to walk through the demo, contact the author via the repository issues or add a note on the submission.

Acknowledgements

- Built for the Razorpay hackathon using FastAPI, Supabase, Razorpay, OpenAI (optional), React, Vite, and Tailwind.

