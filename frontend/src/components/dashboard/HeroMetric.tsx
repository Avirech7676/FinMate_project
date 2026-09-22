import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface HeroMetricProps {
  value: number;
  label: string;
  comparison?: {
    value: number;
    trend: 'up' | 'down' | 'neutral';
    period: string;
  };
  animate?: boolean;
}

export default function HeroMetric({ value, label, comparison, animate = true }: HeroMetricProps) {
  const isPositive = comparison?.trend === 'down'; // Down is good for spending

  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 20 } : {}}
      animate={animate ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.8 }}
      className="glass-card p-8 md:p-12 rounded-2xl border border-white/10 overflow-hidden relative"
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 pointer-events-none" />

      <div className="relative z-10">
        <p className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">{label}</p>

        {/* Main metric */}
        <motion.div
          initial={animate ? { scale: 0.8, opacity: 0 } : {}}
          animate={animate ? { scale: 1, opacity: 1 } : {}}
          transition={{ delay: 0.2, duration: 0.6, type: 'spring' }}
          className="mb-6"
        >
          <div className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </motion.div>

        {/* Comparison */}
        {comparison && (
          <motion.div
            initial={animate ? { opacity: 0, x: -20 } : {}}
            animate={animate ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.4, duration: 0.6 }}
            className={`flex items-center gap-2 text-sm font-medium ${
              isPositive ? 'text-green-400' : 'text-orange-400'
            }`}
          >
            {isPositive ? (
              <TrendingDown className="w-4 h-4" />
            ) : (
              <TrendingUp className="w-4 h-4" />
            )}
            <span>
              {isPositive ? '↓' : '↑'} {Math.abs(comparison.value).toFixed(1)}% {comparison.trend === 'neutral' ? 'vs' : 'from'} {comparison.period}
            </span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
