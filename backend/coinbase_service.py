"""Coinbase Pro (Advanced Trade) Integration Service"""
from coinbase.rest import RESTClient
from trading_config import trading_config
import logging
from typing import Dict, List, Optional
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)

class CoinbaseService:
    """Coinbase Pro trading service"""
    
    def __init__(self):
        self.client = None
        self.enabled = trading_config.COINBASE_ENABLED
        
        if self.enabled:
            try:
                self.client = RESTClient(
                    api_key=trading_config.COINBASE_API_KEY,
                    api_secret=trading_config.COINBASE_API_SECRET
                )
                logger.info("Coinbase Pro service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Coinbase: {e}")
                self.enabled = False
    
    async def get_accounts(self) -> List[Dict]:
        """Get all Coinbase accounts with balances"""
        if not self.enabled:
            return []
        
        try:
            response = self.client.get_accounts()
            accounts = response.get('accounts', [])
            
            return [
                {
                    'uuid': acc['uuid'],
                    'name': acc['name'],
                    'currency': acc['currency'],
                    'available_balance': float(acc['available_balance']['value']),
                    'hold': float(acc.get('hold', {}).get('value', 0)),
                    'type': acc['type']
                }
                for acc in accounts
                if float(acc['available_balance']['value']) > 0
            ]
        except Exception as e:
            logger.error(f"Error getting Coinbase accounts: {e}")
            return []
    
    async def get_account_balance(self, currency: str) -> float:
        """Get balance for specific currency"""
        accounts = await self.get_accounts()
        for acc in accounts:
            if acc['currency'] == currency.upper():
                return acc['available_balance']
        return 0.0
    
    async def place_market_order(self, product_id: str, side: str, size: Optional[float] = None,
                                 funds: Optional[float] = None) -> Dict:
        """Place a market order on Coinbase
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            side: 'BUY' or 'SELL'
            size: Amount of base currency (for SELL)
            funds: Amount of quote currency (for BUY)
        """
        if not self.enabled:
            return {'error': 'Coinbase not configured'}
        
        try:
            order_config = {'market_market_ioc': {}}
            
            if side == 'BUY' and funds:
                order_config['market_market_ioc']['quote_size'] = str(funds)
            elif side == 'SELL' and size:
                order_config['market_market_ioc']['base_size'] = str(size)
            else:
                return {'error': 'Invalid order parameters'}
            
            order = self.client.create_order(
                client_order_id=str(uuid.uuid4()),
                product_id=product_id,
                side=side,
                order_configuration=order_config
            )
            
            return {
                'success': True,
                'order_id': order.get('order_id'),
                'product_id': order.get('product_id'),
                'side': order.get('side'),
                'status': order.get('status'),
                'filled_size': float(order.get('filled_size', 0)),
                'exchange': 'Coinbase Pro'
            }
        
        except Exception as e:
            logger.error(f"Coinbase order error: {e}")
            return {'error': str(e), 'exchange': 'Coinbase Pro'}
    
    async def place_limit_order(self, product_id: str, side: str, size: float, price: float) -> Dict:
        """Place a limit order on Coinbase"""
        if not self.enabled:
            return {'error': 'Coinbase not configured'}
        
        try:
            order_config = {
                'limit_limit_gtc': {
                    'base_size': str(size),
                    'limit_price': str(price),
                    'post_only': False
                }
            }
            
            order = self.client.create_order(
                client_order_id=str(uuid.uuid4()),
                product_id=product_id,
                side=side,
                order_configuration=order_config
            )
            
            return {
                'success': True,
                'order_id': order.get('order_id'),
                'product_id': order.get('product_id'),
                'side': order.get('side'),
                'status': order.get('status'),
                'price': float(price),
                'size': float(size),
                'exchange': 'Coinbase Pro'
            }
        
        except Exception as e:
            logger.error(f"Coinbase limit order error: {e}")
            return {'error': str(e), 'exchange': 'Coinbase Pro'}
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        if not self.enabled:
            return {'error': 'Coinbase not configured'}
        
        try:
            result = self.client.cancel_orders(order_ids=[order_id])
            return {
                'success': True,
                'cancelled_orders': result.get('results', []),
                'exchange': 'Coinbase Pro'
            }
        except Exception as e:
            logger.error(f"Coinbase cancel order error: {e}")
            return {'error': str(e), 'exchange': 'Coinbase Pro'}
    
    async def get_product_info(self, product_id: str) -> Dict:
        """Get trading pair information"""
        if not self.enabled:
            return {}
        
        try:
            product = self.client.get_product(product_id=product_id)
            return {
                'product_id': product.get('product_id'),
                'price': float(product.get('price', 0)),
                'price_percentage_change_24h': float(product.get('price_percentage_change_24h', 0)),
                'volume_24h': float(product.get('volume_24h', 0)),
                'status': product.get('status'),
                'exchange': 'Coinbase Pro'
            }
        except Exception as e:
            logger.error(f"Error getting product info: {e}")
            return {}

coinbase_service = CoinbaseService()
