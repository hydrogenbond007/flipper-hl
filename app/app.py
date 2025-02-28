from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from auth import Auth
from interface import TradingService
import json
import os

# Load config file
config_path = os.path.join(os.path.dirname(__file__), "../examples/config.json")
with open(config_path) as f:
    config = json.load(f)

app = FastAPI()
auth = Auth("your-secret-key")
trading = TradingService(private_key=config["secret_key"])

class OrderRequest(BaseModel):
    asset: str
    is_buy: bool
    size: float
    price: float
    order_type: Optional[dict] = None

async def get_wallet_address(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    wallet_address = auth.verify_auth_token(authorization.split(" ")[1])
    if not wallet_address:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return wallet_address

@app.post("/place_order")
async def place_order(order_data: dict):
    return trading.place_order(
        order_data["wallet_address"],
        order_data["asset"],
        order_data["is_buy"],
        order_data["size"],
        order_data["price"],
        order_data["order_type"]
    )

@app.get("/positions/{wallet_address}")
async def get_positions(wallet_address: str):
    return trading.get_positions(wallet_address)

@app.post("/api/cancel/{asset}/{order_id}")
async def cancel_order(asset: str, order_id: str, wallet_address: str = Depends(get_wallet_address)):
    result = trading.cancel_order(wallet_address, asset, order_id)
    return result

@app.delete("/api/close/{asset}/{order_id}")
async def close_position(asset: str, order_id: str, wallet_address: str = Depends(get_wallet_address)):
    result = trading.close_position(wallet_address, asset, order_id)
    return result

@app.get("/api/open_orders")
async def get_open_orders(wallet_address: str = Depends(get_wallet_address)):
    result = trading.get_open_orders(wallet_address)
    return result


