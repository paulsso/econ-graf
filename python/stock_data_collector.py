import os
import time
import schedule
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB connection parameters
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "my-super-secret-token")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "faang_stocks")
INFLUXDB_BUCKET = os.environ.get("INFLUXDB_BUCKET", "stock_data")

# List of FAANG+ stocks to track based on the article
STOCK_SYMBOLS = [
    "META",   # Meta Platforms (formerly Facebook)
    "AMZN",   # Amazon
    "AAPL",   # Apple
    "NFLX",   # Netflix
    "GOOGL",  # Alphabet (Google)
    "NVDA",   # NVIDIA
    "TSM",    # Taiwan Semiconductor Manufacturing
    "AMD",    # Advanced Micro Devices
    "ADBE",   # Adobe
    "CRM",    # Salesforce
    "MSFT"    # Microsoft (often included with FAANG)
]

def fetch_and_store_stock_data():
    """Fetch current stock data and store it in InfluxDB"""
    print(f"Fetching stock data at {datetime.now()}")
    
    # Create InfluxDB client
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        # Get current stock data
        try:
            # Fetch stock data for all symbols
            stock_data = yf.download(STOCK_SYMBOLS, period="1d")
            
            # Process and write data to InfluxDB
            current_time = datetime.utcnow()
            
            for symbol in STOCK_SYMBOLS:
                try:
                    # Get the latest price
                    latest_close = stock_data['Close'][symbol].iloc[-1]
                    latest_open = stock_data['Open'][symbol].iloc[-1]
                    latest_high = stock_data['High'][symbol].iloc[-1]
                    latest_low = stock_data['Low'][symbol].iloc[-1]
                    latest_volume = stock_data['Volume'][symbol].iloc[-1]
                    
                    # Create InfluxDB point
                    point = Point("stock_price") \
                        .tag("symbol", symbol) \
                        .field("close", float(latest_close)) \
                        .field("open", float(latest_open)) \
                        .field("high", float(latest_high)) \
                        .field("low", float(latest_low)) \
                        .field("volume", float(latest_volume)) \
                        .time(current_time)
                    
                    # Write to InfluxDB
                    write_api.write(bucket=INFLUXDB_BUCKET, record=point)
                    print(f"Stored data for {symbol}: Close = {latest_close}")
                except Exception as e:
                    print(f"Error processing {symbol}: {str(e)}")
            
        except Exception as e:
            print(f"Error fetching stock data: {str(e)}")

def fetch_historical_data():
    """Fetch historical stock data for initial population"""
    print("Fetching historical stock data...")
    
    # Create InfluxDB client
    with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        # Get data for the past 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Format dates for yfinance
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        try:
            # Fetch historical data
            hist_data = yf.download(STOCK_SYMBOLS, start=start_str, end=end_str)
            
            # Process and write data to InfluxDB
            for date_idx in hist_data.index:
                for symbol in STOCK_SYMBOLS:
                    try:
                        # Get data for this date and symbol
                        close = hist_data['Close'][symbol].loc[date_idx]
                        open_price = hist_data['Open'][symbol].loc[date_idx]
                        high = hist_data['High'][symbol].loc[date_idx]
                        low = hist_data['Low'][symbol].loc[date_idx]
                        volume = hist_data['Volume'][symbol].loc[date_idx]
                        
                        # Create InfluxDB point
                        point = Point("stock_price") \
                            .tag("symbol", symbol) \
                            .field("close", float(close)) \
                            .field("open", float(open_price)) \
                            .field("high", float(high)) \
                            .field("low", float(low)) \
                            .field("volume", float(volume)) \
                            .time(date_idx)
                        
                        # Write to InfluxDB
                        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
                    except Exception as e:
                        print(f"Error processing historical data for {symbol} on {date_idx}: {str(e)}")
            
            print("Historical data loaded successfully")
            
        except Exception as e:
            print(f"Error fetching historical stock data: {str(e)}")

def wait_for_influxdb():
    """Wait for InfluxDB to be ready"""
    max_retries = 30
    retry_interval = 5
    
    for i in range(max_retries):
        try:
            with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG) as client:
                health = client.health()
                if health.status == "pass":
                    print("InfluxDB is ready!")
                    return True
        except Exception as e:
            print(f"InfluxDB not ready yet: {str(e)}")
        
        print(f"Waiting for InfluxDB to be ready... ({i+1}/{max_retries})")
        time.sleep(retry_interval)
    
    print("Failed to connect to InfluxDB after multiple retries")
    return False

if __name__ == "__main__":
    # Wait for InfluxDB to be ready
    if wait_for_influxdb():
        # Load historical data on startup
        fetch_historical_data()
        
        # Schedule regular updates (every 30 minutes during market hours)
        schedule.every(30).minutes.do(fetch_and_store_stock_data)
        
        # Also fetch immediately
        fetch_and_store_stock_data()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("Exiting due to InfluxDB connection failure") 