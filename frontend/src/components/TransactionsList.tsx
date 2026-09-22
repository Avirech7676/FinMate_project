import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, Edit2, Search, X, Check, CheckSquare, Square, Filter } from 'lucide-react';

interface Transaction {
  transaction_id: number;
  amount: number;
  description: string;
  category: string;
  date: string;
  source: string;
}

const CATEGORIES = ['Food', 'Transportation', 'Entertainment', 'Utilities', 'Healthcare', 'Shopping', 'Housing', 'Other'];

export default function TransactionsList() {
  const auth = useContext(AuthContext);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ amount: '', description: '', category: '', date: '' });
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null);

  const fetchTransactions = async () => {
    try {
      const allRes = await axios.get(`${API_URL}/transactions`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setTransactions(allRes.data || []);
      setFilteredTransactions(allRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (auth?.token) fetchTransactions();
  }, [auth?.token]);

  useEffect(() => {
    let filtered = transactions.filter(t =>
      t.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.category.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    // Apply category filter
    if (selectedCategories.size > 0) {
      filtered = filtered.filter(t => selectedCategories.has(t.category.toLowerCase()));
    }
    
    setFilteredTransactions(filtered);
  }, [searchQuery, transactions, selectedCategories]);

  const toggleCategory = (category: string) => {
    const newSelected = new Set(selectedCategories);
    const lowerCategory = category.toLowerCase();
    if (newSelected.has(lowerCategory)) {
      newSelected.delete(lowerCategory);
    } else {
      newSelected.add(lowerCategory);
    }
    setSelectedCategories(newSelected);
  };

  const clearCategoryFilter = () => {
    setSelectedCategories(new Set());
    setShowCategoryFilter(false);
  };

  const handleRowClick = (id: number, index: number, event: React.MouseEvent) => {
    if (editingId) return; // Don't select while editing

    if (event.shiftKey && lastSelectedIndex !== null) {
      // Shift+Click: Select range
      const start = Math.min(lastSelectedIndex, index);
      const end = Math.max(lastSelectedIndex, index);
      const newSelected = new Set(selectedIds);
      for (let i = start; i <= end; i++) {
        newSelected.add(filteredTransactions[i].transaction_id);
      }
      setSelectedIds(newSelected);
    } else if (event.ctrlKey || event.metaKey) {
      // Ctrl/Cmd+Click: Toggle individual
      const newSelected = new Set(selectedIds);
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      setSelectedIds(newSelected);
      setLastSelectedIndex(index);
    } else {
      // Regular click: Select only this one
      setSelectedIds(new Set([id]));
      setLastSelectedIndex(index);
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.size === filteredTransactions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredTransactions.map(t => t.transaction_id)));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return;
    
    const count = selectedIds.size;
    if (!confirm(`Delete ${count} transaction${count > 1 ? 's' : ''}?`)) return;

    try {
      await Promise.all(
        Array.from(selectedIds).map(id =>
          axios.delete(`${API_URL}/transactions/${id}`, {
            headers: { Authorization: `Bearer ${auth?.token}` }
          })
        )
      );
      setTransactions(transactions.filter(t => !selectedIds.has(t.transaction_id)));
      setSelectedIds(new Set());
    } catch (err) {
      console.error(err);
      alert('Failed to delete some transactions');
    }
  };

  const startEdit = (t: Transaction, event: React.MouseEvent) => {
    event.stopPropagation();
    setEditingId(t.transaction_id);
    setEditForm({
      amount: t.amount.toString(),
      description: t.description,
      category: t.category,
      date: t.date
    });
  };

  const handleUpdate = async (id: number) => {
    try {
      await axios.put(`${API_URL}/transactions/${id}`, {
        ...editForm,
        amount: parseFloat(editForm.amount)
      }, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setTransactions(transactions.map(t =>
        t.transaction_id === id ? { ...t, ...editForm, amount: parseFloat(editForm.amount) } : t
      ));
      setEditingId(null);
    } catch (err) {
      console.error(err);
      alert('Failed to update transaction');
    }
  };

  if (loading) {
    return (
      <div className="glass-card p-8 rounded-2xl text-center">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto"></div>
        <p className="text-gray-400 mt-4">Loading transactions...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        {/* Search & Filter */}
        <div className="flex gap-2 flex-1 max-w-2xl">
          <div className="glass-card p-3 rounded-xl flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search transactions..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-transparent border-none pl-10 pr-3 py-1 text-sm outline-none"
              />
            </div>
          </div>
          
          {/* Category Filter Button */}
          <button
            onClick={() => setShowCategoryFilter(!showCategoryFilter)}
            className={`glass-card p-3 rounded-xl hover:bg-white/10 transition ${
              selectedCategories.size > 0 ? 'bg-cyan-500/20 text-cyan-400' : ''
            }`}
          >
            <Filter className="w-4 h-4" />
          </button>
        </div>

        {/* Bulk Actions */}
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-3 rounded-xl flex items-center gap-3"
          >
            <span className="text-sm text-gray-400">{selectedIds.size} selected</span>
            <button
              onClick={handleDeleteSelected}
              className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition text-sm"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
            <button
              onClick={() => setSelectedIds(new Set())}
              className="p-1.5 hover:bg-white/10 rounded text-gray-400"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </div>

      {/* Category Filter Popup */}
      <AnimatePresence>
        {showCategoryFilter && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-card p-4 rounded-xl"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-sm">Filter by Category</h4>
              <button
                onClick={() => setShowCategoryFilter(false)}
                className="p-1 hover:bg-white/10 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map(cat => {
                const lowerCat = cat.toLowerCase();
                const isSelected = selectedCategories.has(lowerCat);
                return (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition ${
                      isSelected
                        ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/50'
                        : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                    }`}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>
            {selectedCategories.size > 0 && (
              <button
                onClick={clearCategoryFilter}
                className="mt-3 text-xs text-gray-400 hover:text-white transition"
              >
                Clear filters
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Help Text */}
      <div className="text-xs text-gray-500 bg-blue-500/10 border border-blue-500/20 rounded-lg p-2">
        💡 <strong>Tip:</strong> Click to select, Ctrl+Click for multiple, Shift+Click for range
      </div>

      {/* Transactions Table */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-white/5 border-b border-white/10">
              <tr>
                <th className="p-4 w-12">
                  <button
                    onClick={handleSelectAll}
                    className="hover:bg-white/10 rounded p-1 transition"
                  >
                    {selectedIds.size === filteredTransactions.length && filteredTransactions.length > 0 ? (
                      <CheckSquare className="w-4 h-4 text-cyan-400" />
                    ) : (
                      <Square className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                </th>
                <th className="text-left p-4 text-xs font-semibold text-gray-400 uppercase">Date</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-400 uppercase">Description</th>
                <th className="text-left p-4 text-xs font-semibold text-gray-400 uppercase">Category</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-400 uppercase">Amount</th>
                <th className="text-right p-4 text-xs font-semibold text-gray-400 uppercase w-24">Actions</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filteredTransactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center p-8 text-gray-400">
                      {searchQuery ? 'No transactions found' : 'No transactions yet. Add one to get started!'}
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((t, i) => (
                    <motion.tr
                      key={t.transaction_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ delay: i * 0.02 }}
                      onClick={(e) => handleRowClick(t.transaction_id, i, e)}
                      className={`border-b border-white/5 hover:bg-white/5 transition cursor-pointer ${
                        selectedIds.has(t.transaction_id) ? 'bg-cyan-500/10' : ''
                      }`}
                    >
                      <td className="p-4" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const newSelected = new Set(selectedIds);
                            if (newSelected.has(t.transaction_id)) {
                              newSelected.delete(t.transaction_id);
                            } else {
                              newSelected.add(t.transaction_id);
                            }
                            setSelectedIds(newSelected);
                          }}
                          className="hover:bg-white/10 rounded p-1 transition"
                        >
                          {selectedIds.has(t.transaction_id) ? (
                            <CheckSquare className="w-4 h-4 text-cyan-400" />
                          ) : (
                            <Square className="w-4 h-4 text-gray-400" />
                          )}
                        </button>
                      </td>
                      {editingId === t.transaction_id ? (
                        <>
                          <td className="p-4" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="date"
                              value={editForm.date}
                              onChange={e => setEditForm({ ...editForm, date: e.target.value })}
                              className="bg-white/10 border border-white/20 rounded px-2 py-1 text-xs w-full"
                            />
                          </td>
                          <td className="p-4" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="text"
                              value={editForm.description}
                              onChange={e => setEditForm({ ...editForm, description: e.target.value })}
                              className="bg-white/10 border border-white/20 rounded px-2 py-1 text-xs w-full"
                            />
                          </td>
                          <td className="p-4" onClick={(e) => e.stopPropagation()}>
                            <select
                              value={editForm.category}
                              onChange={e => setEditForm({ ...editForm, category: e.target.value })}
                              className="bg-white/10 border border-white/20 rounded px-2 py-1 text-xs w-full"
                            >
                              {CATEGORIES.map(c => <option key={c} value={c.toLowerCase()}>{c}</option>)}
                            </select>
                          </td>
                          <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="number"
                              step="0.01"
                              value={editForm.amount}
                              onChange={e => setEditForm({ ...editForm, amount: e.target.value })}
                              className="bg-white/10 border border-white/20 rounded px-2 py-1 text-xs w-24 text-right"
                            />
                          </td>
                          <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={() => handleUpdate(t.transaction_id)}
                                className="p-1.5 hover:bg-green-500/20 rounded text-green-400 transition"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="p-1.5 hover:bg-red-500/20 rounded text-red-400 transition"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="p-4 text-sm">{new Date(t.date).toLocaleDateString()}</td>
                          <td className="p-4 text-sm font-medium">{t.description}</td>
                          <td className="p-4">
                            <span className="inline-block px-2 py-1 bg-cyan-500/20 text-cyan-300 rounded text-xs capitalize">
                              {t.category}
                            </span>
                          </td>
                          <td className="p-4 text-right text-sm font-semibold">${t.amount.toFixed(2)}</td>
                          <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={(e) => startEdit(t, e)}
                                className="p-1.5 hover:bg-blue-500/20 rounded text-blue-400 transition"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </>
                      )}
                    </motion.tr>
                  ))
                )}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      {filteredTransactions.length > 0 && (
        <div className="glass-card p-4 rounded-xl flex justify-between items-center">
          <span className="text-sm text-gray-400">
            Showing {filteredTransactions.length} transaction{filteredTransactions.length !== 1 ? 's' : ''}
            {selectedCategories.size > 0 && ` in ${selectedCategories.size} categor${selectedCategories.size > 1 ? 'ies' : 'y'}`}
          </span>
          <div className="flex items-center gap-4">
            {selectedIds.size > 0 && (
              <span className="text-sm text-cyan-400">
                Selected: ${filteredTransactions
                  .filter(t => selectedIds.has(t.transaction_id))
                  .reduce((sum, t) => sum + t.amount, 0)
                  .toFixed(2)}
              </span>
            )}
            <span className="text-sm font-semibold">
              Total: ${filteredTransactions.reduce((sum, t) => sum + t.amount, 0).toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
