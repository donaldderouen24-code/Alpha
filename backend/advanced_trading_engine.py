"""
ALPHA Advanced Trading Engine
Combines historical trading wisdom with modern AI/ML

Based on research of:
- Warren Buffett (Value Investing)
- George Soros (Macro Trading)  
- Renaissance Technologies (Quant/Algo Trading)
- Modern ML/AI strategies (2024-2025)

⚠️ EXTREME RISK WARNING:
This is an advanced algorithmic trading system.
You can lose significant amounts of money.
Use at your own risk. Not financial advice.
"""

import yfinance as yf
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

class AdvancedTradingEngine:
    """
    Multi-strategy trading engine combining:
    1. Value Investing (Buffett)
    2. Momentum Trading (Quant)
    3. Mean Reversion (Statistical)
    4. Technical Analysis
    5. Machine Learning Predictions
    6. Risk Management
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.ml_model = None
        
    def analyze_comprehensive(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """
        Comprehensive multi-strategy analysis
        """
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            info = stock.info
            
            if hist.empty:
                return {"success": False, "error": "No data"}
            
            # 1. VALUE INVESTING ANALYSIS (Buffett Style)
            value_score = self._value_investing_analysis(info)
            
            # 2. MOMENTUM ANALYSIS (Quant Style)
            momentum_score = self._momentum_analysis(hist)
            
            # 3. MEAN REVERSION ANALYSIS
            mean_reversion_score = self._mean_reversion_analysis(hist)
            
            # 4. TECHNICAL INDICATORS
            technical_signals = self._technical_indicators(hist)
            
            # 5. MACHINE LEARNING PREDICTION
            ml_prediction = self._ml_prediction(hist)
            
            # 6. RISK ASSESSMENT
            risk_metrics = self._risk_assessment(hist, info)
            
            # 7. COMBINED SCORE & DECISION
            combined_decision = self._combine_strategies(
                value_score,
                momentum_score,
                mean_reversion_score,
                technical_signals,
                ml_prediction,
                risk_metrics
            )
            
            current_price = hist['Close'].iloc[-1]
            
            return {
                "success": True,
                "symbol": symbol,
                "current_price": float(current_price),
                
                # Individual Strategy Scores
                "value_score": value_score,
                "momentum_score": momentum_score,
                "mean_reversion_score": mean_reversion_score,
                "technical_signals": technical_signals,
                "ml_prediction": ml_prediction,
                "risk_metrics": risk_metrics,
                
                # Combined Decision
                "recommendation": combined_decision['recommendation'],
                "action": combined_decision['action'],
                "confidence": combined_decision['confidence'],
                "reasoning": combined_decision['reasoning'],
                "target_price": combined_decision['target_price'],
                "stop_loss": combined_decision['stop_loss'],
                
                # Metadata
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _value_investing_analysis(self, info: Dict) -> Dict[str, Any]:
        """
        Warren Buffett style value analysis
        """
        score = 0
        signals = []
        
        # P/E Ratio (Lower is better, typically < 15 is good)
        pe = info.get('trailingPE', 999)
        if pe < 15:
            score += 2
            signals.append("✅ Low P/E ratio (undervalued)")
        elif pe < 25:
            score += 1
            signals.append("🟡 Moderate P/E ratio")
        else:
            score -= 1
            signals.append("⚠️ High P/E ratio (potentially overvalued)")
        
        # P/B Ratio (Price to Book, < 1 is often undervalued)
        pb = info.get('priceToBook', 999)
        if pb < 1:
            score += 2
            signals.append("✅ Trading below book value")
        elif pb < 3:
            score += 1
            signals.append("🟡 Reasonable price to book")
        
        # Debt to Equity (Lower is better)
        debt_to_equity = info.get('debtToEquity', 999)
        if debt_to_equity < 50:
            score += 1
            signals.append("✅ Low debt (financially stable)")
        elif debt_to_equity > 100:
            score -= 1
            signals.append("⚠️ High debt levels")
        
        # Return on Equity (Higher is better, > 15% is excellent)
        roe = info.get('returnOnEquity', 0) * 100
        if roe > 15:
            score += 2
            signals.append(f"✅ Strong ROE ({roe:.1f}%)")
        elif roe > 10:
            score += 1
            signals.append(f"🟡 Decent ROE ({roe:.1f}%)")
        
        # Profit Margins
        profit_margin = info.get('profitMargins', 0) * 100
        if profit_margin > 20:
            score += 1
            signals.append(f"✅ High profit margin ({profit_margin:.1f}%)")
        
        # Dividend Yield (bonus for income)
        dividend_yield = info.get('dividendYield', 0) * 100
        if dividend_yield > 2:
            score += 1
            signals.append(f"✅ Good dividend yield ({dividend_yield:.2f}%)")
        
        return {
            "score": score,
            "max_score": 10,
            "signals": signals,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "roe": roe,
            "strategy": "Value Investing (Buffett)"
        }
    
    def _momentum_analysis(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """
        Momentum/Trend following (Renaissance/Quant style)
        """
        score = 0
        signals = []
        
        close = hist['Close']
        
        # Multiple timeframe momentum
        returns_1d = close.pct_change(1).iloc[-1] * 100
        returns_5d = close.pct_change(5).iloc[-1] * 100
        returns_20d = close.pct_change(20).iloc[-1] * 100
        returns_60d = close.pct_change(60).iloc[-1] * 100
        
        # Short-term momentum (1-5 days)
        if returns_1d > 1:
            score += 1
            signals.append(f"✅ Strong 1-day momentum (+{returns_1d:.2f}%)")
        elif returns_1d < -1:
            score -= 1
            signals.append(f"⚠️ Negative 1-day momentum ({returns_1d:.2f}%)")
        
        # Medium-term momentum (5-20 days)
        if returns_20d > 5:
            score += 2
            signals.append(f"✅ Strong 20-day momentum (+{returns_20d:.2f}%)")
        elif returns_20d < -5:
            score -= 2
            signals.append(f"⚠️ Negative 20-day momentum ({returns_20d:.2f}%)")
        
        # Long-term momentum (60 days)
        if returns_60d > 10:
            score += 2
            signals.append(f"✅ Strong 60-day momentum (+{returns_60d:.2f}%)")
        elif returns_60d < -10:
            score -= 2
            signals.append(f"⚠️ Negative 60-day momentum ({returns_60d:.2f}%)")
        
        # Moving average crossovers
        ma_20 = close.rolling(20).mean().iloc[-1]
        ma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else ma_20
        current_price = close.iloc[-1]
        
        if current_price > ma_20 > ma_50:
            score += 2
            signals.append("✅ Golden cross pattern (bullish)")
        elif current_price < ma_20 < ma_50:
            score -= 2
            signals.append("⚠️ Death cross pattern (bearish)")
        
        # Rate of change (acceleration)
        roc_20 = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21] * 100) if len(close) > 21 else 0
        if roc_20 > 10:
            score += 1
            signals.append(f"✅ Strong momentum acceleration ({roc_20:.1f}%)")
        
        return {
            "score": score,
            "max_score": 10,
            "signals": signals,
            "returns_1d": returns_1d,
            "returns_20d": returns_20d,
            "returns_60d": returns_60d,
            "strategy": "Momentum Trading (Quant)"
        }
    
    def _mean_reversion_analysis(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """
        Mean reversion / Statistical arbitrage
        """
        score = 0
        signals = []
        
        close = hist['Close']
        
        # Bollinger Bands
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        upper_band = sma_20 + (2 * std_20)
        lower_band = sma_20 - (2 * std_20)
        
        current_price = close.iloc[-1]
        current_sma = sma_20.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Check if oversold (near lower band) - buy signal
        if current_price < current_lower:
            score += 3
            signals.append("✅ Oversold - price below lower Bollinger Band")
        elif current_price < current_sma * 0.95:
            score += 2
            signals.append("✅ Below mean - potential reversion up")
        
        # Check if overbought (near upper band) - sell signal
        if current_price > current_upper:
            score -= 3
            signals.append("⚠️ Overbought - price above upper Bollinger Band")
        elif current_price > current_sma * 1.05:
            score -= 2
            signals.append("⚠️ Above mean - potential reversion down")
        
        # RSI (Relative Strength Index)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            score += 2
            signals.append(f"✅ RSI oversold ({current_rsi:.1f}) - buy signal")
        elif current_rsi > 70:
            score -= 2
            signals.append(f"⚠️ RSI overbought ({current_rsi:.1f}) - sell signal")
        
        # Z-score (distance from mean in standard deviations)
        z_score = (current_price - current_sma) / std_20.iloc[-1]
        if z_score < -2:
            score += 2
            signals.append(f"✅ Extremely oversold (Z-score: {z_score:.2f})")
        elif z_score > 2:
            score -= 2
            signals.append(f"⚠️ Extremely overbought (Z-score: {z_score:.2f})")
        
        return {
            "score": score,
            "max_score": 10,
            "signals": signals,
            "rsi": current_rsi,
            "z_score": z_score,
            "bollinger_position": "oversold" if current_price < current_lower else "overbought" if current_price > current_upper else "neutral",
            "strategy": "Mean Reversion (Statistical)"
        }
    
    def _technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """
        Technical indicators analysis
        """
        close = hist['Close']
        volume = hist['Volume']
        
        signals = []
        score = 0
        
        # MACD (Moving Average Convergence Divergence)
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9).mean()
        macd_histogram = macd - signal_line
        
        if macd.iloc[-1] > signal_line.iloc[-1] and macd_histogram.iloc[-1] > 0:
            score += 2
            signals.append("✅ MACD bullish crossover")
        elif macd.iloc[-1] < signal_line.iloc[-1]:
            score -= 1
            signals.append("⚠️ MACD bearish")
        
        # Volume trend
        avg_volume = volume.rolling(20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        
        if current_volume > avg_volume * 1.5:
            score += 1
            signals.append("✅ High volume (strong interest)")
        
        # ADX (Average Directional Index) - trend strength
        # Simplified version
        high = hist['High']
        low = hist['Low']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        
        atr = tr.rolling(14).mean()
        
        return {
            "score": score,
            "max_score": 5,
            "signals": signals,
            "macd_bullish": macd.iloc[-1] > signal_line.iloc[-1],
            "high_volume": current_volume > avg_volume * 1.5
        }
    
    def _ml_prediction(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """
        Machine Learning price prediction
        """
        try:
            # Prepare features
            df = hist.copy()
            df['Returns'] = df['Close'].pct_change()
            df['MA_5'] = df['Close'].rolling(5).mean()
            df['MA_20'] = df['Close'].rolling(20).mean()
            df['Vol_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
            df['RSI'] = self._calculate_rsi(df['Close'])
            
            # Drop NaN
            df = df.dropna()
            
            if len(df) < 50:
                return {"prediction": "insufficient_data", "confidence": 0}
            
            # Create target (1 if price goes up next day, 0 if down)
            df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
            df = df[:-1]  # Remove last row (no target)
            
            # Features
            features = ['Returns', 'MA_5', 'MA_20', 'Vol_ratio', 'RSI']
            X = df[features].values[-60:]  # Last 60 days
            y = df['Target'].values[-60:]
            
            # Train simple ML model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X[:-5], y[:-5])  # Train on all but last 5
            
            # Predict next day
            last_features = X[-1].reshape(1, -1)
            prediction = model.predict(last_features)[0]
            confidence = model.predict_proba(last_features)[0][prediction]
            
            # Calculate predicted price change
            recent_volatility = df['Returns'].std() * 100
            predicted_change = recent_volatility if prediction == 1 else -recent_volatility
            
            return {
                "prediction": "UP" if prediction == 1 else "DOWN",
                "confidence": float(confidence * 100),
                "predicted_change_percent": float(predicted_change),
                "model": "RandomForest"
            }
            
        except Exception as e:
            return {"prediction": "error", "confidence": 0, "error": str(e)}
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _risk_assessment(self, hist: pd.DataFrame, info: Dict) -> Dict[str, Any]:
        """
        Comprehensive risk assessment
        """
        close = hist['Close']
        
        # Volatility (annualized)
        returns = close.pct_change()
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Beta (market correlation)
        beta = info.get('beta', 1.0)
        
        # Sharpe ratio estimate
        avg_return = returns.mean() * 252 * 100  # Annualized
        risk_free_rate = 4.0  # Approximate
        sharpe = (avg_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Risk level
        if volatility < 20:
            risk_level = "LOW"
        elif volatility < 35:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"
        
        return {
            "volatility": float(volatility),
            "max_drawdown": float(max_drawdown),
            "beta": float(beta),
            "sharpe_ratio": float(sharpe),
            "risk_level": risk_level
        }
    
    def _combine_strategies(
        self,
        value_score: Dict,
        momentum_score: Dict,
        mean_reversion_score: Dict,
        technical_signals: Dict,
        ml_prediction: Dict,
        risk_metrics: Dict
    ) -> Dict[str, Any]:
        """
        Combine all strategies with weighted scoring
        """
        # Weighted combination (adjust weights based on market conditions)
        total_score = 0
        max_score = 0
        reasoning = []
        
        # Value investing weight: 25%
        value_weight = 0.25
        total_score += (value_score['score'] / value_score['max_score']) * 100 * value_weight
        max_score += 100 * value_weight
        if value_score['score'] > 5:
            reasoning.append(f"Strong value fundamentals ({value_score['score']}/10)")
        
        # Momentum weight: 30%
        momentum_weight = 0.30
        total_score += (momentum_score['score'] / momentum_score['max_score']) * 100 * momentum_weight
        max_score += 100 * momentum_weight
        if momentum_score['score'] > 5:
            reasoning.append(f"Strong momentum ({momentum_score['score']}/10)")
        
        # Mean reversion weight: 20%
        mr_weight = 0.20
        total_score += (mean_reversion_score['score'] / mean_reversion_score['max_score']) * 100 * mr_weight
        max_score += 100 * mr_weight
        
        # Technical weight: 15%
        tech_weight = 0.15
        total_score += (technical_signals['score'] / technical_signals['max_score']) * 100 * tech_weight
        max_score += 100 * tech_weight
        
        # ML prediction weight: 10%
        ml_weight = 0.10
        if ml_prediction['prediction'] == "UP":
            ml_contribution = ml_prediction['confidence'] * ml_weight
            total_score += ml_contribution
            reasoning.append(f"ML predicts UP ({ml_prediction['confidence']:.0f}% confidence)")
        elif ml_prediction['prediction'] == "DOWN":
            ml_contribution = -ml_prediction['confidence'] * ml_weight
            total_score += ml_contribution
            reasoning.append(f"ML predicts DOWN ({ml_prediction['confidence']:.0f}% confidence)")
        
        max_score += 100 * ml_weight
        
        # Normalize to 0-100
        confidence = max(0, min(100, total_score))
        
        # Risk adjustment
        if risk_metrics['risk_level'] == "HIGH":
            confidence *= 0.85  # Reduce confidence for high-risk stocks
            reasoning.append("⚠️ High volatility - confidence reduced")
        
        # Generate recommendation
        if confidence >= 75:
            recommendation = "🟢 STRONG BUY"
            action = "BUY"
            target_multiplier = 1.15
            stop_multiplier = 0.95
        elif confidence >= 60:
            recommendation = "🟡 BUY"
            action = "BUY"
            target_multiplier = 1.10
            stop_multiplier = 0.96
        elif confidence >= 40:
            recommendation = "⚪ HOLD"
            action = "HOLD"
            target_multiplier = 1.05
            stop_multiplier = 0.97
        elif confidence >= 25:
            recommendation = "🟠 SELL"
            action = "SELL"
            target_multiplier = 0.95
            stop_multiplier = 1.03
        else:
            recommendation = "🔴 STRONG SELL"
            action = "SELL"
            target_multiplier = 0.90
            stop_multiplier = 1.05
        
        # Calculate target and stop-loss (simplified)
        current_price = 100  # Will be replaced with actual
        target_price = current_price * target_multiplier
        stop_loss = current_price * stop_multiplier
        
        return {
            "recommendation": recommendation,
            "action": action,
            "confidence": round(confidence, 1),
            "reasoning": reasoning,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "weighted_scores": {
                "value": value_score['score'],
                "momentum": momentum_score['score'],
                "mean_reversion": mean_reversion_score['score'],
                "technical": technical_signals['score']
            }
        }
