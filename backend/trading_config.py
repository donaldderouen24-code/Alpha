"""Trading Platform Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

class TradingConfig:
    # Coinbase Pro API Keys
    COINBASE_API_KEY = os.getenv('COINBASE_API_KEY', '')
    COINBASE_API_SECRET = os.getenv('COINBASE_API_SECRET', '')
    
    # Binance API Keys
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    
    # Alpha Vantage API Key (Free tier)
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', '')
    
    # Trading Parameters
    AUTO_PROFIT_THRESHOLD = float(os.getenv('AUTO_PROFIT_THRESHOLD', '0.05'))  # 5% profit
    MAX_TRADE_AMOUNT = float(os.getenv('MAX_TRADE_AMOUNT', '10000'))  # $10,000 max per trade
    
    # Enable/Disable Exchanges
    COINBASE_ENABLED = COINBASE_API_KEY != ''
    BINANCE_ENABLED = BINANCE_API_KEY != ''
    
trading_config = TradingConfig()
