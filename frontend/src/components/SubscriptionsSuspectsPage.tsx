import { useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { AlertCircle, ToggleLeft, ToggleRight } from 'lucide-react';
import { motion } from 'framer-motion';

type Suspect = {
  candidate_id: string;
  merchant: string;
  avg_amount: number;
  estimated_monthly_cost: number;
  occurrences: number;
  interval_days: number;
  last_seen_at: string;
  confidence: number;
  decision?: string | null;
};

export default function SubscriptionsSuspectsPanel() {
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [suspects, setSuspects] = useState<Suspect[]>([]);

  useEffect(() => {
    const fetchSuspects = async () => {
      if (!auth?.token) return;
      setError('');
      setLoading(true);
      try {
        const res = await axios.get<Suspect[]>(`${API_URL}/subscriptions/suspects`, {
          headers: { Authorization: `Bearer ${auth.token}` },
        });
        setSuspects(res.data || []);
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load subscription suspects.');
      } finally {
        setLoading(false);
      }
    };
    fetchSuspects();
  }, [auth?.token]);

  const updateDecision = async (candidateId: string, decision: 'keep' | 'removed') => {
    if (!auth?.token) return;
    try {
      await axios.post(
        `${API_URL}/subscriptions/suspects/${candidateId}/decision`,
        { decision },
        { headers: { Authorization: `Bearer ${auth.token}` } },
      );
      setSuspects(prev =>
        prev.map(s =>
          s.candidate_id === candidateId ? { ...s, decision } : s,
        ),
      );
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to save decision.');
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold mb-1">Subscription Suspects</h2>
        <p className="text-sm text-gray-400">
          Merchants that look like recurring subscriptions. Mark them as kept or removed.
        </p>
      </div>

      {error && (
        <div className="mb-2 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          <AlertCircle className="mt-0.5 h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="glass-card p-6 text-center text-sm text-gray-300">
          Detecting recurring merchants…
        </div>
      ) : suspects.length === 0 ? (
        <div className="glass-card p-6 text-center text-sm text-gray-300">
          No clear subscription-like merchants yet. Import more history to improve detection.
        </div>
      ) : (
        <div className="space-y-3">
          {suspects.map((s, idx) => (
            <motion.div
              key={s.candidate_id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.03 }}
              className="glass-card flex items-start justify-between gap-4 rounded-xl border border-white/10 p-4"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-semibold">{s.merchant}</p>
                  <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-gray-300">
                    {Math.round((s.confidence || 0) * 100)}% suspect
                  </span>
                </div>
                <p className="mt-1 text-xs text-gray-400">
                  {auth?.user?.currency_symbol || '$'}
                  {s.estimated_monthly_cost.toFixed(0)} / month · {s.occurrences} charges · every ~
                  {s.interval_days} days
                </p>
                <p className="mt-1 text-[10px] text-gray-500">
                  Last seen on {new Date(s.last_seen_at).toLocaleDateString()}
                </p>
              </div>

              <div className="flex shrink-0 flex-col items-end gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateDecision(s.candidate_id, 'keep')}
                    className={`flex items-center gap-1 rounded-full px-3 py-1 border text-xs ${
                      s.decision === 'keep'
                        ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200'
                        : 'border-white/15 bg-white/5 text-gray-300 hover:bg-white/10'
                    }`}
                  >
                    <ToggleRight className="h-3 w-3" />
                    Keep
                  </button>
                  <button
                    onClick={() => updateDecision(s.candidate_id, 'removed')}
                    className={`flex items-center gap-1 rounded-full px-3 py-1 border text-xs ${
                      s.decision === 'removed'
                        ? 'border-red-400 bg-red-500/20 text-red-200'
                        : 'border-white/15 bg-white/5 text-gray-300 hover:bg-white/10'
                    }`}
                  >
                    <ToggleLeft className="h-3 w-3" />
                    Removed
                  </button>
                </div>
                {s.decision && (
                  <p className="text-[10px] text-gray-400">
                    Marked as <span className="font-semibold">{s.decision}</span>
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

