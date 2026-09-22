import React, { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { Bot, Send, Flame, Sparkles } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isFallback?: boolean;
}

export default function AIAdvisorPanel() {
  const auth = useContext(AuthContext);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I am FinMate 2.0, your personal financial intelligence advisor. I analyze your real transaction history, budgets, and cash flow to provide deterministic, grounded financial insights. How can I help you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [roastMode, setRoastMode] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);

    try {
      setLoading(true);
      const res = await axios.post(
        `${API_URL}/api/v1/ai/chat`,
        {
          message: userMsg,
          roast_mode: roastMode
        },
        {
          headers: { Authorization: `Bearer ${auth?.token}` }
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.reply || 'No response generated.',
          isFallback: res.data.is_fallback
        }
      ]);
    } catch (err: any) {
      console.error('AI chat failed:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'AI insights are temporarily unavailable. Your core transactions and financial analytics remain securely accessible.',
          isFallback: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Roast Mode Toggle */}
      <div className="glass-card p-6 rounded-2xl border border-white/10 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white shadow-lg">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              FinMate 2.0 AI Advisor
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                Guardrailed
              </span>
            </h2>
            <p className="text-xs text-gray-400">
              Grounded personal financial intelligence with strict anti-hallucination guardrails.
            </p>
          </div>
        </div>

        {/* Persona Toggle */}
        <button
          onClick={() => setRoastMode(!roastMode)}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border transition ${
            roastMode
              ? 'bg-gradient-to-r from-orange-500/20 to-red-500/20 border-orange-500/40 text-orange-300'
              : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
          }`}
        >
          <Flame className={`w-4 h-4 ${roastMode ? 'text-orange-400 fill-orange-400' : 'text-gray-400'}`} />
          <span>{roastMode ? 'Roast Mode: Active 🔥' : 'Enable Roast Mode'}</span>
        </button>
      </div>

      {/* Chat Messages Log */}
      <div className="glass-card p-6 rounded-2xl border border-white/10 h-[480px] flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-br-none'
                    : 'bg-white/5 border border-white/10 text-gray-200 rounded-bl-none'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="flex items-center gap-1.5 text-[11px] text-cyan-400 font-semibold mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>FinMate Intelligence</span>
                    {m.isFallback && (
                      <span className="text-[10px] text-gray-400 ml-2 font-normal">(Rule-based fallback)</span>
                    )}
                  </div>
                )}
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 text-xs text-gray-400 flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-cyan-400"></div>
                <span>Analyzing deterministic financial context...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="mt-4 pt-4 border-t border-white/10 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              roastMode
                ? "Ask for financial advice and get roasted..."
                : "Ask about your spending, budget status, runway, or upcoming goals..."
            }
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white px-5 rounded-xl transition flex items-center justify-center disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
