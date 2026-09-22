import { motion } from 'framer-motion';
import { Star } from 'lucide-react';

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'Product Manager',
    content: 'FinMate helped me save $500/month just by identifying duplicate subscriptions. The AI is genuinely helpful!',
    rating: 5,
  },
  {
    name: 'Marcus Johnson',
    role: 'Freelancer',
    content: 'The gamification keeps me motivated. I love competing with friends on the leaderboard.',
    rating: 5,
  },
  {
    name: 'Emma Rodriguez',
    role: 'Student',
    content: 'Finally, a finance app that doesn\'t feel like a chore. The roast mode is hilarious and actually helpful.',
    rating: 5,
  },
];

const stats = [
  { label: 'Active Users', value: '1,000+' },
  { label: 'Money Saved', value: '$2.5M+' },
  { label: 'Avg. Savings', value: '$450/mo' },
];

export default function SocialProof() {
  return (
    <motion.section
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      viewport={{ once: true }}
      className="py-20 px-6 bg-gradient-to-b from-blue-500/5 to-transparent"
    >
      <div className="max-w-6xl mx-auto">
        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              whileHover={{ scale: 1.05 }}
              className="text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                whileInView={{ scale: 1 }}
                transition={{ delay: 0.2 + index * 0.1, type: 'spring' }}
                viewport={{ once: true }}
                className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-2"
              >
                {stat.value}
              </motion.div>
              <p className="text-gray-400">{stat.label}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Testimonials */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          viewport={{ once: true }}
          className="mb-8"
        >
          <h3 className="text-2xl font-bold text-white text-center mb-12">Loved by Users</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -4 }}
                className="glass-card p-6 rounded-lg border border-white/10 hover:border-white/20 transition-all"
              >
                {/* Rating */}
                <div className="flex gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ scale: 0 }}
                      whileInView={{ scale: 1 }}
                      transition={{ delay: 0.5 + i * 0.05 }}
                      viewport={{ once: true }}
                    >
                      <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    </motion.div>
                  ))}
                </div>

                {/* Content */}
                <p className="text-gray-300 mb-4 italic">"{testimonial.content}"</p>

                {/* Author */}
                <div>
                  <p className="font-semibold text-white">{testimonial.name}</p>
                  <p className="text-sm text-gray-400">{testimonial.role}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}
