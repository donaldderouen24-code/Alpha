"""Binance Integration Service"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
from trading_config import trading_config
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BinanceService:
    """Binance trading service"""
    
    def __init__(self):
        self.client = None
        self.enabled = trading_config.BINANCE_ENABLED
        
        if self.enabled:
            try:
                self.client = Client(
                    api_key=trading_config.BINANCE_API_KEY,
                    api_secret=trading_config.BINANCE_API_SECRET
                )
                # Test connection
                self.client.get_account()
                logger.info("Binance service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Binance: {e}")
                self.enabled = False
    
    async def get_account_info(self) -> Dict:
        """Get Binance account information"""
        if not self.enabled:
            return {}
        
        try:
            account = self.client.get_account()
            return {
                'account_type': account['accountType'],
                'can_trade': account['canTrade'],
                'can_withdraw': account['canWithdraw'],
                'can_deposit': account['canDeposit'],
                'balances': [
                    {
                        'asset': bal['asset'],
                        'free': float(bal['free']),
                        'locked': float(bal['locked']),
                        'total': float(bal['free']) + float(bal['locked'])
                    }
                    for bal in account['balances']
                    if float(bal['free']) > 0 or float(bal['locked']) > 0
                ]
            }
        except BinanceAPIException as e:
            logger.error(f"Binance account error: {e}")
            return {'error': str(e)}
    
    async def get_asset_balance(self, asset: str) -> float:
        """Get balance for specific asset"""
        if not self.enabled:
            return 0.0
        
        try:
            balance = self.client.get_asset_balance(asset=asset.upper())
            if balance:
                return float(balance['free'])
        except Exception as e:
            logger.error(f"Error getting {asset} balance: {e}")
        return 0.0
    
    async def place_market_order(self, symbol: str, side: str, quantity: Optional[float] = None,
                                 quote_order_qty: Optional[float] = None) -> Dict:
        """Place a market order on Binance
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount of base asset
            quote_order_qty: Amount in quote asset (USDT)
        """
        if not self.enabled:
            return {'error': 'Binance not configured'}
        
        try:
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'MARKET'
            }
            
            if quote_order_qty:
                params['quoteOrderQty'] = quote_order_qty
            elif quantity:
                params['quantity'] = quantity
            else:
                return {'error': 'Must specify either quantity or quote_order_qty'}
            
            order = self.client.create_order(**params)
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'status': order['status'],
                'executed_qty': float(order['executedQty']),
                'cumulative_quote_qty': float(order['cummulativeQuoteQty']),
                'exchange': 'Binance'
            }
        
        except BinanceAPIException as e:
            logger.error(f"Binance order error: {e}")
            return {'error': str(e), 'exchange': 'Binance'}
    
    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """Place a limit order on Binance"""
        if not self.enabled:
            return {'error': 'Binance not configured'}
        
        try:
            order = self.client.create_order(
                symbol=symbol.upper(),
                side=side.upper(),
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'status': order['status'],
                'price': float(order['price']),
                'quantity': float(order['origQty']),
                'exchange': 'Binance'
            }
        
        except BinanceAPIException as e:
            logger.error(f"Binance limit order error: {e}")
            return {'error': str(e), 'exchange': 'Binance'}
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        if not self.enabled:
            return {'error': 'Binance not configured'}
        
        try:
            result = self.client.cancel_order(symbol=symbol.upper(), orderId=order_id)
            return {
                'success': True,
                'order_id': result['orderId'],
                'status': result['status'],
                'exchange': 'Binance'
            }
        except BinanceAPIException as e:
            logger.error(f"Binance cancel order error: {e}")
            return {'error': str(e), 'exchange': 'Binance'}
    
    async def get_symbol_price(self, symbol: str) -> Dict:
        """Get current price for a symbol"""
        if not self.enabled:
            return {}
        
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol.upper())
            return {
                'symbol': ticker['symbol'],
                'price': float(ticker['price']),
                'exchange': 'Binance'
            }
        except BinanceAPIException as e:
            logger.error(f"Error getting price: {e}")
            return {'error': str(e)}
    
    async def get_all_tickers(self) -> List[Dict]:
        """Get prices for all symbols"""
        if not self.enabled:
            return []
        
        try:
            tickers = self.client.get_all_tickers()
            return [
                {
                    'symbol': ticker['symbol'],
                    'price': float(ticker['price'])
                }
                for ticker in tickers[:50]  # Limit to first 50
            ]
        except BinanceAPIException as e:
            logger.error(f"Error getting tickers: {e}")
            return []

binance_service = BinanceService()
