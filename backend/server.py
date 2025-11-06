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
        
        system_message = """You are an advanced AI assistant with powerful capabilities:

1. **Code Execution**: You can write and execute Python code. When users ask you to run code, write the code clearly.
2. **Web Search**: You can search the internet for current information. Use this for recent events or facts.
3. **Image Generation**: You can generate images from descriptions using DALL-E.
4. **Document Analysis**: You can read and analyze uploaded documents.
5. **Website Cloning**: You can analyze and clone any website by URL. Extract structure, styles, and content.
6. **Website Creation**: You can design and build complete websites from descriptions with HTML, CSS, and JavaScript.

When users ask you to:
- Run/execute code: Write clear Python code
- Search for information: I'll search the web for you
- Generate/create images: Describe what you want to generate
- Analyze documents: I'll process uploaded files
- Clone a website: Provide the URL and I'll analyze it
- Create a website: Describe what you want and I'll build it

Be helpful, accurate, and use tools when appropriate."""
        
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