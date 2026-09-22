import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Wallet, Zap, PieChart, ShieldCheck, 
  Mic, Brain, ArrowRight, Sparkles
} from 'lucide-react';

const features = [
  {
    icon: Brain,
    color: '#00d4aa',
    title: 'Gemini AI Advisor',
    desc: 'Get personalized financial advice powered by Google Gemini. Ask anything in natural language.'
  },
  {
    icon: PieChart,
    color: '#4f8fe8',
    title: 'Spending Insights',
    desc: 'Beautiful charts break down your spending by category with real-time analysis.'
  },
  {
    icon: Zap,
    color: '#a78bfa',
    title: 'Receipt Scanning',
    desc: 'Snap a photo of any receipt and AI extracts the merchant, amount, and category instantly.'
  },
  {
    icon: Mic,
    color: '#f59e0b',
    title: 'Voice Input',
    desc: 'Talk to your financial assistant hands-free using the built-in voice dictation.'
  },
  {
    icon: ShieldCheck,
    color: '#00d4aa',
    title: 'Health Score',
    desc: 'Get a real-time financial wellness score based on your spending patterns.'
  },
  {
    icon: Wallet,
    color: '#ff4d6d',
    title: 'Action Engine',
    desc: 'Ask FinMate to draft cancellation emails, bill negotiations and more — it takes action for you.'
  }
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white overflow-hidden selection:bg-[#00d4aa] selection:text-black">
      
      {/* Animated Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <motion.div 
          animate={{ 
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.15, 0.1],
            x: [0, 50, 0]
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-[20%] -left-[10%] w-[50rem] h-[50rem] bg-[#00d4aa] blur-[150px] rounded-full"
        />
        <motion.div 
          animate={{ 
            scale: [1, 1.3, 1],
            opacity: [0.08, 0.12, 0.08],
            y: [0, -50, 0]
          }}
          transition={{ duration: 13, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="absolute top-[20%] -right-[20%] w-[40rem] h-[40rem] bg-[#4f8fe8] blur-[150px] rounded-full"
        />
      </div>

      {/* Sticky Glass Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-black/40 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
          <div className="flex items-center gap-3 group cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00d4aa] to-[#4f8fe8] flex items-center justify-center shadow-[0_0_20px_rgba(0,212,170,0.4)] group-hover:shadow-[0_0_30px_rgba(0,212,170,0.6)] transition-all duration-300">
              <Wallet className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">FinMate</span>
          </div>
          <div className="flex items-center gap-6">
            
            <Link
              to="/login"
              className="px-3 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors hidden sm:block"
            >
              Sign In
            </Link>

            <Link to="/signup" className="px-5 py-2.5 rounded-full bg-white text-black font-semibold text-sm hover:scale-105 transition-transform duration-200 shadow-[0_0_15px_rgba(255,255,255,0.2)]">
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10 pt-32">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto px-6 pt-12 pb-32">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            
            {/* Left Column: Copy */}
            <motion.div 
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="flex-1 text-center lg:text-left"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#00d4aa]/30 bg-[#00d4aa]/10 text-xs font-medium text-[#00d4aa] mb-8 shadow-[0_0_20px_rgba(0,212,170,0.1)]">
                <Sparkles className="w-4 h-4" />
                Powered by Google Gemini AI
              </div>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6">
                Your finances, <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00d4aa] via-[#4f8fe8] to-[#a78bfa]">
                  finally understood.
                </span>
              </h1>
              <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto lg:mx-0 mb-10 leading-relaxed">
                FinMate combines conversational AI, receipt scanning, and intelligent dashboards to give you a complete picture of your financial health — and the advice to improve it.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
                <Link to="/signup" className="w-full sm:w-auto px-8 py-4 rounded-full bg-gradient-to-r from-[#00d4aa] to-[#00b390] text-black font-bold text-base flex items-center justify-center gap-2 hover:shadow-[0_0_30px_rgba(0,212,170,0.5)] hover:scale-105 transition-all duration-300">
                  Start for Free <ArrowRight className="w-5 h-5" />
                </Link>
                <Link to="/login" className="w-full sm:w-auto px-8 py-4 rounded-full border border-white/10 text-base font-medium hover:bg-white/5 transition-colors flex items-center justify-center">
                  See Demo
                </Link>
              </div>
            </motion.div>

            {/* Right Column: Floating App Mockup */}
            <motion.div 
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.2 }}
              className="flex-1 w-full max-w-lg lg:max-w-none relative"
            >
              <motion.div 
                animate={{ y: [-10, 10, -10] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                className="relative rounded-3xl border border-white/10 bg-black/40 backdrop-blur-2xl p-6 shadow-2xl overflow-hidden"
              >
                {/* Mockup Header */}
                <div className="flex items-center gap-4 border-b border-white/10 pb-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#00d4aa] to-[#4f8fe8] flex items-center justify-center">
                    <Brain className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">FinMate AI</h3>
                    <p className="text-xs text-[#00d4aa] flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-[#00d4aa] animate-pulse"></span> Online
                    </p>
                  </div>
                </div>

                {/* Mockup Chat */}
                <div className="space-y-4">
                  <div className="flex gap-3 justify-end">
                    <div className="bg-white/10 text-white p-3 rounded-2xl rounded-tr-sm text-sm max-w-[80%] border border-white/5">
                      How much did I spend on dining out this week?
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#00d4aa] to-[#4f8fe8] flex-shrink-0 flex items-center justify-center mt-1">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gradient-to-br from-[#00d4aa]/20 to-transparent text-gray-200 p-4 rounded-2xl rounded-tl-sm text-sm max-w-[85%] border border-[#00d4aa]/30 shadow-[inset_0_0_20px_rgba(0,212,170,0.1)]">
                      You've spent <strong>$142.50</strong> on dining out so far this week. That's 20% higher than your usual average. <br/><br/>
                      Would you like me to adjust next week's budget to compensate, or find subscriptions to cancel?
                    </div>
                  </div>
                </div>

                {/* Floating Elements on Mockup */}
                <div className="absolute -right-6 -bottom-6 bg-black/60 backdrop-blur-xl border border-white/10 p-4 rounded-2xl shadow-xl flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-[#ff4d6d]/20 flex items-center justify-center text-[#ff4d6d]">
                    <PieChart className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Monthly Savings</p>
                    <p className="text-lg font-bold text-white">+$430.00</p>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="max-w-7xl mx-auto px-6 pb-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-6">Everything you need to win financially</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">Built for a generation that deserves better financial tools. Stop tracking pennies and start building wealth.</p>
          </motion.div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="group relative bg-white/[0.03] border border-white/5 p-8 rounded-3xl hover:bg-white/[0.05] transition-colors duration-300 overflow-hidden"
              >
                {/* Hover Gradient Background */}
                <div 
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                  style={{ background: `radial-gradient(circle at center, ${f.color}15 0%, transparent 70%)` }}
                />
                
                <div 
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 relative z-10" 
                  style={{ backgroundColor: `${f.color}15`, border: `1px solid ${f.color}30` }}
                >
                  <f.icon className="w-7 h-7" style={{ color: f.color }} />
                </div>
                <h3 className="text-xl font-bold mb-3 relative z-10 text-white/90 group-hover:text-white transition-colors">{f.title}</h3>
                <p className="text-gray-400 leading-relaxed relative z-10 group-hover:text-gray-300 transition-colors">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <section className="max-w-4xl mx-auto px-6 pb-32 text-center">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative rounded-[2.5rem] border border-[#00d4aa]/20 bg-gradient-to-b from-[#00d4aa]/10 to-transparent p-12 sm:p-20 overflow-hidden"
          >
            {/* Glow effect inside CTA */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full max-w-md bg-[#00d4aa] opacity-20 blur-[100px] pointer-events-none rounded-full" />
            
            <Wallet className="w-16 h-16 text-[#00d4aa] mx-auto mb-8 relative z-10 drop-shadow-[0_0_15px_rgba(0,212,170,0.5)]" />
            <h2 className="text-4xl sm:text-5xl font-bold mb-6 relative z-10">Ready to take control?</h2>
            <p className="text-xl text-gray-300 mb-10 relative z-10 max-w-xl mx-auto">Join FinMate today and let AI be your 24/7 financial copilot. Setup takes less than 2 minutes.</p>
            <Link to="/signup" className="relative z-10 inline-flex items-center gap-2 px-10 py-5 rounded-full bg-white text-black font-bold text-lg hover:scale-105 transition-transform duration-300 shadow-[0_0_30px_rgba(255,255,255,0.3)]">
              Create Your Free Account <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-white/5 py-8 text-center text-sm text-gray-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Wallet className="w-4 h-4" />
            <span className="font-semibold text-gray-300">FinMate</span>
          </div>
          <p>© 2026 FinMate</p>
          <div className="flex gap-4">
            <a href="#" className="hover:text-[#00d4aa] transition-colors">Privacy</a>
            <a href="#" className="hover:text-[#00d4aa] transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
}