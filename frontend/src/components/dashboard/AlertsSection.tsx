import { motion } from 'framer-motion';
import { AlertCircle, TrendingUp, Zap } from 'lucide-react';

interface Alert {
  id: string;
  type: 'warning' | 'info' | 'success';
  title: string;
  message: string;
  action?: string;
}

interface AlertsSectionProps {
  alerts: Alert[];
  onDismiss?: (id: string) => void;
}

const alertConfig = {
  warning: {
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    icon: AlertCircle,
    color: 'text-orange-400',
  },
  info: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    icon: Zap,
    color: 'text-blue-400',
  },
  success: {
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    icon: TrendingUp,
    color: 'text-green-400',
  },
};

export default function AlertsSection({ alerts, onDismiss }: AlertsSectionProps) {
  if (alerts.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-3"
    >
      {alerts.map((alert, index) => {
        const config = alertConfig[alert.type];
        const Icon = config.icon;

        return (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`${config.bg} ${config.border} border rounded-lg p-4 flex items-start gap-3 group hover:border-opacity-50 transition-all`}
          >
            <Icon className={`w-5 h-5 ${config.color} flex-shrink-0 mt-0.5`} />
            <div className="flex-1 min-w-0">
              <p className={`font-semibold text-sm ${config.color}`}>{alert.title}</p>
              <p className="text-gray-400 text-sm mt-1">{alert.message}</p>
              {alert.action && (
                <button className={`text-xs font-medium ${config.color} hover:underline mt-2`}>
                  {alert.action}
                </button>
              )}
            </div>
            {onDismiss && (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => onDismiss(alert.id)}
                className="text-gray-500 hover:text-gray-300 transition flex-shrink-0"
              >
                ✕
              </motion.button>
            )}
          </motion.div>
        );
      })}
    </motion.div>
  );
}
