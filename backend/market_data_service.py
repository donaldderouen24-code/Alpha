"""Market Data Aggregation Service - CoinGecko, Alpha Vantage, Yahoo Finance"""
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from trading_config import trading_config
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class MarketDataService:
    """Aggregates market data from multiple free sources"""
    
    def __init__(self):
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        self.alpha_vantage = None
        if trading_config.ALPHA_VANTAGE_KEY:
            self.alpha_vantage = TimeSeries(key=trading_config.ALPHA_VANTAGE_KEY, output_format='json')
    
    async def get_crypto_price_coingecko(self, symbol: str) -> Optional[Dict]:
        """Get crypto price from CoinGecko (Free tier) - Direct API"""
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'USDT': 'tether',
                'USDC': 'usd-coin',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'SOL': 'solana',
                'DOGE': 'dogecoin'
            }
            
            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            
            # Direct API call
            url = f"{self.coingecko_api_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            # Check for rate limit
            if response.status_code == 429:
                logger.warning(f"CoinGecko rate limited - using Yahoo Finance fallback")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            if coin_id in data:
                return {
                    'symbol': symbol.upper(),
                    'price': data[coin_id]['usd'],
                    'market_cap': data[coin_id].get('usd_market_cap', 0),
                    'volume_24h': data[coin_id].get('usd_24h_vol', 0),
                    'change_24h': data[coin_id].get('usd_24h_change', 0),
                    'source': 'CoinGecko',
                    'timestamp': datetime.utcnow().isoformat()
                }
        except requests.Timeout:
            logger.warning(f"CoinGecko timeout for {symbol} - trying fallback")
        except Exception as e:
            logger.warning(f"CoinGecko error for {symbol}: {e} - trying fallback")
        return None
    
    async def get_stock_price_alphavantage(self, symbol: str) -> Optional[Dict]:
        """Get stock price from Alpha Vantage (Free 25 calls/day)"""
        if not self.alpha_vantage:
            return None
        
        try:
            data, meta = self.alpha_vantage.get_quote_endpoint(symbol=symbol)
            
            if data:
                return {
                    'symbol': symbol.upper(),
                    'price': float(data['05. price']),
                    'open': float(data['02. open']),
                    'high': float(data['03. high']),
                    'low': float(data['04. low']),
                    'volume': int(data['06. volume']),
                    'change': float(data['09. change']),
                    'change_percent': data['10. change percent'].replace('%', ''),
                    'source': 'Alpha Vantage',
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
        return None
    
    async def get_stock_price_yahoo(self, symbol: str) -> Optional[Dict]:
        """Get stock price from Yahoo Finance (Free, unofficial)"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.history(period='1d')
            
            if not info.empty:
                latest = info.iloc[-1]
                return {
                    'symbol': symbol.upper(),
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']),
                    'source': 'Yahoo Finance',
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
        return None
    
    async def get_aggregated_price(self, symbol: str, asset_type: str = 'crypto') -> Dict:
        """Get price from multiple sources and aggregate"""
        results = []
        
        if asset_type == 'crypto':
            # Try CoinGecko first (with timeout)
            try:
                cg_data = await self.get_crypto_price_coingecko(symbol)
                if cg_data:
                    results.append(cg_data)
            except:
                pass
        
        elif asset_type == 'stock':
            # Try Alpha Vantage
            try:
                av_data = await self.get_stock_price_alphavantage(symbol)
                if av_data:
                    results.append(av_data)
            except:
                pass
        
        # If no results, use fallback data
        if not results:
            from simple_market_data import get_fallback_price
            fallback = get_fallback_price(symbol)
            results.append(fallback)
        
        # Return all sources
        return {
            'symbol': symbol,
            'sources': results,
            'primary_price': results[0]['price'] if results else 0,
            'data_available': len(results)
        }
    
    async def get_trending_cryptos(self) -> List[Dict]:
        """Get trending cryptocurrencies from CoinGecko"""
        try:
            url = f"{self.coingecko_api_url}/search/trending"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            trending = response.json()
            
            return [
                {
                    'name': coin['item']['name'],
                    'symbol': coin['item']['symbol'],
                    'market_cap_rank': coin['item'].get('market_cap_rank', 0),
                    'price_btc': coin['item'].get('price_btc', 0)
                }
                for coin in trending.get('coins', [])[:10]
            ]
        except Exception as e:
            logger.error(f"Error getting trending cryptos: {e}")
            return []
    
    async def get_market_summary(self) -> Dict:
        """Get overall market summary"""
        try:
            url = f"{self.coingecko_api_url}/global"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            result = response.json()
            
            # Handle response structure
            data = result.get('data', result)
            
            return {
                'total_market_cap_usd': data.get('total_market_cap', {}).get('usd', 0),
                'total_volume_24h_usd': data.get('total_volume', {}).get('usd', 0),
                'bitcoin_dominance': data.get('market_cap_percentage', {}).get('btc', 0),
                'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                'markets': data.get('markets', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            # Return empty but valid structure
            return {
                'total_market_cap_usd': 0,
                'total_volume_24h_usd': 0,
                'bitcoin_dominance': 0,
                'active_cryptocurrencies': 0,
                'markets': 0,
                'timestamp': datetime.utcnow().isoformat()
            }

market_data_service = MarketDataService()
