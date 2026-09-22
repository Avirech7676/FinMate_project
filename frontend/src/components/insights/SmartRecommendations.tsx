import { motion } from 'framer-motion';
import { Lightbulb, Check } from 'lucide-react';

interface Recommendation {
  id: string;
  title: string;
  description: string;
  potentialSavings: number;
  category: string;
  actionText?: string;
}

interface SmartRecommendationsProps {
  recommendations: Recommendation[];
  onDismiss?: (id: string) => void;
  onAccept?: (id: string) => void;
}

export default function SmartRecommendations({
  recommendations,
  onDismiss,
  onAccept,
}: SmartRecommendationsProps) {
  if (recommendations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="glass-card p-8 rounded-lg border border-white/10 text-center"
      >
        <p className="text-gray-400">No recommendations yet. Keep tracking to get personalized suggestions!</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-4"
    >
      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <Lightbulb className="w-5 h-5 text-yellow-400" />
        Smart Recommendations
      </h3>

      {recommendations.map((rec, index) => (
        <motion.div
          key={rec.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ x: 4 }}
          className="glass-card p-4 rounded-lg border border-white/10 hover:border-white/20 transition-all group"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-semibold text-white text-sm">{rec.title}</p>
                <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400 font-medium">
                  Save ${rec.potentialSavings.toFixed(0)}/mo
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-3">{rec.description}</p>

              {/* Action buttons */}
              <div className="flex gap-2">
                {onAccept && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onAccept(rec.id)}
                    className="flex items-center gap-1 text-xs px-3 py-1.5 bg-green-500/20 text-green-400 hover:bg-green-500/30 rounded-lg transition font-medium"
                  >
                    <Check className="w-3 h-3" />
                    {rec.actionText || 'Apply'}
                  </motion.button>
                )}
                {onDismiss && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onDismiss(rec.id)}
                    className="text-xs px-3 py-1.5 bg-white/5 text-gray-400 hover:bg-white/10 rounded-lg transition font-medium"
                  >
                    Dismiss
                  </motion.button>
                )}
              </div>
            </div>

            {/* Category badge */}
            <div className="flex-shrink-0 text-right">
              <span className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">
                {rec.category}
              </span>
            </div>
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
