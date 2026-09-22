import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { Navigate, useNavigate } from 'react-router-dom';
import { API_URL } from '../apiConfig';
import DataImport from './DataImport';
import ManualTransactionForm from './ManualTransactionForm';
import { 
  LogOut, LayoutDashboard, HelpCircle, Menu, X, Home, 
  List, Repeat, TrendingUp, Calculator, FileText, Bot, Sparkles 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Import core and new FinMate 2.0 panels
import InteractiveTutorial from './onboarding/InteractiveTutorial';
import ScreenReaderAnnouncer from './accessibility/ScreenReaderAnnouncer';
import ConfettiAnimation from './common/ConfettiAnimation';
import TransactionsList from './TransactionsList';
import SubscriptionsSuspectsPanel from './SubscriptionsSuspectsPage';
import DebatePurchaseV2 from './DebatePurchaseV2';

import FinancialOverviewPanel from './FinancialOverviewPanel';
import SimulationPanel from './SimulationPanel';
import ForecastPanel from './ForecastPanel';
import AIAdvisorPanel from './AIAdvisorPanel';
import ReportBriefingPanel from './ReportBriefingPanel';

interface DashboardProps {
  initialSection?: string;
}

export default function Dashboard({ initialSection = 'overview' }: DashboardProps) {
  const auth = useContext(AuthContext);
  const navigate = useNavigate();
  const [recentTransactions, setRecentTransactions] = useState<any[]>([]);
  const [showTutorial, setShowTutorial] = useState(false);
  const [announceMessage, setAnnounceMessage] = useState('');
  const [showConfetti, setShowConfetti] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState(initialSection);

  useEffect(() => {
    if (initialSection) {
      setActiveSection(initialSection);
    }
  }, [initialSection]);

  const fetchAnalytics = async () => {
    try {
      const analyticsRes = await axios.get(`${API_URL}/analytics`, {
        headers: { Authorization: `Bearer ${auth?.token}` }
      });
      
      setRecentTransactions(analyticsRes.data.recent_transactions || []);
    } catch (err) {
      console.error('Analytics fetch failed:', err);
    }
  };

  useEffect(() => {
    if (auth?.token) fetchAnalytics();
  }, [auth?.token]);

  if (!auth?.user || !auth?.token) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    auth.logout();
    navigate('/login');
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'transactions', label: 'Transactions', icon: List },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp },
    { id: 'subscriptions', label: 'Subscriptions', icon: Repeat },
    { id: 'simulation', label: 'Simulator', icon: Calculator },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'advisor', label: 'AI Advisor', icon: Bot },
    { id: 'debate', label: 'Debate', icon: Sparkles }
  ];

  return (
    <div className="min-h-screen bg-mesh text-white">
      {/* Accessibility */}
      <ScreenReaderAnnouncer message={announceMessage} />
      <ConfettiAnimation trigger={showConfetti} onComplete={() => setShowConfetti(false)} />
      <InteractiveTutorial
        isVisible={showTutorial}
        onComplete={() => {
          setShowTutorial(false);
          setShowConfetti(true);
          setAnnounceMessage('Tutorial completed!');
        }}
        onSkip={() => setShowTutorial(false)}
      />

      {/* Sleek Navbar */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="sticky top-0 z-40 glass-card border-b border-white/10 backdrop-blur-xl"
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center shadow-lg">
              <LayoutDashboard className="text-white w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight hidden sm:block">FinMate 2.0</h1>
              <span className="text-[10px] text-cyan-300 font-medium hidden sm:block">Financial Intelligence</span>
            </div>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition text-xs font-medium ${
                  activeSection === item.id
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <item.icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 hidden sm:inline">{auth.user.full_name || auth.user.email}</span>
            <button 
              onClick={() => setShowTutorial(true)}
              className="text-gray-400 hover:text-white transition p-1.5 rounded-lg hover:bg-white/5"
              aria-label="Help"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
            <button 
              onClick={handleLogout}
              className="text-gray-400 hover:text-red-400 transition p-1.5 rounded-lg hover:bg-white/5"
              aria-label="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden text-gray-400 hover:text-white p-1.5 rounded-lg hover:bg-white/5"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-white/10 bg-white/5"
            >
              <div className="px-6 py-4 space-y-1">
                {navItems.map(item => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveSection(item.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg transition text-xs ${
                      activeSection === item.id
                        ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {activeSection === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-8"
            >
              {/* Financial Overview Intelligence Component */}
              <FinancialOverviewPanel />

              {/* Data Import and Quick Manual Entry */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ManualTransactionForm onSuccess={fetchAnalytics} />
                <DataImport onSuccess={fetchAnalytics} />
              </div>

              {/* Recent Transactions Snippet */}
              <div className="glass-card p-5 rounded-2xl border border-white/10">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-semibold text-sm text-white">Recent Transactions</h3>
                  <button 
                    onClick={() => setActiveSection('transactions')}
                    className="text-xs text-cyan-400 hover:underline"
                  >
                    View all
                  </button>
                </div>
                <div className="space-y-2">
                  {recentTransactions.length > 0 ? (
                    recentTransactions.slice(0, 5).map((txn, i) => (
                      <div key={i} className="flex justify-between items-center text-xs p-2.5 rounded-xl bg-white/5 hover:bg-white/10 transition">
                        <div className="min-w-0">
                          <p className="font-medium text-white truncate">{txn.description}</p>
                          <p className="text-[11px] text-gray-500">{new Date(txn.date).toLocaleDateString()}</p>
                        </div>
                        <p className="font-semibold text-white shrink-0">
                          {auth?.user?.currency_symbol || '$'}{Number(txn.amount || 0).toFixed(2)}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-400 text-center py-4">No recent transactions recorded.</p>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeSection === 'transactions' && (
            <motion.div
              key="transactions"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <TransactionsList />
            </motion.div>
          )}

          {activeSection === 'forecast' && (
            <motion.div
              key="forecast"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <ForecastPanel />
            </motion.div>
          )}

          {activeSection === 'subscriptions' && (
            <motion.div
              key="subscriptions"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <SubscriptionsSuspectsPanel />
            </motion.div>
          )}

          {activeSection === 'simulation' && (
            <motion.div
              key="simulation"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <SimulationPanel />
            </motion.div>
          )}

          {activeSection === 'reports' && (
            <motion.div
              key="reports"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <ReportBriefingPanel />
            </motion.div>
          )}

          {activeSection === 'advisor' && (
            <motion.div
              key="advisor"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <AIAdvisorPanel />
            </motion.div>
          )}

          {activeSection === 'debate' && (
            <motion.div
              key="debate"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="space-y-6"
            >
              <DebatePurchaseV2 />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}