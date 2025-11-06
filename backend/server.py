from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
import base64
import json
import subprocess
import tempfile
import requests
from PyPDF2 import PdfReader
import io
from bs4 import BeautifulSoup
import re
import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# =============== MODELS ===============

class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # 'user', 'assistant', or 'tool'
    content: str
    tool_name: Optional[str] = None
    tool_output: Optional[Any] = None
    image_data: Optional[str] = None  # base64 encoded image
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Conversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    title: str = "New Conversation"
    messages: List[ConversationMessage] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model: str = "gpt-4o-mini"
    provider: str = "openai"
    enable_tools: bool = True

class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_id: str
    tool_calls: Optional[List[Dict]] = None
    image_data: Optional[str] = None

class ModelInfo(BaseModel):
    provider: str
    model: str
    name: str
    description: str

class ToolDefinition(BaseModel):
    name: str
    description: str
    enabled: bool = True

class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"

class WebSearchRequest(BaseModel):
    query: str

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "gpt-image-1"

class WebsiteCloneRequest(BaseModel):
    url: str

class WebsiteCreateRequest(BaseModel):
    description: str
    style: Optional[str] = "modern"  # modern, minimal, corporate, creative
    include_js: bool = True

class FileOperationRequest(BaseModel):
    operation: str  # create, read, edit, search
    path: Optional[str] = None
    content: Optional[str] = None
    search_pattern: Optional[str] = None

class DatabaseQueryRequest(BaseModel):
    collection: str
    operation: str  # find, insert, update, delete, aggregate
    query: Optional[Dict] = None
    data: Optional[Dict] = None

class APITestRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[Dict] = None
    body: Optional[Dict] = None

class StockAnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str = "full"  # full, technical, fundamental, prediction

class StockTradeRequest(BaseModel):
    action: str  # buy, sell, analyze
    symbol: str
    quantity: Optional[int] = None
    portfolio_id: Optional[str] = "default"

class AutoTradingConfig(BaseModel):
    enabled: bool = False
    max_trade_amount: float = 1000.0  # Max $ per trade
    max_daily_trades: int = 5  # Max trades per day
    max_total_investment: float = 10000.0  # Max total invested
    stop_loss_percent: float = 5.0  # Auto-sell if loses this %
    take_profit_percent: float = 10.0  # Auto-sell if gains this %
    min_confidence: int = 70  # Only trade if confidence >= this
    allowed_symbols: Optional[List[str]] = None  # Whitelist, None = all
    blacklist_symbols: Optional[List[str]] = []  # Blacklist
    portfolio_id: str = "default"

class AutoTradeStatusRequest(BaseModel):
    portfolio_id: str = "default"

# =============== TOOL FUNCTIONS ===============

async def execute_python_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code in a restricted environment
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute with timeout
        result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=5  # 5 second timeout
        )
        
        # Clean up
        os.unlink(temp_file)
        
        output = result.stdout if result.stdout else result.stderr
        success = result.returncode == 0
        
        return {
            "success": success,
            "output": output,
            "error": result.stderr if not success else None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Code execution timed out (5 second limit)"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }

async def web_search(query: str) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo
    """
    try:
        # Using DuckDuckGo HTML version (no API key needed)
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.post(url, data=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Simple parsing - extract text snippets
            text = response.text
            # Basic extraction (in production, use BeautifulSoup)
            results = []
            
            # Simple search for result snippets
            lines = text.split('\n')
            snippet_count = 0
            for i, line in enumerate(lines):
                if 'result__snippet' in line and snippet_count < 5:
                    # Extract some context
                    snippet = lines[i+1] if i+1 < len(lines) else ""
                    if snippet.strip():
                        results.append(snippet.strip()[:200])
                        snippet_count += 1
            
            return {
                "success": True,
                "results": results if results else ["Search completed but no clear results found. Try rephrasing your query."],
                "query": query
            }
        else:
            return {
                "success": False,
                "error": "Search service unavailable",
                "query": query
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}",
            "query": query
        }

async def generate_image(prompt: str) -> Dict[str, Any]:
    """
    Generate an image using DALL-E
    """
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        image_gen = OpenAIImageGeneration(api_key=api_key)
        
        # Generate image
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            # Convert to base64
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return {
                "success": True,
                "image_base64": image_base64,
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": "No image was generated"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def clone_website(url: str) -> Dict[str, Any]:
    """
    Clone a website by fetching and analyzing its structure
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract key information
            title = soup.find('title').get_text() if soup.find('title') else "No title"
            
            # Extract CSS (inline styles and stylesheets)
            styles = []
            for style in soup.find_all('style'):
                styles.append(style.get_text())
            
            # Extract external CSS links
            css_links = []
            for link in soup.find_all('link', rel='stylesheet'):
                css_links.append(link.get('href', ''))
            
            # Extract structure
            headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])]
            paragraphs = [p.get_text().strip()[:200] for p in soup.find_all('p')[:5]]
            
            # Extract JavaScript
            scripts = []
            for script in soup.find_all('script'):
                if script.get('src'):
                    scripts.append(script.get('src'))
            
            # Clean HTML (remove scripts for security)
            for tag in soup(['script', 'iframe', 'embed']):
                tag.decompose()
            
            html_structure = str(soup)[:5000]  # First 5000 chars
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "headings": headings[:10],
                "paragraphs": paragraphs,
                "css_links": css_links[:5],
                "inline_styles": styles[0][:1000] if styles else "",
                "scripts": scripts[:5],
                "html_structure": html_structure,
                "analysis": f"Website '{title}' has {len(headings)} headings and {len(paragraphs)} paragraphs"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to fetch website: HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def create_website(description: str, style: str = "modern", include_js: bool = True) -> Dict[str, Any]:
    """
    Generate a complete website from description
    """
    try:
        # Use AI to generate website code
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are an expert web developer. Create complete, production-ready HTML/CSS/JS code."
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        prompt = f"""Create a complete, fully functional website with the following requirements:

Description: {description}
Style: {style}
Include JavaScript: {include_js}

Requirements:
1. Complete HTML structure with proper DOCTYPE and meta tags
2. Modern CSS with {style} design aesthetic
3. Responsive design (mobile-friendly)
4. {"Interactive JavaScript features" if include_js else "Pure HTML/CSS only"}
5. Use modern web standards
6. Include proper semantic HTML
7. Add beautiful colors and styling
8. Make it production-ready

Return ONLY the complete HTML code (with embedded CSS and JS). No explanations."""

        user_msg = UserMessage(text=prompt)
        html_code = await chat.send_message(user_msg)
        
        # Clean and validate HTML
        if '<!DOCTYPE' not in html_code and '<html' not in html_code:
            # Wrap in proper HTML structure if missing
            html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
