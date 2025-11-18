import { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, TrendingDown, RefreshCw, DollarSign, BarChart3, Activity, AlertCircle, CheckCircle, Wallet } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TradingPlatform() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [portfolio, setPortfolio] = useState(null);
  const [marketData, setMarketData] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [selectedExchange, setSelectedExchange] = useState('binance');
  const [orderType, setOrderType] = useState('market');
  const [orderSide, setOrderSide] = useState('buy');
  const [orderAmount, setOrderAmount] = useState('');
  const [orderPrice, setOrderPrice] = useState('');
  const [tradeHistory, setTradeHistory] = useState([]);
  const [autoProfitEnabled, setAutoProfitEnabled] = useState(false);

  useEffect(() => {
    loadPortfolio();
    loadMarketData();
    loadTradeHistory();
  }, []);

  const loadPortfolio = async () => {
    try {
      const response = await axios.get(`${API}/trading/portfolio`);
      setPortfolio(response.data);
      setAutoProfitEnabled(response.data.auto_profit_enabled);
    } catch (error) {
      console.error('Error loading portfolio:', error);
    }
  };

  const loadMarketData = async () => {
    try {
      const symbols = ['BTC', 'ETH', 'BNB'];
      const dataPromises = symbols.map(symbol =>
        axios.get(`${API}/trading/market-data/${symbol}?asset_type=crypto`)
      );
      const results = await Promise.all(dataPromises);
      
      const data = {};
      results.forEach((result, index) => {
        data[symbols[index]] = result.data;
      });
      
      setMarketData(data);
    } catch (error) {
      console.error('Error loading market data:', error);
    }
  };

  const loadTradeHistory = async () => {
    try {
      const response = await axios.get(`${API}/trading/history`);
      setTradeHistory(response.data.trades || []);
    } catch (error) {
      console.error('Error loading trade history:', error);
    }
  };

  const placeOrder = async () => {
    if (!orderAmount) {
      alert('Please enter an amount');
      return;
    }

    setLoading(true);
    try {
      let endpoint = '';
      let payload = {};

      if (selectedExchange === 'binance') {
        endpoint = orderType === 'market'
          ? `${API}/trading/binance/order/market`
          : `${API}/trading/binance/order/limit`;
        
        const symbol = `${selectedSymbol}USDT`;
        payload = {
          symbol,
          side: orderSide.toUpperCase(),
          ...(orderType === 'market'
            ? { quote_order_qty: parseFloat(orderAmount) }
            : { quantity: parseFloat(orderAmount), price: parseFloat(orderPrice) })
        };
      } else if (selectedExchange === 'coinbase') {
        endpoint = orderType === 'market'
          ? `${API}/trading/coinbase/order/market`
          : `${API}/trading/coinbase/order/limit`;
        
        const product_id = `${selectedSymbol}-USD`;
        payload = {
          product_id,
          side: orderSide.toUpperCase(),
          ...(orderType === 'market'
            ? { funds: parseFloat(orderAmount) }
            : { size: parseFloat(orderAmount), price: parseFloat(orderPrice) })
        };
      }

      const response = await axios.post(endpoint, payload);
      
      if (response.data.success) {
        alert(`Order placed successfully! Order ID: ${response.data.order_id}`);
        loadPortfolio();
        loadTradeHistory();
        setOrderAmount('');
        setOrderPrice('');
      } else {
        alert(`Order failed: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Error placing order:', error);
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleAutoProfitTaking = async () => {
    try {
      if (autoProfitEnabled) {
        // Disable
        await axios.post(`${API}/trading/auto-profit/disable`);
      } else {
        // Enable - send empty positions array
        await axios.post(`${API}/trading/auto-profit/enable`, {
          positions: []
        });
      }
      setAutoProfitEnabled(!autoProfitEnabled);
      alert(`Auto profit-taking ${!autoProfitEnabled ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Error toggling auto profit:', error);
      alert(`Failed to toggle auto profit-taking: ${error.response?.data?.detail || error.message}`);
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm text-gray-400">Total Balance</h3>
            <DollarSign className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-3xl font-bold text-white">
            ${portfolio?.balances?.total_usd_value?.toLocaleString() || '0.00'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Across all exchanges</p>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm text-gray-400">Active Exchanges</h3>
            <Activity className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-white">
            {(portfolio?.exchanges_connected?.coinbase ? 1 : 0) +
              (portfolio?.exchanges_connected?.binance ? 1 : 0)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {portfolio?.exchanges_connected?.coinbase && 'Coinbase '}
            {portfolio?.exchanges_connected?.binance && 'Binance'}
          </p>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm text-gray-400">Auto Profit</h3>
            {autoProfitEnabled ? (
              <CheckCircle className="w-5 h-5 text-green-500" />
            ) : (
              <AlertCircle className="w-5 h-5 text-orange-500" />
            )}
          </div>
          <button
            onClick={toggleAutoProfitTaking}
            className={`mt-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              autoProfitEnabled
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {autoProfitEnabled ? 'Enabled' : 'Disabled'}
          </button>
        </div>
      </div>

      {/* Market Data - Split Screen */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Live Market Data
          <button
            onClick={loadMarketData}
            className="ml-auto p-2 hover:bg-gray-700 rounded-lg"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(marketData).map(([symbol, data]) => (
            <div
              key={symbol}
              className="bg-gray-900/50 rounded-lg p-4 border border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-lg font-bold">{symbol}</h4>
                <div className="text-xs text-gray-400">
                  {data.sources?.length || 0} sources
                </div>
              </div>

              {data.sources?.map((source, idx) => (
                <div key={idx} className="mb-3 pb-3 border-b border-gray-700 last:border-0">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">{source.source}</span>
                    {source.change_24h && (
                      <span className={`text-xs ${source.change_24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {source.change_24h >= 0 ? '+' : ''}{source.change_24h.toFixed(2)}%
                      </span>
                    )}
                  </div>
                  <p className="text-2xl font-bold">${source.price?.toLocaleString()}</p>
                  {source.volume_24h && (
                    <p className="text-xs text-gray-500 mt-1">
                      Vol: ${(source.volume_24h / 1000000).toFixed(2)}M
                    </p>
                  )}
                </div>
              ))}

              {data.error && (
                <div className="text-sm text-red-400">{data.error}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Trades */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-bold mb-4">Recent Trades</h3>
        <div className="space-y-2">
          {tradeHistory.slice(0, 5).map((trade, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                {trade.side === 'BUY' ? (
                  <TrendingUp className="w-5 h-5 text-green-500" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-red-500" />
                )}
                <div>
                  <p className="font-medium">{trade.symbol}</p>
                  <p className="text-xs text-gray-400">{trade.exchange}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-medium ${trade.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                  {trade.side}
                </p>
                <p className="text-xs text-gray-400">{trade.type}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTrading = () => (
    <div className="space-y-6">
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-bold mb-6">Place Order</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Order Configuration */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Exchange</label>
              <select
                value={selectedExchange}
                onChange={(e) => setSelectedExchange(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
              >
                <option value="binance">Binance</option>
                <option value="coinbase">Coinbase Pro</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Symbol</label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
              >
                <option value="BTC">BTC</option>
                <option value="ETH">ETH</option>
                <option value="BNB">BNB</option>
                <option value="ADA">ADA</option>
                <option value="SOL">SOL</option>
                <option value="XRP">XRP</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Order Type</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setOrderType('market')}
                  className={`flex-1 py-2 rounded-lg ${
                    orderType === 'market'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Market
                </button>
                <button
                  onClick={() => setOrderType('limit')}
                  className={`flex-1 py-2 rounded-lg ${
                    orderType === 'limit'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Limit
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Side</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setOrderSide('buy')}
                  className={`flex-1 py-2 rounded-lg ${
                    orderSide === 'buy'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Buy
                </button>
                <button
                  onClick={() => setOrderSide('sell')}
                  className={`flex-1 py-2 rounded-lg ${
                    orderSide === 'sell'
                      ? 'bg-red-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Sell
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Amount ({orderType === 'market' ? 'USDT' : selectedSymbol})
              </label>
              <input
                type="number"
                value={orderAmount}
                onChange={(e) => setOrderAmount(e.target.value)}
                placeholder="Enter amount"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
              />
            </div>

            {orderType === 'limit' && (
              <div>
                <label className="block text-sm text-gray-400 mb-2">Price (USDT)</label>
                <input
                  type="number"
                  value={orderPrice}
                  onChange={(e) => setOrderPrice(e.target.value)}
                  placeholder="Enter price"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white"
                />
              </div>
            )}

            <button
              onClick={placeOrder}
              disabled={loading}
              className={`w-full py-3 rounded-lg font-medium transition-colors ${
                orderSide === 'buy'
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-red-600 hover:bg-red-700'
              } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {loading ? 'Placing Order...' : `${orderSide.toUpperCase()} ${selectedSymbol}`}
            </button>
          </div>

          {/* Current Market Price */}
          <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-700">
            <h4 className="text-lg font-bold mb-4">Current Price</h4>
            {marketData[selectedSymbol]?.sources?.[0] ? (
              <div>
                <p className="text-4xl font-bold mb-2">
                  ${marketData[selectedSymbol].sources[0].price?.toLocaleString()}
                </p>
                <p className="text-sm text-gray-400 mb-4">
                  Source: {marketData[selectedSymbol].sources[0].source}
                </p>
                {marketData[selectedSymbol].sources[0].change_24h && (
                  <div className={`text-lg ${
                    marketData[selectedSymbol].sources[0].change_24h >= 0
                      ? 'text-green-500'
                      : 'text-red-500'
                  }`}>
                    {marketData[selectedSymbol].sources[0].change_24h >= 0 ? '+' : ''}
                    {marketData[selectedSymbol].sources[0].change_24h.toFixed(2)}% (24h)
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-400">Loading price data...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderBalances = () => (
    <div className="space-y-6">
      {/* Coinbase Balances */}
      {portfolio?.balances?.coinbase && portfolio.balances.coinbase.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Coinbase Pro Balances
          </h3>
          <div className="space-y-2">
            {portfolio.balances.coinbase.map((acc, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg"
              >
                <div>
                  <p className="font-medium">{acc.currency}</p>
                  <p className="text-xs text-gray-400">{acc.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{acc.available_balance.toFixed(8)}</p>
                  <p className="text-xs text-gray-400">Available</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Binance Balances */}
      {portfolio?.balances?.binance && portfolio.balances.binance.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Binance Balances
          </h3>
          <div className="space-y-2">
            {portfolio.balances.binance.map((bal, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg"
              >
                <div>
                  <p className="font-medium">{bal.asset}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{bal.total.toFixed(8)}</p>
                  <p className="text-xs text-gray-400">
                    Free: {bal.free.toFixed(8)} | Locked: {bal.locked.toFixed(8)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(!portfolio?.balances?.coinbase || portfolio.balances.coinbase.length === 0) &&
        (!portfolio?.balances?.binance || portfolio.balances.binance.length === 0) && (
        <div className="text-center py-12 text-gray-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No exchange accounts configured</p>
          <p className="text-sm mt-2">Add your API keys to start trading</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="flex-1 flex flex-col h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="p-6 border-b border-gray-700/50 bg-gray-800/30 backdrop-blur-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
              Trading Platform
            </h1>
            <p className="text-sm text-gray-400 mt-1">Live trading on Coinbase Pro & Binance</p>
          </div>
          <button
            onClick={() => {
              loadPortfolio();
              loadMarketData();
              loadTradeHistory();
            }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh All
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700/50 bg-gray-800/20">
        <div className="flex gap-4 px-6">
          {['dashboard', 'trading', 'balances', 'history'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-6 font-medium transition-colors border-b-2 ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'trading' && renderTrading()}
        {activeTab === 'balances' && renderBalances()}
        {activeTab === 'history' && (
          <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
            <h3 className="text-xl font-bold mb-4">Trade History</h3>
            <div className="space-y-2">
              {tradeHistory.map((trade, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    {trade.side === 'BUY' ? (
                      <TrendingUp className="w-6 h-6 text-green-500" />
                    ) : (
                      <TrendingDown className="w-6 h-6 text-red-500" />
                    )}
                    <div>
                      <p className="font-medium">{trade.symbol}</p>
                      <p className="text-xs text-gray-400">
                        {trade.exchange} • {trade.type}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium ${trade.side === 'BUY' ? 'text-green-500' : 'text-red-500'}`}>
                      {trade.side}
                    </p>
                    {trade.profit_percent && (
                      <p className="text-xs text-gray-400">
                        Profit: {trade.profit_percent.toFixed(2)}%
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {tradeHistory.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                  <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No trades yet</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
