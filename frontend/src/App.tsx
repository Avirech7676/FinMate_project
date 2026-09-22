import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import Landing from './components/Landing';
import Login from './components/Login';
import Signup from './components/Signup';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/dashboard" element={<Dashboard initialSection="overview" />} />
          <Route path="/financial-overview" element={<Dashboard initialSection="overview" />} />
          <Route path="/forecast" element={<Dashboard initialSection="forecast" />} />
          <Route path="/subscriptions" element={<Dashboard initialSection="subscriptions" />} />
          <Route path="/simulation" element={<Dashboard initialSection="simulation" />} />
          <Route path="/financial-report" element={<Dashboard initialSection="reports" />} />
          <Route path="/ai-advisor" element={<Dashboard initialSection="advisor" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
