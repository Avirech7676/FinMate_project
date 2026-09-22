import { useContext, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { motion } from 'framer-motion';
import { Search, Sparkles, ExternalLink, User } from 'lucide-react';

type DebatePriority = 'cheapest' | 'fastest' | 'best_overall';

type Offer = {
  provider: 'amazon' | 'flipkart' | 'blinkit' | 'web';
  title: string;
  price?: number | null;
  currency: 'USD' | 'INR' | 'EUR' | 'GBP';
  delivery_eta_minutes?: number | null;
  url: string;
  image_url?: string | null;
};

type DebateRole = {
  role: 'FrugalCoach' | 'ValueAnalyst' | 'ConvenienceAdvocate' | 'Referee';
  text: string;
};

type DebateOut = {
  query: string;
  priority: DebatePriority;
  offers: Offer[];
  chosen_offer?: Offer | null;
  confidence: number;
  roles: DebateRole[];
  final_recommendation: string;
};

type BubbleRole = DebateRole['role'];

const ROLE_META: Record<
  BubbleRole,
  { name: string; border: string; bg: string; text: string; icon: string }
> = {
  FrugalCoach: {
    name: 'Frugal Coach',
    border: 'border-emerald-400/30',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-200',
    icon: 'text-emerald-300'
  },
  ValueAnalyst: {
    name: 'Value Analyst',
    border: 'border-blue-400/30',
    bg: 'bg-blue-500/10',
    text: 'text-blue-200',
    icon: 'text-blue-300'
  },
  ConvenienceAdvocate: {
    name: 'Convenience',
    border: 'border-purple-400/30',
    bg: 'bg-purple-500/10',
    text: 'text-purple-200',
    icon: 'text-purple-300'
  },
  Referee: {
    name: 'Referee',
    border: 'border-cyan-400/30',
    bg: 'bg-cyan-500/10',
    text: 'text-cyan-200',
    icon: 'text-cyan-300'
  }
};

function providerLabel(p: Offer['provider']) {
  if (p === 'amazon') return 'Amazon';
  if (p === 'flipkart') return 'Flipkart';
  if (p === 'blinkit') return 'Blinkit';
  return 'Web';
}

function formatMoney(currency: Offer['currency'], price?: number | null) {
  if (typeof price !== 'number') return '—';
  return `${currency} ${price}`;
}

function computeSavings(offers: Offer[], chosen?: Offer | null) {
  const chosenPrice = chosen?.price;
  if (typeof chosenPrice !== 'number') return null;
  const comparable = offers
    .filter((o) => typeof o.price === 'number' && o.url !== chosen?.url)
    .map((o) => o.price as number);
  if (comparable.length === 0) return null;
  const minOther = Math.min(...comparable);
  const maxOther = Math.max(...comparable);
  const bestAlt = minOther;
  const savingsVsBestAlt = bestAlt - chosenPrice;
  const savingsVsWorst = maxOther - chosenPrice;
  return {
    savingsVsBestAlt: Math.round(savingsVsBestAlt * 100) / 100,
    savingsVsWorst: Math.round(savingsVsWorst * 100) / 100,
    bestAlt,
    maxOther
  };
}

function Bubble({ role, text }: { role: BubbleRole; text: string }) {
  const m = ROLE_META[role];
  return (
    <div className={`rounded-xl border ${m.border} ${m.bg} p-3`}>
      <div className="flex items-start gap-2">
        <div className={`w-8 h-8 rounded-full border ${m.border} flex items-center justify-center ${m.bg}`}>
          <User className={`w-4 h-4 ${m.icon}`} />
        </div>
        <div className="min-w-0">
          <div className={`text-xs font-semibold ${m.text}`}>{m.name}</div>
          <div className="text-sm text-gray-100 mt-1 whitespace-pre-wrap">{text}</div>
        </div>
      </div>
    </div>
  );
}

export default function DebatePurchase() {
  const auth = useContext(AuthContext);
  const [query, setQuery] = useState('');
  const [priority, setPriority] = useState<DebatePriority>('best_overall');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DebateOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [debateMode, setDebateMode] = useState<'idle' | 'realtime' | 'side'>('idle');
  const [realtimeBubbles, setRealtimeBubbles] = useState<Array<{ role: BubbleRole; text: string }>>([]);
  const [realtimeConclusion, setRealtimeConclusion] = useState<string>('');
  const timers = useRef<number[]>([]);

  const offersByProvider = useMemo(() => {
    const map: Record<string, Offer[]> = {};
    for (const o of result?.offers || []) {
      map[o.provider] = map[o.provider] || [];
      map[o.provider].push(o);
    }
    return map;
  }, [result]);

  const savings = useMemo(() => {
    if (!result) return null;
    return computeSavings(result.offers || [], result.chosen_offer || null);
  }, [result]);

  const clearTimers = () => {
    for (const t of timers.current) window.clearTimeout(t);
    timers.current = [];
  };

  useEffect(() => {
    return () => clearTimers();
  }, []);

  const startRealtimeDebate = (q: string) => {
    clearTimers();
    setDebateMode('realtime');
    setRealtimeBubbles([]);
    setRealtimeConclusion('Forming a recommendation…');

    // Pre-debate “live” reveal; will be replaced with actual debate once API returns.
    const steps: Array<{ delay: number; role: BubbleRole; text: string }> = [
      { delay: 250, role: 'FrugalCoach', text: `Goal: keep '${q}' cost low. Pulling prices across sites…` },
      { delay: 900, role: 'ValueAnalyst', text: 'Checking which offers have clear price signals and trusted sources…' },
      { delay: 1550, role: 'ConvenienceAdvocate', text: 'Considering availability and fastest checkout path. Links matter.' },
      { delay: 2200, role: 'Referee', text: 'Hold. I will pick the best option once comparisons arrive.' }
    ];

    for (const s of steps) {
      const id = window.setTimeout(() => {
        setRealtimeBubbles((prev) => [...prev, { role: s.role, text: s.text }]);
      }, s.delay);
      timers.current.push(id);
    }
  };

  const runDebate = async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    setResult(null);
    startRealtimeDebate(q);
    try {
      const res = await axios.post(
        `${API_URL}/debate/run`,
        { query: q, priority, max_results: 8 },
        { headers: { Authorization: `Bearer ${auth?.token}` } }
      );
      setResult(res.data);
      // Swap in real debate messages and move debate to side layout
      const roles: Array<{ role: BubbleRole; text: string }> = (res.data?.roles || []).map((r: any) => ({
        role: r.role,
        text: r.text
      }));
      if (res.data?.final_recommendation) setRealtimeConclusion(res.data.final_recommendation);
      if (roles.length === 4) setRealtimeBubbles(roles);
      setDebateMode('side');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Debate failed. Please try again.');
      setDebateMode('idle');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="glass-card p-6 rounded-xl border border-white/10">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-300" />
              Debate a Purchase
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              Search across sites and get a short multi-voice recommendation.
            </p>
          </div>
          <div className="text-xs text-gray-400">
            Prices are best-effort—verify at checkout.
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 lg:grid-cols-5 gap-3">
          <div className="lg:col-span-3">
            <label className="text-xs text-gray-400">What do you want to buy?</label>
            <div className="mt-1 flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
              <Search className="w-4 h-4 text-gray-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. basmati rice 5kg / wireless mouse"
                className="w-full bg-transparent outline-none text-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') runDebate();
                }}
              />
            </div>
          </div>

          <div className="lg:col-span-1">
            <label className="text-xs text-gray-400">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as DebatePriority)}
              className="mt-1 w-full bg-white text-black border border-white/20 rounded-lg px-3 py-2 text-sm outline-none"
            >
              <option value="best_overall">Best overall</option>
              <option value="cheapest">Cheapest</option>
              <option value="fastest">Fastest</option>
            </select>
          </div>

          <div className="lg:col-span-1 flex items-end">
            <button
              onClick={runDebate}
              disabled={loading || !query.trim()}
              className={`w-full px-4 py-2 rounded-lg text-sm font-semibold transition ${
                loading || !query.trim()
                  ? 'bg-white/5 text-gray-500 border border-white/10'
                  : 'bg-gradient-to-r from-purple-500/40 to-cyan-500/30 border border-white/10 hover:from-purple-500/50 hover:to-cyan-500/40'
              }`}
            >
              {loading ? 'Comparing…' : 'Compare & Debate'}
            </button>
          </div>
        </div>

        {error && <div className="mt-4 text-sm text-red-300">{error}</div>}
      </div>

      {debateMode === 'realtime' && (
        <div className="glass-card p-6 rounded-xl border border-white/10">
          <div className="text-xs text-gray-400">Live debate</div>
          <div className="mt-2 text-lg font-semibold text-cyan-200">{realtimeConclusion}</div>
          <div className="mt-4 space-y-3 max-w-3xl mx-auto">
            {realtimeBubbles.map((b, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <Bubble role={b.role} text={b.text} />
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="glass-card p-6 rounded-xl border border-white/10">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <h3 className="text-lg font-semibold">Offers</h3>
                {result.chosen_offer && (
                  <div className="text-base font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    Recommended: {providerLabel(result.chosen_offer.provider)}
                    {typeof result.chosen_offer.price === 'number' && (
                      <span className="text-gray-300 font-semibold">
                        {' '}({result.chosen_offer.currency} {result.chosen_offer.price})
                      </span>
                    )}
                  </div>
                )}
              </div>

              {result.chosen_offer && (
                <div className="mt-3 bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-400/50 rounded-lg p-4 space-y-3">
                  <div className="text-xs font-semibold text-cyan-300 uppercase tracking-wide">Recommended</div>
                  
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <div className="w-32 h-32 rounded-lg bg-white/5 border border-white/10 overflow-hidden shrink-0 flex items-center justify-center">
                      {result.chosen_offer.image_url ? (
                        <img
                          src={result.chosen_offer.image_url}
                          alt={result.chosen_offer.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="text-xs text-gray-500 text-center px-2">No image available</div>
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 flex flex-col justify-between">
                      <div>
                        <div className="text-lg font-bold text-white mb-2">{result.chosen_offer.title}</div>
                        <div className="text-3xl font-bold text-emerald-300 mb-3">
                          {formatMoney(result.chosen_offer.currency, result.chosen_offer.price)}
                        </div>
                      </div>

                      {/* Provider and Savings */}
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-xs text-gray-400">From</div>
                          <div className="text-base font-bold text-cyan-300">
                            {providerLabel(result.chosen_offer.provider)}
                          </div>
                        </div>
                        {savings && typeof savings.savingsVsWorst === 'number' && savings.savingsVsWorst > 0 && (
                          <div className="text-right">
                            <div className="text-xs text-gray-400">You save</div>
                            <div className="text-base font-bold text-emerald-300">
                              {result.chosen_offer.currency} {Math.max(0, savings.savingsVsWorst)}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <a
                    href={result.chosen_offer.url}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full px-4 py-3 rounded-lg text-sm font-semibold bg-gradient-to-r from-cyan-500/40 to-purple-500/40 border border-cyan-400/50 hover:from-cyan-500/60 hover:to-purple-500/60 transition flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Go to {providerLabel(result.chosen_offer.provider)}
                  </a>
                </div>
              )}

              <div className="mt-4 space-y-4">
                {Object.keys(offersByProvider).length === 0 && (
                  <div className="text-sm text-gray-400">No offers found. Try a different query.</div>
                )}
                {Object.entries(offersByProvider).map(([prov, offers]) => (
                  <div key={prov} className="bg-white/5 border border-white/10 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold">{providerLabel(prov as any)}</div>
                      <div className="text-xs text-gray-400">{offers.length} result(s)</div>
                    </div>
                    <div className="mt-2 space-y-3">
                      {offers.slice(0, 4).map((o, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg hover:bg-white/10 transition border border-white/10 bg-white/5"
                        >
                          <div className="flex items-start gap-4">
                            {/* Product Image - Larger */}
                            <div className="w-24 h-24 rounded-lg bg-white/5 border border-white/10 overflow-hidden shrink-0 flex items-center justify-center">
                              {o.image_url ? (
                                <img
                                  src={o.image_url}
                                  alt={o.title}
                                  className="w-full h-full object-cover"
                                  loading="lazy"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center text-xs text-gray-500 text-center px-2">
                                  No image
                                </div>
                              )}
                            </div>

                            <div className="flex-1 min-w-0 flex flex-col justify-between">
                              {/* Title and Price */}
                              <div>
                                <div className="text-base font-bold text-white mb-1">{o.title}</div>
                                <div className="text-lg font-bold text-emerald-300 mb-2">
                                  {formatMoney(o.currency, o.price)}
                                </div>
                              </div>

                              {/* Comparison */}
                              {result.chosen_offer && typeof o.price === 'number' && typeof result.chosen_offer.price === 'number' && (
                                <div className="text-xs text-gray-400">
                                  {result.chosen_offer.currency}{' '}
                                  {Math.abs(o.price - result.chosen_offer.price).toFixed(2)}{' '}
                                  {o.price > result.chosen_offer.price ? 'more than chosen' : 'less than chosen'}
                                </div>
                              )}
                            </div>

                            <a
                              href={o.url}
                              target="_blank"
                              rel="noreferrer"
                              className="shrink-0 px-3 py-2 rounded-lg text-xs font-semibold bg-white/10 border border-white/10 hover:bg-white/15 transition flex items-center gap-1 h-fit"
                            >
                              <ExternalLink className="w-3 h-3" />
                              Go
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="glass-card p-6 rounded-xl border border-white/10">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Debate</h3>
                <div className="text-xs text-gray-400">
                  Confidence: {Math.round((result.confidence || 0) * 100)}%
                </div>
              </div>

              <div className="mt-3 text-sm font-semibold text-cyan-200">{realtimeConclusion}</div>
              <div className="mt-4 space-y-3">
                {realtimeBubbles.map((b, i) => (
                  <Bubble key={i} role={b.role} text={b.text} />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}

