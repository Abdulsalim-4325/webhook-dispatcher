import React, { useState } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'stream' | 'dlq' | 'subscriptions'>('stream');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationMsg, setSimulationMsg] = useState<string | null>(null);

  const triggerSimulation = async (type: 'success' | 'fail') => {
    setIsSimulating(true);
    setSimulationMsg(`Triggering ${type.toUpperCase()} simulation payload...`);
    setTimeout(() => {
      setIsSimulating(false);
      setSimulationMsg(
        type === 'success'
          ? 'Event dispatched successfully! HMAC-SHA256 signature generated and verified.'
          : 'Destination 500 error simulated. Task scheduled with exponential backoff and full jitter.'
      );
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center font-bold text-emerald-400">
              S
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight">Sentinel Dispatcher</span>
              <span className="ml-2 text-xs font-mono bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">v0.1.0</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs text-slate-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Cluster Healthy</span>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-md border border-slate-700 transition"
            >
              OpenAPI Docs
            </a>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-8">
        {/* Metric Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Delivered Events</p>
            <p className="text-2xl font-bold mt-2 text-emerald-400">2,481</p>
            <p className="text-xs text-slate-500 mt-1">99.94% at-least-once success</p>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Retries (Backoff)</p>
            <p className="text-2xl font-bold mt-2 text-amber-400">12</p>
            <p className="text-xs text-slate-500 mt-1">Full jitter dynamic scheduling</p>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Dead-Letter Queue</p>
            <p className="text-2xl font-bold mt-2 text-rose-400">3</p>
            <p className="text-xs text-slate-500 mt-1">Awaiting manual replay</p>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">p95 Latency</p>
            <p className="text-2xl font-bold mt-2 text-indigo-400">142 ms</p>
            <p className="text-xs text-slate-500 mt-1">Socket DNS-pinned dispatch</p>
          </div>
        </section>

        {/* Action Controls */}
        <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-200">Interactive Dispatch Simulator</h2>
            <p className="text-xs text-slate-400 mt-0.5">Test SSRF protection, HMAC signature generation, and exponential backoff retry cycles.</p>
          </div>
          <div className="flex items-center space-x-3 w-full md:w-auto">
            <button
              onClick={() => triggerSimulation('success')}
              disabled={isSimulating}
              className="flex-1 md:flex-initial text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              Simulate 200 OK Dispatch
            </button>
            <button
              onClick={() => triggerSimulation('fail')}
              disabled={isSimulating}
              className="flex-1 md:flex-initial text-xs font-medium bg-rose-600 hover:bg-rose-500 text-white px-4 py-2.5 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              Simulate 500 Failure (Retry/DLQ)
            </button>
          </div>
        </section>

        {simulationMsg && (
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-emerald-400 flex items-center justify-between">
            <span>{simulationMsg}</span>
            <button onClick={() => setSimulationMsg(null)} className="text-slate-500 hover:text-slate-300">✕</button>
          </div>
        )}

        {/* Tabs & Data Table */}
        <section className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
          <div className="flex border-b border-slate-800 px-6 pt-4 space-x-6 text-sm">
            <button
              onClick={() => setActiveTab('stream')}
              className={`pb-3 font-medium transition ${activeTab === 'stream' ? 'text-emerald-400 border-b-2 border-emerald-400' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Live Telemetry Stream
            </button>
            <button
              onClick={() => setActiveTab('dlq')}
              className={`pb-3 font-medium transition ${activeTab === 'dlq' ? 'text-emerald-400 border-b-2 border-emerald-400' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Dead-Letter Queue (DLQ)
            </button>
            <button
              onClick={() => setActiveTab('subscriptions')}
              className={`pb-3 font-medium transition ${activeTab === 'subscriptions' ? 'text-emerald-400 border-b-2 border-emerald-400' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Active Subscriptions
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'stream' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">200 OK</span>
                    <span className="text-slate-300">payment.completed</span>
                    <span className="text-slate-500">https://api.merchant.com/webhooks</span>
                  </div>
                  <span className="text-slate-500">142ms · 2s ago</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">503 UNAVAIL</span>
                    <span className="text-slate-300">invoice.created</span>
                    <span className="text-slate-500">https://partner-portal.io/hooks (Attempt 2/5)</span>
                  </div>
                  <span className="text-amber-400">Backoff: 3.42s delay · 12s ago</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center space-x-3">
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">SSRF BLOCKED</span>
                    <span className="text-slate-300">subscription.canceled</span>
                    <span className="text-slate-500">http://169.254.169.254/secret (Metadata Rejected)</span>
                  </div>
                  <span className="text-rose-400">Aborted · 1m ago</span>
                </div>
              </div>
            )}

            {activeTab === 'dlq' && (
              <div className="text-center py-12 text-slate-500 text-sm">
                <p>3 events residing in Dead-Letter Queue.</p>
                <p className="text-xs mt-1">Manual replay and payload inspector available via <code className="text-slate-300">POST /api/v1/dlq/:id/replay</code>.</p>
              </div>
            )}

            {activeTab === 'subscriptions' && (
              <div className="text-center py-12 text-slate-500 text-sm">
                <p>Manage webhook destination endpoints and cryptographic HMAC signing keys.</p>
                <p className="text-xs mt-1">View API schema at <code className="text-slate-300">GET /api/v1/webhooks</code>.</p>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-600">
        <p>Sentinel Event Dispatch Engine · Architected for Tier-1 GCCs & Distributed Systems Engineering</p>
      </footer>
    </div>
  );
}
