import { motion } from 'framer-motion';
import { Zap, Brain, Trophy, TrendingDown, Receipt, Share2 } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI Financial Twin',
    description: 'Get personalized financial advice from an AI that learns your spending habits',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: Trophy,
    title: 'Gamified Savings',
    description: 'Earn XP, unlock achievements, and compete on leaderboards',
    color: 'from-yellow-500 to-orange-500',
  },
  {
    icon: TrendingDown,
    title: 'Smart Insights',
    description: 'Predictive analytics warn you before you overspend',
    color: 'from-green-500 to-emerald-500',
  },
  {
    icon: Receipt,
    title: 'Receipt Scanning',
    description: 'Snap a photo and let AI extract transaction details instantly',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Zap,
    title: 'Budget Optimization',
    description: 'AI finds ways to save money on subscriptions and bills',
    color: 'from-red-500 to-pink-500',
  },
  {
    icon: Share2,
    title: 'Social Challenges',
    description: 'Team up with friends and compete on savings goals',
    color: 'from-indigo-500 to-purple-500',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6 },
  },
};

export default function FeatureShowcase() {
  return (
    <motion.section
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      viewport={{ once: true }}
      className="py-20 px-6 bg-gradient-to-b from-transparent to-blue-500/5"
    >
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl font-bold text-white mb-4">Packed with Features</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Everything you need to take control of your finances, all in one beautiful app
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                variants={itemVariants}
                whileHover={{ y: -8, transition: { duration: 0.3 } }}
                className="group glass-card p-8 rounded-xl border border-white/10 hover:border-white/20 transition-all duration-300"
              >
                {/* Icon */}
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  transition={{ duration: 0.3 }}
                  className={`w-14 h-14 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 shadow-lg`}
                >
                  <Icon className="w-7 h-7 text-white" />
                </motion.div>

                {/* Content */}
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{feature.description}</p>

                {/* Hover indicator */}
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  whileHover={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="mt-4 flex items-center gap-2 text-cyan-400 text-sm font-medium"
                >
                  <span>Learn more</span>
                  <motion.span animate={{ x: [0, 4, 0] }} transition={{ duration: 1.5, repeat: Infinity }}>
                    →
                  </motion.span>
                </motion.div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </motion.section>
  );
}
