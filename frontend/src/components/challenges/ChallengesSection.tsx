import { motion } from 'framer-motion';
import { Trophy, Plus, Share2, Users } from 'lucide-react';

interface Challenge {
  id: number;
  name: string;
  description: string;
  goalAmount: number;
  currentProgress: number;
  participants: number;
  daysRemaining: number;
  userRank?: number;
}

interface ChallengesSectionProps {
  challenges: Challenge[];
  onCreateChallenge?: () => void;
  onJoinChallenge?: (id: number) => void;
  onShareChallenge?: (id: number) => void;
}

export default function ChallengesSection({
  challenges,
  onCreateChallenge,
  onJoinChallenge,
  onShareChallenge,
}: ChallengesSectionProps) {
  const activeChallenges = challenges.slice(0, 3);
  const progressPercentage = (current: number, goal: number) => (current / goal) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trophy className="w-6 h-6 text-yellow-400" />
          <h3 className="text-2xl font-bold text-white">Active Challenges</h3>
        </div>
        {onCreateChallenge && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onCreateChallenge}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg text-sm font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-shadow"
          >
            <Plus className="w-4 h-4" />
            New Challenge
          </motion.button>
        )}
      </div>

      {/* Challenges Grid */}
      {activeChallenges.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ staggerChildren: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {activeChallenges.map((challenge, index) => {
            const progress = progressPercentage(challenge.currentProgress, challenge.goalAmount);

            return (
              <motion.div
                key={challenge.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -4 }}
                className="glass-card p-6 rounded-lg border border-white/10 hover:border-white/20 transition-all group"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h4 className="font-semibold text-white text-lg">{challenge.name}</h4>
                    <p className="text-xs text-gray-400 mt-1">{challenge.description}</p>
                  </div>
                  {challenge.userRank && (
                    <div className="text-right">
                      <div className="text-2xl font-bold text-yellow-400">#{challenge.userRank}</div>
                      <p className="text-xs text-gray-400">Your Rank</p>
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">
                      ${challenge.currentProgress.toFixed(0)} / ${challenge.goalAmount.toFixed(0)}
                    </span>
                    <span className="text-sm font-semibold text-cyan-400">{progress.toFixed(0)}%</span>
                  </div>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ delay: 0.3, duration: 0.8, ease: 'easeOut' }}
                    className="h-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                  />
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-xs text-gray-400 mb-4 pb-4 border-b border-white/10">
                  <div className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    <span>{challenge.participants} participants</span>
                  </div>
                  <span>{challenge.daysRemaining} days left</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {onJoinChallenge && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => onJoinChallenge(challenge.id)}
                      className="flex-1 px-3 py-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 hover:from-cyan-500/30 hover:to-blue-500/30 rounded-lg text-sm font-medium transition"
                    >
                      Join
                    </motion.button>
                  )}
                  {onShareChallenge && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => onShareChallenge(challenge.id)}
                      className="px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition"
                    >
                      <Share2 className="w-4 h-4" />
                    </motion.button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-8 rounded-lg border border-white/10 text-center"
        >
          <Trophy className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 mb-4">No active challenges yet</p>
          {onCreateChallenge && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onCreateChallenge}
              className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg text-sm font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-shadow"
            >
              Create Your First Challenge
            </motion.button>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
