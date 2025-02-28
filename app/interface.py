from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
import json
import os
from eth_account import Account
from eth_account.signers.local import LocalAccount

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
    def __init__(self, private_key):
        # Convert private key to Account object
        self.wallet: LocalAccount = Account.from_key(private_key)
        self.exchange = Exchange(self.wallet, constants.TESTNET_API_URL)
        # Cached clients for different users
        self.exchange_clients = {}
        self.info_clients = {}

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

    def user_state(self, wallet_address):
        """Get user state using cached info client"""
        _, info = self.get_clients(wallet_address, self.wallet.key.hex())
        
        user_state = info.user_state(wallet_address)
        for asset_position in user_state["assetPositions"]:
            coin = asset_position["position"]["coin"]
            leverage = asset_position["position"]["leverage"]
            print(f"Current leverage for {coin}: {leverage}")
        return user_state

    def get_positions(self, wallet_address):
        info = self.info_clients.get(wallet_address)
        if not info:
            return {"error": "User not initialized"}
        
        user_state = info.user_state(wallet_address)
        return user_state["assetPositions"]
    
    def place_order(self, wallet_address, asset, is_buy, size, price, order_type=None):
        exchange = self.exchange_clients.get(wallet_address)
        if not exchange:
            return {"error": "User not initialized"}
        
        if order_type is None:
            order_type = {"limit": {"tif": "Gtc"}}
        
        return exchange.order(asset, is_buy, size, price, order_type)
    
    def cancel_order(self, wallet_address, asset, order_id):
        exchange = self.exchange_clients.get(wallet_address)
        if not exchange:
            return {"error": "User not initialized"}
        
        return exchange.cancel(asset, order_id)
    
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

    def close_position(self, wallet_address, asset):
        """Close an existing position"""
        info = self.info_clients.get(wallet_address)
        exchange = self.exchange_clients.get(wallet_address)
        if not info or not exchange:
            return {"error": "User not initialized"}
            
        position = self.get_position_for_asset(wallet_address, asset)
        if not position or position['size'] == 0:
            return {"error": "No position to close"}
            
        # Place market order in opposite direction
        is_buy = position['size'] < 0  # if short, need to buy to close
        size = abs(float(position['size']))
        market_price = self.get_market_price(asset)
        
        return exchange.order(
            asset,
            is_buy,
            size,
            market_price,
            {"market": {}}  # Use market order to ensure closure
        )

    def get_position_for_asset(self, wallet_address, asset):
        """Get position details for specific asset"""
        positions = self.get_positions(wallet_address)
        return next((p for p in positions if p['asset'] == asset), None)

    def place_market_order(self, wallet_address, asset, is_buy, size):
        """Place a market order"""
        exchange = self.exchange_clients.get(wallet_address)
        if not exchange:
            return {"error": "User not initialized"}
            
        market_price = self.get_market_price(asset)
        return exchange.order(
            asset,
            is_buy,
            size,
            market_price,
            {"market": {}}
        )

    def get_open_orders(self, wallet_address):
        """Get all open orders for a user"""
        info = self.info_clients.get(wallet_address)
        if not info:
            return {"error": "User not initialized"}
            
        return info.user_state(wallet_address).get("orders", [])