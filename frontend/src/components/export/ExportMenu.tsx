import { motion } from 'framer-motion';
import { Download, Share2, FileText, Calendar } from 'lucide-react';
import { useState } from 'react';

interface ExportMenuProps {
  onExportPDF?: () => void;
  onExportCSV?: () => void;
  onExportYearInReview?: () => void;
  onShareAchievement?: () => void;
}

export default function ExportMenu({
  onExportPDF,
  onExportCSV,
  onExportYearInReview,
  onShareAchievement,
}: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const options = [
    {
      icon: FileText,
      label: 'Export PDF Report',
      description: 'Download a detailed financial report',
      onClick: onExportPDF,
      color: 'from-red-500 to-pink-500',
    },
    {
      icon: Download,
      label: 'Export CSV',
      description: 'Download all transactions as CSV',
      onClick: onExportCSV,
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: Calendar,
      label: 'Year in Review',
      description: 'Generate your annual summary',
      onClick: onExportYearInReview,
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Share2,
      label: 'Share Achievement',
      description: 'Share your wins on social media',
      onClick: onShareAchievement,
      color: 'from-blue-500 to-cyan-500',
    },
  ];

  return (
    <motion.div className="relative">
      {/* Trigger Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 rounded-lg text-cyan-400 hover:border-cyan-500/50 transition-all"
      >
        <Download className="w-4 h-4" />
        Export & Share
      </motion.button>

      {/* Dropdown Menu */}
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={isOpen ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: -10, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className={`absolute right-0 mt-2 w-72 glass-card rounded-lg border border-white/10 overflow-hidden z-50 ${
          isOpen ? 'pointer-events-auto' : 'pointer-events-none'
        }`}
      >
        <div className="p-4 space-y-2">
          {options.map((option, index) => {
            const Icon = option.icon;
            return (
              <motion.button
                key={index}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  option.onClick?.();
                  setIsOpen(false);
                }}
                className="w-full text-left p-3 rounded-lg hover:bg-white/5 transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${option.color} flex items-center justify-center flex-shrink-0 group-hover:shadow-lg transition-shadow`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white text-sm">{option.label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{option.description}</p>
                  </div>
                </div>
              </motion.button>
            );
          })}
        </div>
      </motion.div>

      {/* Backdrop */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 z-40"
        />
      )}
    </motion.div>
  );
}
