import { motion } from 'framer-motion';
import { ArrowRight, Monitor, PieChart, Crown, Wifi } from 'lucide-react';

export default function RegisterRoleSelector({ onSelectRole, onBack }) {
  const roles = [
    {
      id: 'noc_engineer',
      title: 'NOC Engineer',
      subtitle: 'Network Operations Center',
      icon: Monitor,
      color: 'from-blue-600 to-blue-400',
      description: 'Monitor real-time network performance',
      features: [
        'Real-time KPI monitoring',
        'Anomaly & alert detection',
        'Automated diagnostics',
        'Issue root-cause analysis',
        'SLA violation alerts',
        'Performance dashboards'
      ]
    },
    {
      id: 'network_planner',
      title: 'Network Planner',
      subtitle: 'Strategic Planning',
      icon: PieChart,
      color: 'from-cyan-600 to-cyan-400',
      description: 'Plan and optimize network investments',
      features: [
        'Zone performance scoring',
        'CAPEX recommendations',
        'Network capacity analysis',
        'Investment ROI forecasting',
        'Area-wise risk assessment',
        'Strategic planning insights'
      ]
    },
    {
      id: 'executive',
      title: 'Executive',
      subtitle: 'Leadership & Strategy',
      icon: Crown,
      color: 'from-amber-600 to-amber-400',
      description: 'High-level network health & business impact overview',
      features: [
        'Executive dashboard overview',
        'SLA compliance metrics',
        'Financial impact analysis',
        'Critical incidents only',
        'Business KPI summaries',
        'Strategic risk assessment'
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-6xl"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-3 mb-4 p-3 rounded-2xl bg-cyan-500/20 border border-cyan-500/30"
          >
            <Wifi className="w-6 h-6 text-cyan-400" />
            <span className="text-lg font-bold text-white">QoS Buddy</span>
          </motion.div>

          <h1 className="text-4xl font-bold text-white mb-3">Choose Your Role</h1>
          <p className="text-slate-400 text-lg">
            Select your role to get personalized features and dashboards
          </p>
        </div>

        {/* Role Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {roles.map((role, idx) => {
            const Icon = role.icon;
            return (
              <motion.button
                key={role.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + idx * 0.1 }}
                onClick={() => onSelectRole(role.id)}
                className="group p-8 rounded-2xl border border-white/10 bg-slate-800/50 hover:bg-slate-800/80 transition-all text-left hover:border-white/30 hover:shadow-2xl"
              >
                {/* Background gradient effect */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${role.color} opacity-0 group-hover:opacity-5 transition-opacity`} />

                <div className="relative z-10">
                  {/* Icon */}
                  <div className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br ${role.color} mb-4`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>

                  {/* Title */}
                  <h2 className="text-2xl font-bold text-white mb-1">{role.title}</h2>
                  <p className="text-sm text-slate-400 mb-4">{role.subtitle}</p>

                  {/* Description */}
                  <p className="text-slate-300 mb-6">{role.description}</p>

                  {/* Features list */}
                  <div className="space-y-2 mb-6">
                    {role.features.map((feature) => (
                      <div key={feature} className="flex items-start gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0 bg-gradient-to-r ${role.color}`} />
                        <span className="text-sm text-slate-300">{feature}</span>
                      </div>
                    ))}
                  </div>

                  {/* CTA */}
                  <div className="flex items-center gap-2 text-sm font-semibold group-hover:gap-3 transition-all">
                    <span className={`bg-gradient-to-r ${role.color} bg-clip-text text-transparent`}>
                      Continue as {role.title}
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
                  </div>
                </div>
              </motion.button>
            );
          })}
        </div>

        {/* Back button */}
        <div className="text-center">
          <button
            type="button"
            onClick={onBack}
            className="text-slate-400 hover:text-white text-sm transition-colors"
          >
            ← Back to Home
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-slate-600 mt-8">
          Your role determines which features and dashboards you'll see
        </p>
      </motion.div>
    </div>
  );
}
