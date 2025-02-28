import os
from eth_account import Account
from interface import TradingService
from hyperliquid.utils import constants
import json
import time

def setup_test_account():
    # Generate a random test account
    # WARNING: In production, never expose private keys
    test_account = Account.create()
    return test_account.address, test_account.key.hex()

def main():
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "../examples/config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    private_key = config["secret_key"]
    wallet_address = config["account_address"]
    
    print(f"\nInitializing trading service...")
    trading = TradingService(private_key)
    
    try:
        print(f"\nGetting clients for wallet: {wallet_address[:10]}...")
        exchange, info = trading.get_clients(wallet_address, private_key)
        print("✓ Clients initialized successfully")
        
        # Test 1: Check current leverage settings
        print("\n1. Checking current leverage settings...")
        user_state = trading.user_state(wallet_address)
        print("✓ Current leverage settings retrieved")
        
        # Test 2: Set leverage for ETH
        print("\n2. Setting leverage for ETH to 3x...")
        leverage_result = trading.set_leverage(wallet_address, "ETH", 3.0)
        print(f"Leverage update result: {json.dumps(leverage_result, indent=2)}")
        
        # Small delay to allow changes to propagate
        time.sleep(2)
        
        # Test 3: Verify leverage change
        print("\n3. Verifying new leverage settings...")
        updated_state = trading.user_state(wallet_address)
        print("✓ Updated leverage settings retrieved")
        
        # Test 4: Try setting leverage for BTC
        print("\n4. Setting leverage for BTC to 2x...")
        btc_leverage_result = trading.set_leverage(wallet_address, "BTC", 2.0)
        print(f"BTC leverage update result: {json.dumps(btc_leverage_result, indent=2)}")
        
        # Test 5: Get current positions
        print("\n5. Fetching current positions...")
        positions = trading.get_positions(wallet_address)
        print(f"Current positions: {json.dumps(positions, indent=2)}")
        
        # Test 6: Place a test order with new leverage
        print("\n6. Placing test order with new leverage...")
        order_result = trading.place_order(
            wallet_address,
            "ETH",
            True,  # buy
            0.01,  # size
            2000,  # price
            {"limit": {"tif": "Gtc"}}  # order type
        )
        print(f"Order result: {json.dumps(order_result, indent=2)}")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()