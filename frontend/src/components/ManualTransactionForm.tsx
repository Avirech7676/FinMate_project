import { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { PlusCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  onSuccess?: () => void;
}

const CATEGORIES = ['Food', 'Transportation', 'Entertainment', 'Utilities', 'Healthcare', 'Shopping', 'Housing', 'Other'];

export default function ManualTransactionForm({ onSuccess }: Props) {
  const auth = useContext(AuthContext);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const [form, setForm] = useState({
    amount: '',
    description: '',
    category: 'Food',
    date: new Date().toISOString().split('T')[0],
    source: 'manual'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_URL}/transactions`, {
        ...form,
        amount: parseFloat(form.amount)
      }, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setSuccess(true);
      setForm({ amount: '', description: '', category: 'Food', date: new Date().toISOString().split('T')[0], source: 'manual' });
      onSuccess?.();
      setTimeout(() => {
        setSuccess(false);
        setIsOpen(false);
      }, 1500);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-5 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-24 h-24 bg-[--color-accent-purple] opacity-[0.15] blur-3xl rounded-full"></div>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left group"
      >
        <span className="font-semibold flex items-center gap-2">
          <PlusCircle className="w-5 h-5 text-[--color-accent-purple]" />
          Add Transaction
        </span>
        <span className={`text-[--color-text-muted] text-xl transition-transform duration-300 ${isOpen ? 'rotate-45' : ''}`}>+</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.form
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            onSubmit={handleSubmit}
            className="overflow-hidden"
          >
            <div className="pt-5 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[--color-text-secondary] mb-1">Amount ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    min="0"
                    placeholder="0.00"
                    value={form.amount}
                    onChange={e => setForm({ ...form, amount: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-[--color-accent-purple] transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs text-[--color-text-secondary] mb-1">Date</label>
                  <input
                    type="date"
                    required
                    value={form.date}
                    onChange={e => setForm({ ...form, date: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-[--color-accent-purple] transition-colors"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-[--color-text-secondary] mb-1">Category</label>
                <select
                  value={form.category}
                  onChange={e => setForm({ ...form, category: e.target.value })}
                  className="w-full bg-[#0d1220] border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-[--color-accent-purple] transition-colors"
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-[--color-text-secondary] mb-1">Description</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Lunch at Subway"
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm outline-none focus:border-[--color-accent-purple] transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={loading || success}
                className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-all flex items-center justify-center gap-2 ${
                  success
                    ? 'bg-green-500/20 text-[--color-accent-green] border border-green-500/30'
                    : 'bg-gradient-to-r from-[--color-accent-blue] to-[--color-accent-purple] text-white hover:opacity-90'
                }`}
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {success ? '✓ Saved!' : loading ? 'Saving...' : 'Add Transaction'}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
