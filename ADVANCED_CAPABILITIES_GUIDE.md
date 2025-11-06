# 🚀 AI Assistant - Advanced Capabilities Guide

## Overview

Your AI Assistant now has **powerful advanced capabilities** that go far beyond simple conversations:

1. ✅ **Code Execution** - Write and run Python code
2. ✅ **Web Search** - Search the internet for current information
3. ✅ **Image Generation** - Create images with DALL-E
4. ✅ **Document Analysis** - Upload and analyze PDFs and documents

---

## 🔥 Feature 1: Code Execution

### What It Does
- Write Python code and execute it in a safe sandbox
- Get real-time output
- Perfect for calculations, data processing, testing algorithms

### How to Use

**Method 1: Natural Language**
```
You: "Write Python code to calculate the first 10 fibonacci numbers"
AI: [Writes and executes code, shows output]
```

**Method 2: Code Blocks**
```
You: 
```python
import math
result = math.factorial(10)
print(f"10! = {result}")
```
AI: [Executes and shows: "10! = 3628800"]
```

**Method 3: Direct API**
```bash
curl -X POST http://localhost:8001/api/tools/execute-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(sum([1,2,3,4,5]))",
    "language": "python"
  }'
```

### Examples

**Data Analysis:**
```
You: "Write code to analyze this data: [23, 45, 67, 12, 89, 34]"
AI: Calculates mean, median, standard deviation
```

**Algorithm Testing:**
```
You: "Implement bubble sort for [5, 2, 8, 1, 9]"
AI: Writes and runs sorting algorithm
```

**Math Calculations:**
```
You: "Calculate compound interest: $1000 at 5% for 10 years"
AI: Writes formula and computes result
```

### Limitations
- 5 second execution timeout
- No network access from code
- No file system access
- Python 3 only

---

## 🔍 Feature 2: Web Search

### What It Does
- Search the internet for current information
- Get real-time data, news, facts
- Perfect for questions about recent events

### How to Use

**Natural Language:**
```
You: "Search for latest developments in quantum computing 2025"
AI: [Searches web and provides summary of findings]
```

```
You: "Find information about the current weather in Tokyo"
AI: [Searches and returns current weather data]
```

**Direct API:**
```bash
curl -X POST http://localhost:8001/api/tools/web-search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence trends 2025"}'
```

### Examples

**Recent News:**
```
You: "What are the latest AI breakthroughs this month?"
AI: Searches and summarizes recent news
```

**Current Events:**
```
You: "Search for information about SpaceX latest launch"
AI: Finds and reports current information
```

**Fact Checking:**
```
You: "Look up the current population of India"
AI: Searches and provides accurate data
```

### Tips
- Be specific in your search queries
- Use recent dates for time-sensitive information
- Combine with code execution for data analysis

---

## 🎨 Feature 3: Image Generation

### What It Does
- Generate images from text descriptions using DALL-E
- Create custom visuals, art, diagrams
- Powered by OpenAI's gpt-image-1 model

### How to Use

**Natural Language:**
```
You: "Generate image of a futuristic city at sunset"
AI: [Creates and displays image]
```

```
You: "Create image of a cat wearing sunglasses on a beach"
AI: [Generates and shows image]
```

**Direct API:**
```bash
curl -X POST http://localhost:8001/api/tools/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene mountain landscape with aurora borealis",
    "model": "gpt-image-1"
  }'
```

### Examples

**Concept Visualization:**
```
You: "Generate image of a modern minimalist office space"
AI: Creates professional office image
```

**Creative Art:**
```
You: "Create image of a steampunk robot reading a book"
AI: Generates unique steampunk artwork
```

**Product Mockups:**
```
You: "Generate image of a sleek smartphone with holographic display"
AI: Creates product visualization
```

### Tips for Best Results
- Be specific with details (colors, style, mood)
- Mention artistic style (realistic, cartoon, abstract)
- Include lighting and atmosphere details
- Specify composition (close-up, wide shot, etc.)

### Response Format
- Images returned as base64 encoded PNG
- Displayed directly in chat interface
- Can be downloaded from the UI

---

## 📄 Feature 4: Document Analysis

### What It Does
- Upload PDF, text, code files
- Extract and analyze content
- Answer questions about documents
- Summarize large documents

### How to Use

**Web Interface:**
1. Click the upload button (📎)
2. Select your file (.pdf, .txt, .md, .py, .js, .json)
3. Add a message like "Summarize this document"
4. AI reads and analyzes the content

**Direct API:**
```bash
curl -X POST http://localhost:8001/api/tools/upload-document \
  -F "file=@/path/to/document.pdf"
```

### Supported File Types
- PDF documents (.pdf)
- Text files (.txt)
- Markdown files (.md)
- Python code (.py)
- JavaScript code (.js)
- JSON files (.json)

### Examples

**Document Summary:**
```
You: [Uploads contract.pdf] "Summarize the key points"
AI: Extracts and summarizes main clauses
```

**Code Review:**
```
You: [Uploads script.py] "Review this code for bugs"
AI: Analyzes code and suggests improvements
```

**Data Extraction:**
```
You: [Uploads report.pdf] "Extract all the statistics"
AI: Pulls out numbers and data points
```

### Limitations
- First 5000 characters analyzed
- PDF text extraction only (no OCR for images)
- Maximum file size: reasonable limits

---

## 🎯 Combining Features

The real power comes from combining multiple capabilities:

### Example 1: Research + Code + Visualization
```
You: "Search for recent stock market data, analyze it with Python, and generate a chart"
AI: 
1. Searches for market data
2. Writes code to process it
3. Could generate visualization diagram
```

