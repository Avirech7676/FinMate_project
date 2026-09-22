import { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { AuthContext } from '../AuthContext';
import { API_URL } from '../apiConfig';
import { motion } from 'framer-motion';
import { UserPlus, Wallet } from 'lucide-react';

export default function Signup() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // 1. Register User
      await axios.post(`${API_URL}/signup`, {
        email,
        password,
        full_name: fullName
      });

      // 2. Automatically Login exactly like Login.tsx
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await axios.post(`${API_URL}/login`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const token = res.data.access_token;
      
      // Fetch real user data from /me
      const meRes = await axios.get(`${API_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      auth?.login(token, meRes.data);
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;

      // #region agent log
      fetch('http://127.0.0.1:7500/ingest/cac223f9-661c-41c5-83f1-0a6ae276f3f1', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Debug-Session-Id': '907a7e',
        },
        body: JSON.stringify({
          sessionId: '907a7e',
          runId: 'signup-pre-fix',
          hypothesisId: 'H1-H3',
          location: 'Signup.tsx:48-52',
          message: 'signup_error_response',
          data: { detail },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion

      let friendly = 'Failed to sign up.';
      if (Array.isArray(detail)) {
        // Pydantic validation errors: join all messages
        friendly = detail
          .map((d: any) => d?.msg || JSON.stringify(d))
          .join(' | ');
      } else if (typeof detail === 'string') {
        friendly = detail;
      } else if (detail && typeof detail === 'object') {
        friendly = (detail as any).msg || JSON.stringify(detail);
      }

      setError(friendly);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-mesh px-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="glass-card w-full max-w-md p-8 relative overflow-hidden"
      >
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[--color-accent-blue] to-[--color-accent-purple]"></div>
        
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/10 glow-blue">
            <UserPlus className="text-[--color-accent-blue] w-6 h-6" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight">Create Account</h2>
          <p className="text-[--color-text-secondary] mt-2 text-sm text-center">Join FinMate to master your finances</p>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-lg bg-[--color-accent-red-glow] border border-[--color-accent-red] text-[--color-accent-red] text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[--color-text-secondary] mb-1">Full Name</label>
            <input 
              type="text" 
              required
              className="w-full bg-[#111827]/50 border border-white/10 rounded-lg px-4 py-2.5 outline-none focus:border-[--color-accent-blue] transition-colors"
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[--color-text-secondary] mb-1">Email</label>
            <input 
              type="email" 
              required
              className="w-full bg-[#111827]/50 border border-white/10 rounded-lg px-4 py-2.5 outline-none focus:border-[--color-accent-blue] transition-colors"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[--color-text-secondary] mb-1">Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-[#111827]/50 border border-white/10 rounded-lg px-4 py-2.5 outline-none focus:border-[--color-accent-blue] transition-colors"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full btn-primary bg-gradient-to-r from-[--color-accent-blue] to-[--color-accent-purple] hover:shadow-[0_8px_24px_rgba(167,139,250,0.25)] mt-4 flex items-center justify-center gap-2"
          >
            {loading ? 'Creating Account...' : (
              <>
                <Wallet className="w-4 h-4" /> Initialize Workspace 
              </>
            )}
          </button>
        </form>
        
        <p className="text-center mt-6 text-sm text-[--color-text-secondary]">
          Already have an account? <Link to="/login" className="text-[--color-accent-blue] hover:underline">Log in</Link>
        </p>
      </motion.div>
    </div>
  );
}
