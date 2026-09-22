import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

interface CategoryData {
  name: string;
  value: number;
  color: string;
}

interface BarChartRaceProps {
  data: CategoryData[][];
  weeks: number;
  animationDuration?: number;
}

export default function BarChartRace({ data, weeks = 12, animationDuration = 1000 }: BarChartRaceProps) {
  // Show empty state if no data
  if (!data || data.length === 0 || data[0]?.length === 0) {
    return (
      <div className="glass-card p-6 rounded-lg border border-white/10">
        <h3 className="text-xl font-bold text-white mb-6">Spending by Category</h3>
        <div className="text-center py-12">
          <div className="text-5xl mb-4">📊</div>
          <p className="text-gray-400">No category data available</p>
          <p className="text-sm text-gray-500 mt-2">Add transactions to see category breakdown</p>
        </div>
      </div>
    );
  }

  const [currentWeek, setCurrentWeek] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!isPlaying) return;
    
    const interval = setInterval(() => {
      setCurrentWeek(prev => {
        if (prev >= weeks - 1) {
          setIsPlaying(false);
          return 0;
        }
        return prev + 1;
      });
    }, animationDuration);

    return () => clearInterval(interval);
  }, [isPlaying, weeks, animationDuration]);

  const currentData = data[currentWeek] || [];
  const maxValue = Math.max(...currentData.map(d => d.value));

  return (
    <div className="glass-card p-6 rounded-lg border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white">Spending by Category</h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">Week {currentWeek + 1} of {weeks}</span>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition"
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {currentData.slice(0, 5).map((item, index) => (
          <motion.div
            key={item.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center gap-3"
          >
            <div className="w-8 text-right text-sm font-bold text-gray-400">
              #{index + 1}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-white">{item.name}</span>
                <span className="text-sm text-gray-400">${item.value.toFixed(0)}</span>
              </div>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(item.value / maxValue) * 100}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className="h-6 rounded-lg"
                style={{ backgroundColor: item.color }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}