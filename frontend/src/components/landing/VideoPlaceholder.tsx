import { motion } from 'framer-motion';
import { Play } from 'lucide-react';
import { useState } from 'react';

export default function VideoPlaceholder() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.section
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      viewport={{ once: true }}
      className="py-20 px-6 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent"
    >
      <div className="max-w-5xl mx-auto">
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          viewport={{ once: true }}
          className="text-4xl font-bold text-center mb-12 text-white"
        >
          See FinMate in Action
        </motion.h2>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          viewport={{ once: true }}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="relative w-full aspect-video rounded-2xl overflow-hidden glass-card border border-white/10 group cursor-pointer"
        >
          {/* Video Placeholder */}
          <div className="w-full h-full bg-gradient-to-br from-gray-900 via-blue-900/30 to-gray-900 flex items-center justify-center relative">
            {/* Placeholder content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <motion.div
                animate={{ scale: isHovered ? 1.1 : 1 }}
                transition={{ duration: 0.3 }}
                className="mb-4"
              >
                <div className="w-20 h-20 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/50">
                  <Play className="w-8 h-8 text-white fill-white" />
                </div>
              </motion.div>
              <p className="text-white text-lg font-semibold">Demo Video</p>
              <p className="text-gray-400 text-sm mt-2">Your video will be added here</p>
            </div>

            {/* Animated border on hover */}
            <motion.div
              animate={{ opacity: isHovered ? 1 : 0 }}
              className="absolute inset-0 rounded-2xl border-2 border-cyan-500/50 pointer-events-none"
            />
          </div>

          {/* Play button overlay */}
          <motion.div
            animate={{ opacity: isHovered ? 1 : 0, scale: isHovered ? 1 : 0.8 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 bg-black/40 flex items-center justify-center"
          >
            <motion.div
              animate={{ scale: isHovered ? 1.2 : 1 }}
              transition={{ duration: 0.3 }}
              className="w-24 h-24 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30"
            >
              <Play className="w-10 h-10 text-white fill-white" />
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Video info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          viewport={{ once: true }}
          className="mt-8 text-center"
        >
          <p className="text-gray-400 text-sm">
            Watch how FinMate helps you save money, track spending, and achieve your financial goals
          </p>
        </motion.div>
      </div>
    </motion.section>
  );
}
