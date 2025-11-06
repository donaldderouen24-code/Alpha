import { useState, useEffect, useRef } from 'react';
import '@/App.css';
import axios from 'axios';
import { Send, Trash2, MessageSquare, Settings, Sparkles, Bot, Code, Search, Image as ImageIcon, FileText, Upload, X, Globe, Zap, Eye } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini');
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [availableModels, setAvailableModels] = useState([]);
  const [availableTools, setAvailableTools] = useState([]);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewHtml, setPreviewHtml] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
    loadModels();
    loadTools();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API}/conversations`);
      setConversations(response.data);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadModels = async () => {
    try {
      const response = await axios.get(`${API}/models`);
      setAvailableModels(response.data);
    } catch (error) {
      console.error('Error loading models:', error);
    }
  };

  const loadTools = async () => {
    try {
      const response = await axios.get(`${API}/tools`);
      setAvailableTools(response.data);
    } catch (error) {
      console.error('Error loading tools:', error);
    }
  };

  const loadConversation = async (convSessionId) => {
    try {
      const response = await axios.get(`${API}/conversations/${convSessionId}`);
      setMessages(response.data.messages);
      setSessionId(convSessionId);
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const uploadDocument = async () => {
    if (!selectedFile) return null;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post(`${API}/tools/upload-document`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading document:', error);
      return null;
    }
  };

  const sendMessage = async () => {
    if ((!input.trim() && !selectedFile) || loading) return;

    let messageText = input;

    // Handle file upload
    if (selectedFile) {
      const uploadResult = await uploadDocument();
      if (uploadResult && uploadResult.success) {
        messageText = `Analyze this document: ${selectedFile.name}\n\nContent:\n${uploadResult.content}`;
      } else {
        alert('Failed to upload document');
        return;
      }
    }

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input || `Uploaded: ${selectedFile.name}`,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSelectedFile(null);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: messageText,
        session_id: sessionId,
        model: selectedModel,
        provider: selectedProvider,
        enable_tools: true,
      });

      const assistantMessage = {
        id: Date.now().toString() + '1',
        role: 'assistant',
        content: response.data.response,
        tool_output: response.data.tool_calls?.[0]?.result,
        image_data: response.data.image_data,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (!sessionId) {
        setSessionId(response.data.session_id);
      }

      loadConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now().toString() + '1',
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setSessionId(null);
    setSelectedFile(null);
    setPreviewHtml(null);
  };

  const deleteConversation = async (convSessionId) => {
    try {
      await axios.delete(`${API}/conversations/${convSessionId}`);
      loadConversations();
      if (sessionId === convSessionId) {
        startNewConversation();
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const insertPrompt = (prompt) => {
    setInput(prompt);
  };

  const previewWebsite = (html) => {
    setPreviewHtml(html);
  };

  const downloadWebsite = (html, filename = 'generated-website.html') => {
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Sidebar */}
      <div className="w-80 bg-gray-800/50 backdrop-blur-lg border-r border-gray-700/50 flex flex-col">
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                AI Assistant Pro
              </h1>
              <p className="text-xs text-gray-400">Ultimate Edition</p>
            </div>
          </div>
          <button
            onClick={startNewConversation}
            className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all flex items-center justify-center gap-2 shadow-lg"
            data-testid="new-conversation-btn"
          >
            <MessageSquare className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
            Recent Conversations
          </h2>
          {conversations.map((conv) => (
            <div
              key={conv.session_id}
              className={`p-3 rounded-lg cursor-pointer transition-all group ${
                sessionId === conv.session_id
                  ? 'bg-gray-700/70 border border-blue-500/50'
                  : 'bg-gray-700/30 hover:bg-gray-700/50 border border-transparent'
              }`}
              data-testid={`conversation-${conv.session_id}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div
                  onClick={() => loadConversation(conv.session_id)}
                  className="flex-1 min-w-0"
                >
                  <p className="text-sm font-medium truncate">{conv.title}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {conv.messages?.length || 0} messages
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.session_id);
                  }}
                  className="p-1.5 hover:bg-red-500/20 rounded transition-colors opacity-0 group-hover:opacity-100"
                  data-testid={`delete-conversation-${conv.session_id}`}
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-700/50">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="w-full px-4 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-all flex items-center justify-center gap-2 mb-3"
            data-testid="settings-btn"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
          
          <div className="text-xs text-gray-400 space-y-1">
            <p className="font-semibold text-gray-300">🛠️ Tools ({availableTools.filter(t => t.enabled).length}):</p>
            {availableTools.filter(t => t.enabled).map((tool) => (
              <div key={tool.name} className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span className="capitalize text-xs">{tool.name.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-700/50 bg-gray-800/30 backdrop-blur-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-lg border border-blue-500/30">
                <Bot className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h2 className="font-semibold text-lg">AI with Website Cloning & Creation</h2>
                <p className="text-sm text-gray-400">
                  {selectedProvider} - {selectedModel}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="p-4 bg-gray-800/50 border-b border-gray-700/50">
            <h3 className="text-sm font-semibold mb-3">Model Settings</h3>
            <div className="grid grid-cols-2 gap-3">
              {availableModels.map((model) => (
                <button
                  key={`${model.provider}-${model.model}`}
                  onClick={() => {
                    setSelectedProvider(model.provider);
                    setSelectedModel(model.model);
                  }}
                  className={`p-3 rounded-lg text-left transition-all ${
                    selectedModel === model.model && selectedProvider === model.provider
                      ? 'bg-blue-500/20 border border-blue-500/50'
                      : 'bg-gray-700/30 border border-transparent hover:bg-gray-700/50'
                  }`}
                  data-testid={`model-${model.provider}-${model.model}`}
                >
                  <p className="font-medium text-sm">{model.name}</p>
                  <p className="text-xs text-gray-400 mt-1">{model.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Website Preview Modal */}
        {previewHtml && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg w-full max-w-6xl h-5/6 flex flex-col">
              <div className="p-4 border-b border-gray-700 flex justify-between items-center">
                <h3 className="font-semibold text-lg">Website Preview</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => downloadWebsite(previewHtml)}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm"
                  >
                    Download HTML
                  </button>
                  <button
                    onClick={() => setPreviewHtml(null)}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
                  >
                    Close
                  </button>
                </div>
              </div>
              <iframe
                srcDoc={previewHtml}
                className="flex-1 w-full bg-white"
                title="Website Preview"
              />
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6" data-testid="messages-container">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-4xl">
                <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-2xl flex items-center justify-center border border-blue-500/30">
                  <Zap className="w-10 h-10 text-blue-400" />
                </div>
                <h2 className="text-3xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  Ultimate AI Assistant
                </h2>
                <p className="text-gray-400 mb-6">
                  Clone any website or build new ones from scratch!
                </p>
                <div className="grid grid-cols-3 gap-3 text-sm mb-6">
                  <button
                    onClick={() => insertPrompt('Write Python code to sort a list of numbers')}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all text-left"
                  >
                    <Code className="w-5 h-5 text-blue-400 mb-2" />
                    <p className="font-medium mb-1">💻 Code Execution</p>
                    <p className="text-gray-400 text-xs">Run Python code</p>
                  </button>
                  <button
                    onClick={() => insertPrompt('Search for latest web development trends')}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all text-left"
                  >
                    <Search className="w-5 h-5 text-green-400 mb-2" />
                    <p className="font-medium mb-1">🔍 Web Search</p>
                    <p className="text-gray-400 text-xs">Find info online</p>
                  </button>
                  <button
                    onClick={() => insertPrompt('Generate image of modern office space')}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all text-left"
                  >
                    <ImageIcon className="w-5 h-5 text-purple-400 mb-2" />
                    <p className="font-medium mb-1">🎨 Image Gen</p>
                    <p className="text-gray-400 text-xs">Create images</p>
                  </button>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all text-left"
                  >
                    <FileText className="w-5 h-5 text-orange-400 mb-2" />
                    <p className="font-medium mb-1">📄 Doc Analysis</p>
                    <p className="text-gray-400 text-xs">Analyze PDFs</p>
                  </button>
                  <button
                    onClick={() => insertPrompt('Clone this website: https://example.com')}
                    className="p-4 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg border border-cyan-500/50 hover:border-cyan-400 transition-all text-left"
                  >
                    <Globe className="w-5 h-5 text-cyan-400 mb-2" />
                    <p className="font-medium mb-1">🌐 Clone Website</p>
                    <p className="text-gray-400 text-xs">Copy any site</p>
                  </button>
                  <button
                    onClick={() => insertPrompt('Create website for a coffee shop with modern design')}
                    className="p-4 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-lg border border-pink-500/50 hover:border-pink-400 transition-all text-left"
                  >
                    <Zap className="w-5 h-5 text-pink-400 mb-2" />
                    <p className="font-medium mb-1">✨ Build Website</p>
                    <p className="text-gray-400 text-xs">Generate full sites</p>
                  </button>
                </div>
                <p className="text-gray-500 text-sm">Try any capability above! 🚀</p>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id}>
              <div
                className={`flex gap-4 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
                data-testid={`message-${message.role}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5" />
                  </div>
                )}
                <div className="max-w-3xl">
                  <div
                    className={`px-5 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                        : 'bg-gray-800/70 border border-gray-700/50'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  
                  {/* Tool Output */}
                  {message.tool_output && (
                    <div className="mt-3 p-4 bg-gray-900/50 rounded-lg border border-gray-600/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-gray-400 font-semibold">🔧 Tool Output</p>
                        {message.tool_output.html && (
                          <button
                            onClick={() => previewWebsite(message.tool_output.html)}
                            className="px-3 py-1 bg-blue-500 hover:bg-blue-600 rounded text-xs flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            Preview Website
                          </button>
                        )}
                      </div>
                      {message.tool_output.success ? (
                        <div className="space-y-2">
                          {message.tool_output.output && (
                            <pre className="text-xs text-green-400 whitespace-pre-wrap">
                              {message.tool_output.output}
                            </pre>
                          )}
                          {message.tool_output.results && (
                            <div className="text-xs text-gray-300">
                              {Array.isArray(message.tool_output.results) ? (
                                message.tool_output.results.map((r, i) => (
                                  <div key={i} className="mb-2">
                                    • {r}
                                  </div>
                                ))
                              ) : (
                                <pre>{JSON.stringify(message.tool_output.results, null, 2)}</pre>
                              )}
                            </div>
                          )}
                          {message.tool_output.title && (
                            <div className="text-sm">
                              <p className="text-gray-400">Title: <span className="text-white">{message.tool_output.title}</span></p>
                              {message.tool_output.headings && message.tool_output.headings.length > 0 && (
                                <div className="mt-2">
                                  <p className="text-gray-400 text-xs">Headings:</p>
                                  {message.tool_output.headings.slice(0, 5).map((h, i) => (
                                    <p key={i} className="text-xs text-gray-300 ml-2">• {h}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          {message.tool_output.html && (
                            <div className="mt-2">
                              <p className="text-xs text-green-400">✅ Website generated successfully!</p>
                              <button
                                onClick={() => downloadWebsite(message.tool_output.html)}
                                className="mt-2 px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs"
                              >
                                Download HTML
                              </button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-xs text-red-400">{message.tool_output.error}</p>
                      )}
                    </div>
                  )}
                  
                  {/* Generated Image */}
                  {message.image_data && (
                    <div className="mt-3">
                      <img
                        src={`data:image/png;base64,${message.image_data}`}
                        alt="Generated"
                        className="rounded-lg max-w-full shadow-lg"
                      />
                    </div>
                  )}
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium">You</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="max-w-2xl px-5 py-3 rounded-2xl bg-gray-800/70 border border-gray-700/50">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-gray-700/50 bg-gray-800/30 backdrop-blur-lg">
          {selectedFile && (
            <div className="mb-3 flex items-center gap-2 p-2 bg-gray-700/50 rounded-lg">
              <FileText className="w-4 h-4 text-blue-400" />
              <span className="text-sm flex-1">{selectedFile.name}</span>
              <button
                onClick={() => setSelectedFile(null)}
                className="p-1 hover:bg-gray-600 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          <div className="flex gap-3">
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              accept=".pdf,.txt,.md,.py,.js,.json"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-3 bg-gray-700/50 hover:bg-gray-700 rounded-xl transition-all"
              title="Upload document"
              data-testid="upload-btn"
            >
              <Upload className="w-5 h-5" />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Clone websites, build apps, run code, search web, generate images..."
              className="flex-1 px-5 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
              disabled={loading}
              data-testid="message-input"
            />
            <button
              onClick={sendMessage}
              disabled={loading || (!input.trim() && !selectedFile)}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg"
              data-testid="send-message-btn"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3 text-center">
            🚀 Clone any website • Build custom sites • Run code • Generate images • Search web
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;