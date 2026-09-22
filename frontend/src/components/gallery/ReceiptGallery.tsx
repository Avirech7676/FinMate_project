import { motion } from 'framer-motion';
import { Search, Download, Trash2 } from 'lucide-react';
import { useState } from 'react';

interface Receipt {
  id: number;
  merchant: string;
  amount: number;
  date: string;
  thumbnail?: string;
}

interface ReceiptGalleryProps {
  receipts: Receipt[];
  onSearch?: (query: string) => void;
  onDelete?: (id: number) => void;
}

export default function ReceiptGallery({ receipts, onSearch, onDelete }: ReceiptGalleryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date');

  const filteredReceipts = receipts
    .filter((r) => r.merchant.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      }
      return b.amount - a.amount;
    });

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    onSearch?.(query);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white">Receipt Gallery</h3>
          <p className="text-gray-400 text-sm mt-1">
            {receipts.length} receipts scanned
          </p>
        </div>
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring' }}
          className="text-center"
        >
          <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            {receipts.length}
          </div>
          <p className="text-xs text-gray-400">Total Scanned</p>
        </motion.div>
      </div>

      {/* Search and Sort */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by merchant..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none transition"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'date' | 'amount')}
          className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none transition"
        >
          <option value="date">Newest First</option>
          <option value="amount">Highest Amount</option>
        </select>
      </div>

      {/* Gallery Grid */}
      {filteredReceipts.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ staggerChildren: 0.05 }}
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          {filteredReceipts.map((receipt, index) => (
            <motion.div
              key={receipt.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ y: -4 }}
              className="group relative glass-card rounded-lg overflow-hidden border border-white/10 hover:border-white/20 transition-all cursor-pointer"
            >
              {/* Placeholder thumbnail */}
              <div className="aspect-square bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center relative">
                <div className="text-center">
                  <div className="text-3xl font-bold text-cyan-400 mb-1">
                    ${receipt.amount.toFixed(0)}
                  </div>
                  <p className="text-xs text-gray-400 truncate px-2">{receipt.merchant}</p>
                </div>

                {/* Overlay on hover */}
                <motion.div
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                  transition={{ duration: 0.2 }}
                  className="absolute inset-0 bg-black/60 flex items-center justify-center gap-2"
                >
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition"
                  >
                    <Download className="w-4 h-4 text-white" />
                  </motion.button>
                  {onDelete && (
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => onDelete(receipt.id)}
                      className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg transition"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </motion.button>
                  )}
                </motion.div>
              </div>

              {/* Info */}
              <div className="p-3 bg-white/[0.02]">
                <p className="text-xs font-medium text-white truncate">{receipt.merchant}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(receipt.date).toLocaleDateString()}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <p className="text-gray-400">
            {searchQuery ? 'No receipts found' : 'No receipts yet. Start scanning!'}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}
