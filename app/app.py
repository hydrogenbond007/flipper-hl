from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from .interface import TradingService
import json
import os

# Load config file
config_path = os.path.join(os.path.dirname(__file__), "../examples/config.json")
with open(config_path) as f:
    config = json.load(f)

app = FastAPI(
    title="Hyperliquid Trading API",
    description="REST API for trading on Hyperliquid protocol",
    version="1.0.0"
)

trading = TradingService(private_key=config["secret_key"])

class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"

class OrderRequest(BaseModel):
    asset: str = Field(..., description="Trading pair symbol (e.g. ETH-PERP)")
    is_buy: bool = Field(..., description="True for buy order, False for sell")
    size: float = Field(..., gt=0, description="Order size")
    price: float = Field(..., gt=0, description="Order price (ignored for market orders)")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")

class MarketOrderRequest(BaseModel):
    asset: str = Field(..., description="Trading pair symbol (e.g. ETH-PERP)")
    is_buy: bool = Field(..., description="True for buy order, False for sell")
    size: float = Field(..., gt=0, description="Order size")

class Position(BaseModel):
    asset: str
    size: float
    entry_price: float
    unrealized_pnl: float

class Order(BaseModel):
    asset: str
    order_id: str
    size: float
    price: float
    is_buy: bool
    status: str

class MarketInfo(BaseModel):
    asset: str
    mark_price: float
    index_price: float
    open_interest: float
    funding_rate: float

@app.get("/market/{asset}", response_model=MarketInfo, tags=["market"])
async def get_market_info(asset: str):
    """
    Get current market information for an asset
    """
    try:
        return trading.get_market_info(asset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/market_order", response_model=Order, tags=["trading"])
async def place_market_order(order: MarketOrderRequest):
    """
    Place a market order (executes immediately at market price)
    """
    try:
        return trading.place_market_order(
            config["account_address"],
            order.asset,
            order.is_buy,
            order.size
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/limit_order", response_model=Order, tags=["trading"])
async def place_limit_order(order: OrderRequest):
    """
    Place a limit order at a specific price
    """
    try:
        return trading.place_limit_order(
            config["account_address"],
            order.asset,
            order.is_buy,
            order.size,
            order.price
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/positions", response_model=List[Position], tags=["trading"])
async def get_positions():
    """
    Get all open positions
    """
    try:
        return trading.get_positions(config["account_address"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cancel/{asset}/{order_id}", tags=["trading"])
async def cancel_order(asset: str, order_id: str):
    """
    Cancel an existing order
    """
    try:
        result = trading.cancel_order(config["account_address"], asset, order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/close/{asset}/{order_id}", tags=["trading"])
async def close_position(asset: str, order_id: str):
    """
    Close an existing position
    """
    try:
        result = trading.close_position(config["account_address"], asset, order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/open_orders", response_model=List[Order], tags=["trading"])
async def get_open_orders():
    """
    Get all open orders
    """
    try:
        result = trading.get_open_orders(config["account_address"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


