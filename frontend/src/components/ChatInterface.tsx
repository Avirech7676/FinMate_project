import { useState, useContext, useEffect, useRef } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { Send, Mic, MicOff, Flame, Mail, Sparkles, Target, AlertTriangle, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Web Speech API Types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  action_type?: string;
  action_payload?: any;
}

const quickActions = [
  {
    id: 'month-summary',
    label: 'Month summary',
    icon: Activity,
    prompt: 'Give me a 3-bullet summary of my last 30 days of spending.',
  },
  {
    id: 'save-5000',
    label: 'Save ₹5,000/mo',
    icon: Target,
    prompt: 'Help me save about ₹5,000 per month. Suggest 2–3 specific cuts based on my data.',
  },
  {
    id: 'subscriptions',
    label: 'Subscriptions check',
    icon: AlertTriangle,
    prompt: 'Check my spending and tell me which subscriptions or recurring charges I should review first.',
  },
  {
    id: 'prediction-link',
    label: 'Next 3 months',
    icon: Sparkles,
    prompt: 'Based on my recent activity, explain how my spending might look over the next 3 months, and which 1–2 categories I should reduce.',
  },
];

function renderMarkdown(text: string, keyPrefix: string) {
  // Very small markdown subset: **bold** support
  const segments = text.split(/(\*\*[^*]+\*\*)/g);
  return segments.map((seg, idx) => {
    const match = seg.match(/^\*\*(.+)\*\*$/);
    if (match) {
      return (
        <strong key={`${keyPrefix}-b-${idx}`} className="font-semibold">
          {match[1]}
        </strong>
      );
    }
    return (
      <span key={`${keyPrefix}-t-${idx}`}>
        {seg}
      </span>
    );
  });
}

