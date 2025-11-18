"""Portfolio Tracking and Automated Profit-Taking Service"""
from motor.motor_asyncio import AsyncIOMotorClient
from trading_config import trading_config
from coinbase_service import coinbase_service
from binance_service import binance_service
from market_data_service import market_data_service
import logging
from typing import Dict, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

class PortfolioService:
    """Portfolio tracking and automated trading service"""
    
    def __init__(self):
        self.auto_profit_enabled = False
        self.monitoring_positions = {}
    
    async def get_all_balances(self) -> Dict:
        """Get balances from all connected exchanges"""
        balances = {
            'coinbase': [],
            'binance': [],
            'total_usd_value': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Get Coinbase balances
        if coinbase_service.enabled:
            cb_accounts = await coinbase_service.get_accounts()
            balances['coinbase'] = cb_accounts
        
        # Get Binance balances
        if binance_service.enabled:
            bn_info = await binance_service.get_account_info()
            if 'balances' in bn_info:
                balances['binance'] = bn_info['balances']
        
        # Calculate total USD value
        total_value = 0
        
        # Coinbase balances (already in USD terms mostly)
        for acc in balances['coinbase']:
            if acc['currency'] == 'USD' or acc['currency'] == 'USDT' or acc['currency'] == 'USDC':
                total_value += acc['available_balance']
            else:
                # Get crypto price
                price_data = await market_data_service.get_aggregated_price(acc['currency'], 'crypto')
                if price_data.get('primary_price'):
                    total_value += acc['available_balance'] * price_data['primary_price']
        
        # Binance balances
        for bal in balances['binance']:
            if bal['asset'] in ['USDT', 'USDC', 'BUSD']:
                total_value += bal['total']
            else:
                price_data = await market_data_service.get_aggregated_price(bal['asset'], 'crypto')
                if price_data.get('primary_price'):
                    total_value += bal['total'] * price_data['primary_price']
        
        balances['total_usd_value'] = round(total_value, 2)
        
        return balances
    
    async def save_trade_to_history(self, trade_data: Dict):
        """Save trade to database for tracking"""
        try:
            trade_data['timestamp'] = datetime.utcnow()
            await db.trade_history.insert_one(trade_data)
            logger.info(f"Trade saved: {trade_data['symbol']} {trade_data['side']}")
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
    
    async def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trade history"""
        try:
            trades = await db.trade_history.find().sort('timestamp', -1).limit(limit).to_list(length=limit)
            for trade in trades:
                trade['_id'] = str(trade['_id'])
                if 'timestamp' in trade:
                    trade['timestamp'] = trade['timestamp'].isoformat() if hasattr(trade['timestamp'], 'isoformat') else str(trade['timestamp'])
            return trades
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    async def calculate_position_profit(self, symbol: str, exchange: str, entry_price: float) -> Dict:
        """Calculate current profit/loss for a position"""
        try:
            # Get current price
            if exchange == 'coinbase':
                product_info = await coinbase_service.get_product_info(symbol)
                current_price = product_info.get('price', 0)
            elif exchange == 'binance':
                price_info = await binance_service.get_symbol_price(symbol)
                current_price = price_info.get('price', 0)
            else:
                return {'error': 'Unknown exchange'}
            
            if current_price > 0:
                profit_percent = ((current_price - entry_price) / entry_price) * 100
                return {
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'profit_percent': round(profit_percent, 2),
                    'should_sell': profit_percent >= (trading_config.AUTO_PROFIT_THRESHOLD * 100)
                }
        
        except Exception as e:
            logger.error(f"Error calculating profit: {e}")
        
        return {'error': 'Could not calculate profit'}
    
    async def monitor_and_take_profit(self, position: Dict) -> Dict:
        """Monitor a position and automatically take profit if threshold met"""
        try:
            profit_check = await self.calculate_position_profit(
                position['symbol'],
                position['exchange'],
                position['entry_price']
            )
            
            if profit_check.get('should_sell') and self.auto_profit_enabled:
                logger.info(f"Profit threshold reached for {position['symbol']}: {profit_check['profit_percent']}%")
                
                # Execute sell order
                if position['exchange'] == 'coinbase':
                    result = await coinbase_service.place_market_order(
                        position['symbol'],
                        'SELL',
                        size=position['quantity']
                    )
                elif position['exchange'] == 'binance':
                    result = await binance_service.place_market_order(
                        position['symbol'],
                        'SELL',
                        quantity=position['quantity']
                    )
                else:
                    return {'error': 'Unknown exchange'}
                
                if result.get('success'):
                    # Save trade
                    await self.save_trade_to_history({
                        'symbol': position['symbol'],
                        'side': 'SELL',
                        'type': 'AUTO_PROFIT',
                        'quantity': position['quantity'],
                        'entry_price': position['entry_price'],
                        'exit_price': profit_check['current_price'],
                        'profit_percent': profit_check['profit_percent'],
                        'exchange': position['exchange']
                    })
                    
                    return {
                        'action': 'sold',
                        'profit_percent': profit_check['profit_percent'],
                        'order': result
                    }
            
            return profit_check
        
        except Exception as e:
            logger.error(f"Error in profit monitoring: {e}")
            return {'error': str(e)}
    
    async def enable_auto_profit_taking(self, positions: List[Dict]):
        """Enable automatic profit taking for specified positions"""
        self.auto_profit_enabled = True
        self.monitoring_positions = {pos['symbol']: pos for pos in positions}
        logger.info(f"Auto profit-taking enabled for {len(positions)} positions")
    
    async def disable_auto_profit_taking(self):
        """Disable automatic profit taking"""
        self.auto_profit_enabled = False
        self.monitoring_positions = {}
        logger.info("Auto profit-taking disabled")
    
    async def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        balances = await self.get_all_balances()
        trade_history = await self.get_trade_history(limit=10)
        
        return {
            'balances': balances,
            'recent_trades': trade_history,
            'auto_profit_enabled': self.auto_profit_enabled,
            'monitored_positions': len(self.monitoring_positions),
            'exchanges_connected': {
                'coinbase': coinbase_service.enabled,
                'binance': binance_service.enabled
            }
        }

portfolio_service = PortfolioService()
