import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { FileText, Download, Sparkles, CheckCircle2, Calendar } from 'lucide-react';

export default function ReportBriefingPanel() {
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [briefing, setBriefing] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const currencySymbol = auth?.user?.currency_symbol || '$';

  useEffect(() => {
    const fetchBriefing = async () => {
      if (!auth?.token) return;
      try {
        setLoading(true);
        setError(null);
        const res = await axios.get(`${API_URL}/api/v1/analytics/briefing/weekly`, {
          headers: { Authorization: `Bearer ${auth.token}` }
        });
        setBriefing(res.data);
      } catch (err: any) {
        console.error('Failed to load weekly briefing:', err);
        setError('Unable to assemble weekly briefing.');
      } finally {
        setLoading(false);
      }
    };

    fetchBriefing();
  }, [auth?.token]);

  const handleDownloadReport = () => {
    if (!auth?.token) return;
    window.open(`${API_URL}/api/v1/analytics/report/download?token=${auth.token}`, '_blank');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mr-3"></div>
        <span>Synthesizing weekly financial briefing...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 rounded-2xl border border-white/10 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white shadow-lg">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Financial Reports & AI Weekly Briefing</h2>
            <p className="text-xs text-gray-400">
              Deterministic period summaries, spending changes, and exportable intelligence reports.
            </p>
          </div>
        </div>

        <button
          onClick={handleDownloadReport}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium py-2 px-4 rounded-xl transition shadow-lg flex items-center gap-2 text-xs"
        >
          <Download className="w-4 h-4" /> Download Full Report (PDF / Print)
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-300 p-3 rounded-xl text-xs">
          {error}
        </div>
      )}

      {briefing && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Briefing Card */}
          <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-white/10 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <span className="text-xs font-semibold text-cyan-300 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> 7-Day Cycle Summary ({briefing.period?.start} → {briefing.period?.end})
              </span>
              <span className="text-xs text-gray-400">
                Week-over-week: <span className={briefing.spending?.week_over_week_change_pct > 0 ? 'text-orange-400' : 'text-emerald-400 font-semibold'}>
                  {briefing.spending?.week_over_week_change_pct > 0 ? '+' : ''}{briefing.spending?.week_over_week_change_pct}%
                </span>
              </span>
            </div>

            {/* Vital Stats */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                <p className="text-xs text-gray-400">Past 7 Days Spent</p>
                <p className="text-xl font-bold text-white mt-1">
                  {currencySymbol}{Number(briefing.spending?.this_week_spent || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white/5 p-4 rounded-xl border border-white/5">
                <p className="text-xs text-gray-400">Prior Week Spent</p>
                <p className="text-xl font-bold text-gray-300 mt-1">
                  {currencySymbol}{Number(briefing.spending?.prior_week_spent || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white/5 p-4 rounded-xl border border-white/5 col-span-2 md:col-span-1">
                <p className="text-xs text-gray-400">Month-to-Date Total</p>
                <p className="text-xl font-bold text-cyan-400 mt-1">
                  {currencySymbol}{Number(briefing.budget_status?.month_to_date_spent || 0).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Top Categories */}
            <div>
              <h4 className="text-xs font-semibold text-gray-300 mb-3 uppercase tracking-wider">
                Largest Spending Categories This Cycle
              </h4>
              <div className="space-y-2">
                {(briefing.largest_categories || []).map((c: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center text-xs p-2.5 rounded-lg bg-white/5">
                    <span className="capitalize text-gray-200 font-medium">{c.category}</span>
                    <span className="text-white font-bold">{currencySymbol}{c.amount.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Actionable Suggestions */}
            <div>
              <h4 className="text-xs font-semibold text-gray-300 mb-3 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Actionable Intelligence Suggestions
              </h4>
              <div className="space-y-2">
                {(briefing.actionable_suggestions || []).map((s: string, idx: number) => (
                  <div key={idx} className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-200 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Side Panel: Active Goals & Anomaly Watch */}
          <div className="space-y-6">
            <div className="glass-card p-6 rounded-2xl border border-white/10 space-y-4">
              <h4 className="text-sm font-semibold text-white">Active Goals Pacing</h4>
              <div className="space-y-3">
                {(briefing.goal_progress || []).slice(0, 3).map((g: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-xl bg-white/5 border border-white/5 text-xs space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-white">Goal #{g.goal_id}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        g.status === 'ON_TRACK' || g.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                      }`}>
                        {g.status}
                      </span>
                    </div>
                    <p className="text-gray-400">{currencySymbol}{g.current_progress} of {currencySymbol}{g.target_amount}</p>
                    <p className="text-gray-500 text-[11px]">{g.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
