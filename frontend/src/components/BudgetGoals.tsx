import { useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { Plus, Trash2, Target } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function BudgetGoals() {
  const auth = useContext(AuthContext);
  const [goals, setGoals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    goal_type: 'savings',
    target_amount: '',
    deadline: ''
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchGoals();
  }, [auth?.token]);

  const fetchGoals = async () => {
    try {
      const res = await axios.get(`${API_URL}/goals`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setGoals(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.target_amount || !formData.deadline) {
      setError('All fields are required');
      return;
    }

    try {
      const res = await axios.post(`${API_URL}/goals`, formData, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setGoals([...goals, res.data]);
      setFormData({ goal_type: 'savings', target_amount: '', deadline: '' });
      setShowForm(false);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create goal');
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    try {
      await axios.delete(`${API_URL}/goals/${goalId}`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setGoals(goals.filter(g => g.goal_id !== goalId));
    } catch (err) {
      console.error(err);
    }
  };

  const goalIcons: Record<string, string> = {
    savings: '💰',
    debt_repayment: '📉',
    investment: '📈'
  };

  if (loading) {
    return <div className="glass-card p-6 text-center">Loading goals...</div>;
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Target className="w-5 h-5 text-cyan-400" />
            <h2 className="text-2xl font-bold">Budget Goals</h2>
          </div>
          <motion.button
            onClick={() => setShowForm(!showForm)}
            whileHover={{ scale: 1.05 }}
            className="glass-btn flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg text-white hover:shadow-lg transition"
          >
            <Plus size={18} /> New Goal
          </motion.button>
        </div>

        <AnimatePresence>
          {showForm && (
            <motion.form
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              onSubmit={handleCreateGoal}
              className="bg-white/5 p-4 rounded-lg mb-6 border border-white/10"
            >
              {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">Goal Type</label>
                  <select
                    value={formData.goal_type}
                    onChange={(e) => setFormData({ ...formData, goal_type: e.target.value })}
                    className="w-full px-4 py-2 rounded bg-white border border-gray-300 text-black focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="savings" className="text-black">Savings</option>
                    <option value="debt_repayment" className="text-black">Debt Repayment</option>
                    <option value="investment" className="text-black">Investment</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2">Target Amount ({auth?.user?.currency_symbol || '$'})</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.target_amount}
                      onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                      className="w-full px-4 py-2 rounded bg-white/10 border border-white/20 text-white"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold mb-2">Deadline</label>
                    <input
                      type="date"
                      value={formData.deadline}
                      onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                      className="w-full px-4 py-2 rounded bg-white/10 border border-white/20 text-white"
                      required
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-cyan-500 rounded text-white hover:bg-cyan-600 transition"
                  >
                    Create Goal
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-4 py-2 bg-white/10 rounded text-white hover:bg-white/20 transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.form>
          )}
        </AnimatePresence>

        <div className="grid gap-4">
          <AnimatePresence>
            {goals.length === 0 ? (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center text-gray-400 py-8">
                No goals yet. Create one to get started! 🎯
              </motion.p>
            ) : (
              goals.map((goal) => (
                <motion.div
                  key={goal.goal_id}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: 20, opacity: 0 }}
                  className="bg-gradient-to-r from-white/5 to-white/10 p-4 rounded-lg border border-white/20 hover:border-cyan-500/50 transition"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">{goalIcons[goal.goal_type]}</span>
                        <div>
                          <h3 className="font-semibold capitalize">{goal.goal_type.replace('_', ' ')}</h3>
                          <p className="text-xs text-gray-400">Deadline: {new Date(goal.deadline).toLocaleDateString()}</p>
                        </div>
                      </div>

                      <div className="mt-3">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm text-gray-300">Progress</span>
                          <span className="text-sm font-semibold">
                            {auth?.user?.currency_symbol || '$'}{goal.current_progress.toFixed(2)} / {auth?.user?.currency_symbol || '$'}{goal.target_amount.toFixed(2)}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(goal.current_progress / goal.target_amount) * 100}%` }}
                            transition={{ duration: 1 }}
                            className="h-full bg-gradient-to-r from-cyan-400 to-blue-500"
                          />
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          goal.status === 'active'
                            ? 'bg-green-500/20 text-green-300'
                            : goal.status === 'completed'
                            ? 'bg-blue-500/20 text-blue-300'
                            : 'bg-red-500/20 text-red-300'
                        }`}>
                          {goal.status.charAt(0).toUpperCase() + goal.status.slice(1)}
                        </span>
                        <button
                          onClick={() => handleDeleteGoal(goal.goal_id)}
                          className="text-red-400 hover:text-red-300 transition"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
