# ALPHA Trading Platform - Complete Setup Guide

## Overview

ALPHA now includes a comprehensive Trading Platform that enables live crypto trading on **Coinbase Pro** and **Binance** with real-time market data from multiple sources.

## Features

### ✅ Live Trading
- **Coinbase Pro Integration**: Market & limit orders on Coinbase Advanced Trade API
- **Binance Integration**: Market & limit orders on Binance spot trading
- **Multi-Exchange Portfolio**: Track balances across all connected exchanges

### 📊 Multi-Source Market Data
The platform aggregates real-time price data from 3 free sources:
1. **CoinGecko** (Crypto prices, market data, trending coins)
2. **Alpha Vantage** (Stock quotes - 25 calls/day free tier)
3. **Yahoo Finance** (Stock data - unofficial but free)

### 💰 Automated Profit-Taking
- Set profit thresholds (default: 5%)
- Automatically sell positions when profit targets are met
- Monitor multiple positions simultaneously

### 🎯 Split-Screen Market View
- View live prices from multiple data sources side-by-side
- Compare data quality and detect delays
- Real-time price updates with change indicators

## Getting Started

### 1. Obtain API Keys

#### Coinbase Pro API Keys
1. Go to https://www.coinbase.com/settings/api
2. Create a new API key
3. Enable permissions: `view_accounts` and `trade`
4. Save your API key and secret immediately (secret is shown only once)

#### Binance API Keys
1. Go to https://www.binance.com/en/my/settings/api-management
2. Create a new API key
3. Enable "Enable Spot & Margin Trading"
4. Restrict IP addresses for security (optional but recommended)
5. Save your API key and secret

#### Alpha Vantage API Key (Free)
1. Go to https://www.alphavantage.co/support/#api-key
2. Click "Get Your Free API Key Today"
3. Fill out the form and get your key instantly
4. Free tier: 25 API calls per day

### 2. Configure API Keys

Add your API keys to `/app/backend/.env`:

```bash
# Coinbase Pro
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret

# Binance
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Alpha Vantage (Free)
ALPHA_VANTAGE_KEY=your_alpha_vantage_key

# Trading Configuration
AUTO_PROFIT_THRESHOLD=0.05  # 5% profit threshold
MAX_TRADE_AMOUNT=10000      # Maximum $10,000 per trade
```

**Note**: You can leave any API key empty to disable that exchange. The platform will work with whatever exchanges you configure.

### 3. Restart Backend

After adding your keys, restart the backend:

```bash
sudo supervisorctl restart backend
```

## Using the Trading Platform

### Access the Platform
1. Open ALPHA in your browser
2. Click the **"Trading Platform"** button in the sidebar
3. You'll see the trading dashboard with 4 tabs:
   - **Dashboard**: Portfolio overview and market data
   - **Trading**: Place orders
   - **Balances**: View account balances
   - **History**: Trade history log

### Dashboard Tab
- **Total Balance**: Combined USD value across all exchanges
- **Active Exchanges**: Shows which exchanges are connected
- **Auto Profit**: Enable/disable automated profit-taking
- **Live Market Data**: Real-time prices from multiple sources in split-screen view
- **Recent Trades**: Last 5 trades across all exchanges

### Trading Tab
1. Select your exchange (Binance or Coinbase Pro)
2. Choose a cryptocurrency (BTC, ETH, BNB, ADA, SOL, XRP)
3. Pick order type:
   - **Market Order**: Execute immediately at current price
   - **Limit Order**: Set your desired price
4. Choose side:
   - **Buy**: Purchase crypto
   - **Sell**: Sell crypto
5. Enter amount:
   - For Market orders: Amount in USDT/USD to spend
   - For Limit orders: Amount of crypto + desired price
6. Click "BUY" or "SELL" button
7. Confirmation alert will show order ID

### Automated Profit-Taking
1. Enable auto profit-taking in the Dashboard tab
2. The system monitors all your positions
3. When a position reaches the profit threshold (default 5%), it automatically sells
4. Trade history records all automated trades with profit percentages

### Balances Tab
- View all your cryptocurrency balances
- Separate sections for Coinbase Pro and Binance
- Shows available, locked, and total amounts

### History Tab
- Complete trade history
- Shows symbol, exchange, order type, side (BUY/SELL)
- Displays profit percentages for auto-profit trades
- Sorted by most recent first

## Market Data Sources Explained

### CoinGecko
- **Coverage**: 10,000+ cryptocurrencies
- **Rate Limit**: Free tier, reasonable limits
- **Data Quality**: Excellent, aggregated from 400+ exchanges
- **Delay**: Real-time to 1-minute delay
- **Best For**: Crypto prices, market caps, trending coins

### Alpha Vantage
- **Coverage**: Stocks, ETFs, forex, crypto
- **Rate Limit**: 25 API calls per day (free tier)
- **Data Quality**: Very good, sourced from IEX
- **Delay**: Real-time to 15-minute delay (free tier)
- **Best For**: Stock quotes when you haven't exhausted daily limit

### Yahoo Finance
- **Coverage**: Stocks, ETFs, indices, crypto
- **Rate Limit**: Generous (unofficial API)
- **Data Quality**: Good but unofficial
- **Delay**: 15-minute delay for stocks, real-time for crypto
- **Best For**: Backup source when other APIs are unavailable

