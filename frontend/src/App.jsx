import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, LogOut, MessageCircle } from 'lucide-react';
import ChatbotPanel from './components/ChatbotPanel';
import DiagnosticPanel from './components/DiagnosticPanel';
import LoginPage from './components/LoginPage';
import HomePage from './components/HomePage';
import RegisterRoleSelector from './components/RegisterRoleSelector';
import NOCEngineerRegister from './components/NOCEngineerRegister';
import NetworkPlannerRegister from './components/NetworkPlannerRegister';
import ExecutiveRegister from './components/ExecutiveRegister';
import { DashboardProvider, useDashboard } from './context/DashboardContext';
import Sidebar from './components/dashboard/Sidebar';
import DashboardMain from './components/dashboard/DashboardMain';
import MlStudioPanel from './components/dashboard/MlStudioPanel';
import { BO_MENU_ITEMS } from './constants/boMenu';
import { authAPI } from './services/api';

function MobileDrawer({ open, onClose, activeTab, onTabChange }) {
  const { selectedBoId, selectBo } = useDashboard();
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 md:hidden"
      role="presentation"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'tween', duration: 0.28 }}
        className="absolute right-0 top-0 h-full w-[min(100%,320px)] bg-slate-950 border-l border-white/10 shadow-2xl p-4 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <span className="text-white font-semibold">Menu</span>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:bg-white/10"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Business objectives</p>
        <div className="space-y-1 mb-6">
          {BO_MENU_ITEMS.map((item) => (
            <button
              key={item.id ?? 'all'}
              type="button"
              onClick={() => {
                selectBo(item.id);
                onClose();
              }}
              className={`w-full text-left rounded-xl px-3 py-2 text-sm border ${
                item.id === selectedBoId
                  ? 'border-cyan-500/50 bg-cyan-500/10 text-white'
                  : 'border-transparent text-slate-400'
              }`}
            >
              <span className="font-medium">{item.short}</span>
            </button>
          ))}
        </div>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Navigate</p>
        <div className="space-y-1">
          {[
            { id: 'dashboard', label: 'Dashboard' },
            { id: 'ml', label: 'Detection & prediction' },
            { id: 'diagnostics', label: 'Diagnostics' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                onTabChange(t.id);
                onClose();
              }}
              className={`w-full text-left rounded-xl px-3 py-2.5 text-sm ${
                activeTab === t.id ? 'bg-white/15 text-white' : 'text-slate-400'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

function AppShell({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <div className="flex">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

        <div className="flex-1 flex flex-col min-w-0 min-h-screen">
          <header className="sticky top-0 z-40 flex items-center justify-between px-4 py-3 border-b border-white/10 bg-slate-950/90 backdrop-blur-xl">
            <span className="font-semibold text-white hidden md:block">QoS Buddy</span>
            <span className="font-semibold text-white md:hidden">QoS Buddy</span>

            <div className="flex items-center gap-3">
              {user && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">
                    {user.username}{' '}
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400">
                      {user.role}
                    </span>
                  </span>
                  <button
                    type="button"
                    onClick={onLogout}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Sign out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              )}
              <button
                type="button"
                onClick={() => setMobileOpen(true)}
                className="p-2 rounded-xl bg-white/10 text-white md:hidden"
                aria-label="Open menu"
              >
                <Menu className="w-5 h-5" />
              </button>
            </div>
          </header>

          <AnimatePresence>
            {mobileOpen && (
              <MobileDrawer
                open={mobileOpen}
                onClose={() => setMobileOpen(false)}
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />
            )}
          </AnimatePresence>

          <main className="flex-1 p-4 md:p-8 max-w-[1600px] w-full mx-auto">
            <AnimatePresence mode="wait">
              {activeTab === 'dashboard' && (
                <motion.div
                  key="dashboard"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <DashboardMain />
                </motion.div>
              )}
              {activeTab === 'ml' && (
                <motion.div
                  key="ml"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <MlStudioPanel />
                </motion.div>
              )}
              {activeTab === 'diagnostics' && (
                <motion.div
                  key="diagnostics"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-[calc(100vh-8rem)] md:h-[calc(100vh-4rem)]"
                >
                  <DiagnosticPanel />
                </motion.div>
              )}
            </AnimatePresence>
          </main>

          <AnimatePresence>
            {chatOpen && (
              <div className="fixed inset-0 z-50 pointer-events-none">
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                  className="absolute inset-0 bg-gradient-to-l from-slate-950/35 via-transparent to-transparent"
                />
                <motion.div
                  initial={{ opacity: 0, y: 20, scale: 0.95, x: 10 }}
                  animate={{ opacity: 1, y: 0, scale: 1, x: 0 }}
                  exit={{ opacity: 0, y: 20, scale: 0.95, x: 10 }}
                  transition={{ type: 'spring', stiffness: 260, damping: 24, mass: 0.8 }}
                  className="pointer-events-auto absolute right-4 md:right-6 bottom-24 h-[70vh] min-h-[520px] w-[min(560px,calc(100vw-2rem))]"
                >
                  <ChatbotPanel />
                </motion.div>
              </div>
            )}
          </AnimatePresence>

          <button
            type="button"
            onClick={() => setChatOpen((prev) => !prev)}
            className="fixed right-6 bottom-8 z-50 h-14 w-14 rounded-full bg-cyan-500 text-slate-950 shadow-xl shadow-cyan-500/30 transition hover:bg-cyan-400 hover:scale-105 active:scale-95 flex items-center justify-center"
            title={chatOpen ? 'Close AI Advisor' : 'Open AI Advisor'}
            aria-label={chatOpen ? 'Close AI Advisor' : 'Open AI Advisor'}
          >
            {chatOpen ? <X className="w-6 h-6" /> : <MessageCircle className="w-6 h-6" />}
          </button>

          <footer className="border-t border-white/10 py-4 px-6 text-center text-[11px] text-slate-600">
            QoS Buddy v2.0 · Esprit PIDEV · Unified dataset primary source
          </footer>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(() => authAPI.getStoredUser());
  const [screen, setScreen] = useState('home'); // home, login, role-selector, noc-register, planner-register, executive-register
  
  useEffect(() => {
    // If user exists, they should see dashboard
    if (user) {
      setScreen('dashboard');
    } else {
      // Start at home page for new visitors
      setScreen('home');
    }
  }, [user]);

  const handleGetStarted = () => {
    setScreen('role-selector');
  };

  const handleSelectRole = (role) => {
    if (role === 'noc_engineer') {
      setScreen('noc-register');
    } else if (role === 'network_planner') {
      setScreen('planner-register');
    } else if (role === 'executive') {
      setScreen('executive-register');
    }
  };

  const handleRegisterSuccess = (userData) => {
    setUser(userData);
    setScreen('dashboard');
  };

  const handleLogin = (userData) => {
    setUser(userData);
    setScreen('dashboard');
  };

  const handleLogout = () => {
    authAPI.logout();
    setUser(null);
    setScreen('home');
  };

  // Home Page
  if (screen === 'home') {
    return (
      <HomePage key="home" onGetStarted={handleGetStarted} />
    );
  }

  // Role Selector
  if (screen === 'role-selector') {
    return (
      <RegisterRoleSelector 
        key="role-selector"
        onSelectRole={handleSelectRole}
        onBack={() => setScreen('home')}
      />
    );
  }

  // NOC Engineer Registration
  if (screen === 'noc-register') {
    return (
      <NOCEngineerRegister 
        key="noc-register"
        onRegisterSuccess={handleRegisterSuccess}
        onBack={() => setScreen('role-selector')}
      />
    );
  }

  // Network Planner Registration
  if (screen === 'planner-register') {
    return (
      <NetworkPlannerRegister 
        key="planner-register"
        onRegisterSuccess={handleRegisterSuccess}
        onBack={() => setScreen('role-selector')}
      />
    );
  }

  // Executive Registration
  if (screen === 'executive-register') {
    return (
      <ExecutiveRegister 
        key="executive-register"
        onRegisterSuccess={handleRegisterSuccess}
        onBack={() => setScreen('role-selector')}
      />
    );
  }

  // Login Page
  if (screen === 'login' || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <LoginPage onLogin={handleLogin} />
        <button
          onClick={() => setScreen('home')}
          className="fixed bottom-4 left-4 text-slate-400 hover:text-white text-sm transition-colors"
        >
          ← Back to Home
        </button>
      </div>
    );
  }

  // Dashboard
  return (
    <DashboardProvider>
      <AppShell user={user} onLogout={handleLogout} />
    </DashboardProvider>
  );
}
