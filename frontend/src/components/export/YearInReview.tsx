import { motion } from 'framer-motion';
import { Calendar, TrendingUp, Award, DollarSign } from 'lucide-react';

interface YearInReviewData {
  year: number;
  totalSpent: number;
  topCategories: Array<{ name: string; amount: number; percentage: number }>;
  achievements: Array<{ title: string; icon: string; date: string }>;
  monthlyTrend: number[];
  savingsGoalsMet: number;
  totalGoals: number;
}

interface YearInReviewProps {
  data: YearInReviewData;
  onShare?: () => void;
  onDownload?: () => void;
}

export default function YearInReview({ data, onShare, onDownload }: YearInReviewProps) {
  const avgMonthlySpending = data.totalSpent / 12;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto space-y-8"
    >
      {/* Header */}
      <motion.div
        initial={{ scale: 0.9 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2 }}
        className="text-center glass-card p-8 rounded-2xl border border-white/10"
      >
        <Calendar className="w-16 h-16 text-cyan-400 mx-auto mb-4" />
        <h1 className="text-4xl font-bold text-white mb-2">{data.year} in Review</h1>
        <p className="text-gray-400">Your financial journey this year</p>
      </motion.div>

      {/* Total Spending */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-6 rounded-lg border border-white/10"
      >
        <div className="flex items-center gap-3 mb-4">
          <DollarSign className="w-6 h-6 text-green-400" />
          <h2 className="text-xl font-bold text-white">Total Spending</h2>
        </div>
        <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2">
          ${data.totalSpent.toLocaleString()}
        </div>
        <p className="text-gray-400">Average ${avgMonthlySpending.toFixed(0)}/month</p>
      </motion.div>

      {/* Top Categories */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-card p-6 rounded-lg border border-white/10"
      >
        <h2 className="text-xl font-bold text-white mb-4">Top Spending Categories</h2>
        <div className="space-y-3">
          {data.topCategories.slice(0, 3).map((category, index) => (
            <motion.div
              key={category.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold text-sm">
                  {index + 1}
                </div>
                <span className="font-medium text-white">{category.name}</span>
              </div>
              <div className="text-right">
                <div className="font-semibold text-white">${category.amount.toLocaleString()}</div>
                <div className="text-xs text-gray-400">{category.percentage}%</div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Achievements */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="glass-card p-6 rounded-lg border border-white/10"
      >
        <div className="flex items-center gap-3 mb-4">
          <Award className="w-6 h-6 text-yellow-400" />
          <h2 className="text-xl font-bold text-white">Achievements Unlocked</h2>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {data.achievements.slice(0, 4).map((achievement, index) => (
            <motion.div
              key={achievement.title}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.7 + index * 0.1 }}
              className="bg-white/5 p-3 rounded-lg text-center"
            >
              <div className="text-2xl mb-1">{achievement.icon}</div>
              <div className="text-sm font-medium text-white">{achievement.title}</div>
              <div className="text-xs text-gray-400">{achievement.date}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Goals Progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="glass-card p-6 rounded-lg border border-white/10"
      >
        <div className="flex items-center gap-3 mb-4">
          <TrendingUp className="w-6 h-6 text-purple-400" />
          <h2 className="text-xl font-bold text-white">Goals Achievement</h2>
        </div>
        <div className="text-center">
          <div className="text-4xl font-bold text-purple-400 mb-2">
            {data.savingsGoalsMet}/{data.totalGoals}
          </div>
          <p className="text-gray-400">Goals completed this year</p>
          <div className="mt-4 w-full bg-gray-700 rounded-full h-3">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(data.savingsGoalsMet / data.totalGoals) * 100}%` }}
              transition={{ delay: 0.9, duration: 1 }}
              className="h-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
            />
          </div>
        </div>
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="flex gap-4"
      >
        {onShare && (
          <button
            onClick={onShare}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-shadow"
          >
            Share Your Year
          </button>
        )}
        {onDownload && (
          <button
            onClick={onDownload}
            className="flex-1 px-6 py-3 border border-white/20 rounded-lg font-semibold hover:bg-white/10 transition-colors"
          >
            Download PDF
          </button>
        )}
      </motion.div>
    </motion.div>
  );
}