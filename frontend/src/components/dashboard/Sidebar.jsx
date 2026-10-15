import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  BarChart3,
  Activity,
  Briefcase,
  BrainCircuit,
} from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { BO_MENU_ITEMS } from '../../constants/boMenu';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'ml', label: 'Détection & prédiction', icon: BrainCircuit },
  { id: 'diagnostics', label: 'Diagnostics', icon: BarChart3 },
];

export default function Sidebar({ activeTab, onTabChange }) {
  const { selectedBoId, selectBo } = useDashboard();

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-white/10 bg-slate-950/80 backdrop-blur-2xl min-h-[calc(100vh-0px)] sticky top-0">
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">QoS Buddy</h1>
            <p className="text-xs uppercase tracking-widest text-slate-500">Telecom intelligence</p>
          </div>
        </div>
      </div>

      <div className="p-4 flex-1 flex flex-col gap-6 overflow-y-auto">
        <div>
          <p className="px-2 mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500 flex items-center gap-2">
            <Briefcase className="w-3 h-3" />
            Business objectives
          </p>
          <nav className="space-y-1">
            {BO_MENU_ITEMS.map((item) => {
              const active = item.id === selectedBoId;
              return (
                <motion.button
                  key={item.id ?? 'all'}
                  type="button"
                  whileTap={{ scale: 0.98 }}
                  onClick={() => selectBo(item.id)}
                  className={`w-full text-left rounded-xl px-3 py-3 text-base transition-all border ${
                    active
                      ? 'bg-gradient-to-r from-cyan-500/25 to-violet-600/25 border-cyan-500/50 text-white shadow-lg shadow-cyan-500/10'
                      : 'border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-200'
                  }`}
                >
                  <span className="font-bold block text-lg">{item.short}</span>
                  <span className="text-sm opacity-80 line-clamp-2 leading-relaxed">{item.description}</span>
                </motion.button>
              );
            })}
          </nav>
        </div>

        <div>
          <p className="px-2 mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Application
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`w-full flex items-center gap-3 rounded-xl px-3 py-3 text-base font-medium transition-all ${
                    active
                      ? 'bg-white/10 text-white shadow-inner'
                      : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                  }`}
                >
                  <Icon className={`w-5 h-5 shrink-0 ${active ? 'text-cyan-400' : ''}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="p-4 border-t border-white/10 text-xs text-slate-500 leading-relaxed">
        Fichier unifié : chaque BO = filtre <code className="text-slate-400">source_bo</code> dans l’API.
      </div>
    </aside>
  );
}
