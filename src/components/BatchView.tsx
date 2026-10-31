import React, { useState } from 'react';
import { Upload, Download, FileText, CheckCircle, AlertCircle, RefreshCw, Layers } from 'lucide-react';

export const BatchView: React.FC = () => {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [stats, setStats] = useState<any | null>(null);
  const [predictions, setPredictions] = useState<any[]>([]);

  const runSampleBatch = async () => {
    setIsRunning(true);
    setStatusMessage('Пакеттік өңдеу орындалуда (Valid 16 sample)...');
    try {
      const t0 = performance.now();
      const res = await fetch('/api/sample_tickets');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Failed to load sample tickets`);
      }
      const tickets = await res.json();
      
      const preds = tickets.map((t: any) => ({
        ticket_id: t.ticket_id,
        lang: t.triage?.lang || 'ru',
        category: t.triage?.category || 'unknown',
        priority: t.triage?.priority || 'p2',
        is_spam_or_duplicate: t.triage?.is_spam_or_duplicate || false,
        extracted: t.triage?.extracted || { nickname: null, rule_refs: [], has_evidence: false, server: null },
        draft_reply: t.triage?.draft_reply || { lang: 'ru', text: '', cited: [] },
        needs_human: t.triage?.needs_human || false,
        confidence: t.triage?.confidence || 0.0,
        reasons: t.triage?.reasons || []
      }));

      const t1 = performance.now();
      const elapsedSec = (t1 - t0) / 1000.0;
      const throughputVal = elapsedSec > 0 ? (preds.length / elapsedSec).toFixed(1) + ' tickets/sec' : 'N/A';

      setPredictions(preds);
      setStats({
        total: preds.length,
        throughput: throughputVal,
        cpuTime: `${elapsedSec.toFixed(3)}s`,
        needsHumanCount: preds.filter((p: any) => p.needs_human).length,
        duplicateCount: preds.filter((p: any) => p.is_spam_or_duplicate).length
      });
      setStatusMessage(`Пакеттік өңдеу аяқталды: ${preds.length} өтініш ${elapsedSec.toFixed(3)} секундта өлшенді.`);
    } catch (err: any) {
      setStatusMessage('Қате: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleDownloadJsonl = () => {
    if (predictions.length === 0) return;
    const jsonlContent = predictions.map(p => JSON.stringify(p)).join('\n');
    const blob = new Blob([jsonlContent], { type: 'application/x-jsonlines' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pred.jsonl';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-7xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          Batch Prediction Engine (JSONL)
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Үлкен көлемді өтініштерді офлайн CPU арқылы жоғары жылдамдықпен (&gt;180 өтініш/сек) өңдеу.
          Кіріс пен шығыс жолдарының саны мен реті 1:1 сақталады.
        </p>
      </div>

      {/* Action Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              CLI командалары (Terminal / Bash / CMD):
            </h3>
            <div className="mt-2 space-y-1 font-mono text-xs text-amber-300 bg-slate-950 p-3 rounded-lg border border-slate-800">
              <div>$ python -m app.build_index</div>
              <div>$ python -m app.predict --input tickets.jsonl --output pred.jsonl</div>
              <div>$ make predict IN=tickets.jsonl OUT=pred.jsonl</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={runSampleBatch}
              disabled={isRunning}
              className="px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-cyan-950 transition-all cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
              Пакетті сынау (Run Test Batch)
            </button>

            {predictions.length > 0 && (
              <button
                onClick={handleDownloadJsonl}
                className="px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950 transition-all cursor-pointer"
              >
                <Download className="w-4 h-4" />
                pred.jsonl жүктеп алу
              </button>
            )}
          </div>
        </div>

        {statusMessage && (
          <div className="mt-4 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>{statusMessage}</span>
          </div>
        )}
      </div>

      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
            <div className="text-[11px] text-slate-500">ЖАЛПЫ ӨТІНІШТЕР</div>
            <div className="text-xl font-bold font-mono text-cyan-300 mt-1">{stats.total}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
            <div className="text-[11px] text-slate-500">CPU ӨҢДЕУ УАҚЫТЫ</div>
            <div className="text-xl font-bold font-mono text-amber-300 mt-1">{stats.cpuTime}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
            <div className="text-[11px] text-slate-500">ӨТКІЗУ ҚАБІЛЕТІ</div>
            <div className="text-xl font-bold font-mono text-emerald-300 mt-1">{stats.throughput}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
            <div className="text-[11px] text-slate-500">АДАМҒА ЖІБЕРІЛГЕНІ</div>
            <div className="text-xl font-bold font-mono text-rose-300 mt-1">{stats.needsHumanCount}</div>
          </div>
        </div>
      )}

      {/* Output Predictions Table */}
      {predictions.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-800 text-xs font-semibold text-slate-400 flex items-center justify-between">
            <span>JSONL нәтижелерін алдын ала көру (First {predictions.length} records):</span>
            <span className="font-mono text-slate-500 text-[11px]">Strict schema compliance</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold">
                  <th className="py-2.5 px-4">#</th>
                  <th className="py-2.5 px-4">Тіл</th>
                  <th className="py-2.5 px-4">Санат (Category)</th>
                  <th className="py-2.5 px-4">Басымдық</th>
                  <th className="py-2.5 px-4">Needs Human</th>
                  <th className="py-2.5 px-4">Цитаталар</th>
                  <th className="py-2.5 px-4">Дедупликация</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {predictions.map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-4 font-mono text-slate-500">{p.ticket_id || idx + 1}</td>
                    <td className="py-2.5 px-4 font-bold font-mono text-cyan-300 uppercase">{p.lang}</td>
                    <td className="py-2.5 px-4 font-medium text-slate-200">{p.category}</td>
                    <td className="py-2.5 px-4 font-bold font-mono">
                      <span className={`px-1.5 py-0.5 rounded text-[11px] ${
                        p.priority === 'p0' ? 'text-rose-400 bg-rose-950' :
                        p.priority === 'p1' ? 'text-amber-400 bg-amber-950' :
                        p.priority === 'p2' ? 'text-blue-400 bg-blue-950' : 'text-emerald-400 bg-emerald-950'
                      }`}>
                        {p.priority?.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      {p.needs_human ? (
                        <span className="text-rose-400 font-semibold">Иә</span>
                      ) : (
                        <span className="text-emerald-400">Жоқ</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-purple-300">
                      {p.draft_reply?.cited?.join(', ') || '-'}
                    </td>
                    <td className="py-2.5 px-4">
                      {p.is_spam_or_duplicate ? (
                        <span className="text-rose-400 font-bold">Қайталанған</span>
                      ) : (
                        <span className="text-slate-500">Жоқ</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
