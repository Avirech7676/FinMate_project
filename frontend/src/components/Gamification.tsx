import { useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { Trophy, Zap, Award } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Gamification() {
  const auth = useContext(AuthContext);
  const [stats, setStats] = useState<any>(null);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (auth?.token) {
      fetchStats();
      fetchAchievements();
      fetchLeaderboard();
    }
  }, [auth?.token]);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/stats`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setStats(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAchievements = async () => {
    try {
      const res = await axios.get(`${API_URL}/achievements`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setAchievements(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const res = await axios.get(`${API_URL}/leaderboard/savings-rate`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      setLeaderboard(res.data.leaderboard || []);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="glass-card p-6 text-center">Loading gamification...</div>;
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Stats */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="glass-card p-6"
      >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" /> Your Stats
        </h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Total XP</span>
            <span className="text-2xl font-bold text-yellow-400">{stats?.total_xp || 0}</span>
          </div>
          <div className="h-px bg-white/10" />
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Current Streak</span>
            <span className="text-2xl font-bold text-cyan-400">{stats?.current_streak || 0} 🔥</span>
          </div>
          <div className="h-px bg-white/10" />
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Best Streak</span>
            <span className="text-2xl font-bold text-purple-400">{stats?.longest_streak || 0}</span>
          </div>
          <div className="h-px bg-white/10" />
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Transactions</span>
            <span className="text-2xl font-bold text-blue-400">{stats?.total_transactions || 0}</span>
          </div>
        </div>
      </motion.div>

      {/* Achievements */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="glass-card p-6"
      >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Award className="w-5 h-5 text-purple-400" /> Achievements
        </h3>
        <div className="space-y-2">
          <AnimatePresence>
            {achievements.length === 0 ? (
              <p className="text-gray-400 text-sm">Keep tracking to unlock achievements! 🏆</p>
            ) : (
              achievements.slice(0, 5).map((achievement) => (
                <motion.div
                  key={achievement.achievement_id}
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="bg-white/5 p-2 rounded flex items-center gap-2 hover:bg-white/10 transition"
                >
                  <span className="text-xl">{achievement.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm truncate">{achievement.title}</p>
                    <p className="text-xs text-gray-400">+{achievement.xp_reward} XP</p>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Leaderboard */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-6"
      >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Trophy className="w-5 h-5 text-yellow-400" /> Top Savers
        </h3>
        <div className="space-y-2">
          {leaderboard.slice(0, 5).map((user) => (
            <motion.div
              key={user.rank}
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: user.rank * 0.05 }}
              className={`flex items-center gap-3 p-2 rounded transition ${
                user.rank === 1
                  ? 'bg-yellow-500/10 border border-yellow-500/20'
                  : user.rank === 2
                  ? 'bg-gray-400/10 border border-gray-400/20'
                  : user.rank === 3
                  ? 'bg-orange-500/10 border border-orange-500/20'
                  : 'bg-white/5 border border-white/10'
              }`}
            >
              <span className="text-lg font-bold w-6 text-center">
                {user.rank === 1 ? '🥇' : user.rank === 2 ? '🥈' : user.rank === 3 ? '🥉' : user.rank}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm truncate">{user.name}</p>
                <p className="text-xs text-gray-400">{user.streak} day streak</p>
              </div>
              <span className="text-xs font-semibold text-yellow-400">{user.xp} XP</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