export default function ChatInterface() {
  const auth = useContext(AuthContext);
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'ai', text: "Hello! I'm FinMate. How can I help you optimize your finances today?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Features State
  const [roastMode, setRoastMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Setup Web Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput((prev) => prev + (prev ? ' ' : '') + transcript);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.onerror = (event: any) => {
        if (event.error !== 'no-speech') {
          console.error("Speech recognition error", event.error);
        }
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = { id: `user-${Date.now()}-${Math.random()}`, sender: 'user', text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, 
      {
        message: userMessage.text,
        roast_mode: roastMode
      },
      {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });

      const aiMessage: Message = {
        id: `ai-${Date.now()}-${Math.random()}`,
        sender: 'ai',
        text: res.data.response,
        action_type: res.data.action_type,
        action_payload: res.data.action_payload
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { 
        id: `err-${Date.now()}`, 
        sender: 'ai', 
        text: "I'm having trouble connecting to my servers. Check back in a moment." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = input;
    setInput('');
    await sendMessage(text);
  };

  const handleQuickAction = async (prompt: string) => {
    setInput('');
    await sendMessage(prompt);
  };

  return (
    <div className="flex h-[520px] flex-col rounded-2xl border border-white/10 bg-[#020617]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${loading ? 'bg-yellow-400 animate-pulse' : 'bg-emerald-400'}`} />
          <h3 className="text-sm font-semibold tracking-wide text-gray-100">FinMate Coach</h3>
        </div>
        <button 
          onClick={() => setRoastMode(!roastMode)}
          className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-medium transition-colors ${
            roastMode
              ? 'border-red-400 bg-red-500/10 text-red-200'
              : 'border-slate-600 bg-slate-800 text-slate-300 hover:border-slate-400'
          }`}
        >
          <Flame className="h-3 w-3" />
          {roastMode ? 'Roast mode' : 'Calm mode'}
        </button>
      </div>

      {/* Quick actions */}
      <div className="flex flex-wrap gap-2 border-b border-white/5 px-4 py-3">
        {quickActions.map(({ id, label, icon: Icon, prompt }) => (
          <button
            key={id}
            type="button"
            onClick={() => handleQuickAction(prompt)}
            className="flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-900/60 px-3 py-1 text-[11px] text-slate-200 hover:border-slate-400 hover:bg-slate-800 transition-colors"
          >
            <Icon className="h-3 w-3" />
            {label}
          </button>
        ))}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex flex-col max-w-[85%] ${msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
            >
              <div 
                className={`p-3 rounded-2xl text-sm ${
                  msg.sender === 'user' 
                    ? 'rounded-br-sm bg-sky-600 text-white'
                    : roastMode 
                      ? 'rounded-bl-sm border border-red-400/40 bg-red-900/40 text-red-50'
                      : 'rounded-bl-sm border border-slate-600 bg-slate-900 text-slate-50'
                }`}
              >
                {/* Parse basic markdown + line breaks safely */}
                {msg.text.split('\n').map((line, i) => (
                  <p key={`${msg.id}-line-${i}`} className="mb-1 last:mb-0">
                    {renderMarkdown(line, `${msg.id}-line-${i}`)}
                  </p>
                ))}
              </div>

              {/* Action UI Component if LLM triggered an Action */}
              {msg.action_type === 'email_template' && msg.action_payload && (
                <div className="mt-2 w-full max-w-sm bg-[#0d1220] border border-[--color-border-bright] rounded-xl p-4 glow-green">
                  <div className="flex items-center gap-2 mb-3 text-[--color-accent-green]">
                    <Mail className="w-4 h-4" />
                    <span className="text-xs font-semibold uppercase tracking-wider">Generated Email action</span>
                  </div>
                  <div className="text-sm border-b border-white/10 pb-2 mb-2">
                    <span className="text-[--color-text-muted]">Subject:</span> {msg.action_payload.subject}
                  </div>
                  <div className="text-sm text-[--color-text-secondary] whitespace-pre-wrap">
                    {msg.action_payload.body}
                  </div>
                  <button className="mt-4 w-full bg-[--color-accent-green]/20 text-[--color-accent-green] hover:bg-[--color-accent-green]/30 py-2 rounded-lg text-sm font-medium transition-colors">
                    Draft in Email Client
                  </button>
                </div>
              )}

              {msg.action_type === 'create_budget_goal' && msg.action_payload && (
                <div className="mt-2 w-full max-w-sm bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-xs text-gray-400">Goal created</p>
                  <p className="text-sm font-semibold mt-1 capitalize">{msg.action_payload.goal_type}</p>
                  <p className="text-sm text-gray-300 mt-1">
                    Target: {auth?.user?.currency_symbol || '$'}
                    {Number(msg.action_payload.target_amount || 0).toFixed(0)} by {msg.action_payload.deadline}
                  </p>
                </div>
              )}

              {msg.action_type === 'show_transactions' && msg.action_payload && (
                <div className="mt-2 w-full max-w-lg bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-xs text-gray-400">
                    Matching: <span className="text-gray-200">{msg.action_payload.merchant_query}</span>
                  </p>
                  <div className="mt-3 space-y-2">
                    {(msg.action_payload.transactions || []).length === 0 ? (
                      <p className="text-sm text-gray-400">No matching transactions found.</p>
                    ) : (
                      (msg.action_payload.transactions || []).map((t: any) => (
                        <div key={t.transaction_id} className="flex items-start justify-between gap-3 bg-black/20 border border-white/5 rounded-lg p-2">
                          <div className="min-w-0">
                            <p className="text-sm font-medium truncate">{t.description}</p>
                            <p className="text-xs text-gray-400">{t.date} · {String(t.category || '').toLowerCase()}</p>
                          </div>
                          <p className="text-sm font-semibold shrink-0">
                            {auth?.user?.currency_symbol || '$'}
                            {Number(t.amount || 0).toFixed(2)}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {msg.action_type === 'recategorize_transactions' && msg.action_payload && (
                <div className="mt-2 w-full max-w-sm bg-white/5 border border-white/10 rounded-xl p-4">
                  <p className="text-xs text-gray-400">Re-categorization</p>
                  <p className="text-sm text-gray-300 mt-1">
                    Updated <span className="font-semibold text-white">{msg.action_payload.updated}</span> transactions to{' '}
                    <span className="font-semibold text-white">{msg.action_payload.category}</span>.
                  </p>
                </div>
              )}
            </motion.div>
          ))}
          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mr-auto flex items-center gap-2 rounded-full bg-slate-900 px-3 py-1 text-xs text-slate-400">
              <span className="flex gap-1">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" style={{ animationDelay: '0ms' }} />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" style={{ animationDelay: '150ms' }} />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" style={{ animationDelay: '300ms' }} />
              </span>
              Thinking…
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <div className="border-t border-white/10 bg-[#020617] p-3">
        <form onSubmit={handleSend} className="relative flex items-center">
          <button 
            type="button"
            onClick={toggleListen}
            className={`absolute left-3 p-1.5 rounded-full transition-colors ${
              isListening ? 'animate-pulse bg-rose-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            {isListening ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </button>
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isListening ? "Listening..." : "Ask FinMate anything..."}
            className="w-full rounded-xl border border-slate-700 bg-slate-950 px-12 py-3 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-sky-500"
          />
          
          <button 
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 rounded-lg bg-sky-600 p-2 text-white transition-opacity hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
