import { useContext, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { motion } from 'framer-motion';
import { Search, Sparkles, ExternalLink, User, TrendingDown } from 'lucide-react';

type DebatePriority = 'cheapest' | 'fastest' | 'best_overall';

type Offer = {
  provider: 'amazon' | 'flipkart' | 'blinkit' | 'bigbasket' | 'zepto';
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

const PROVIDER_LABELS: Record<Offer['provider'], string> = {
  amazon: 'Amazon',
  flipkart: 'Flipkart',
  blinkit: 'Blinkit',
  bigbasket: 'BigBasket',
  zepto: 'Zepto'
};

function formatMoney(currency: Offer['currency'], price?: number | null) {
  if (typeof price !== 'number') return '—';
  return `${currency} ${price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
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
  const savingsVsBestAlt = minOther - chosenPrice;
  const savingsVsWorst = maxOther - chosenPrice;
  return {
    savingsVsBestAlt: Math.round(savingsVsBestAlt * 100) / 100,
    savingsVsWorst: Math.round(savingsVsWorst * 100) / 100,
    bestAlt: minOther,
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

function ProductCard({ offer, isChosen, savings }: { offer: Offer; isChosen: boolean; savings?: any }) {
  return (
    <motion.a
      href={offer.url}
      target="_blank"
      rel="noreferrer"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`block p-4 rounded-lg border transition hover:shadow-lg ${
        isChosen
          ? 'bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border-cyan-400/50'
          : 'bg-white/5 border-white/10 hover:bg-white/10'
      }`}
    >
      <div className="flex gap-4">
        {/* Image */}
        <div className="w-20 h-20 rounded-lg bg-white/5 border border-white/10 overflow-hidden shrink-0 flex items-center justify-center">
          {offer.image_url ? (
            <img
              src={offer.image_url}
              alt={offer.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="text-xs text-gray-500 text-center px-1">No image</div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            <div className="text-sm font-bold text-white truncate">{offer.title}</div>
            <div className="text-lg font-bold text-emerald-300 mt-1">
              {formatMoney(offer.currency, offer.price)}
            </div>
          </div>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-gray-400">{PROVIDER_LABELS[offer.provider]}</span>
            {isChosen && savings && savings.savingsVsWorst > 0 && (
              <span className="text-emerald-300 font-semibold flex items-center gap-1">
                <TrendingDown className="w-3 h-3" />
                Save {offer.currency} {savings.savingsVsWorst}
              </span>
            )}
          </div>
        </div>

        {/* External link icon */}
        <div className="shrink-0 flex items-center">
          <ExternalLink className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </motion.a>
  );
}

export default function DebatePurchaseV2() {
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

  const savings = useMemo(() => {
    if (!result) return null;
    return computeSavings(result.offers || [], result.chosen_offer || null);
  }, [result]);

  // Categorize offers: top choice, similar (within 10%), rest
  const categorizedOffers = useMemo(() => {
    if (!result?.offers) return { top: null, similar: [], rest: [] };
    
    const sorted = [...result.offers].sort((a, b) => {
      const priceA = a.price ?? Infinity;
      const priceB = b.price ?? Infinity;
      return priceA - priceB;
    });

    const top = sorted[0] || null;
    const topPrice = top?.price ?? 0;
    const threshold = topPrice * 0.1; // 10% threshold

    const similar = sorted.slice(1).filter(o => {
      const price = o.price ?? Infinity;
      return price <= topPrice + threshold;
    });

    const rest = sorted.filter(o => {
      const price = o.price ?? Infinity;
      return price > topPrice + threshold;
    });

    return { top, similar, rest };
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
    setRealtimeConclusion('Analyzing prices across platforms…');

    const steps: Array<{ delay: number; role: BubbleRole; text: string }> = [
      { delay: 250, role: 'FrugalCoach', text: `Searching for '${q}' across all platforms…` },
      { delay: 900, role: 'ValueAnalyst', text: 'Comparing prices and verifying availability…' },
      { delay: 1550, role: 'ConvenienceAdvocate', text: 'Checking delivery options and stock status…' },
      { delay: 2200, role: 'Referee', text: 'Finalizing recommendation…' }
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
        { query: q, priority, max_results: 12 },
        { headers: { Authorization: `Bearer ${auth?.token}` } }
      );
      setResult(res.data);
      const roles: Array<{ role: BubbleRole; text: string }> = (res.data?.roles || []).map((r: any) => ({
        role: r.role,
        text: r.text
      }));
      if (res.data?.final_recommendation) setRealtimeConclusion(res.data.final_recommendation);
      if (roles.length === 4) setRealtimeBubbles(roles);
      setDebateMode('side');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Search failed. Please try again.');
      setDebateMode('idle');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Search Header */}
      <div className="glass-card p-6 rounded-xl border border-white/10">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-300" />
              Price Comparison
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              Search across Indian e-commerce platforms and get instant recommendations.
            </p>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 lg:grid-cols-5 gap-3">
          <div className="lg:col-span-3">
            <label className="text-xs text-gray-400">What are you looking for?</label>
            <div className="mt-1 flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
              <Search className="w-4 h-4 text-gray-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. basmati rice 5kg, wireless mouse, coffee maker"
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
              {loading ? 'Searching…' : 'Search'}
            </button>
          </div>
        </div>

        {error && <div className="mt-4 text-sm text-red-300">{error}</div>}
      </div>

      {/* Realtime Debate - Central Card */}
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

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Results */}
          <div className="lg:col-span-2 space-y-4">
            {!categorizedOffers.top && result.offers.length === 0 && (
              <div className="glass-card p-6 rounded-xl border border-white/10">
                <div className="text-center py-8">
                  <p className="text-gray-400">No results found. Try a different search.</p>
                </div>
              </div>
            )}

            {/* Top Choice */}
            {categorizedOffers.top && (
              <div className="glass-card p-6 rounded-xl border border-white/10">
                <div className="mb-4">
                  <div className="text-xs font-semibold text-cyan-300 uppercase tracking-wide">Best Price</div>
                  <h3 className="text-lg font-bold text-white mt-1">Top Choice</h3>
                </div>
                <ProductCard
                  offer={categorizedOffers.top}
                  isChosen={true}
                  savings={savings}
                />
              </div>
            )}

            {/* Similar Prices */}
            {categorizedOffers.similar.length > 0 && (
              <div className="glass-card p-6 rounded-xl border border-white/10">
                <div className="mb-4">
                  <div className="text-xs font-semibold text-blue-300 uppercase tracking-wide">Within 10%</div>
                  <h3 className="text-lg font-bold text-white mt-1">Similar Prices</h3>
                </div>
                <div className="space-y-3">
                  {categorizedOffers.similar.map((offer, idx) => (
                    <ProductCard key={idx} offer={offer} isChosen={false} />
                  ))}
                </div>
              </div>
            )}

            {/* Other Options */}
            {categorizedOffers.rest.length > 0 && (
              <div className="glass-card p-6 rounded-xl border border-white/10">
                <div className="mb-4">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Other Options</div>
                  <h3 className="text-lg font-bold text-white mt-1">More Choices</h3>
                </div>
                <div className="space-y-3">
                  {categorizedOffers.rest.map((offer, idx) => (
                    <ProductCard key={idx} offer={offer} isChosen={false} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Debate Panel */}
          <div className="glass-card p-6 rounded-xl border border-white/10">
            <h3 className="text-lg font-semibold mb-2">Expert Analysis</h3>
            <div className="text-xs text-gray-400 mb-4">
              Confidence: {Math.round((result.confidence || 0) * 100)}%
            </div>
            <div className="text-sm font-semibold text-cyan-200 mb-4 p-3 bg-cyan-500/10 rounded-lg border border-cyan-400/30">
              {realtimeConclusion}
            </div>
            <div className="space-y-3">
              {realtimeBubbles.map((b, i) => (
                <Bubble key={i} role={b.role} text={b.text} />
              ))}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
