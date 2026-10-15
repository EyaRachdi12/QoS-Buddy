import { useState } from 'react';
import { motion } from 'framer-motion';
import { LogIn, UserPlus, Wifi, Monitor, PieChart, Crown, CheckCircle2 } from 'lucide-react';
import { authAPI, getApiError } from '../services/api';

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const roleConfig = {
    noc_engineer: {
      title: 'NOC Engineer',
      icon: Monitor,
      color: 'from-blue-600 to-blue-400',
      borderColor: 'border-blue-500/30',
      focusColor: 'focus:border-blue-500/50 focus:ring-blue-500/30',
      buttonColor: 'bg-blue-600 hover:bg-blue-500',
      welcomeText: 'Monitor your network in real-time',
      tips: [
        'Real-time KPI monitoring',
        'Anomaly & alert detection',
        'Automated diagnostics',
        'SLA violation alerts'
      ]
    },
    network_planner: {
      title: 'Network Planner',
      icon: PieChart,
      color: 'from-cyan-600 to-cyan-400',
      borderColor: 'border-cyan-500/30',
      focusColor: 'focus:border-cyan-500/50 focus:ring-cyan-500/30',
      buttonColor: 'bg-cyan-600 hover:bg-cyan-500',
      welcomeText: 'Plan smart investments for your network',
      tips: [
        'Zone performance scoring',
        'CAPEX recommendations',
        'Network capacity analysis',
        'Investment ROI forecasting'
      ]
    },
    executive: {
      title: 'Executive',
      icon: Crown,
      color: 'from-amber-600 to-amber-400',
      borderColor: 'border-amber-500/30',
      focusColor: 'focus:border-amber-500/50 focus:ring-amber-500/30',
      buttonColor: 'bg-amber-600 hover:bg-amber-500',
      welcomeText: 'Get high-level network health insights',
      tips: [
        'Executive dashboard overview',
        'SLA compliance metrics',
        'Financial impact analysis',
        'Strategic risk assessment'
      ]
    }
  };

  const currentRole = selectedRole ? roleConfig[selectedRole] : null;
  const Icon = currentRole?.icon;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!selectedRole) {
      setError('Please select a role');
      return;
    }

    setLoading(true);

    try {
      const data = await authAPI.login(username, password);
      authAPI.saveSession(data);
      onLogin({ username: data.username, role: data.role });
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-cyan-500/20 border border-cyan-500/30">
              <Wifi className="w-8 h-8 text-cyan-400" />
            </div>
            <h1 className="text-4xl font-bold text-white tracking-tight">QoS Buddy</h1>
          </div>
          <p className="text-slate-400 text-sm">Telecom Network Quality Analytics Platform</p>
        </div>

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl border border-white/10 bg-slate-900/80 backdrop-blur-xl overflow-hidden shadow-2xl"
        >
          <div className="grid md:grid-cols-2 gap-0">
            {/* Left: Role Selection */}
            <div className="p-8 border-r border-white/10">
              <h3 className="text-sm uppercase tracking-widest text-slate-400 mb-4">Step 1: Select Your Role</h3>
              <div className="space-y-3">
                {Object.entries(roleConfig).map(([roleId, config]) => {
                  const RoleIcon = config.icon;
                  return (
                    <motion.button
                      key={roleId}
                      type="button"
                      onClick={() => setSelectedRole(roleId)}
                      whileHover={{ scale: 1.02 }}
                      className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                        selectedRole === roleId
                          ? `${config.borderColor} bg-slate-800 border-current`
                          : 'border-white/10 bg-slate-800/50 hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg bg-gradient-to-br ${config.color}`}>
                          <RoleIcon className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <div className="font-semibold text-white">{config.title}</div>
                          <div className="text-xs text-slate-400">{config.welcomeText}</div>
                        </div>
                      </div>
                    </motion.button>
                  );
                })}
              </div>
            </div>

            {/* Right: Login Form & Tips */}
            <div className="p-8 flex flex-col">
              <motion.div
                key={selectedRole}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                {/* Role Header */}
                {currentRole && (
                  <div className="mb-6">
                    <h2 className={`text-xl font-semibold bg-gradient-to-r ${currentRole.color} bg-clip-text text-transparent mb-1`}>
                      {currentRole.title}
                    </h2>
                    <p className="text-sm text-slate-400">{currentRole.welcomeText}</p>
                  </div>
                )}

                {/* Login Form */}
                <form onSubmit={handleSubmit} className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm text-slate-400 mb-1.5 font-medium">Username</label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className={`w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-white/10 text-white placeholder-slate-500 focus:outline-none ${currentRole?.focusColor || 'focus:border-cyan-500/50 focus:ring-cyan-500/30'} transition-all`}
                      placeholder="Enter username"
                      required
                      minLength={3}
                      disabled={!selectedRole}
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-slate-400 mb-1.5 font-medium">Password</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={`w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-white/10 text-white placeholder-slate-500 focus:outline-none ${currentRole?.focusColor || 'focus:border-cyan-500/50 focus:ring-cyan-500/30'} transition-all`}
                      placeholder="Enter password"
                      required
                      minLength={6}
                      disabled={!selectedRole}
                    />
                  </div>

                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5"
                    >
                      {error}
                    </motion.div>
                  )}

                  <button
                    type="submit"
                    disabled={loading || !selectedRole}
                    className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl ${currentRole?.buttonColor || 'bg-cyan-600 hover:bg-cyan-500'} text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <LogIn className="w-4 h-4" /> Sign In
                      </>
                    )}
                  </button>
                </form>

                {/* Role Tips */}
                {currentRole && (
                  <div className="pt-4 border-t border-white/10">
                    <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">Quick Access</p>
                    <div className="space-y-2">
                      {currentRole.tips.map((tip) => (
                        <div key={tip} className="flex items-center gap-2 text-sm text-slate-300">
                          <CheckCircle2 className={`w-4 h-4 flex-shrink-0 bg-gradient-to-r ${currentRole.color} bg-clip-text text-transparent`} />
                          {tip}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-slate-400 text-sm mb-3">
            Don't have an account yet?
          </p>
          <a
            href="#register"
            className="text-cyan-400 hover:text-cyan-300 text-sm font-medium transition-colors"
          >
            Create an account as a new user
          </a>
          <p className="text-center text-[11px] text-slate-600 mt-4">
            QoS Buddy · Esprit PIDEV · 4DS8
          </p>
        </div>
      </motion.div>
    </div>
  );
}
