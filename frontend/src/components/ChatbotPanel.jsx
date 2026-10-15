import { useState, useRef, useEffect, useMemo } from 'react';
import { Send, Bot, User, Loader, Brain, Shield } from 'lucide-react';
import { chatAPI, getApiError } from '../services/api';

// Generate a stable conversation ID per session
function useConversationId() {
  return useMemo(() => `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`, []);
}

function ConfidenceBadge({ confidence, intent }) {
  if (confidence == null) return null;

  let color = 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
  let label = 'High';
  if (confidence < 0.4) {
    color = 'text-red-400 bg-red-500/15 border-red-500/30';
    label = 'Low';
  } else if (confidence < 0.7) {
    color = 'text-amber-400 bg-amber-500/15 border-amber-500/30';
    label = 'Medium';
  }

  return (
    <div className="flex items-center gap-2 mt-2">
      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${color}`}>
        <Shield className="w-2.5 h-2.5 inline mr-0.5 -mt-0.5" />
        {label} confidence ({(confidence * 100).toFixed(0)}%)
      </span>
      {intent && (
        <span className="text-[10px] px-2 py-0.5 rounded-full border border-slate-600 text-slate-400 bg-slate-800">
          <Brain className="w-2.5 h-2.5 inline mr-0.5 -mt-0.5" />
          {intent.replace('_', ' ')}
        </span>
      )}
    </div>
  );
}

export default function ChatbotPanel() {
  const conversationId = useConversationId();

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your telecom network advisor. Ask me about network issues, KPIs, causes, or solutions. I remember our conversation context for follow-up questions.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(input, {
        conversationId,
        includeLiveInsights: true,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        confidence: response.confidence,
        intent: response.intent,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${getApiError(error)}. Check backend / API keys.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestedQuestions = [
    'Show me the top 10 rows of my dataset',
    'How many issues are in my data?',
    'What causes high latency?',
    'How to fix call drops?',
    'What is the health of my worst cells?',
  ];

  return (
    <div className="flex flex-col h-full bg-slate-900/85 rounded-2xl shadow-2xl border border-white/15 backdrop-blur-2xl overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-4 md:p-5 rounded-t-2xl border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg md:text-xl font-bold text-white tracking-tight">Agent 1: Telecom Advisor</h2>
            <p className="text-blue-100/95 text-sm">RAG + Intent Classification + Conversation Memory</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 md:p-6 space-y-4 bg-slate-950/50">
        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center flex-shrink-0 shadow-md">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-2xl p-4 shadow-md ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800/95 text-slate-50 border border-white/15'
              }`}
            >
              <p className="whitespace-pre-wrap text-[15px] leading-7 tracking-[0.01em]">
                {message.content}
              </p>
              <div className="flex items-center justify-between mt-1">
                <span className={`text-xs ${
                  message.role === 'user' ? 'text-blue-100' : 'text-slate-400'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              {message.role === 'assistant' && (
                <ConfidenceBadge confidence={message.confidence} intent={message.intent} />
              )}
            </div>

            {message.role === 'user' && (
              <div className="w-9 h-9 rounded-xl bg-gray-800 flex items-center justify-center flex-shrink-0 shadow-md">
                <User className="w-5 h-5 text-white" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center shadow-md">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-slate-800/90 border border-white/10 rounded-xl p-4 shadow-md">
              <Loader className="w-5 h-5 text-blue-600 animate-spin" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="px-6 pb-3 bg-slate-900/85 border-t border-white/10">
          <p className="text-slate-400 text-xs mb-2 font-medium">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => setInput(q)}
                className="text-xs px-3 py-1.5 bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-200 rounded-full transition border border-cyan-400/35 font-medium"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-white/10 bg-slate-900/90 rounded-b-2xl">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about network issues, a specific cell, your data, or follow up on previous questions..."
            className="flex-1 px-4 py-3 bg-slate-950/90 text-slate-100 text-[15px] rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-500 border border-white/15 placeholder:text-slate-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 text-white rounded-xl transition flex items-center gap-2 shadow-lg hover:shadow-blue-600/30 font-medium"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}