### Example 2: Document + Analysis + Search
```
You: [Uploads legal document] "Analyze this contract and search for recent similar cases"
AI:
1. Reads document
2. Analyzes key terms
3. Searches for precedents
```

### Example 3: Code + Execution + Image
```
You: "Write code to generate mandelbrot set data, then create an artistic visualization"
AI:
1. Writes mathematical code
2. Executes to get data
3. Generates fractal image
```

---

## 📊 API Reference

### Code Execution
```
POST /api/tools/execute-code
{
  "code": "print('Hello')",
  "language": "python"
}

Response:
{
  "success": true,
  "output": "Hello\n",
  "error": null
}
```

### Web Search
```
POST /api/tools/web-search
{
  "query": "your search query"
}

Response:
{
  "success": true,
  "results": ["result1", "result2"],
  "query": "your search query"
}
```

### Image Generation
```
POST /api/tools/generate-image
{
  "prompt": "your image description",
  "model": "gpt-image-1"
}

Response:
{
  "success": true,
  "image_base64": "base64_encoded_image_data",
  "prompt": "your image description"
}
```

### Document Upload
```
POST /api/tools/upload-document
Content-Type: multipart/form-data
file: [binary file data]

Response:
{
  "success": true,
  "content": "extracted text",
  "pages": 5,
  "filename": "document.pdf"
}
```

### Chat with Tools
```
POST /api/chat
{
  "message": "your message",
  "session_id": "optional",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "enable_tools": true
}

Response:
{
  "response": "AI response",
  "session_id": "session-uuid",
  "conversation_id": "conversation-uuid",
  "tool_calls": [{"tool": "tool_name", "result": {...}}],
  "image_data": "base64_if_image_generated"
}
```

---

## 🎨 Frontend Features

### Quick Actions
Click the example cards on the home screen:
- 💻 Code Execution example
- 🔍 Web Search example
- 🎨 Image Generation example
- 📄 Document Upload

### Tool Output Display
- Code output shown in formatted terminal-style boxes
- Images displayed inline
- Search results formatted cleanly
- Document content extracted and shown

### File Upload
- Click upload button or drag & drop
- See file preview before sending
- Remove selected file with X button

---

## 💡 Pro Tips

### For Code Execution:
1. Start simple, then iterate
2. Use print() statements for debugging
3. Import standard libraries freely
4. Test mathematical formulas
5. Process small datasets

### For Web Search:
1. Be specific with queries
2. Include year for recent info
3. Use proper keywords
4. Combine multiple searches for comprehensive info

### For Image Generation:
1. Describe mood and atmosphere
2. Specify art style
3. Include color preferences
4. Mention perspective/composition
5. Be creative but clear

### For Document Analysis:
1. Upload clean, text-based PDFs
2. Ask specific questions
3. Request summaries for long docs
4. Combine with search for context

---

## 🔒 Security & Limits

### Code Execution Security:
- Runs in isolated subprocess
- 5 second timeout
- No network access
- No file system access
- No system commands

### Web Search:
- Uses DuckDuckGo (privacy-focused)
- No API key tracking
- Limited to public information

### Image Generation:
- Uses Emergent Universal Key
- Credits deducted per image
- Appropriate content guidelines apply

### Document Upload:
- Files processed in memory
- Not permanently stored
- 5000 character analysis limit

---

## 📈 Usage Examples by Category

### Data Science:
```
"Write code to calculate correlation between [data1] and [data2]"
"Search for latest pandas dataframe methods"
"Generate visualization of dataset distribution"
```

### Education:
```
"Write code to demonstrate sorting algorithms"
"Search for recent discoveries in physics"
"Create diagram explaining photosynthesis"
```

### Business:
```
"Analyze this sales report [upload PDF]"
"Search for market trends in tech sector"
"Generate infographic for quarterly results"
```

### Creative:
```
"Write code to generate random story prompts"
"Create image of fantasy landscape"
"Search for current design trends"
```

---

## 🐛 Troubleshooting

### Code Not Executing?
- Check for syntax errors
- Verify timeout (5 seconds max)
- Try simpler code first

### Search Not Working?
- Check internet connectivity
- Try different search terms
- Backend must be running

### Image Not Generating?
- Verify EMERGENT_LLM_KEY in .env
- Check account balance
- Wait up to 60 seconds for generation

### Document Upload Fails?
- Check file type is supported
- Verify file size is reasonable
- Try different format

---

## 🚀 What's Next?

### Potential Additions:
1. **Code in Multiple Languages** (JavaScript, Java, etc.)
2. **Enhanced Web Scraping** (specific site data)
3. **Video Generation** (text-to-video)
4. **Audio Processing** (speech-to-text, music gen)
5. **Database Queries** (SQL execution)
6. **API Integration** (custom API calls)
7. **Automated Testing** (test code execution)
8. **Chart Generation** (data visualization)

---

## 📞 Support

- **Backend API**: http://localhost:8001/api/
- **API Docs**: http://localhost:8001/docs (FastAPI auto-docs)
- **Logs**: `/var/log/supervisor/backend.*.log`
- **Code**: `/app/backend/server.py`

---

## ✨ Summary

You now have an AI Assistant that can:
✅ Have natural conversations
✅ Write and execute code
✅ Search the web
✅ Generate images
✅ Analyze documents
✅ Remember all interactions
✅ Switch between multiple AI models
✅ Combine all features together

**Start exploring these capabilities and build amazing things!** 🚀
