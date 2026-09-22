import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext } from '../AuthContext';
import Dashboard from './Dashboard';
import Login from './Login';

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} }))
  }
}));

const mockAuthContext = {
  user: {
    user_id: 1,
    email: 'test@example.com',
    full_name: 'Test User',
    currency: 'USD',
    currency_symbol: '$'
  },
  token: 'mock-jwt-token',
  login: vi.fn(),
  logout: vi.fn()
};

const renderWithAuth = (component: React.ReactNode, authValue = mockAuthContext) => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={authValue as any}>
        {component}
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('Dashboard Component', () => {
  it('renders FinMate 2.0 when user is authenticated', () => {
    renderWithAuth(<Dashboard />);
    expect(screen.getByText(/FinMate 2.0/i)).toBeInTheDocument();
  });

  it('renders navigation tabs for financial intelligence', () => {
    renderWithAuth(<Dashboard />);
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Transactions')).toBeInTheDocument();
    expect(screen.getByText('Forecast')).toBeInTheDocument();
    expect(screen.getByText('Subscriptions')).toBeInTheDocument();
    expect(screen.getByText('Simulator')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('AI Advisor')).toBeInTheDocument();
    expect(screen.getByText('Debate')).toBeInTheDocument();
  });

  it('allows clicking simulator tab', () => {
    renderWithAuth(<Dashboard />);
    const simTab = screen.getByText('Simulator');
    fireEvent.click(simTab);
    expect(simTab).toBeInTheDocument();
  });
});

describe('Login Component', () => {
  it('renders login form', () => {
    renderWithAuth(<Login />, { user: null, token: null, login: vi.fn(), logout: vi.fn() });
    expect(screen.getByText(/Welcome Back/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Access Dashboard/i })).toBeInTheDocument();
  });
});
