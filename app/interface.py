from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
import json
import os
from eth_account import Account
from eth_account.signers.local import LocalAccount
from typing import List, Dict, Optional

# Load config file
config_path = os.path.join(os.path.dirname(__file__), "../examples/config.json")
with open(config_path) as f:
    config = json.load(f)

# Get private key from config
private_key = config["secret_key"]

# Initialize exchange (if needed)
exchange = Exchange(private_key, constants.TESTNET_API_URL)

# Initialize clients
info = Info(constants.TESTNET_API_URL)

class TradingService:
    def __init__(self, private_key: str):
        # Convert private key to Account object
        self.wallet: LocalAccount = Account.from_key(private_key)
        self.exchange = Exchange(self.wallet, constants.TESTNET_API_URL)
        self.info = Info(constants.TESTNET_API_URL)

    def get_market_info(self, asset: str) -> dict:
        """Get current market price and info for an asset"""
        try:
            meta = self.info.meta()
            for coin in meta["universe"]:
                if coin["name"] == asset:
                    return {
                        "asset": asset,
                        "mark_price": float(coin["markPrice"]),
                        "index_price": float(coin["indexPrice"]),
                        "open_interest": float(coin["openInterest"]),
                        "funding_rate": float(coin["fundingRate"])
                    }
            raise Exception(f"Asset {asset} not found")
        except Exception as e:
            raise Exception(f"Failed to get market info: {str(e)}")

    def place_order(self, wallet_address: str, asset: str, is_buy: bool, size: float, price: float, order_type: Optional[dict] = None) -> dict:
        """Place an order on Hyperliquid"""
        try:
            if order_type is None:
                # Default to market order for immediate execution
                market_info = self.get_market_info(asset)
                price = market_info["mark_price"]
                order_type = {"market": {}}
            
            result = self.exchange.order(asset, is_buy, size, price, order_type)
            
            # Format response to match API schema
            return {
                "asset": asset,
                "order_id": result.get("order_id", "unknown"),
                "size": size,
                "price": price,
                "is_buy": is_buy,
                "status": "open"
            }
        except Exception as e:
            raise Exception(f"Failed to place order: {str(e)}")

    def place_limit_order(self, wallet_address: str, asset: str, is_buy: bool, size: float, price: float) -> dict:
        """Place a limit order"""
        return self.place_order(wallet_address, asset, is_buy, size, price, {"limit": {"tif": "Gtc"}})

    def place_market_order(self, wallet_address: str, asset: str, is_buy: bool, size: float) -> dict:
        """Place a market order"""
        return self.place_order(wallet_address, asset, is_buy, size, 0, {"market": {}})

    def get_positions(self, wallet_address: str) -> List[dict]:
        """Get all positions for a wallet"""
        try:
            user_state = self.info.user_state(wallet_address)
            positions = []
            
            for pos in user_state.get("assetPositions", []):
                position = pos.get("position", {})
                positions.append({
                    "asset": position.get("coin", ""),
                    "size": float(position.get("size", 0)),
                    "entry_price": float(position.get("entryPx", 0)),
                    "unrealized_pnl": float(position.get("unrealizedPnl", 0))
                })
            
            return positions
        except Exception as e:
            raise Exception(f"Failed to get positions: {str(e)}")

    def cancel_order(self, wallet_address: str, asset: str, order_id: str) -> dict:
        """Cancel an order"""
        try:
            result = self.exchange.cancel(asset, order_id)
            return {
                "asset": asset,
                "order_id": order_id,
                "size": 0,
                "price": 0,
                "is_buy": True,
                "status": "cancelled"
            }
        except Exception as e:
            raise Exception(f"Failed to cancel order: {str(e)}")

    def close_position(self, wallet_address: str, asset: str, order_id: str) -> dict:
        """Close a position"""
        try:
            position = self.get_position_for_asset(wallet_address, asset)
            if not position or position["size"] == 0:
                raise Exception("No position to close")

            # Place market order in opposite direction
            is_buy = position["size"] < 0  # if short, need to buy to close
            size = abs(float(position["size"]))
            
            result = self.exchange.order(
                asset,
                is_buy,
                size,
                0,  # Market order
                {"market": {}}
            )
            
            return {
                "asset": asset,
                "order_id": result.get("order_id", "unknown"),
                "size": size,
                "price": 0,
                "is_buy": is_buy,
                "status": "closing"
            }
        except Exception as e:
            raise Exception(f"Failed to close position: {str(e)}")

    def get_open_orders(self, wallet_address: str) -> List[dict]:
        """Get all open orders"""
        try:
            user_state = self.info.user_state(wallet_address)
            orders = []
            
            for order in user_state.get("orders", []):
                orders.append({
                    "asset": order.get("coin", ""),
                    "order_id": order.get("oid", "unknown"),
                    "size": float(order.get("sz", 0)),
                    "price": float(order.get("px", 0)),
                    "is_buy": order.get("side", "B") == "B",
                    "status": "open"
                })
            
            return orders
        except Exception as e:
            raise Exception(f"Failed to get open orders: {str(e)}")

    def get_position_for_asset(self, wallet_address: str, asset: str) -> Optional[dict]:
        """Get position details for specific asset"""
        try:
            positions = self.get_positions(wallet_address)
            return next((p for p in positions if p["asset"] == asset), None)
        except Exception as e:
            raise Exception(f"Failed to get position: {str(e)}")

    def user_state(self, wallet_address):
        """Get user state using cached info client"""
        _, info = self.get_clients(wallet_address, self.wallet.key.hex())
        
        user_state = info.user_state(wallet_address)
        for asset_position in user_state["assetPositions"]:
            coin = asset_position["position"]["coin"]
            leverage = asset_position["position"]["leverage"]
            print(f"Current leverage for {coin}: {leverage}")
        return user_state

    def get_clients(self, wallet_address, private_key):
        """Get or create exchange and info clients for a wallet"""
        if wallet_address not in self.exchange_clients:
            # Create new clients for this user
            wallet = Account.from_key(private_key)
            exchange = Exchange(wallet, constants.TESTNET_API_URL)
            info = Info(constants.TESTNET_API_URL)
            
            self.exchange_clients[wallet_address] = exchange
            self.info_clients[wallet_address] = info
        
        return self.exchange_clients[wallet_address], self.info_clients[wallet_address]

    def set_leverage(self, wallet_address, asset, leverage):
        exchange = self.exchange_clients.get(wallet_address)
        if not exchange:
            return {"error": "User not initialized"}
        try:
            # Fix: str[asset] to just asset
            return exchange.update_leverage(int(leverage), asset, False)
        except Exception as e:
            return {"error": str(e)}

    #def get_market_price(self, asset):
    #    return self.exchange.get_market_price(asset)