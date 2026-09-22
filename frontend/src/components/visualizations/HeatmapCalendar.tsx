import { motion } from 'framer-motion';
import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface DayData {
  date: string;
  amount: number;
}

interface HeatmapCalendarProps {
  data: DayData[];
  currencySymbol?: string;
}

export default function HeatmapCalendar({ data, currencySymbol = '$' }: HeatmapCalendarProps) {
  // Detect year range from data
  const getYearRange = () => {
    if (!data || data.length === 0) return { minYear: new Date().getFullYear(), maxYear: new Date().getFullYear() };
    
    const years = data.map(d => new Date(d.date).getFullYear());
    return {
      minYear: Math.min(...years),
      maxYear: Math.max(...years)
    };
  };
  
  const { minYear, maxYear } = getYearRange();
  const [selectedYear, setSelectedYear] = useState(maxYear); // Start with most recent year

  // Show empty state if no data
  if (!data || data.length === 0) {
    return (
      <div className="glass-card p-6 rounded-lg border border-white/10">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">Spending Heatmap</h3>
        </div>
        <div className="text-center py-12">
          <div className="text-5xl mb-4">📅</div>
          <p className="text-gray-400">No spending data available</p>
          <p className="text-sm text-gray-500 mt-2">Add transactions to see your spending patterns</p>
        </div>
      </div>
    );
  }

  const maxAmount = Math.max(...data.map(d => d.amount));
  
  const getIntensity = (amount: number) => {
    if (amount === 0) return 0;
    const normalized = amount / maxAmount;
    if (normalized < 0.25) return 1;
    if (normalized < 0.5) return 2;
    if (normalized < 0.75) return 3;
    return 4;
  };

  const getColor = (intensity: number) => {
    const colors = [
      'bg-gray-800/50',
      'bg-green-900/60',
      'bg-green-700/70',
      'bg-green-500/80',
      'bg-green-400'
    ];
    return colors[intensity] || colors[0];
  };

  // Generate GitHub-style grid for selected year
  const generateYearGrid = () => {
    const startDate = new Date(selectedYear, 0, 1);
    const endDate = new Date(selectedYear, 11, 31);
    
    // Start from the first Sunday before or on Jan 1
    const firstDay = new Date(startDate);
    firstDay.setDate(firstDay.getDate() - firstDay.getDay());
    
    const weeks: Array<Array<{ date: Date; amount: number; intensity: number } | null>> = [];
    let currentWeek: Array<{ date: Date; amount: number; intensity: number } | null> = [];
    
    const currentDate = new Date(firstDay);
    
    while (currentDate <= endDate || currentWeek.length > 0) {
      if (currentDate.getDay() === 0 && currentWeek.length > 0) {
        weeks.push([...currentWeek]);
        currentWeek = [];
      }
      
      if (currentDate <= endDate) {
        const dateStr = currentDate.toISOString().split('T')[0];
        const dayData = data.find(d => d.date === dateStr);
        const amount = dayData?.amount || 0;
        
        // Only show days within the selected year
        if (currentDate.getFullYear() === selectedYear) {
          currentWeek.push({
            date: new Date(currentDate),
            amount,
            intensity: getIntensity(amount)
          });
        } else {
          currentWeek.push(null);
        }
      }
      
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    if (currentWeek.length > 0) {
      // Pad the last week
      while (currentWeek.length < 7) {
        currentWeek.push(null);
      }
      weeks.push(currentWeek);
    }
    
    return weeks;
  };

  const weeks = generateYearGrid();
  const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
  // Calculate which week index each month starts
  const getMonthPositions = () => {
    const positions: Array<{ month: string; weekIndex: number }> = [];
    let lastMonth = -1;
    
    weeks.forEach((week, weekIndex) => {
      const firstDay = week.find(d => d !== null);
      if (firstDay) {
        const month = firstDay.date.getMonth();
        if (month !== lastMonth) {
          positions.push({ month: monthLabels[month], weekIndex });
          lastMonth = month;
        }
      }
    });
    
    return positions;
  };

  const monthPositions = getMonthPositions();
  const yearTotal = data
    .filter(d => new Date(d.date).getFullYear() === selectedYear)
    .reduce((sum, d) => sum + d.amount, 0);

  return (
    <div className="glass-card p-6 rounded-lg border border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white">Spending Heatmap</h3>
        
        {/* Year Selector */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSelectedYear(selectedYear - 1)}
            disabled={selectedYear <= minYear}
            className="p-1 hover:bg-white/10 rounded transition disabled:opacity-30 disabled:cursor-not-allowed"
            aria-label="Previous year"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm font-semibold min-w-[60px] text-center">{selectedYear}</span>
          <button
            onClick={() => setSelectedYear(selectedYear + 1)}
            disabled={selectedYear >= maxYear}
            className="p-1 hover:bg-white/10 rounded transition disabled:opacity-30 disabled:cursor-not-allowed"
            aria-label="Next year"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>Less</span>
          {[0, 1, 2, 3, 4].map(i => (
            <div key={i} className={`w-3 h-3 rounded-sm ${getColor(i)}`} />
          ))}
          <span>More</span>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-full">
          {/* Month Labels */}
          <div className="flex mb-2 ml-8">
            {monthPositions.map((pos, idx) => (
              <div
                key={idx}
                className="text-xs text-gray-400"
                style={{ 
                  marginLeft: idx === 0 ? `${pos.weekIndex * 14}px` : `${(pos.weekIndex - monthPositions[idx - 1].weekIndex) * 14 - 24}px`,
                  minWidth: '24px'
                }}
              >
                {pos.month}
              </div>
            ))}
          </div>

          {/* Grid with day labels */}
          <div className="flex">
            {/* Day labels */}
            <div className="flex flex-col gap-1 mr-2">
              {dayLabels.map((day, idx) => (
                <div key={day} className="h-3 flex items-center">
                  {idx % 2 === 1 && (
                    <span className="text-xs text-gray-500 w-6">{day.slice(0, 1)}</span>
                  )}
                </div>
              ))}
            </div>

            {/* Weeks grid */}
            <div className="flex gap-1">
              {weeks.map((week, weekIndex) => (
                <div key={weekIndex} className="flex flex-col gap-1">
                  {week.map((day, dayIndex) => {
                    if (!day) {
                      return <div key={dayIndex} className="w-3 h-3" />;
                    }
                    
                    return (
                      <motion.div
                        key={`${weekIndex}-${dayIndex}`}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: weekIndex * 0.005 }}
                        whileHover={{ scale: 1.5, zIndex: 10 }}
                        className={`w-3 h-3 rounded-sm cursor-pointer ${getColor(day.intensity)} relative group`}
                        title={`${day.date.toLocaleDateString()}: ${currencySymbol}${day.amount.toFixed(2)}`}
                      >
                        {/* Tooltip on hover */}
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap z-20">
                          {day.date.toLocaleDateString()}: {currencySymbol}{day.amount.toFixed(2)}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 flex items-center justify-between text-xs text-gray-400">
        <span>
          {data.filter(d => new Date(d.date).getFullYear() === selectedYear).length} days of spending in {selectedYear}
        </span>
        <span className="font-semibold text-white">
          Total: {currencySymbol}{yearTotal.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
