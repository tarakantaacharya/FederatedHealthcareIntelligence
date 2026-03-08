import React, { useState, useRef, useEffect } from 'react';
import { CopilotService, CopilotChatRequest, CopilotMode, CopilotPageContext } from '../services/copilotService';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface CopilotChatbotProps {
  pageContext: CopilotPageContext;
  defaultMode?: CopilotMode;
}

const CopilotChatbot: React.FC<CopilotChatbotProps> = ({
  pageContext,
  defaultMode = 'quick_summary'
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<CopilotMode>(defaultMode);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const request: CopilotChatRequest = {
        message: input,
        mode,
        page_context: pageContext
      };

      const response = await CopilotService.chat(request);

      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className="fixed bottom-4 right-4 bg-purple-600 hover:bg-purple-700 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg text-xl"
        title="Open Federated Copilot"
      >
        💬
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-80 h-96 bg-white rounded-lg shadow-xl flex flex-col border-2 border-purple-600">
      {/* Header */}
      <div className="bg-purple-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div>
          <h3 className="font-bold">Federated Copilot</h3>
          <p className="text-xs opacity-90">Context-aware AI Assistant</p>
        </div>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-white hover:bg-purple-700 p-1 rounded"
        >
          ×
        </button>
      </div>

      {/* Mode Selector */}
      <div className="px-4 py-2 bg-purple-50 border-b">
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as CopilotMode)}
          className="w-full px-2 py-1 text-xs border rounded bg-white"
        >
          <option value="quick_summary">Quick Summary</option>
          <option value="deep_analysis">Deep Analysis</option>
          <option value="governance_check">Governance Check</option>
          <option value="troubleshooting">Troubleshooting</option>
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 text-sm mt-8">
            <p>👋 Hello! I'm your Federated Learning Assistant</p>
            <p className="mt-2 text-xs">Ask me about your models, predictions, or privacy budget</p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`px-3 py-2 rounded-lg max-w-xs text-sm ${
                msg.role === 'user'
                  ? 'bg-purple-600 text-white rounded-br-none'
                  : 'bg-gray-100 text-gray-900 rounded-bl-none'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 px-3 py-2 rounded-lg rounded-bl-none">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-3 bg-gray-50 rounded-b-lg">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask me something..."
            className="flex-1 px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-600"
            disabled={loading}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-3 py-2 rounded text-sm font-semibold"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default CopilotChatbot;
