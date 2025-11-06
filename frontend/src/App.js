import { useState, useEffect, useRef } from 'react';
import '@/App.css';
import axios from 'axios';
import { Send, Trash2, MessageSquare, Settings, Sparkles, Bot } from 'lucide-react';

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
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
    loadModels();
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

  const loadConversation = async (convSessionId) => {
    try {
      const response = await axios.get(`${API}/conversations/${convSessionId}`);
      setMessages(response.data.messages);
      setSessionId(convSessionId);
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: input,
        session_id: sessionId,
        model: selectedModel,
        provider: selectedProvider,
      });

      const assistantMessage = {
        id: Date.now().toString() + '1',
        role: 'assistant',
        content: response.data.response,
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

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Sidebar */}
      <div className="w-80 bg-gray-800/50 backdrop-blur-lg border-r border-gray-700/50 flex flex-col">
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
              <Sparkles className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              AI Assistant
            </h1>
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
            className="w-full px-4 py-2 bg-gray-700/50 hover:bg-gray-700 rounded-lg transition-all flex items-center justify-center gap-2"
            data-testid="settings-btn"
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
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
                <h2 className="font-semibold text-lg">AI Chat</h2>
                <p className="text-sm text-gray-400">
                  Powered by {selectedProvider} - {selectedModel}
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

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6" data-testid="messages-container">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-2xl flex items-center justify-center border border-blue-500/30">
                  <Sparkles className="w-10 h-10 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                  Welcome to AI Assistant
                </h2>
                <p className="text-gray-400 mb-6">
                  I'm an advanced AI with comprehensive capabilities. I can help you with:
                </p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                    <p className="font-medium mb-1">💡 Problem Solving</p>
                    <p className="text-gray-400 text-xs">Complex analysis & reasoning</p>
                  </div>
                  <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                    <p className="font-medium mb-1">💻 Coding</p>
                    <p className="text-gray-400 text-xs">Programming assistance</p>
                  </div>
                  <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                    <p className="font-medium mb-1">✍️ Writing</p>
                    <p className="text-gray-400 text-xs">Creative & technical content</p>
                  </div>
                  <div className="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                    <p className="font-medium mb-1">📚 Learning</p>
                    <p className="text-gray-400 text-xs">Explanations & tutorials</p>
                  </div>
                </div>
                <p className="text-gray-500 text-sm mt-6">Start a conversation below!</p>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
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
              <div
                className={`max-w-2xl px-5 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                    : 'bg-gray-800/70 border border-gray-700/50'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-medium">You</span>
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="max-w-2xl px-5 py-3 rounded-2xl bg-gray-800/70 border border-gray-700/50">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-gray-700/50 bg-gray-800/30 backdrop-blur-lg">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything..."
              className="flex-1 px-5 py-3 bg-gray-700/50 border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all"
              disabled={loading}
              data-testid="message-input"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg"
              data-testid="send-message-btn"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3 text-center">
            AI Assistant can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;