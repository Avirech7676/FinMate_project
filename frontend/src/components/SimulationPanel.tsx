import { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { Calculator, CheckCircle2, AlertTriangle, XCircle, Sparkles } from 'lucide-react';

export default function SimulationPanel() {
  const auth = useContext(AuthContext);
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('shopping');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const currencySymbol = auth?.user?.currency_symbol || '$';

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || Number(amount) <= 0) return;

    try {
      setLoading(true);
      setError(null);
      const res = await axios.post(
        `${API_URL}/api/v1/simulation/purchase`,
        {
          purchase_amount: Number(amount),
          purchase_category: category,
          description: description || undefined
        },
        {
          headers: { Authorization: `Bearer ${auth?.token}` }
        }
      );
      setResult(res.data);
    } catch (err: any) {
      console.error('Simulation error:', err);
      setError('Unable to run purchase simulation. Please ensure input values are valid.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 rounded-2xl border border-white/10">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white shadow-lg">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Financial What-If Purchase Simulator</h2>
            <p className="text-xs text-gray-400">
              Deterministic simulation testing how an intended expense affects your monthly budget, goals, and 30-day cash flow.
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-300 p-3 rounded-xl text-xs mt-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSimulate} className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Purchase Amount ({currencySymbol})</label>
            <input
              type="number"
              step="0.01"
              required
              placeholder="e.g. 250.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-gray-900 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-400"
            >
              <option value="shopping">Shopping</option>
              <option value="electronics">Electronics & Tech</option>
              <option value="travel">Travel & Vacation</option>
              <option value="entertainment">Entertainment</option>
              <option value="food">Dining & Food</option>
              <option value="housing">Housing & Home</option>
              <option value="other">Other Discretionary</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Item Description (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Noise Cancelling Headphones"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium py-2.5 px-4 rounded-xl transition shadow-lg flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              {loading ? 'Simulating...' : (
                <>
                  <Sparkles className="w-4 h-4" /> Run Simulation
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Simulation Results Display */}
      {result && (
        <div className="space-y-6">
          {/* Verdict Banner */}
          <div className={`p-6 rounded-2xl border ${
            result.verdict === 'AFFORDABLE' 
              ? 'bg-emerald-500/10 border-emerald-500/30' 
              : result.verdict === 'PROCEED_WITH_CAUTION'
              ? 'bg-amber-500/10 border-amber-500/30'
              : 'bg-red-500/10 border-red-500/30'
          }`}>
            <div className="flex items-start gap-4">
              {result.verdict === 'AFFORDABLE' ? (
                <CheckCircle2 className="w-8 h-8 text-emerald-400 shrink-0" />
              ) : result.verdict === 'PROCEED_WITH_CAUTION' ? (
                <AlertTriangle className="w-8 h-8 text-amber-400 shrink-0" />
              ) : (
                <XCircle className="w-8 h-8 text-red-400 shrink-0" />
              )}
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-white">Verdict: {result.verdict.replace(/_/g, ' ')}</h3>
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-white/10 uppercase">
                    Risk Level: {result.risk_level}
                  </span>
                </div>
                <p className="text-sm text-gray-200 mt-1">{result.recommendation}</p>
              </div>
            </div>
          </div>

          {/* Breakdown Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Budget Impact */}
            <div className="glass-card p-6 rounded-2xl border border-white/10 space-y-4">
              <h4 className="text-sm font-semibold text-white">Monthly Budget Impact</h4>
              <div className="space-y-3">
                <div className="flex justify-between text-xs text-gray-300">
                  <span>Current Utilization</span>
                  <span className="font-semibold">{result.budget_impact.current_utilization_pct}%</span>
                </div>
                <div className="flex justify-between text-xs text-gray-300">
                  <span>Post-Purchase Utilization</span>
                  <span className="font-bold text-cyan-400">{result.budget_impact.post_utilization_pct}%</span>
                </div>
                <div className="w-full bg-white/10 h-2.5 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all ${
                      result.budget_impact.post_utilization_pct > 100 ? 'bg-red-500' : 'bg-gradient-to-r from-cyan-400 to-blue-500'
                    }`}
                    style={{ width: `${Math.min(100, result.budget_impact.post_utilization_pct)}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400 pt-2 border-t border-white/10">
                  <span>Total Spent After Purchase:</span>
                  <span className="text-white font-medium">
                    {currencySymbol}{result.budget_impact.post_purchase_spent.toLocaleString()} / {currencySymbol}{result.budget_impact.monthly_budget.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Cash Flow Runway */}
            <div className="glass-card p-6 rounded-2xl border border-white/10 space-y-4">
              <h4 className="text-sm font-semibold text-white">30-Day Cash Flow Projection</h4>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between text-gray-300">
                  <span>Projected End Balance (Before):</span>
                  <span className="font-medium text-white">{currencySymbol}{result.cash_flow_impact.current_projected_end_balance.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-gray-300">
                  <span>Projected End Balance (After):</span>
                  <span className="font-bold text-cyan-400">{currencySymbol}{result.cash_flow_impact.post_purchase_projected_end_balance.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-gray-300">
                  <span>Direct Outflow Impact:</span>
                  <span className="font-medium text-red-400">-{currencySymbol}{result.purchase_amount.toLocaleString()}</span>
                </div>
                <div className="pt-2 border-t border-white/10 flex justify-between text-xs">
                  <span className="text-gray-400">Post-Purchase Runway Status:</span>
                  <span className="font-semibold capitalize text-emerald-400">
                    {result.cash_flow_impact.post_purchase_risk_status} Risk
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
