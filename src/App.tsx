import React, { useState, useEffect } from 'react';
import { TicketItem } from './types';
import { QueueView } from './components/QueueView';
import { PlaygroundView } from './components/PlaygroundView';
import { BatchView } from './components/BatchView';
import { RulesExplorer } from './components/RulesExplorer';
import { MetricsView } from './components/MetricsView';
import { 
  Inbox, Play, Layers, BookOpen, BarChart3, Shield, 
  Cpu, Zap, CheckCircle2, AlertCircle
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'queue' | 'playground' | 'batch' | 'rules' | 'metrics'>('queue');
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  const fetchTickets = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/sample_tickets');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Backend service responded with error`);
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setTickets(data);
      } else {
        throw new Error('Invalid data format received from backend');
      }
    } catch (err: any) {
      console.error('Failed to load tickets:', err);
      setErrorMessage(`Сервермен байланыс қатесі: ${err.message}. Қайта көру үшін жаңартыңыз.`);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHealth = () => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealthStatus(data))
      .catch(err => console.error('Health check error:', err));
  };

  useEffect(() => {
    fetchTickets();
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateTicketStatus = (ticketId: string, status: TicketItem['status'], draftText?: string) => {
    setTickets(prev => prev.map(t => {
      if (t.ticket_id === ticketId) {
        return {
          ...t,
          status,
          triage: t.triage ? {
            ...t.triage,
            draft_reply: {
              ...t.triage.draft_reply,
              text: draftText || t.triage.draft_reply.text
            }
          } : undefined
        };
      }
      return t;
    }));
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Top Application Navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between shrink-0 z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-900/30">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-wide text-white block">
                GRAND MOBILE <span className="text-cyan-400 font-normal">COPILOT</span>
              </span>
              <span className="text-[10px] text-slate-400 font-medium block">
                Decentrathon 6.0 &bull; Official Taxonomy & 266 Authentic Rules
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-2 ml-4 pl-4 border-l border-slate-800 text-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              100% Offline Local CPU
            </span>
            <span className="text-slate-400 text-[11px]">
              p50: <strong className="text-slate-200">~3.2ms</strong> &bull; API Cost: <strong className="text-emerald-400">$0.00</strong>
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800/80">
          <button
            onClick={() => setActiveTab('queue')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              activeTab === 'queue'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Inbox className="w-3.5 h-3.5" />
            <span>Кезек (Queue)</span>
            <span className="px-1.5 py-0.2 rounded-full bg-cyan-950 text-cyan-300 text-[10px] font-mono border border-cyan-800/50">
              {tickets.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('playground')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              activeTab === 'playground'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            <span>Playground</span>
          </button>

          <button
            onClick={() => setActiveTab('batch')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              activeTab === 'batch'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Batch JSONL</span>
          </button>

          <button
            onClick={() => setActiveTab('rules')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              activeTab === 'rules'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Ережелер базасы (266)</span>
          </button>

          <button
            onClick={() => setActiveTab('metrics')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer ${
              activeTab === 'metrics'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Метрикалар мен есеп</span>
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === 'queue' && (
          <QueueView
            tickets={tickets}
            onUpdateTicketStatus={handleUpdateTicketStatus}
            onRefresh={fetchTickets}
            isLoading={isLoading}
            errorMessage={errorMessage}
          />
        )}
        {activeTab === 'playground' && <PlaygroundView />}
        {activeTab === 'batch' && <BatchView />}
        {activeTab === 'rules' && <RulesExplorer />}
        {activeTab === 'metrics' && <MetricsView />}
      </main>
    </div>
  );
}
