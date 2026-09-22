import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { 
  AlertTriangle, ShieldCheck, 
  ArrowUpRight, ArrowDownRight, Clock, CheckCircle2 
} from 'lucide-react';

export default function FinancialOverviewPanel() {
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [healthScore, setHealthScore] = useState<any>(null);
  const [cashflow, setCashflow] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      if (!auth?.token) return;
      try {
        setLoading(true);
        setError(null);
        const headers = { Authorization: `Bearer ${auth.token}` };

        const [ovRes, hsRes, cfRes, anomRes] = await Promise.allSettled([
          axios.get(`${API_URL}/api/v1/analytics/financial-overview`, { headers }),
          axios.get(`${API_URL}/api/v1/analytics/health-score/explainable`, { headers }),
          axios.get(`${API_URL}/api/v1/cashflow/projection`, { headers }),
          axios.get(`${API_URL}/api/v1/analytics/anomalies/layered?days=30`, { headers })
        ]);

        if (ovRes.status === 'fulfilled') setOverview(ovRes.value.data);
        if (hsRes.status === 'fulfilled') setHealthScore(hsRes.value.data);
        if (cfRes.status === 'fulfilled') setCashflow(cfRes.value.data);
        if (anomRes.status === 'fulfilled') setAnomalies(anomRes.value.data?.anomalies || []);
      } catch (err: any) {
        console.error('Failed to load financial overview:', err);
        setError('Unable to load full financial overview data. Some widgets may show fallback state.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [auth?.token]);

  const currencySymbol = auth?.user?.currency_symbol || '$';

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mr-3"></div>
        <span>Calculating financial metrics and health score...</span>
      </div>
    );
  }

  const income = overview?.monthly_income || 0;
  const spent = overview?.spending?.total_spent || 0;
  const surplus = income > 0 ? (income - spent) : 0;
  const savingsRate = income > 0 ? Math.round((surplus / income) * 100) : 0;

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-300 p-4 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Top Vital Financial Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-xl border border-white/10">
          <p className="text-xs text-gray-400 font-medium">Monthly Income</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">
              {currencySymbol}{income.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-green-400 flex items-center">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> Tracked
            </span>
          </div>
          <p className="text-[11px] text-gray-500 mt-1">From active financial profile</p>
        </div>

        <div className="glass-card p-5 rounded-xl border border-white/10">
          <p className="text-xs text-gray-400 font-medium">30-Day Spending</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold text-white">
              {currencySymbol}{spent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <span className="text-xs text-orange-400 flex items-center">
              <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" /> Outflow
            </span>
          </div>
          <p className="text-[11px] text-gray-500 mt-1">{overview?.spending?.transaction_count || 0} transactions</p>
        </div>

        <div className="glass-card p-5 rounded-xl border border-white/10">
          <p className="text-xs text-gray-400 font-medium">Net Savings Rate</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className={`text-2xl font-bold ${surplus >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
              {savingsRate}%
            </span>
            <span className={`text-xs ${surplus >= 0 ? 'text-cyan-300' : 'text-red-300'}`}>
              {currencySymbol}{surplus.toLocaleString(undefined, { minimumFractionDigits: 0 })}
            </span>
          </div>
          <p className="text-[11px] text-gray-500 mt-1">Target baseline: ≥ 20%</p>
        </div>

        <div className="glass-card p-5 rounded-xl border border-white/10">
          <p className="text-xs text-gray-400 font-medium">Cash Flow Risk</p>
          <div className="flex items-baseline justify-between mt-2">
            <span className={`text-2xl font-bold capitalize ${
              cashflow?.cash_flow_risk === 'low' ? 'text-emerald-400' :
              cashflow?.cash_flow_risk === 'moderate' ? 'text-amber-400' : 'text-red-400'
            }`}>
              {cashflow?.cash_flow_risk || 'Optimal'}
            </span>
            <span className="text-xs text-gray-400">30-day projection</span>
          </div>
          <p className="text-[11px] text-gray-500 mt-1">
            Proj. cashflow: {currencySymbol}{Number(cashflow?.projected_cash_flow || 0).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Health Score Breakdown Card */}
      {healthScore && (
        <div className="glass-card p-6 rounded-2xl border border-white/10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
            <div className="flex items-center gap-4">
              <div 
                className="w-16 h-16 rounded-2xl flex items-center justify-center font-bold text-2xl shadow-lg border border-white/20"
                style={{ backgroundColor: `${healthScore.color}20`, color: healthScore.color }}
              >
                {healthScore.overall_score}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">Explainable Financial Health Score</h3>
                  <span 
                    className="text-xs px-2.5 py-0.5 rounded-full font-semibold border"
                    style={{ 
                      borderColor: `${healthScore.color}40`,
                      backgroundColor: `${healthScore.color}15`,
                      color: healthScore.color 
                    }}
                  >
                    {healthScore.label}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">Multi-factor algorithmic assessment across 5 key pillars</p>
              </div>
            </div>

            {/* Positive/Negative Drivers */}
            <div className="space-y-1 text-xs">
              {(healthScore.reasons_for_changes || []).slice(0, 2).map((reason: string, idx: number) => (
                <div key={idx} className="flex items-center gap-1.5 text-gray-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Component Score Bars */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-6">
            {Object.entries(healthScore.component_scores || {}).map(([key, comp]: [string, any]) => (
              <div key={key} className="bg-white/5 p-3.5 rounded-xl border border-white/5 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-300 capitalize font-medium">
                    {key.replace('_', ' ')}
                  </span>
                  <span className="font-bold text-cyan-400">{comp.score}/100</span>
                </div>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full rounded-full" 
                    style={{ width: `${Math.min(100, Math.max(5, comp.score))}%` }}
                  />
                </div>
                <p className="text-[11px] text-gray-400 leading-tight">{comp.description}</p>
              </div>
            ))}
          </div>

          {/* Disclaimer */}
          <p className="text-[10px] text-gray-500 mt-5 italic">
            {healthScore.disclaimer}
          </p>
        </div>
      )}

      {/* Financial Timeline & Detected Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              Financial Events Timeline
            </h3>
            <span className="text-xs text-gray-400">Current cycle</span>
          </div>

          <div className="relative pl-6 border-l border-white/10 space-y-6 my-2">
            <div className="relative">
              <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-green-500 border-2 border-gray-900" />
              <div className="text-xs text-gray-400">1st of Month</div>
              <div className="text-sm font-semibold text-white">Monthly Salary Deposited</div>
              <p className="text-xs text-gray-400">Income benchmark: {currencySymbol}{income.toLocaleString()}</p>
            </div>

            <div className="relative">
              <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-cyan-500 border-2 border-gray-900" />
              <div className="text-xs text-gray-400">Recurring Bills Cycle</div>
              <div className="text-sm font-semibold text-white">Active Subscriptions & Fixed Obligations</div>
              <p className="text-xs text-gray-400">
                {cashflow?.detected_subscriptions_count || 0} subscriptions tracked
              </p>
            </div>

            {anomalies.slice(0, 2).map((a, idx) => (
              <div key={idx} className="relative">
                <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-amber-500 border-2 border-gray-900" />
                <div className="text-xs text-amber-400">Spending Spike Detected</div>
                <div className="text-sm font-semibold text-white">{a.reason}</div>
                <p className="text-xs text-gray-400">{a.evidence}</p>
              </div>
            ))}

            <div className="relative">
              <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-blue-500 border-2 border-gray-900" />
              <div className="text-xs text-gray-400">30-Day Forward Projection</div>
              <div className="text-sm font-semibold text-white">Projected End Balance</div>
              <p className="text-xs text-cyan-300">
                Estimated reserve: {currencySymbol}{Number(cashflow?.balance_projection_30d?.slice(-1)[0]?.projected_balance || 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Signals and Anomalies Panel */}
        <div className="glass-card p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Active Signals & Anomalies
          </h3>

          {anomalies.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">
              <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              No spending anomalies detected in the past 30 days.
            </div>
          ) : (
            <div className="space-y-3">
              {anomalies.slice(0, 4).map((a, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-white/5 border border-white/5 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-amber-300 capitalize">{a.level || 'Anomaly'}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                      Score: {a.anomaly_score}
                    </span>
                  </div>
                  <p className="text-gray-300">{a.reason}</p>
                  <p className="text-gray-500 text-[11px]">{a.evidence}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
