from fastapi import FastAPI, APIRouter, HTTPException
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
    role: str  # 'user' or 'assistant'
    content: str
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
    model: str = "gpt-4o-mini"  # default model
    provider: str = "openai"  # default provider

class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_id: str

class ModelInfo(BaseModel):
    provider: str
    model: str
    name: str
    description: str

class ToolDefinition(BaseModel):
    name: str
    description: str
    enabled: bool = True

# =============== ROUTES ===============

@api_router.get("/")
async def root():
    return {"message": "AI Assistant API is running"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - sends message to AI and returns response
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create conversation
        conversation = await db.conversations.find_one({"session_id": session_id})
        
        if not conversation:
            # Create new conversation
            conversation = Conversation(
                session_id=session_id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message
            )
            conv_dict = conversation.model_dump()
            conv_dict['created_at'] = conv_dict['created_at'].isoformat()
            conv_dict['updated_at'] = conv_dict['updated_at'].isoformat()
            conv_dict['messages'] = []
            await db.conversations.insert_one(conv_dict)
        else:
            # Load existing messages
            conversation = Conversation(**conversation)
        
        # Initialize AI chat with conversation history
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Create system message based on conversation context
        system_message = """You are an advanced AI assistant with comprehensive capabilities. 
        You can:
        - Answer questions on any topic
        - Help with problem-solving and analysis
        - Assist with coding and technical tasks
        - Engage in creative writing and brainstorming
        - Provide detailed explanations and learning support
        
        You learn from conversations and adapt to user needs. Be helpful, accurate, and thorough."""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        )
        
        # Set the model
        chat.with_model(request.provider, request.model)
        
        # Send message and get response
        user_msg = UserMessage(text=request.message)
        ai_response = await chat.send_message(user_msg)
        
        # Save user message
        user_message_obj = ConversationMessage(
            role="user",
            content=request.message
        )
        
        # Save assistant response
        assistant_message_obj = ConversationMessage(
            role="assistant",
            content=ai_response
        )
        
        # Update conversation in database
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
            conversation_id=conversation.id
        )
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/conversations", response_model=List[Conversation])
async def get_conversations():
    """
    Get all conversations
    """
    conversations = await db.conversations.find({}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    
    # Convert ISO strings back to datetime
    for conv in conversations:
        if isinstance(conv.get('created_at'), str):
            conv['created_at'] = datetime.fromisoformat(conv['created_at'])
        if isinstance(conv.get('updated_at'), str):
            conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
        
        # Convert message timestamps
        for msg in conv.get('messages', []):
            if isinstance(msg.get('timestamp'), str):
                msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return conversations

@api_router.get("/conversations/{session_id}", response_model=Conversation)
async def get_conversation(session_id: str):
    """
    Get a specific conversation by session_id
    """
    conversation = await db.conversations.find_one({"session_id": session_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Convert ISO strings back to datetime
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
    """
    Delete a conversation
    """
    result = await db.conversations.delete_one({"session_id": session_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted successfully"}

@api_router.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """
    Get list of available AI models
    """
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
    """
    Get list of available tools (extensible)
    """
    tools = [
        ToolDefinition(
            name="web_search",
            description="Search the internet for current information",
            enabled=False  # Can be implemented later
        ),
        ToolDefinition(
            name="code_execution",
            description="Execute code in a safe environment",
            enabled=False
        ),
        ToolDefinition(
            name="image_generation",
            description="Generate images from text descriptions",
            enabled=False
        ),
        ToolDefinition(
            name="document_analysis",
            description="Analyze and extract information from documents",
            enabled=False
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()