import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Wifi, 
  TrendingUp, 
  AlertTriangle, 
  Zap, 
  BarChart3,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';

export default function HomePage({ onGetStarted }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 overflow-hidden">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="relative pt-20 pb-32 px-4 sm:px-6 lg:px-8"
      >
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-60 h-60 bg-blue-500/10 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-6xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-4 mb-6 p-4 rounded-2xl bg-slate-800/50 border border-cyan-500/20">
              <div className="p-3 rounded-xl bg-cyan-500/20">
                <Wifi className="w-8 h-8 text-cyan-400" />
              </div>
              <div>
                <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  QoS Buddy
                </h1>
                <p className="text-sm text-slate-400 mt-1">Telecom Network Quality Analytics</p>
              </div>
            </div>

            <h2 className="text-3xl md:text-4xl font-bold text-white mt-8 mb-4 leading-tight">
              Intelligent Network Performance Intelligence Platform
            </h2>

            <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Detect anomalies before they impact your customers, predict SLA violations, and optimize CAPEX investments with AI-driven insights.
            </p>
          </motion.div>

          {/* Features Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="grid md:grid-cols-3 gap-6 mb-16"
          >
            {[
              {
                icon: AlertTriangle,
                title: "Real-time Anomaly Detection",
                desc: "Automatically detect network issues before customers notice"
              },
              {
                icon: TrendingUp,
                title: "SLA Violation Prediction",
                desc: "Forecast service level risks and prevent breaches proactively"
              },
              {
                icon: BarChart3,
                title: "Smart CAPEX Planning",
                desc: "Data-driven investment recommendations for network optimization"
              },
              {
                icon: Zap,
                title: "Automated Diagnostics",
                desc: "Instant root cause analysis for network degradations"
              },
              {
                icon: CheckCircle2,
                title: "Multi-Agent AI System",
                desc: "Collaborative AI agents for comprehensive network intelligence"
              },
              {
                icon: TrendingUp,
                title: "Predictive Analytics",
                desc: "Machine learning models trained on real telecom data"
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + idx * 0.05 }}
                className="p-6 rounded-xl border border-white/10 bg-slate-800/40 hover:bg-slate-800/60 transition-all hover:border-cyan-500/30"
              >
                <feature.icon className="w-8 h-8 text-cyan-400 mb-3" />
                <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-400">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>

          {/* Stats Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="grid md:grid-cols-4 gap-4 mb-16 text-center"
          >
            {[
              { num: "100+", label: "Network Zones" },
              { num: "20+ KPIs", label: "Monitored Metrics" },
              { num: "5 AI Agents", label: "Specialized Bots" },
              { num: "Real-time", label: "Data Processing" }
            ].map((stat, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-slate-800/40 border border-white/5">
                <div className="text-2xl font-bold text-cyan-400">{stat.num}</div>
                <div className="text-xs text-slate-400 mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>

          {/* Project Info */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="mb-16 p-8 rounded-2xl border border-cyan-500/20 bg-slate-800/40"
          >
            <h3 className="text-xl font-semibold text-cyan-400 mb-4">About This Project</h3>
            <div className="space-y-3 text-slate-300 text-sm leading-relaxed">
              <p>
                <strong>QoS Buddy</strong> is a comprehensive telecom network analytics platform developed as part of the PIDEV (Professional Integration Development) program at Esprit School of Engineering.
              </p>
              <p>
                The platform follows the <strong>TDSP (Team Data Science Process)</strong> methodology and implements 5 specialized AI agents for three distinct user roles:
              </p>
              <div className="grid md:grid-cols-3 gap-4 mt-4">
                <div className="p-3 rounded-lg bg-slate-700/50">
                  <div className="font-medium text-blue-400 mb-1">For NOC Engineers</div>
                  <p className="text-xs">Real-time monitoring, anomaly detection, and automated diagnostics</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-700/50">
                  <div className="font-medium text-cyan-400 mb-1">For Network Planners</div>
                  <p className="text-xs">CAPEX recommendations, zone scoring, and strategic insights</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-700/50">
                  <div className="font-medium text-amber-400 mb-1">For Executives</div>
                  <p className="text-xs">High-level health overview, SLA compliance, business impact analysis</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="text-center"
          >
            <button
              onClick={onGetStarted}
              className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-lg transition-all hover:shadow-2xl hover:shadow-cyan-500/25 group"
            >
              Get Started Now
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>

            <p className="text-slate-400 text-sm mt-4">
              Join NOC Engineers, Network Planners, and Executives optimizing telecom networks
            </p>
          </motion.div>
        </div>
      </motion.div>

      {/* Footer */}
      <div className="border-t border-white/10 py-8 px-4 text-center text-sm text-slate-500">
        <p>QoS Buddy · Esprit PIDEV 2025-2026 · 4DS8</p>
      </div>
    </div>
  );
}