## Safety Features

### Built-in Protections
- **Max Trade Amount**: Configurable limit per trade (default $10,000)
- **API Key Permissions**: Uses only trading permissions, no withdrawals
- **Separate Testnet Support**: Test on Binance Testnet before going live
- **Trade History Logging**: All trades saved to database

### Best Practices
1. **Start Small**: Test with small amounts first
2. **Use Stop Limits**: Set limit orders instead of market orders for better control
3. **Monitor Auto Profit**: Check that automated selling works as expected
4. **Secure Your Keys**: Never share API keys, enable IP restrictions
5. **Review Permissions**: Ensure API keys have only necessary permissions

## Rate Limiting

The platform handles rate limiting automatically:
- **Coinbase**: 600 GET requests/10s, 500 POST requests/10s
- **Binance**: 1200 requests/minute
- **CoinGecko**: 10-50 calls/minute (free tier)
- **Alpha Vantage**: 25 calls/day (free tier)
- **Yahoo Finance**: Unofficial, generous limits

## Troubleshooting

### "Exchange not configured" Error
- Check that API keys are properly set in `.env`
- Restart backend after adding keys
- Verify keys are correct (no extra spaces)

### Market Data Not Loading
- Check internet connection
- CoinGecko might be rate-limited (wait 1 minute)
- Alpha Vantage daily limit reached (wait until next day)
- Try refreshing with the "Refresh All" button

### Order Failed
- Insufficient balance in account
- Invalid symbol format (Binance uses BTCUSDT, Coinbase uses BTC-USD)
- Price/quantity doesn't meet exchange minimums
- API key lacks trading permissions

### Backend Won't Start
Check logs:
```bash
tail -50 /var/log/supervisor/backend.err.log
```

Common issues:
- Missing dependencies: `pip install python-binance coinbase-advanced-py pycoingecko alpha-vantage`
- Import errors: Check that all trading modules are in `/app/backend`

## API Rate Limit Status

Monitor your API usage:
- **Alpha Vantage**: 25 calls/day - Use sparingly for stocks
- **CoinGecko**: Free tier is generous - Primary crypto source
- **Yahoo Finance**: Unofficial but reliable - Good backup
- **Binance**: 1200 weight/minute - Plenty for manual trading
- **Coinbase**: High limits - Suitable for active trading

## Architecture

### Backend Modules
```
/app/backend/
├── trading_config.py          # Configuration and API keys
├── market_data_service.py     # Multi-source price aggregation
├── coinbase_service.py        # Coinbase Pro integration
├── binance_service.py         # Binance integration
├── portfolio_service.py       # Portfolio tracking & auto profit
└── server.py                  # FastAPI routes for trading
```

### Frontend Components
```
/app/frontend/src/
├── TradingPlatform.jsx        # Main trading interface
└── App.js                     # Navigation integration
```

### Database Collections
```
MongoDB:
├── trade_history              # All executed trades
└── [future: positions]        # Position tracking
```

## Future Enhancements

Planned features:
- [ ] WebSocket live price feeds
- [ ] Advanced charting (TradingView integration)
- [ ] More exchanges (Kraken, KuCoin)
- [ ] Options trading
- [ ] Futures trading
- [ ] Portfolio analytics dashboard
- [ ] Risk management tools
- [ ] Tax reporting exports

## Support & Documentation

- **Coinbase API Docs**: https://docs.cdp.coinbase.com/advanced-trade/docs
- **Binance API Docs**: https://binance-docs.github.io/apidocs/spot/en/
- **CoinGecko API**: https://www.coingecko.com/en/api/documentation
- **Alpha Vantage API**: https://www.alphavantage.co/documentation/

## Security Warnings

⚠️ **Important Security Notes**:
- Never commit `.env` files to version control
- Use API key IP restrictions when possible
- Disable withdrawal permissions on trading API keys
- Start with small test amounts
- Monitor your accounts regularly
- This is LIVE TRADING with REAL MONEY - test thoroughly

## Disclaimer

This trading platform is for educational and personal use. You are responsible for your own trading decisions. Cryptocurrency and stock trading involve substantial risk of loss. Only trade with money you can afford to lose. The developers are not responsible for any financial losses incurred through use of this platform.

---

## Quick Reference

### Supported Cryptocurrencies
- BTC (Bitcoin)
- ETH (Ethereum)
- BNB (Binance Coin)
- ADA (Cardano)
- SOL (Solana)
- XRP (Ripple)
- More can be added by modifying the symbol dropdown

### Order Types
- **Market Order**: Instant execution at current price
- **Limit Order**: Execute only at specified price or better

### Trading Pairs
- **Binance**: BTCUSDT, ETHUSDT, BNBUSDT, etc.
- **Coinbase**: BTC-USD, ETH-USD, BNB-USD, etc.

### Status Indicators
- 🟢 **Green**: Exchange connected and operational
- 🟡 **Orange**: Auto profit disabled
- 🔴 **Red**: Exchange not configured

---

**Built with**: FastAPI, React, MongoDB, Coinbase Advanced Trade API, Binance API, CoinGecko API, Alpha Vantage API, Yahoo Finance

**Version**: 1.0.0 - Initial Release
