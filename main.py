from fastapi import FastAPI
from app.routers import catalog, quotes, payments, webhooks

app = FastAPI(title="Agentic Commerce - FastAPI MVP")

# include routers
app.include_router(catalog.router, prefix="/catalog", tags=["catalog"]) 
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"]) 
app.include_router(payments.router, prefix="/payments", tags=["payments"]) 
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"]) 


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
