import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface CategoryComparison {
  category: string;
  userAmount: number;
  averageAmount: number;
  difference: number;
  percentDiff: number;
}

interface ComparisonViewProps {
  data: CategoryComparison[];
}

export default function ComparisonView({ data }: ComparisonViewProps) {
  // Show empty state if no data
  if (!data || data.length === 0) {
    return (
      <div className="glass-card p-6 rounded-lg border border-white/10">
        <h3 className="text-xl font-bold text-white mb-6">You vs. Average User</h3>
        <div className="text-center py-12">
          <div className="text-5xl mb-4">📈</div>
          <p className="text-gray-400">No comparison data available</p>
          <p className="text-sm text-gray-500 mt-2">Need more transaction data to compare</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 rounded-lg border border-white/10">
      <h3 className="text-xl font-bold text-white mb-6">You vs. Average User</h3>
      
      <div className="space-y-4">
        {data.map((item, index) => {
          const isAbove = item.userAmount > item.averageAmount;
          const maxAmount = Math.max(item.userAmount, item.averageAmount);
          
          return (
            <motion.div
              key={item.category}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{item.category}</span>
                <div className={`flex items-center gap-1 text-sm ${
                  isAbove ? 'text-orange-400' : 'text-green-400'
                }`}>
                  {isAbove ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {Math.abs(item.percentDiff).toFixed(0)}% {isAbove ? 'above' : 'below'} average
                </div>
              </div>
              
              <div className="space-y-2">
                {/* User bar */}
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-12">You</span>
                  <div className="flex-1 relative">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(item.userAmount / maxAmount) * 100}%` }}
                      transition={{ duration: 0.8, delay: index * 0.1 }}
                      className={`h-4 rounded ${isAbove ? 'bg-orange-500' : 'bg-green-500'}`}
                    />
                    <span className="absolute right-2 top-0 text-xs text-white font-medium leading-4">
                      ${item.userAmount.toFixed(0)}
                    </span>
                  </div>
                </div>
                
                {/* Average bar */}
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-12">Avg</span>
                  <div className="flex-1 relative">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(item.averageAmount / maxAmount) * 100}%` }}
                      transition={{ duration: 0.8, delay: index * 0.1 + 0.2 }}
                      className="h-4 rounded bg-gray-600"
                    />
                    <span className="absolute right-2 top-0 text-xs text-gray-300 font-medium leading-4">
                      ${item.averageAmount.toFixed(0)}
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
      
      <div className="mt-6 p-4 bg-white/5 rounded-lg">
        <p className="text-sm text-gray-400">
          Comparison based on anonymized data from similar users in your region
        </p>
      </div>
    </div>
  );
}