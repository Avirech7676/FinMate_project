import { useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { AlertCircle } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

type Transaction = {
  transaction_id: number;
  amount: number;
  category: string;
  description: string;
  date: string;
  source: string;
};

type MonthPoint = {
  month: string; // e.g. "2025-03"
  label: string; // e.g. "Mar"
  isFuture: boolean;
  total: number;
  [category: string]: string | number | boolean;
};

const CATEGORY_COLORS: Record<string, string> = {
  food: '#22c55e',
  transportation: '#3b82f6',
  entertainment: '#a855f7',
  utilities: '#f97316',
  healthcare: '#ec4899',
  shopping: '#eab308',
  housing: '#6366f1',
  other: '#9ca3af',
};

export default function PredictionPanel() {
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [sliderFactors, setSliderFactors] = useState<Record<string, number>>({});

  useEffect(() => {
    const fetchTransactions = async () => {
      if (!auth?.token) return;
      setError('');
      setLoading(true);
      try {
        const res = await axios.get<Transaction[]>(`${API_URL}/transactions`, {
          headers: { Authorization: `Bearer ${auth.token}` },
        });
        setTransactions(res.data || []);
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load transactions.');
      } finally {
        setLoading(false);
      }
    };
    fetchTransactions();
  }, [auth?.token]);

  // Build monthly aggregates and simple 3-month forecast per category
  const { chartData, categories, futureTotal } = useMemo(() => {
    if (!transactions.length) {
      return { chartData: [] as MonthPoint[], categories: [] as string[], futureTotal: 0 };
    }

    const byMonthCat = new Map<string, Map<string, number>>();
    const allMonths: Set<string> = new Set();

    for (const t of transactions) {
      if (!t.date) continue;
      const d = new Date(t.date);
      if (Number.isNaN(d.getTime())) continue;
      const ym = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      allMonths.add(ym);
      const cat = (t.category || 'other').toLowerCase();
      if (!byMonthCat.has(ym)) byMonthCat.set(ym, new Map());
      const inner = byMonthCat.get(ym)!;
      inner.set(cat, (inner.get(cat) || 0) + t.amount);
    }

    const sortedMonths = Array.from(allMonths).sort();
    if (!sortedMonths.length) {
      return { chartData: [] as MonthPoint[], categories: [] as string[], futureTotal: 0 };
    }

    const lastThree = sortedMonths.slice(-3);

    // Determine top categories by total in recent months
    const catTotals = new Map<string, number>();
    for (const ym of lastThree) {
      const inner = byMonthCat.get(ym);
      if (!inner) continue;
      for (const [cat, amt] of inner.entries()) {
        catTotals.set(cat, (catTotals.get(cat) || 0) + amt);
      }
    }
    const topCategories = Array.from(catTotals.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([cat]) => cat);

    // Compute simple trend (slope & intercept) per category across all historical months
    const catTrend = new Map<string, { a: number; b: number }>(); // y = a + b * t
    const monthIndex: Record<string, number> = {};
    sortedMonths.forEach((m, idx) => {
      monthIndex[m] = idx;
    });

    for (const cat of topCategories) {
      const xs: number[] = [];
      const ys: number[] = [];
      for (const ym of sortedMonths) {
        const inner = byMonthCat.get(ym);
        if (!inner) continue;
        const amt = inner.get(cat) || 0;
        xs.push(monthIndex[ym]);
        ys.push(amt);
      }
      if (xs.length < 2) {
        // fallback: flat line at average
        const avg =
          ys.length === 0 ? 0 : ys.reduce((s, v) => s + v, 0) / ys.length;
        catTrend.set(cat, { a: avg, b: 0 });
      } else {
        const n = xs.length;
        const sumX = xs.reduce((s, v) => s + v, 0);
        const sumY = ys.reduce((s, v) => s + v, 0);
        const sumXY = xs.reduce((s, v, i) => s + v * ys[i], 0);
        const sumX2 = xs.reduce((s, v) => s + v * v, 0);
        const denom = n * sumX2 - sumX * sumX;
        let b = 0;
        if (denom !== 0) {
          b = (n * sumXY - sumX * sumY) / denom;
        }
        const a = n ? sumY / n - b * (sumX / n) : 0;
        catTrend.set(cat, { a, b });
      }
    }

    // Build next 3 month keys
    const [lastYear, lastMonthIdx] = lastThree.length
      ? lastThree[lastThree.length - 1].split('-').map(Number)
      : [new Date().getFullYear(), new Date().getMonth() + 1];
    const futureMonths: string[] = [];
    let y = lastYear;
    let m = lastMonthIdx;
    for (let i = 0; i < 3; i++) {
      m += 1;
      if (m === 13) {
        m = 1;
        y += 1;
      }
      futureMonths.push(`${y}-${String(m).padStart(2, '0')}`);
    }

    const monthLabel = (ym: string) => {
      const [yy, mm] = ym.split('-').map(Number);
      const date = new Date(yy, (mm || 1) - 1, 1);
      return date.toLocaleDateString(undefined, { month: 'short' });
    };

    const combinedMonths = [...lastThree, ...futureMonths];
    const data: MonthPoint[] = combinedMonths.map(ym => {
      const isFuture = futureMonths.includes(ym);
      const base: MonthPoint = {
        month: ym,
        label: monthLabel(ym),
        isFuture,
        total: 0,
      };
      const inner = byMonthCat.get(ym);
      const t = monthIndex[ym] ?? monthIndex[sortedMonths[sortedMonths.length - 1]] ?? 0;
      for (const cat of topCategories) {
        let val = 0;
        if (!isFuture) {
          val = inner?.get(cat) || 0;
        } else {
          const trend = catTrend.get(cat);
          if (trend) {
            val = trend.a + trend.b * t;
          }
        }
        if (val < 0) val = 0;
        base[cat] = val;
        base.total += val;
      }
      return base;
    });

    let futureTotal = 0;
    for (const p of data.filter(d => d.isFuture)) {
      futureTotal += Number(p.total || 0);
    }

    return { chartData: data, categories: topCategories, futureTotal };
  }, [transactions]);

  // Apply slider factors to future points
  const adjustedChartData: MonthPoint[] = useMemo(() => {
    if (!chartData.length || !categories.length) return chartData;
    return chartData.map(p => {
      if (!p.isFuture) return p;
      const updated: MonthPoint = { ...p, total: 0 };
      for (const cat of categories) {
        const factor = sliderFactors[cat] ?? 100;
        const val = Number(p[cat] || 0) * (factor / 100);
        updated[cat] = val;
        updated.total += val;
      }
      return updated;
    });
  }, [chartData, categories, sliderFactors]);

  const adjustedFutureTotal = useMemo(() => {
    if (!adjustedChartData.length) return 0;
    let total = 0;
    for (const p of adjustedChartData.filter(d => d.isFuture)) {
      total += Number(p.total || 0);
    }
    return total;
  }, [adjustedChartData, categories]);

  const handleSliderChange = (cat: string, value: number) => {
    setSliderFactors(prev => ({ ...prev, [cat]: value }));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Spending Prediction</h2>
          <p className="text-sm text-gray-400">
            See where your money is likely to go over the next 3 months — and tweak the sliders to explore “what if” scenarios.
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-2 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <AlertCircle className="mt-0.5 h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="glass-card p-6 text-center text-sm text-gray-300">
          Loading prediction…
        </div>
      ) : !adjustedChartData.length ? (
        <div className="glass-card p-6 text-center text-sm text-gray-300">
          Not enough data yet to build a prediction. Try importing more transactions.
        </div>
      ) : (
        <>
          <div className="glass-card mb-6 rounded-xl border border-white/10 p-4 text-sm text-gray-300">
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <div>
                <p className="text-xs text-gray-400">Projected total (next 3 months)</p>
                <p className="text-2xl font-bold">
                  {auth?.user?.currency_symbol || '$'}
                  {adjustedFutureTotal.toFixed(0)}
                </p>
              </div>
              <div className="text-xs text-gray-400">
                Baseline: {auth?.user?.currency_symbol || '$'}
                {futureTotal.toFixed(0)} · Difference:{' '}
                <span
                  className={
                    adjustedFutureTotal > futureTotal
                      ? 'text-red-300'
                      : adjustedFutureTotal < futureTotal
                      ? 'text-emerald-300'
                      : 'text-gray-200'
                  }
                >
                  {adjustedFutureTotal > futureTotal ? '+' : ''}
                  {(adjustedFutureTotal - futureTotal).toFixed(0)}
                </span>
              </div>
            </div>
          </div>

          <div className="glass-card mb-6 h-80 rounded-xl border border-white/10 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={adjustedChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="label" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#020617',
                    border: '1px solid rgba(148,163,184,0.4)',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="total"
                  name="Total"
                  stroke="#e5e7eb"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="4 4"
                />
                {categories.map(cat => (
                  <Line
                    key={cat}
                    type="monotone"
                    dataKey={cat}
                    name={cat.charAt(0).toUpperCase() + cat.slice(1)}
                    stroke={CATEGORY_COLORS[cat] || '#38bdf8'}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="glass-card rounded-xl border border-white/10 p-4">
            <p className="mb-3 text-xs font-semibold text-gray-400">
              Adjust future spending by category (% of your recent pattern)
            </p>
            <div className="space-y-3">
              {categories.map(cat => {
                const factor = sliderFactors[cat] ?? 100;
                return (
                  <div key={cat} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="flex items-center gap-2">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: CATEGORY_COLORS[cat] || '#38bdf8' }}
                        />
                        {cat.charAt(0).toUpperCase() + cat.slice(1)}
                      </span>
                      <span className="text-gray-400">{factor}% of current pattern</span>
                    </div>
                    <input
                      type="range"
                      min={50}
                      max={150}
                      step={5}
                      value={factor}
                      onChange={e => handleSliderChange(cat, Number(e.target.value))}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

