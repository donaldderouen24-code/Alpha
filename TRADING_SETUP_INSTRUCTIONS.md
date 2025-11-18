# Trading Platform Setup Instructions for User

## 🎉 Your Trading Platform is Ready!

The trading platform has been successfully integrated into ALPHA. However, to start trading, you need to configure your API keys.

## ⚙️ Setup Steps

### Step 1: Get API Keys

You'll need API keys from the exchanges you want to use:

#### Option 1: Coinbase Pro (Recommended for beginners)
1. Go to: https://www.coinbase.com/settings/api
2. Click "New API Key"
3. Enable these permissions:
   - ✅ View accounts
   - ✅ Trade
   - ❌ Transfer (keep disabled for safety)
4. **Save both the API Key and API Secret immediately** (secret shown only once!)

#### Option 2: Binance (More trading pairs)
1. Go to: https://www.binance.com/en/my/settings/api-management
2. Create API Key
3. Enable "Spot & Margin Trading"
4. **Optionally restrict to your IP address** for extra security
5. Save API Key and Secret

#### Option 3: Alpha Vantage (Free stock data - Optional)
1. Go to: https://www.alphavantage.co/support/#api-key
2. Fill out form (takes 30 seconds)
3. Get instant free API key
4. Free tier: 25 API calls per day

### Step 2: Add Keys to Backend

1. Open `/app/backend/.env` file
2. Add your API keys:

```bash
# Coinbase Pro (if using)
COINBASE_API_KEY=your_actual_coinbase_key_here
COINBASE_API_SECRET=your_actual_coinbase_secret_here

# Binance (if using)
BINANCE_API_KEY=your_actual_binance_key_here
BINANCE_API_SECRET=your_actual_binance_secret_here

# Alpha Vantage (optional - for stock data)
ALPHA_VANTAGE_KEY=your_actual_alphavantage_key_here

# Trading settings (optional - these are defaults)
AUTO_PROFIT_THRESHOLD=0.05
MAX_TRADE_AMOUNT=10000
```

**Note**: You don't need to configure ALL exchanges. Configure only the ones you want to use. Leave others empty.

### Step 3: Restart Backend

After adding your keys:
```bash
sudo supervisorctl restart backend
```

### Step 4: Access Trading Platform

1. Open ALPHA in your browser
2. Look in the sidebar (left side)
3. Click the green **"Trading Platform"** button
4. You should now see your trading dashboard!

## 🚀 What You Can Do

### Without Any API Keys (Testing)
- View the trading platform UI
- See how the interface works
- Explore the layout and features
- Test market data (uses free public APIs)

### With Coinbase or Binance Keys (Live Trading)
- ✅ View your real account balances
- ✅ Get live market prices from multiple sources
- ✅ Place real buy/sell orders
- ✅ Track your portfolio
- ✅ Enable automated profit-taking
- ✅ View trade history

## 📊 Features Overview

### Dashboard Tab
- Total portfolio value across all exchanges
- Live market data from multiple sources (split-screen view)
- Auto profit-taking toggle
- Recent trade history

### Trading Tab
- Place market orders (instant execution)
- Place limit orders (set your price)
- Support for BTC, ETH, BNB, ADA, SOL, XRP
- Real-time price display

### Balances Tab
- View all your cryptocurrency holdings
- Separate sections for each exchange
- Shows available, locked, and total amounts

### History Tab
- Complete trade log
- Profit/loss tracking for automated trades
- Filterable by exchange and symbol

## 🛡️ Safety Features

### Built-In Protection
- ✅ Max trade amount limit (default: $10,000)
- ✅ API keys never have withdrawal permissions
- ✅ All trades logged to database
- ✅ Auto profit-taking with configurable thresholds

### Best Practices
1. **Start Small**: Test with $10-50 first
2. **Test on One Exchange**: Don't configure all at once
3. **Use Limit Orders**: Better price control than market orders
4. **Monitor First**: Watch the platform for a few hours before automating
5. **Secure Your Keys**: Never share them, enable IP restrictions

## 🔧 Troubleshooting

### "Exchange not configured" error
- Check that API keys are in `.env` file
- Make sure there are no extra spaces around the keys
- Restart backend after adding keys
- Verify keys are correct on exchange website

### No market data showing
- CoinGecko API might be rate-limited (wait 1 minute)
- Alpha Vantage has 25 calls/day limit (free tier)
- Click "Refresh All" button to retry

### Orders failing
- Check if you have sufficient balance
- Verify API key has "trading" permission enabled
- Make sure symbol format is correct (BTCUSDT for Binance, BTC-USD for Coinbase)

## 📈 Market Data Sources

The platform shows prices from 3 FREE sources:

1. **CoinGecko** (Primary)
   - Best for crypto prices
   - Free tier, generous limits
   - Real-time to 1-min delay

2. **Alpha Vantage** (Secondary)
   - Good for stock prices
   - 25 calls/day free
   - Use sparingly

3. **Yahoo Finance** (Backup)
   - Unofficial but reliable
   - Good fallback option
   - No strict rate limits

## ⚠️ Important Warnings

- This is **LIVE TRADING** with **REAL MONEY**
- Cryptocurrency is highly volatile and risky
- Only invest what you can afford to lose
- Test thoroughly with small amounts first
- You are responsible for your trading decisions
- Not financial advice

## 🎯 Quick Start (Minimal Setup)

Want to get started FAST? Do this:

1. Get **just Coinbase Pro** API keys (easiest setup)
2. Add ONLY these two lines to `.env`:
   ```bash
   COINBASE_API_KEY=your_key
   COINBASE_API_SECRET=your_secret
   ```
3. Restart backend: `sudo supervisorctl restart backend`
4. Open Trading Platform in ALPHA
5. Start with a $10 test trade

That's it! You can add more exchanges later.

## 📚 Full Documentation

See `TRADING_PLATFORM_GUIDE.md` for:
- Complete API documentation
- Advanced features
- Rate limit details
- Architecture overview
- Future roadmap

## 💡 Tips

- **API Keys are Optional**: Platform works without them (limited features)
- **Free Data**: Market data works without any API keys
- **Start Simple**: Configure one exchange, test it, then add more
- **Backup Keys**: Keep a copy of your API keys in a secure password manager
- **Monitor Daily**: Check your trades and balances daily

## ✅ Checklist

Before starting live trading:
- [ ] API keys obtained from exchange
- [ ] Keys added to `/app/backend/.env`
- [ ] Backend restarted
- [ ] Trading Platform loads without errors
- [ ] Can see your account balances
- [ ] Placed successful test order (small amount)
- [ ] Verified trade appears in history
- [ ] Understand how to monitor positions
- [ ] Know how to disable auto profit-taking if needed

---

**Need Help?**
- Check `TRADING_PLATFORM_GUIDE.md` for detailed documentation
- Review exchange API documentation
- Test with small amounts first
- Reach out if you have questions

**Happy Trading! 📈🚀**
