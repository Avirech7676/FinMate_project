import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { TrendingUp, Calendar, Info, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function ForecastPanel() {
  const auth = useContext(AuthContext);
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const currencySymbol = auth?.user?.currency_symbol || '$';

  useEffect(() => {
    const fetchForecast = async () => {
      if (!auth?.token) return;
      try {
        setLoading(true);
        setError(null);
        const res = await axios.get(`${API_URL}/api/v1/analytics/forecast`, {
          headers: { Authorization: `Bearer ${auth.token}` }
        });
        setForecast(res.data);
      } catch (err: any) {
        console.error('Forecast fetch failed:', err);
        setError('Unable to calculate spending forecasts. Ensure transactions are loaded.');
      } finally {
        setLoading(false);
      }
    };

    fetchForecast();
  }, [auth?.token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mr-3"></div>
        <span>Generating multi-horizon Holt-Winters spending forecasts...</span>
      </div>
    );
  }

  const horizons = [
    { key: '7d', label: '7-Day Outlook', data: forecast?.['7d'] },
    { key: '30d', label: '30-Day Outlook', data: forecast?.['30d'] },
    { key: '90d', label: '90-Day Outlook', data: forecast?.['90d'] }
  ];

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 rounded-2xl border border-white/10">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white shadow-lg">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Spending & Cash Flow Forecasting</h2>
              <p className="text-xs text-gray-400">
                Statistical projections using exponential smoothing and historical category run-rates.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs bg-white/5 px-3 py-1.5 rounded-lg border border-white/10 text-gray-300">
            <span>Overall Trajectory:</span>
            <span className={`font-semibold capitalize flex items-center ${
              forecast?.trend_direction === 'up' ? 'text-orange-400' : 'text-emerald-400'
            }`}>
              {forecast?.trend_direction === 'up' ? (
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              ) : (
                <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
              )}
              {forecast?.trend_direction || 'Stable'}
            </span>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-300 p-3 rounded-xl text-xs mt-4">
            {error}
          </div>
        )}

        {/* Forecast Horizon Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-6">
          {horizons.map(({ key, label, data }) => (
            <div key={key} className="glass-card p-5 rounded-xl border border-white/10 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-cyan-300 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" /> {label}
                </span>
                <span className="text-[10px] text-gray-400 bg-white/5 px-2 py-0.5 rounded">
                  {key} horizon
                </span>
              </div>

              <div>
                <p className="text-xs text-gray-400">Projected Total Spending</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {currencySymbol}{Number(data?.projected_spending || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>

              <div className="pt-3 border-t border-white/10 space-y-2 text-xs">
                <div className="flex justify-between text-gray-300">
                  <span>Projected Savings:</span>
                  <span className={`font-medium ${Number(data?.expected_savings || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {currencySymbol}{Number(data?.expected_savings || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-gray-300">
                  <span>Daily Run-Rate:</span>
                  <span className="text-gray-400 font-medium">
                    {currencySymbol}{Number(data?.daily_run_rate || (data?.projected_spending || 0) / (key === '7d' ? 7 : key === '30d' ? 30 : 90)).toFixed(0)}/day
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Model Assumptions & Transparency Notice */}
        <div className="mt-6 p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 text-xs text-blue-200 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-blue-300">Forecast Assumptions & Limitations:</span>
            <p className="text-gray-400">
              Projections are computed using exponential smoothing over your rolling 120-day transaction history. 
              Estimates assume current recurring subscription rates and typical discretionary category velocity remain constant. 
              Unforeseen one-time expenses or income fluctuations may alter future outcomes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
