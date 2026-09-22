import { motion } from 'framer-motion';
import { ShieldCheck } from 'lucide-react';

interface Props {
  totalSpent: number;
}

function computeScore(totalSpent: number) {
  // Simple scoring: lower spending = higher health score (0-100)
  // Score degrades past $500, catastrophic past $5000
  if (totalSpent === 0) return { score: 75, label: 'Good', color: '#00d4aa' };
  if (totalSpent < 500) return { score: 90, label: 'Excellent', color: '#00d4aa' };
  if (totalSpent < 1500) return { score: 72, label: 'Good', color: '#4f8fe8' };
  if (totalSpent < 3000) return { score: 55, label: 'Fair', color: '#f59e0b' };
  if (totalSpent < 5000) return { score: 38, label: 'Needs Work', color: '#f97316' };
  return { score: 20, label: 'Critical', color: '#ff4d6d' };
}

export default function HealthScore({ totalSpent }: Props) {
  const { score, label, color } = computeScore(totalSpent);
  const circumference = 2 * Math.PI * 40; // r=40
  const dashOffset = circumference - (score / 100) * circumference;

  return (
    <div className="glass-card p-6 flex items-center gap-6">
      {/* SVG Circular Progress */}
      <div className="relative flex-shrink-0">
        <svg width="100" height="100" viewBox="0 0 100 100" className="-rotate-90">
          {/* Background track */}
          <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
          {/* Progress arc */}
          <motion.circle
            cx="50" cy="50" r="40" fill="none"
            stroke={color} strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center rotate-0">
          <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-1">
          <ShieldCheck className="w-4 h-4" style={{ color }} />
          <h3 className="font-semibold text-sm">Financial Health Score</h3>
        </div>
        <p className="text-2xl font-bold" style={{ color }}>{label}</p>
        <p className="text-xs text-[--color-text-secondary] mt-1">
          Based on your tracked spending patterns.
        </p>
      </div>
    </div>
  );
}
