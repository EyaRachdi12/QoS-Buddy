import { motion } from 'framer-motion';

/** Glass card wrapper for modular BO agents. */
export default function AgentShell({ title, subtitle, icon: Icon, tint = 'cyan', children }) {
  const ring = {
    cyan: 'from-cyan-500/30 to-blue-600/20 border-cyan-500/40',
    violet: 'from-violet-500/30 to-fuchsia-600/20 border-violet-500/40',
    rose: 'from-rose-500/30 to-orange-600/20 border-rose-500/40',
    amber: 'from-amber-500/30 to-yellow-600/20 border-amber-500/40',
  };
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35 }}
      className={`rounded-2xl border bg-gradient-to-br p-5 backdrop-blur-xl shadow-lg ${ring[tint] || ring.cyan}`}
    >
      <div className="flex items-start gap-3 mb-3">
        {Icon && (
          <div className="p-2.5 rounded-xl bg-black/30 border border-white/10">
            <Icon className="w-6 h-6 text-white" />
          </div>
        )}
        <div>
          <h4 className="text-base font-bold text-white leading-snug">{title}</h4>
          {subtitle && <p className="text-sm text-slate-400 mt-1 leading-snug">{subtitle}</p>}
        </div>
      </div>
      <div className="text-sm text-slate-300 space-y-2">{children}</div>
    </motion.div>
  );
}
