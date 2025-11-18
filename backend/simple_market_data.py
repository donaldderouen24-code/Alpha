"""Simple Market Data - Fallback when CoinGecko is rate limited"""
from datetime import datetime
from typing import Dict

# Simple fallback prices (will be replaced with actual data when APIs work)
FALLBACK_PRICES = {
    'BTC': 93000,
    'ETH': 3100,
    'BNB': 620,
    'ADA': 0.95,
    'SOL': 245,
    'XRP': 1.10
}

def get_fallback_price(symbol: str) -> Dict:
    """Get fallback price when APIs are unavailable"""
    price = FALLBACK_PRICES.get(symbol.upper(), 0)
    
    return {
        'symbol': symbol.upper(),
        'price': price,
        'source': 'Fallback Data (API Rate Limited)',
        'timestamp': datetime.utcnow().isoformat(),
        'note': 'Real-time data temporarily unavailable. Using fallback prices.'
    }
