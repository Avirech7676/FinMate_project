import { useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { Mail, ShieldAlert, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type Candidate = {
  candidate_id: string;
  merchant: string;
  avg_amount: number;
  estimated_monthly_cost: number;
  occurrences: number;
  interval_days: number;
  last_seen_at: string;
  confidence: number;
};

export default function SubscriptionsPanel() {
  const auth = useContext(AuthContext);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const [leak, setLeak] = useState(0);
  const [savings, setSavings] = useState(0);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [xp, setXp] = useState(0);
  const [streak, setStreak] = useState(0);

  const [template, setTemplate] = useState<{ subject: string; body: string } | null>(null);
  const [templateTitle, setTemplateTitle] = useState<string>('');

  const fetchSubs = async () => {
    if (!auth?.token) return;
    setError('');
    try {
      const [res, statsRes] = await Promise.all([
        axios.get(`${API_URL}/subscriptions/detect`, {
          headers: { Authorization: `Bearer ${auth?.token}` }
        }),
        axios.get(`${API_URL}/stats`, {
          headers: { Authorization: `Bearer ${auth?.token}` }
        })
      ]);
      setLeak(res.data.estimated_monthly_leak || 0);
      setSavings(res.data.estimated_monthly_savings || 0);
      setCandidates(res.data.candidates || []);
      setXp(statsRes.data?.total_xp || 0);
      setStreak(statsRes.data?.current_streak || 0);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to detect subscriptions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSubs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth?.token]);

  const runAction = async (candidate: Candidate, action: 'keep' | 'cancel' | 'negotiate') => {
    if (!auth?.token) return;
    setError('');
    setTemplate(null);
    setTemplateTitle('');
    try {
      const res = await axios.post(
        `${API_URL}/subscriptions/${candidate.candidate_id}/action`,
        {
          action,
          merchant: candidate.merchant,
          avg_amount: candidate.avg_amount,
          interval_days: candidate.interval_days,
          occurrences: candidate.occurrences,
          last_seen_at: candidate.last_seen_at
        },
        { headers: { Authorization: `Bearer ${auth?.token}` } }
      );

      setSavings(res.data.estimated_monthly_savings || 0);
      setXp(res.data.total_xp || xp);
      setStreak(res.data.current_streak || streak);
      if (res.data.action_type === 'email_template' && res.data.action_payload) {
        setTemplateTitle(`${action === 'cancel' ? 'Cancellation' : 'Negotiation'} email for ${candidate.merchant}`);
        setTemplate({
          subject: res.data.action_payload.subject,
          body: res.data.action_payload.body
        });
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to save action');
    }
  };

  if (loading) {
    return <div className="glass-card p-6 text-center">Detecting subscriptions...</div>;
  }

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/10">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Subscription Creep Radar</h3>
          <p className="text-sm text-gray-400">
            Recurring charges we think are subscriptions. Take one action to start saving.
          </p>
        </div>
        <button
          onClick={() => {
            setRefreshing(true);
            fetchSubs();
          }}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex gap-2">
          <ShieldAlert className="w-4 h-4 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <p className="text-xs text-gray-400">Estimated monthly leak</p>
          <p className="text-3xl font-bold text-orange-300">
            {auth?.user?.currency_symbol || '$'}
            {Number(leak).toFixed(0)}
          </p>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <p className="text-xs text-gray-400">Estimated monthly savings</p>
          <p className="text-3xl font-bold text-cyan-300">
            {auth?.user?.currency_symbol || '$'}
            {Number(savings).toFixed(0)}
          </p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
        <span>XP: <span className="text-yellow-300 font-semibold">{xp}</span></span>
        <span>Action streak: <span className="text-cyan-300 font-semibold">{streak}</span></span>
      </div>

      <div className="mt-5 space-y-3">
        {candidates.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-6">
            No clear recurring charges detected yet. Import more history to improve detection.
          </p>
        ) : (
          candidates.map((c) => (
            <motion.div
              key={c.candidate_id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold truncate">{c.merchant}</p>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-gray-300">
                      {Math.round((c.confidence || 0) * 100)}% match
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mt-1">
                    {auth?.user?.currency_symbol || '$'}
                    {Number(c.estimated_monthly_cost).toFixed(2)} / mo · {c.occurrences} charges · every ~{c.interval_days} days
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => runAction(c, 'keep')}
                    className="px-3 py-1.5 rounded-lg text-sm bg-white/5 hover:bg-white/10 border border-white/10"
                  >
                    Keep
                  </button>
                  <button
                    onClick={() => runAction(c, 'negotiate')}
                    className="px-3 py-1.5 rounded-lg text-sm bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 text-purple-200"
                  >
                    Negotiate
                  </button>
                  <button
                    onClick={() => runAction(c, 'cancel')}
                    className="px-3 py-1.5 rounded-lg text-sm bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      <AnimatePresence>
        {template && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mt-6 p-4 rounded-xl bg-[#0d1220] border border-white/10"
          >
            <div className="flex items-center gap-2 text-cyan-300 mb-3">
              <Mail className="w-4 h-4" />
              <p className="text-sm font-semibold">{templateTitle}</p>
            </div>
            <div className="text-sm border-b border-white/10 pb-2 mb-2">
              <span className="text-gray-400">Subject:</span> {template.subject}
            </div>
            <pre className="text-sm text-gray-200 whitespace-pre-wrap font-sans">{template.body}</pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

