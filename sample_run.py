import subprocess
import time
import os
import sys

def run_demo():
    print("Starting Binance Futures Trading Bot Sample Run...")
    
    # 1. Start Mock Server in background
    print("\n[1/3] Starting Local Mock Server...")
    server_process = subprocess.Popen(
        [sys.executable, "mock_server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)  # Give server time to start
    
    # Set environment variables for the bot
    env = os.environ.copy()
    env["BINANCE_API_KEY"] = "sample_key"
    env["BINANCE_API_SECRET"] = "sample_secret"
    env["BINANCE_BASE_URL"] = "http://127.0.0.1:8000"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        # 2. Place a Market Buy Order
        print("\n[2/3] Placing a Market BUY Order for BTCUSDT...")
        subprocess.run([
            sys.executable, "cli.py", 
            "--symbol", "BTCUSDT", 
            "--side", "BUY", 
            "--type", "MARKET", 
            "--quantity", "0.001"
        ], env=env, check=True)

        time.sleep(1)

        # 3. Place a Limit Sell Order
        print("\n[3/3] Placing a Limit SELL Order for ETHUSDT...")
        subprocess.run([
            sys.executable, "cli.py", 
            "--symbol", "ETHUSDT", 
            "--side", "SELL", 
            "--type", "LIMIT", 
            "--quantity", "0.01", 
            "--price", "3500"
        ], env=env, check=True)

        print("\nSample Run Completed Successfully!")
        print("Check the 'logs/' directory for detailed request/response history.")

    except Exception as e:
        print(f"\nSample Run Failed: {e}")
    finally:
        # Cleanup: Stop the mock server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    run_demo()
