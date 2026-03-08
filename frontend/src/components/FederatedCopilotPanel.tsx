import React, { useMemo, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  CopilotMode,
  CopilotService,
  CopilotChatResponse,
  CopilotPageContext,
} from '../services/copilotService';

const modeOptions: Array<{ value: CopilotMode; label: string }> = [
  { value: 'quick_summary', label: 'Quick Summary' },
  { value: 'deep_analysis', label: 'Deep Analysis' },
  { value: 'governance_check', label: 'Governance Check' },
  { value: 'troubleshooting', label: 'Troubleshooting' },
];

/**
 * Hook for typing animation effect
 */
const useTypingEffect = (text: string, speed: number = 20): string => {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!text) {
      setDisplayedText('');
      setIsComplete(false);
      return;
    }

    if (text.length <= 30) {
      // Short answers appear instantly
      setDisplayedText(text);
      setIsComplete(true);
      return;
    }

    let currentIndex = 0;
    setDisplayedText('');
    setIsComplete(false);

    const interval = setInterval(() => {
      if (currentIndex < text.length) {
        const nextChar = text.charAt(currentIndex);
        if (nextChar) {
          setDisplayedText((prev) => prev + nextChar);
        }
        currentIndex++;
      } else {
        setIsComplete(true);
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return displayedText;
};

const FederatedCopilotPanel: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<CopilotMode>('quick_summary');
  const [message, setMessage] = useState('');
  const [lastMessage, setLastMessage] = useState('');
  const [lastResponse, setLastResponse] = useState<CopilotChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enableTyping, setEnableTyping] = useState(true);
  const [hasAutoGreeted, setHasAutoGreeted] = useState(false);

  const animatedAnswer = useTypingEffect(
    enableTyping && lastResponse ? lastResponse.answer : '',
    15
  );

  const displayAnswer = enableTyping && lastResponse
    ? animatedAnswer
    : lastResponse?.answer || '';

  const pageContext = useMemo<CopilotPageContext>(() => {
    const path = location.pathname;
    const context: CopilotPageContext = {
      page: path,
    };

    const predictionMatch = path.match(/^\/prediction-detail\/(\d+)$/);
    if (predictionMatch) {
      context.prediction_id = Number(predictionMatch[1]);
      context.page = 'prediction_detail';
    }

    const roundMatch = path.match(/^\/aggregation\/round\/(\d+)$/);
    if (roundMatch) {
      context.round_number = Number(roundMatch[1]);
      context.page = 'round_detail';
    }

    const datasetQuery = new URLSearchParams(location.search).get('datasetId');
    if (datasetQuery) {
      context.dataset_id = Number(datasetQuery);
      context.page = 'dataset_detail';
    }

    if (path.startsWith('/governance')) {
      context.page = 'governance';
    }

    return context;
  }, [location.pathname, location.search]);

  // Auto-greet when copilot opens for the first time
  useEffect(() => {
    if (open && !hasAutoGreeted && !lastResponse) {
      setHasAutoGreeted(true);
      setMessage('help');
      setLoading(true);
      setError(null);
      setEnableTyping(true);
      setLastMessage('help');
      
      CopilotService.chat({
        message: 'help',
        mode,
        page_context: pageContext,
      }).then((response) => {
        setLastResponse(response);
        setLoading(false);
      }).catch((err: any) => {
        setError(err?.response?.data?.detail || 'Copilot request failed');
        setLastResponse(null);
        setLoading(false);
      });
    }
  }, [open, hasAutoGreeted, lastResponse, mode, pageContext]);

  const submit = async () => {
    if (!message.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    setEnableTyping(true);
    setLastMessage(message);

    try {
      const response = await CopilotService.chat({
        message: message.trim(),
        mode,
        page_context: pageContext,
      });
      setLastResponse(response);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Copilot request failed');
      setLastResponse(null);
    } finally {
      setLoading(false);
    }
  };

  const regenerate = async () => {
    if (!lastMessage.trim()) {
      return;
    }

    setMessage(lastMessage);
    setLoading(true);
    setError(null);
    setEnableTyping(true);

    try {
      const response = await CopilotService.chat({
        message: lastMessage,
        mode,
        page_context: pageContext,
      });
      setLastResponse(response);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Copilot regeneration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = (isPositive: boolean) => {
    // TODO: Send feedback to backend for analytics
    console.log(`Feedback: ${isPositive ? '👍' : '👎'} on response`);
    // Could send to /api/copilot/feedback endpoint
  };

  const skipTyping = () => {
    setEnableTyping(false);
  };

  const askQuestion = (question: string) => {
    setMessage(question);
    setLoading(true);
    setError(null);
    setEnableTyping(true);
    setLastMessage(question);

    CopilotService.chat({
      message: question,
      mode,
      page_context: pageContext,
    }).then((response) => {
      setLastResponse(response);
      setLoading(false);
    }).catch((err: any) => {
      setError(err?.response?.data?.detail || 'Copilot request failed');
      setLastResponse(null);
      setLoading(false);
    });
  };

  if (!user) {
    return null;
  }

  // Extract model info from guardrails
  const modelInfo = lastResponse?.guardrails?.find((g) =>
    g.toLowerCase().includes('generated by:')
  );
  const responseTime = lastResponse?.guardrails?.find((g) =>
    g.toLowerCase().includes('response time:')
  );
  const isAiGenerated = lastResponse?.guardrails?.some((g) =>
    g.toLowerCase().includes('ai-generated')
  );

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-40 rounded-full bg-blue-600 text-white px-4 py-3 shadow-lg hover:bg-blue-700 transition-all"
          title="Open AI Copilot"
        >
          🤖 AI Copilot
        </button>
      )}

      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[480px] max-h-[85vh] bg-white border border-slate-200 rounded-lg shadow-2xl flex flex-col">
          <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
            <div>
              <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                🤖 Federated AI Copilot
                {isAiGenerated && (
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                    LLM-Powered
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-500">
                Role: {user.role === 'ADMIN' ? 'CENTRAL' : 'HOSPITAL'}
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-500 hover:text-slate-700 text-lg"
              title="Close"
            >
              ✕
            </button>
          </div>

          <div className="p-3 border-b border-slate-200 grid grid-cols-1 gap-2">
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as CopilotMode)}
              className="border border-slate-300 rounded px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {modeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              className="border border-slate-300 rounded px-2 py-2 text-sm h-20 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ask about rounds, predictions, DP, MPC, aggregation, governance..."
            />

            <button
              onClick={submit}
              disabled={loading || !message.trim()}
              className="bg-blue-600 text-white rounded px-3 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '🔄 Analyzing...' : '💬 Ask Copilot'}
            </button>

            <div className="text-[11px] text-slate-500">
              📍 Context: {pageContext.page}
              {pageContext.prediction_id ? ` | prediction #${pageContext.prediction_id}` : ''}
              {pageContext.round_number ? ` | round #${pageContext.round_number}` : ''}
              {pageContext.dataset_id ? ` | dataset #${pageContext.dataset_id}` : ''}
            </div>
          </div>

          <div className="p-4 overflow-auto space-y-3 flex-1">
            {error && (
              <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
                ❌ {error}
              </div>
            )}

            {lastResponse && (
              <>
                <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                  <div className="text-sm text-slate-900 whitespace-pre-wrap leading-relaxed">
                    {displayAnswer}
                    {enableTyping && displayAnswer !== lastResponse.answer && (
                      <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse" />
                    )}
                  </div>

                  {enableTyping && displayAnswer !== lastResponse.answer && (
                    <button
                      onClick={skipTyping}
                      className="text-xs text-blue-600 hover:text-blue-700 mt-2"
                    >
                      ⏩ Skip animation
                    </button>
                  )}

                  {/* Model Info Badge */}
                  {(modelInfo || responseTime) && (
                    <div className="mt-3 pt-3 border-t border-slate-200 flex flex-wrap gap-2 text-[10px]">
                      {modelInfo && (
                        <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                          {modelInfo}
                        </span>
                      )}
                      {responseTime && (
                        <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                          ⚡ {responseTime}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={regenerate}
                      disabled={loading}
                      className="text-xs bg-slate-200 hover:bg-slate-300 text-slate-700 px-3 py-1.5 rounded transition-colors disabled:opacity-50"
                      title="Regenerate response"
                    >
                      🔄 Regenerate
                    </button>
                    <button
                      onClick={() => handleFeedback(true)}
                      className="text-xs bg-green-100 hover:bg-green-200 text-green-700 px-3 py-1.5 rounded transition-colors"
                      title="Helpful response"
                    >
                      👍 Helpful
                    </button>
                    <button
                      onClick={() => handleFeedback(false)}
                      className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1.5 rounded transition-colors"
                      title="Not helpful"
                    >
                      👎 Not helpful
                    </button>
                  </div>
                </div>

                {lastResponse.recommendations?.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <div className="text-xs font-semibold text-blue-900 mb-2">💡 Recommendations</div>
                    <ul className="text-xs text-blue-800 space-y-1.5">
                      {lastResponse.recommendations.map((rec, index) => {
                        const isClickable = rec.startsWith('💡 Ask:');
                        const cleanRec = isClickable ? rec.replace('💡 Ask: ', '').replace(/['"]/g, '') : rec;
                        
                        if (isClickable) {
                          return (
                            <li key={`${rec}-${index}`}>
                              <button
                                onClick={() => askQuestion(cleanRec)}
                                className="text-left hover:bg-blue-100 px-2 py-1 rounded transition-colors w-full text-blue-700 hover:text-blue-900 font-medium"
                              >
                                💬 {cleanRec}
                              </button>
                            </li>
                          );
                        }
                        
                        return (
                          <li key={`${rec}-${index}`} className="list-disc ml-5">{rec}</li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {lastResponse.links?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-700 mb-2">🔗 Quick Navigation</div>
                    <div className="flex flex-wrap gap-2">
                      {lastResponse.links.map((link) => (
                        <button
                          key={`${link.label}-${link.url}`}
                          onClick={() => navigate(link.url)}
                          className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded border border-slate-300 transition-colors"
                        >
                          {link.label} →
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {lastResponse.guardrails?.length > 0 && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-slate-600 hover:text-slate-800 font-medium">
                      🔒 Safety & Governance ({lastResponse.guardrails.length})
                    </summary>
                    <ul className="text-[11px] text-slate-500 list-disc pl-5 space-y-1 mt-2">
                      {lastResponse.guardrails
                        .filter((g) => !g.toLowerCase().includes('generated by:') && !g.toLowerCase().includes('response time:'))
                        .map((g, index) => (
                          <li key={`${g}-${index}`}>{g}</li>
                        ))}
                    </ul>
                  </details>
                )}
              </>
            )}

            {!lastResponse && !error && !loading && (
              <div className="text-center py-8 text-slate-400">
                <div className="text-4xl mb-2">🤖</div>
                <div className="text-sm">Ask me anything about your federated learning platform</div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default FederatedCopilotPanel;
