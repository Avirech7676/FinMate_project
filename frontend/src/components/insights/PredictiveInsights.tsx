import { motion } from 'framer-motion';
import { AlertTriangle, TrendingUp, Calendar, Zap } from 'lucide-react';

interface Insight {
  id: string;
  type: 'overspend' | 'pattern' | 'opportunity';
  title: string;
  message: string;
  confidence: 'high' | 'medium' | 'low';
  predictedDate?: string;
  amount?: number;
}

interface PredictiveInsightsProps {
  insights: Insight[];
}

const insightConfig = {
  overspend: {
    icon: AlertTriangle,
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
  },
  pattern: {
    icon: TrendingUp,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
  opportunity: {
    icon: Zap,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
  },
};

const confidenceConfig = {
  high: { label: 'High Confidence', color: 'text-green-400' },
  medium: { label: 'Medium Confidence', color: 'text-yellow-400' },
  low: { label: 'Low Confidence', color: 'text-gray-400' },
};

export default function PredictiveInsights({ insights }: PredictiveInsightsProps) {
  if (insights.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="glass-card p-8 rounded-lg border border-white/10 text-center"
      >
        <p className="text-gray-400">No predictive insights yet. Keep tracking your spending!</p>
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
      <h3 className="text-xl font-bold text-white mb-4">Predictive Insights</h3>

      {insights.map((insight, index) => {
        const config = insightConfig[insight.type];
        const Icon = config.icon;
        const confidenceLabel = confidenceConfig[insight.confidence];

        return (
          <motion.div
            key={insight.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ x: 4 }}
            className={`${config.bg} ${config.border} border rounded-lg p-4 group hover:border-opacity-50 transition-all`}
          >
            <div className="flex items-start gap-3">
              <Icon className={`w-5 h-5 ${config.color} flex-shrink-0 mt-0.5`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p className={`font-semibold text-sm ${config.color}`}>{insight.title}</p>
                  <span className={`text-xs font-medium ${confidenceLabel.color} whitespace-nowrap`}>
                    {confidenceLabel.label}
                  </span>
                </div>
                <p className="text-gray-400 text-sm mb-2">{insight.message}</p>

                {/* Details */}
                <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                  {insight.amount && (
                    <div className="flex items-center gap-1">
                      <span className="text-gray-600">Amount:</span>
                      <span className={config.color}>
                        ${insight.amount.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {insight.predictedDate && (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{new Date(insight.predictedDate).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </motion.div>
  );
}
