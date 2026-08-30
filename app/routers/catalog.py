from fastapi import APIRouter, Query, HTTPException
from typing import List
from .. import db

router = APIRouter()


@router.get("/", summary="List products for a merchant")
def list_products(merchant_id: str = Query(...)) -> List[dict]:
    prods = db.list_products(merchant_id)
    return prods