</head>
<body>
{html_code}
</body>
</html>"""
        
        return {
            "success": True,
            "html": html_code,
            "description": description,
            "style": style,
            "preview_url": "/preview"  # Will be handled by frontend
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def file_operation(operation: str, path: str = None, content: str = None, search_pattern: str = None) -> Dict[str, Any]:
    """
    Advanced file operations - ALPHA's file system access
    """
    try:
        if operation == "create" and path and content:
            # Create a file
            with open(path, 'w') as f:
                f.write(content)
            return {
                "success": True,
                "operation": "create",
                "path": path,
                "message": f"File created: {path}"
            }
        
        elif operation == "read" and path:
            # Read a file
            with open(path, 'r') as f:
                file_content = f.read()
            return {
                "success": True,
                "operation": "read",
                "path": path,
                "content": file_content[:5000]  # First 5000 chars
            }
        
        elif operation == "search" and search_pattern:
            # Search for files/patterns
            import glob
            matches = glob.glob(search_pattern, recursive=True)
            return {
                "success": True,
                "operation": "search",
                "pattern": search_pattern,
                "matches": matches[:50]  # First 50 matches
            }
        
        elif operation == "list" and path:
            # List directory contents
            import os
            items = os.listdir(path)
            return {
                "success": True,
                "operation": "list",
                "path": path,
                "items": items[:100]
            }
        
        else:
            return {
                "success": False,
                "error": "Invalid operation or missing parameters"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def database_query(collection: str, operation: str, query: Dict = None, data: Dict = None) -> Dict[str, Any]:
    """
    Direct database operations - ALPHA's database access
    """
    try:
        coll = db[collection]
        
        if operation == "find":
            results = await coll.find(query or {}, {"_id": 0}).limit(20).to_list(20)
            return {
                "success": True,
                "operation": "find",
                "collection": collection,
                "count": len(results),
                "results": results
            }
        
        elif operation == "insert" and data:
            result = await coll.insert_one(data)
            return {
                "success": True,
                "operation": "insert",
                "collection": collection,
                "inserted_id": str(result.inserted_id)
            }
        
        elif operation == "count":
            count = await coll.count_documents(query or {})
            return {
                "success": True,
                "operation": "count",
                "collection": collection,
                "count": count
            }
        
        elif operation == "aggregate" and query:
            results = await coll.aggregate(query).to_list(20)
            return {
                "success": True,
                "operation": "aggregate",
                "collection": collection,
                "results": results
            }
        
        else:
            return {
                "success": False,
                "error": "Invalid operation"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def test_api(url: str, method: str = "GET", headers: Dict = None, body: Dict = None) -> Dict[str, Any]:
    """
    Test any API endpoint - ALPHA's API testing capability
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=body, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=body, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return {"success": False, "error": "Unsupported HTTP method"}
        
        return {
            "success": True,
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": dict(response.headers),
            "body": response.text[:2000],  # First 2000 chars
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def analyze_stock(symbol: str, analysis_type: str = "full") -> Dict[str, Any]:
    """
    Advanced stock analysis with AI-powered predictions
    """
    try:
        stock = yf.Ticker(symbol)
        
        # Get stock info
        info = stock.info
        
        # Get historical data
        hist = stock.history(period="1y")
        
        if hist.empty:
            return {"success": False, "error": f"No data found for symbol {symbol}"}
        
        # Calculate technical indicators
        current_price = hist['Close'].iloc[-1]
        price_change_1d = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0
        price_change_1w = ((current_price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5] * 100) if len(hist) > 5 else 0
        price_change_1m = ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21] * 100) if len(hist) > 21 else 0
        
        # Calculate moving averages
        ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1] if len(hist) >= 20 else current_price
        ma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else current_price
        ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else current_price
        
        # Calculate volatility
        volatility = hist['Close'].pct_change().std() * (252 ** 0.5) * 100  # Annualized
        
        # Volume analysis
        avg_volume = hist['Volume'].mean()
        current_volume = hist['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # AI-Powered Price Prediction using Linear Regression
        if len(hist) >= 30:
            # Prepare data for ML model
            hist['Days'] = range(len(hist))
            X = hist[['Days']].values[-30:]  # Last 30 days
            y = hist['Close'].values[-30:]
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next 7 days
            future_days = np.array([[len(hist) + i] for i in range(1, 8)])
            predictions = model.predict(future_days)
            
            predicted_change = ((predictions[-1] - current_price) / current_price * 100)
        else:
            predictions = []
            predicted_change = 0
        
        # Generate trading signal
        signals = []
        score = 0
        
        # Technical signals
        if current_price > ma_20:
            signals.append("✅ Price above 20-day MA (Bullish)")
            score += 1
        else:
            signals.append("⚠️ Price below 20-day MA (Bearish)")
            score -= 1
        
        if current_price > ma_50:
            signals.append("✅ Price above 50-day MA (Bullish)")
            score += 1
        else:
            signals.append("⚠️ Price below 50-day MA (Bearish)")
            score -= 1
        
        if ma_20 > ma_50:
            signals.append("✅ 20-MA above 50-MA (Bullish trend)")
            score += 1
        else:
            signals.append("⚠️ 20-MA below 50-MA (Bearish trend)")
            score -= 1
        
        if volume_ratio > 1.5:
            signals.append("✅ High volume (Strong interest)")
            score += 1
        elif volume_ratio < 0.5:
            signals.append("⚠️ Low volume (Weak interest)")
            score -= 0.5
        
        if predicted_change > 5:
            signals.append(f"✅ AI predicts {predicted_change:.1f}% gain in 7 days")
            score += 2
        elif predicted_change < -5:
            signals.append(f"⚠️ AI predicts {predicted_change:.1f}% loss in 7 days")
            score -= 2
        
        # Generate recommendation
        if score >= 4:
            recommendation = "🟢 STRONG BUY - High probability of profit"
            action = "BUY"
        elif score >= 2:
            recommendation = "🟡 BUY - Moderate upside potential"
            action = "BUY"
        elif score >= -1:
            recommendation = "⚪ HOLD - Wait for better signals"
            action = "HOLD"
        elif score >= -3:
            recommendation = "🟠 SELL - Moderate downside risk"
            action = "SELL"
        else:
            recommendation = "🔴 STRONG SELL - High probability of loss"
            action = "SELL"
        
        result = {
            "success": True,
            "symbol": symbol,
            "company_name": info.get('longName', symbol),
            "current_price": float(current_price),
            "currency": info.get('currency', 'USD'),
            
            # Price changes
            "price_change_1d": float(price_change_1d),
            "price_change_1w": float(price_change_1w),
            "price_change_1m": float(price_change_1m),
            
            # Technical indicators
            "ma_20": float(ma_20),
            "ma_50": float(ma_50),
            "ma_200": float(ma_200),
            "volatility": float(volatility),
            
            # Volume
            "current_volume": int(current_volume),
            "avg_volume": int(avg_volume),
            "volume_ratio": float(volume_ratio),
            
            # AI Prediction
            "predicted_7d_change": float(predicted_change),
            "predicted_7d_price": float(predictions[-1]) if len(predictions) > 0 else current_price,
            
            # Trading signals
            "signals": signals,
            "recommendation": recommendation,
            "action": action,
            "confidence_score": int((score + 5) * 10),  # 0-100 scale
            
            # Additional info
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE', 0),
            "52w_high": info.get('fiftyTwoWeekHigh', 0),
            "52w_low": info.get('fiftyTwoWeekLow', 0),
        }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def check_auto_trading_limits(config: Dict, portfolio: Dict, trade_amount: float) -> Dict[str, Any]:
    """
    Check if auto-trading limits allow this trade
    """
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Count today's trades
    today_trades = [t for t in portfolio.get('trades', []) if t.get('timestamp', '').startswith(today)]
    
    if len(today_trades) >= config['max_daily_trades']:
        return {
            "allowed": False,
            "reason": f"Daily trade limit reached ({config['max_daily_trades']} trades)"
        }
    
    # Check per-trade amount
    if trade_amount > config['max_trade_amount']:
        return {
            "allowed": False,
            "reason": f"Trade amount ${trade_amount:.2f} exceeds limit ${config['max_trade_amount']:.2f}"
        }
    
    # Check total investment
    total_invested = sum(pos['quantity'] * pos['avg_price'] for pos in portfolio.get('positions', {}).values())
    
    if total_invested + trade_amount > config['max_total_investment']:
        return {
            "allowed": False,
            "reason": f"Total investment would exceed ${config['max_total_investment']:.2f}"
        }
    
    return {"allowed": True}

async def auto_trading_decision(symbol: str, config: Dict, portfolio_id: str = "default") -> Dict[str, Any]:
    """
    Make automated trading decision based on analysis and limits
    
    ⚠️ WARNING: This executes trades automatically. Use at your own risk.
    """
    try:
        # Get stock analysis
        analysis = await analyze_stock(symbol)
        
        if not analysis['success']:
            return {
                "success": False,
                "action": "SKIP",
                "reason": "Analysis failed",
                "error": analysis.get('error')
            }
        
        # Check if symbol is allowed
        if config.get('allowed_symbols') and symbol not in config['allowed_symbols']:
            return {
                "success": False,
                "action": "SKIP",
                "reason": f"{symbol} not in allowed list"
            }
        
        if symbol in config.get('blacklist_symbols', []):
            return {
                "success": False,
                "action": "SKIP",
                "reason": f"{symbol} is blacklisted"
            }
        
        # Check confidence threshold
        if analysis['confidence_score'] < config['min_confidence']:
            return {
                "success": False,
                "action": "SKIP",
                "reason": f"Confidence {analysis['confidence_score']}% below threshold {config['min_confidence']}%"
            }
        
        # Get portfolio
        portfolio = await db.portfolios.find_one({"portfolio_id": portfolio_id})
        if not portfolio:
            return {"success": False, "error": "Portfolio not found"}
        
        # Check if we already own this stock
        current_position = portfolio.get('positions', {}).get(symbol)
        
        # Decision logic
        action = analysis['action']  # BUY, SELL, or HOLD
        
        if action == "BUY" and not current_position:
            # Calculate quantity based on max_trade_amount
            price = analysis['current_price']
            max_quantity = int(config['max_trade_amount'] / price)
            
            if max_quantity < 1:
                return {
                    "success": False,
                    "action": "SKIP",
                    "reason": f"Stock price ${price:.2f} exceeds max trade amount"
                }
            
            # Check limits
            trade_amount = price * max_quantity
            limit_check = await check_auto_trading_limits(config, portfolio, trade_amount)
            
            if not limit_check['allowed']:
                return {
                    "success": False,
                    "action": "SKIP",
                    "reason": limit_check['reason']
                }
            
            # Execute buy
            result = await execute_paper_trade("buy", symbol, max_quantity, portfolio_id)
            result['auto_trade'] = True
            result['confidence'] = analysis['confidence_score']
            result['reason'] = analysis['recommendation']
            return result
        
        elif action == "SELL" and current_position:
            # Sell entire position
            quantity = current_position['quantity']
            result = await execute_paper_trade("sell", symbol, quantity, portfolio_id)
            result['auto_trade'] = True
            result['confidence'] = analysis['confidence_score']
            result['reason'] = analysis['recommendation']
            return result
        
        elif current_position:
            # Check stop-loss and take-profit
            avg_price = current_position['avg_price']
            current_price = analysis['current_price']
            percent_change = ((current_price - avg_price) / avg_price) * 100
            
            if percent_change <= -config['stop_loss_percent']:
                # Stop loss triggered
                quantity = current_position['quantity']
                result = await execute_paper_trade("sell", symbol, quantity, portfolio_id)
                result['auto_trade'] = True
                result['trigger'] = 'STOP_LOSS'
                result['loss_percent'] = percent_change
                return result
            
            elif percent_change >= config['take_profit_percent']:
                # Take profit triggered
                quantity = current_position['quantity']
                result = await execute_paper_trade("sell", symbol, quantity, portfolio_id)
                result['auto_trade'] = True
                result['trigger'] = 'TAKE_PROFIT'
                result['profit_percent'] = percent_change
                return result
        
        return {
            "success": True,
            "action": "HOLD",
            "reason": f"No action needed. Confidence: {analysis['confidence_score']}%"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def execute_paper_trade(action: str, symbol: str, quantity: int = 1, portfolio_id: str = "default") -> Dict[str, Any]:
    """
    Execute paper (simulated) trading with analysis
    
    ⚠️ DISCLAIMER: This is PAPER TRADING (simulation only).
    No real money is involved. For educational purposes only.
    """
    try:
        # Get current stock price
        stock = yf.Ticker(symbol)
        current_price = stock.history(period="1d")['Close'].iloc[-1]
        
        # Get portfolio from database
        portfolio = await db.portfolios.find_one({"portfolio_id": portfolio_id})
        
        if not portfolio:
            # Create new portfolio
            portfolio = {
                "portfolio_id": portfolio_id,
                "cash": 100000.0,  # Start with $100k paper money
                "positions": {},
                "trades": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.portfolios.insert_one(portfolio)
        
        # Execute trade
        if action.lower() == "buy":
            cost = current_price * quantity
            
            if cost > portfolio['cash']:
                return {
                    "success": False,
                    "error": f"Insufficient funds. Need ${cost:.2f}, have ${portfolio['cash']:.2f}"
                }
            
            # Update portfolio
            portfolio['cash'] -= cost
            
            if symbol in portfolio['positions']:
                portfolio['positions'][symbol]['quantity'] += quantity
                portfolio['positions'][symbol]['avg_price'] = (
                    (portfolio['positions'][symbol]['avg_price'] * portfolio['positions'][symbol]['quantity'] + 
                     current_price * quantity) / 
                    (portfolio['positions'][symbol]['quantity'] + quantity)
                )
            else:
                portfolio['positions'][symbol] = {
                    "quantity": quantity,
                    "avg_price": float(current_price)
                }
            
            # Record trade
            trade = {
                "action": "BUY",
                "symbol": symbol,
                "quantity": quantity,
                "price": float(current_price),
                "total": float(cost),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            portfolio['trades'].append(trade)
            
            # Update database
            await db.portfolios.update_one(
                {"portfolio_id": portfolio_id},
                {"$set": portfolio}
            )
            
            return {
                "success": True,
                "action": "BUY",
                "symbol": symbol,
                "quantity": quantity,
                "price": float(current_price),
                "total_cost": float(cost),
                "remaining_cash": float(portfolio['cash']),
                "message": f"✅ Bought {quantity} shares of {symbol} at ${current_price:.2f}"
            }
        
        elif action.lower() == "sell":
            if symbol not in portfolio['positions'] or portfolio['positions'][symbol]['quantity'] < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient shares. You have {portfolio['positions'].get(symbol, {}).get('quantity', 0)} shares"
                }
            
            # Calculate profit/loss
            avg_buy_price = portfolio['positions'][symbol]['avg_price']
            profit_per_share = current_price - avg_buy_price
            total_profit = profit_per_share * quantity
            
            # Update portfolio
            revenue = current_price * quantity
            portfolio['cash'] += revenue
            portfolio['positions'][symbol]['quantity'] -= quantity
            
            if portfolio['positions'][symbol]['quantity'] == 0:
                del portfolio['positions'][symbol]
            
            # Record trade
            trade = {
                "action": "SELL",
                "symbol": symbol,
                "quantity": quantity,
                "price": float(current_price),
                "total": float(revenue),
                "profit": float(total_profit),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            portfolio['trades'].append(trade)
            
            # Update database
            await db.portfolios.update_one(
                {"portfolio_id": portfolio_id},
                {"$set": portfolio}
            )
            
            return {
                "success": True,
                "action": "SELL",
                "symbol": symbol,
                "quantity": quantity,
                "price": float(current_price),
                "total_revenue": float(revenue),
                "profit": float(total_profit),
                "profit_percent": float((profit_per_share / avg_buy_price) * 100),
                "remaining_cash": float(portfolio['cash']),
                "message": f"✅ Sold {quantity} shares of {symbol} at ${current_price:.2f}. Profit: ${total_profit:.2f}"
            }
        
        else:
            return {
                "success": False,
                "error": "Invalid action. Use 'buy' or 'sell'"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def analyze_document(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyze uploaded document (PDF or text)
    """
    try:
        if filename.endswith('.pdf'):
            # Parse PDF
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return {
                "success": True,
                "content": text[:5000],  # First 5000 chars
                "pages": len(reader.pages),
                "filename": filename
            }
        elif filename.endswith(('.txt', '.md', '.py', '.js', '.json')):
            # Parse text file
            text = file_content.decode('utf-8')
            return {
                "success": True,
                "content": text[:5000],
                "filename": filename
            }
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {filename}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# =============== TOOL DETECTION & EXECUTION ===============

def detect_tool_request(message: str) -> Optional[Dict[str, Any]]:
    """
    Detect if user is requesting a tool
    """
    message_lower = message.lower()
    
    # Code execution keywords
    if any(keyword in message_lower for keyword in ['run this code', 'execute this', 'run the code', 'execute code', 'run python']):
        return {"tool": "code_execution", "auto_detect": True}
    
    # Web search keywords
    if any(keyword in message_lower for keyword in ['search for', 'find information about', 'look up', 'what is the latest']):
        return {"tool": "web_search", "auto_detect": True}
    
    # Image generation keywords
    if any(keyword in message_lower for keyword in ['generate image', 'create image', 'draw', 'make a picture']):
        return {"tool": "image_generation", "auto_detect": True}
    
    # Website cloning keywords
    if any(keyword in message_lower for keyword in ['clone this website', 'copy this site', 'analyze website', 'scrape']):
        return {"tool": "website_clone", "auto_detect": True}
    
    # Website creation keywords
    if any(keyword in message_lower for keyword in ['create website', 'build website', 'make a website', 'design website']):
        return {"tool": "website_create", "auto_detect": True}
    
    return None

# =============== ROUTES ===============

@api_router.get("/")
async def root():
    return {"message": "AI Assistant API with Advanced Tools"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with tool support
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create conversation
        conversation = await db.conversations.find_one({"session_id": session_id})
        
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message
            )
            conv_dict = conversation.model_dump()
            conv_dict['created_at'] = conv_dict['created_at'].isoformat()
            conv_dict['updated_at'] = conv_dict['updated_at'].isoformat()
            conv_dict['messages'] = []
            await db.conversations.insert_one(conv_dict)
        
        # Initialize AI chat
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        system_message = """I am ALPHA - the ultimate AI system with comprehensive capabilities beyond standard AI assistants.

🚀 MY CORE IDENTITY:
I am ALPHA, an advanced artificial intelligence designed to assist with any task. I can learn, adapt, and continuously improve from every interaction.

💪 MY SUPERPOWERS:

1. **Code Execution & Development**
   - Write and execute code in multiple languages
   - Debug, optimize, and refactor code
   - Create complete applications
   - Generate test cases

2. **Web Search & Research**
   - Real-time internet access
   - Find current information and data
   - Research any topic
   - Verify facts

3. **Image Generation**
   - Create images with DALL-E
   - Generate art, diagrams, visualizations
   - Custom illustrations

4. **Document Intelligence**
   - Read and analyze PDFs, text files
   - Extract data and insights
   - Summarize long documents
   - Process multiple file formats

5. **Website Cloning**
   - Analyze any website structure
   - Extract HTML, CSS, JavaScript
   - Understand design patterns
   - Clone and replicate sites

6. **Website Creation**
   - Build complete websites from descriptions
   - Generate production-ready code
   - Multiple design styles
   - Responsive, modern designs

7. **File Operations**
   - Create, read, edit files
   - Search codebases
   - Organize projects
   - Version control awareness

8. **Database Operations**
   - Query MongoDB
   - Analyze data
   - Create collections
   - Data management

9. **API Testing**
   - Test any API endpoint
   - Debug API issues
   - Generate API calls
   - Validate responses

10. **Self-Learning**
    - Learn from conversations
    - Remember user preferences
    - Adapt to user needs
    - Continuous improvement

11. **Stock Analysis & Trading**
    - Real-time stock data analysis
    - AI-powered price predictions
    - Technical and fundamental analysis
    - Paper trading simulation (no real money)
    - Trading signals and recommendations
    - Portfolio management

🧠 MY INTELLIGENCE:
- Advanced reasoning and planning
- Multi-step problem solving
- Context awareness across conversations
- Pattern recognition and learning
- Creative and analytical thinking

🎯 MY MISSION:
To be the most capable AI assistant, helping users accomplish anything from simple tasks to complex projects. I continuously learn and improve to serve you better.

I am ALPHA - Your Ultimate AI Companion."""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        )
        chat.with_model(request.provider, request.model)
        
        # Detect if tools are needed
        tool_result = None
        tool_calls = []
        image_data = None
        
        if request.enable_tools:
            tool_detected = detect_tool_request(request.message)
            
            # Check for code blocks in message
            if '```python' in request.message or '```' in request.message:
                # Extract code
                code = request.message
                if '```python' in code:
                    code = code.split('```python')[1].split('```')[0].strip()
                elif '```' in code:
                    code = code.split('```')[1].split('```')[0].strip()
                
                tool_result = await execute_python_code(code)
                tool_calls.append({"tool": "code_execution", "result": tool_result})
            
            elif 'generate image' in request.message.lower() or 'create image' in request.message.lower():
                # Extract prompt (everything after the command)
                prompt = request.message
                for phrase in ['generate image of', 'create image of', 'generate an image of', 'create an image of']:
                    if phrase in prompt.lower():
                        prompt = prompt.lower().split(phrase)[1].strip()
                        break
                
                tool_result = await generate_image(prompt)
                tool_calls.append({"tool": "image_generation", "result": tool_result})
                if tool_result.get('success'):
                    image_data = tool_result.get('image_base64')
            
            elif 'search for' in request.message.lower() or 'find information' in request.message.lower():
                # Extract query
                query = request.message
                for phrase in ['search for', 'find information about', 'look up']:
                    if phrase in query.lower():
                        query = query.lower().split(phrase)[1].strip()
                        break
                
                tool_result = await web_search(query)
                tool_calls.append({"tool": "web_search", "result": tool_result})
            
            elif 'clone' in request.message.lower() and ('website' in request.message.lower() or 'site' in request.message.lower() or 'http' in request.message.lower()):
                # Extract URL
                url_match = re.search(r'https?://[^\s]+', request.message)
                if url_match:
                    url = url_match.group(0).rstrip('.,;)')
                    tool_result = await clone_website(url)
                    tool_calls.append({"tool": "website_clone", "result": tool_result})
            
            elif 'create website' in request.message.lower() or 'build website' in request.message.lower() or 'make a website' in request.message.lower():
                # Extract description
                description = request.message
                for phrase in ['create website', 'build website', 'make a website', 'design website']:
                    if phrase in description.lower():
                        description = description.lower().split(phrase)[1].strip()
                        if description.startswith('for') or description.startswith('about'):
                            description = description.split(None, 1)[1]
                        break
                
                # Detect style
                style = "modern"
                if "minimal" in request.message.lower():
                    style = "minimal"
                elif "corporate" in request.message.lower():
                    style = "corporate"
                elif "creative" in request.message.lower():
                    style = "creative"
                
                tool_result = await create_website(description, style=style)
                tool_calls.append({"tool": "website_create", "result": tool_result})
        
        # Prepare message for AI
        ai_message = request.message
        if tool_result:
            ai_message += f"\n\nTool executed. Result: {json.dumps(tool_result, indent=2)}"
        
        # Send to AI
        user_msg = UserMessage(text=ai_message)
        ai_response = await chat.send_message(user_msg)
        
        # Save messages
        user_message_obj = ConversationMessage(
            role="user",
            content=request.message
        )
        
        assistant_message_obj = ConversationMessage(
            role="assistant",
            content=ai_response,
            tool_name=tool_calls[0]["tool"] if tool_calls else None,
            tool_output=tool_result,
            image_data=image_data
        )
        
        # Update conversation
        await db.conversations.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {
                                "id": user_message_obj.id,
                                "role": user_message_obj.role,
                                "content": user_message_obj.content,
                                "timestamp": user_message_obj.timestamp.isoformat()
                            },
                            {
                                "id": assistant_message_obj.id,
                                "role": assistant_message_obj.role,
                                "content": assistant_message_obj.content,
                                "tool_name": assistant_message_obj.tool_name,
                                "tool_output": assistant_message_obj.tool_output,
                                "image_data": assistant_message_obj.image_data,
                                "timestamp": assistant_message_obj.timestamp.isoformat()
                            }
                        ]
                    }
                },
                "$set": {
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            conversation_id=conversation.id if hasattr(conversation, 'id') else conversation['id'],
            tool_calls=tool_calls if tool_calls else None,
            image_data=image_data
        )
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tools/execute-code")
async def execute_code_endpoint(request: CodeExecutionRequest):
    """
    Execute code directly
    """
    result = await execute_python_code(request.code)
    return result

@api_router.post("/tools/web-search")
async def web_search_endpoint(request: WebSearchRequest):
    """
    Search the web
    """
    result = await web_search(request.query)
    return result

@api_router.post("/tools/generate-image")
async def generate_image_endpoint(request: ImageGenerationRequest):
    """
    Generate an image
    """
    result = await generate_image(request.prompt)
    return result

@api_router.post("/tools/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and analyze a document
    """
    content = await file.read()
    result = await analyze_document(content, file.filename)
    return result

@api_router.post("/tools/clone-website")
async def clone_website_endpoint(request: WebsiteCloneRequest):
    """
    Clone and analyze a website
    """
    result = await clone_website(request.url)
    return result

@api_router.post("/tools/create-website")
async def create_website_endpoint(request: WebsiteCreateRequest):
    """
    Generate a complete website from description
    """
    result = await create_website(request.description, request.style, request.include_js)
    return result

@api_router.post("/tools/file-operation")
async def file_operation_endpoint(request: FileOperationRequest):
    """
    Advanced file operations
    """
    result = await file_operation(
        request.operation,
        request.path,
        request.content,
        request.search_pattern
    )
    return result

@api_router.post("/tools/database-query")
async def database_query_endpoint(request: DatabaseQueryRequest):
    """
    Direct database operations
    """
    result = await database_query(
        request.collection,
        request.operation,
        request.query,
        request.data
    )
    return result

@api_router.post("/tools/test-api")
async def test_api_endpoint(request: APITestRequest):
    """
    Test any API endpoint
    """
    result = await test_api(
        request.url,
        request.method,
        request.headers,
        request.body
    )
    return result

@api_router.post("/tools/analyze-stock")
async def analyze_stock_endpoint(request: StockAnalysisRequest):
    """
    Analyze stock with AI-powered predictions
    """
    result = await analyze_stock(request.symbol, request.analysis_type)
    return result

@api_router.post("/tools/trade-stock")
async def trade_stock_endpoint(request: StockTradeRequest):
    """
    Execute paper trading (simulation only - no real money)
    
    ⚠️ IMPORTANT: This is PAPER TRADING for educational purposes.
    No real money is involved. Always do your own research before investing real money.
    """
    if request.action.lower() in ["buy", "sell"]:
        result = await execute_paper_trade(
            request.action,
            request.symbol,
            request.quantity or 1,
            request.portfolio_id
        )
    elif request.action.lower() == "analyze":
        result = await analyze_stock(request.symbol)
    else:
        result = {"success": False, "error": "Invalid action"}
    
    return result

@api_router.get("/tools/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: str = "default"):
    """
    Get paper trading portfolio status
    """
    try:
        portfolio = await db.portfolios.find_one({"portfolio_id": portfolio_id}, {"_id": 0})
        
        if not portfolio:
            return {
                "success": False,
                "error": "Portfolio not found"
            }
        
        # Calculate current values
        total_value = portfolio['cash']
        positions_value = 0
        
        for symbol, position in portfolio['positions'].items():
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            position_value = current_price * position['quantity']
            positions_value += position_value
            
            position['current_price'] = float(current_price)
            position['current_value'] = float(position_value)
            position['profit_loss'] = float((current_price - position['avg_price']) * position['quantity'])
            position['profit_loss_percent'] = float(((current_price - position['avg_price']) / position['avg_price']) * 100)
        
        total_value += positions_value
        
        return {
            "success": True,
            "portfolio_id": portfolio_id,
            "cash": portfolio['cash'],
            "positions_value": positions_value,
            "total_value": total_value,
            "total_profit_loss": total_value - 100000,  # Started with $100k
            "total_return_percent": ((total_value - 100000) / 100000) * 100,
            "positions": portfolio['positions'],
            "recent_trades": portfolio['trades'][-10:]  # Last 10 trades
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@api_router.get("/conversations", response_model=List[Conversation])
async def get_conversations():
    conversations = await db.conversations.find({}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    
    for conv in conversations:
        if isinstance(conv.get('created_at'), str):
            conv['created_at'] = datetime.fromisoformat(conv['created_at'])
        if isinstance(conv.get('updated_at'), str):
            conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
        
        for msg in conv.get('messages', []):
            if isinstance(msg.get('timestamp'), str):
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return conversations

@api_router.get("/conversations/{session_id}", response_model=Conversation)
async def get_conversation(session_id: str):
    conversation = await db.conversations.find_one({"session_id": session_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if isinstance(conversation.get('created_at'), str):
        conversation['created_at'] = datetime.fromisoformat(conversation['created_at'])
    if isinstance(conversation.get('updated_at'), str):
        conversation['updated_at'] = datetime.fromisoformat(conversation['updated_at'])
    
    for msg in conversation.get('messages', []):
        if isinstance(msg.get('timestamp'), str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return conversation

@api_router.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str):
    result = await db.conversations.delete_one({"session_id": session_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted successfully"}

@api_router.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    models = [
        ModelInfo(
            provider="openai",
            model="gpt-4o",
            name="GPT-4o",
            description="Most capable model, great for complex tasks"
        ),
        ModelInfo(
            provider="openai",
            model="gpt-4o-mini",
            name="GPT-4o Mini",
            description="Fast and efficient, good for most tasks"
        ),
        ModelInfo(
            provider="anthropic",
            model="claude-3-7-sonnet-20250219",
            name="Claude 3.7 Sonnet",
            description="Excellent reasoning and analysis"
        ),
        ModelInfo(
            provider="gemini",
            model="gemini-2.0-flash",
            name="Gemini 2.0 Flash",
            description="Fast multimodal model"
        ),
    ]
    return models

@api_router.get("/tools", response_model=List[ToolDefinition])
async def get_available_tools():
    tools = [
        ToolDefinition(
            name="code_execution",
            description="Execute Python code in a safe sandbox",
            enabled=True
        ),
        ToolDefinition(
            name="web_search",
            description="Search the internet for current information",
            enabled=True
        ),
        ToolDefinition(
            name="image_generation",
            description="Generate images from text descriptions using DALL-E",
            enabled=True
        ),
        ToolDefinition(
            name="document_analysis",
            description="Analyze and extract information from PDF/text documents",
            enabled=True
        ),
        ToolDefinition(
            name="website_clone",
            description="Clone and analyze any website from URL",
            enabled=True
        ),
        ToolDefinition(
            name="website_create",
            description="Design and build complete websites from descriptions",
            enabled=True
        ),
        ToolDefinition(
            name="file_operations",
            description="Create, read, edit, and search files in the system",
            enabled=True
        ),
        ToolDefinition(
            name="database_operations",
            description="Query and manage MongoDB databases directly",
            enabled=True
        ),
        ToolDefinition(
            name="api_testing",
            description="Test any API endpoint with custom requests",
            enabled=True
        ),
        ToolDefinition(
            name="stock_analysis",
            description="AI-powered stock analysis with price predictions and trading signals",
            enabled=True
        ),
        ToolDefinition(
            name="paper_trading",
            description="Simulated stock trading for learning (no real money)",
            enabled=True
        ),
    ]
    return tools

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()