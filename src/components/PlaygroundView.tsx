import React, { useState } from 'react';
import { TriageResult } from '../types';
import { Play, Sparkles, Copy, Check, ShieldAlert, AlertTriangle, Code, ArrowRight } from 'lucide-react';

export const PlaygroundView: React.FC = () => {
  const [inputText, setInputText] = useState<string>('Arman_Petrov мені қорлады және балағаттады');
  const [kind, setKind] = useState<string>('complaint');
  const [reporterHash, setReporterHash] = useState<string>('rep_kz_001');
  const [attachmentsCount, setAttachmentsCount] = useState<number>(2);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const presets = [
    {
      title: '🇰🇿 Қазақша Қорлау (complaint.insult)',
      kind: 'complaint',
      text: 'Arman_Petrov мені қорлады және балағаттады, скрин бар',
      rep: 'rep_kz_001',
      att: 2
    },
    {
      title: '🇰🇿 Қазақша CP1251 қате кодировка (complaint.db)',
      kind: 'complaint',
      text: 'Сєлеметсіз бе! Бўл ойыншы автобазарда мені кґлікпен ќасаќана басып ґлтірді, ДБ жасады!',
      rep: 'rep_kz_002',
      att: 1
    },
    {
      title: '🇺🇿 Өзбекше апостроф oʻldirdi (complaint.dm)',
      kind: 'complaint',
      text: "Salom adminlar. Men tinch turgandim, kelib sababsiz oʻldirib ketdi, DM qildi.",
      rep: 'rep_uz_001',
      att: 0
    },
    {
      title: '🇷🇺 Чит / Speedhack (complaint.cheat, p1)',
      kind: 'complaint',
      text: 'Игрок летает speedhack и разносит всех рванкой на спавне!',
      rep: 'rep_ru_001',
      att: 0
    },
    {
      title: '🇷🇺 Донат / Төлем (report.payment, p1)',
      kind: 'report',
      text: 'Задонатил 500 рублей через СБП, деньги списались, а Grand Coins на баланс не поступили уже 2 часа. Чек прикрепил.',
      rep: 'rep_ru_002',
      att: 1
    },
    {
      title: '🇷🇺 Взлом аккаунта (report.account, p0)',
      kind: 'report',
      text: 'Срочно помогите, меня взломали! Захожу на сервер, пишет неверный пароль, почта отвязана и 2FA сброшен. Ник Sergei_Gromov.',
      rep: 'rep_ru_003',
      att: 0
    },
    {
      title: '⚖️ Бан апелляциясы (complaint.admin, needs_human=true)',
      kind: 'complaint',
      text: 'Администратор дал мне бан за DM. Я не согласен с наказанием, прошу пересмотреть.',
      rep: 'rep_ru_004',
      att: 0
    },
    {
      title: '⚖️ Мут апелляциясы (complaint.admin, needs_human=true)',
      kind: 'complaint',
      text: 'Мне выдали мут за оскорбление родных, я с этим наказанием не согласен.',
      rep: 'rep_ru_005',
      att: 0
    },
    {
      title: '🔍 Тіркеме жоқ делінген мәтін (has_evidence=false)',
      kind: 'complaint',
      text: 'Мені ДМ жасап өлтірді, бірақ өкінішке орай скринов нет, дәлел жоқ.',
      rep: 'rep_kz_003',
      att: 0
    }
  ];

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRunTriage = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Official messages format
      const response = await fetch('/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          kind,
          ticket_id: `PLAYGROUND_${Date.now()}`,
          reporter_hash: reporterHash,
          created_at: new Date().toISOString(),
          messages: [
            {
              role: 'player',
              text: inputText,
              attachments: attachmentsCount
            }
          ]
        })
      });
      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errText || response.statusText}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error('Triage error:', err);
      setErrorMessage(err.message || 'Қызметпен байланыс қатесі орын алды');
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-7xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-cyan-400" />
          Interactive Triage Playground (Official Input/Output Contract)
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Ресми келісімшарт: <code className="text-cyan-400 font-mono">&#123;kind, messages: [&#123;role, text, attachments&#125;]&#125;</code> &rarr; Ресми санат кодтары (e.g. <code>complaint.insult</code>).
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="mb-6">
        <div className="text-xs font-semibold text-slate-400 mb-2">Ресми сынақ сценарийлері (Presets):</div>
        <div className="flex flex-wrap gap-2">
          {presets.map((p, i) => (
            <button
              key={i}
              onClick={() => {
                setInputText(p.text);
                setKind(p.kind);
                setReporterHash(p.rep);
                setAttachmentsCount(p.att);
              }}
              className="text-xs bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input Form */}
        <div className="space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300">
                Ойыншы хабарламасы (Player Message Text):
              </label>
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span>Kind:</span>
                <select
                  value={kind}
                  onChange={e => setKind(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-cyan-400 px-2 py-0.5 rounded text-xs font-mono focus:outline-none"
                >
                  <option value="complaint">complaint</option>
                  <option value="report">report</option>
                </select>
              </div>
            </div>

            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              rows={6}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-sans focus:border-cyan-500 focus:outline-none resize-none leading-relaxed"
              placeholder="Хабарлама мәтіні..."
            />

            <div className="grid grid-cols-2 gap-4 mt-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  Reporter Hash:
                </label>
                <input
                  type="text"
                  value={reporterHash}
                  onChange={e => setReporterHash(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 font-mono text-xs focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  Attachments (Тіркеме саны):
                </label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={attachmentsCount}
                  onChange={e => setAttachmentsCount(parseInt(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 font-mono text-xs focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              onClick={handleRunTriage}
              disabled={isLoading || !inputText.trim()}
              className="mt-5 w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-cyan-950 transition-all cursor-pointer"
            >
              {isLoading ? (
                <>Өңделуде...</>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  POST /triage орындау
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Results Display */}
        <div>
          {errorMessage && (
            <div className="bg-rose-950/60 border border-rose-800 text-rose-300 p-4 rounded-xl text-xs flex items-start gap-3 mb-4">
              <div className="p-1 rounded-md bg-rose-900/50 text-rose-300 font-bold">!</div>
              <div>
                <div className="font-semibold text-rose-200">HTTP Байланыс Қатесі:</div>
                <div className="mt-0.5 text-rose-300 font-mono text-[11px]">{errorMessage}</div>
              </div>
            </div>
          )}

          {result ? (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  Triage нәтижесі (Official Schema):
                </span>
                <button
                  onClick={handleCopyJson}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Көшірілді!' : 'JSON көшіру'}
                </button>
              </div>

              {/* Status Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px]">ТІЛ</div>
                  <div className="text-cyan-300 font-bold font-mono text-sm uppercase mt-0.5">{result.lang}</div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px]">БАСЫМДЫҚ</div>
                  <div className={`font-bold font-mono text-sm uppercase mt-0.5 ${
                    result.priority === 'p0' ? 'text-rose-400' :
                    result.priority === 'p1' ? 'text-amber-400' :
                    result.priority === 'p2' ? 'text-blue-400' : 'text-emerald-400'
                  }`}>
                    {result.priority}
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px]">NEEDS HUMAN</div>
                  <div className="font-bold text-xs mt-0.5">
                    {result.needs_human ? (
                      <span className="text-rose-400 font-semibold">ИӘ (Human)</span>
                    ) : (
                      <span className="text-emerald-400 font-semibold">ЖОҚ (Auto)</span>
                    )}
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px]">CONFIDENCE</div>
                  <div className="text-amber-400 font-bold font-mono text-sm mt-0.5">{result.confidence}</div>
                </div>
              </div>

              {/* Official Category Code */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div className="text-slate-500 font-medium">Ресми санат (Official Category Code):</div>
                <div className="text-sm font-bold font-mono text-cyan-300 mt-0.5">{result.category}</div>
              </div>

              {/* Extracted object */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div className="text-slate-500 font-medium mb-1">Extracted Metadata (Ресми құрылым):</div>
                <div className="font-mono text-[11px] text-slate-300 space-y-0.5 bg-slate-900/60 p-2.5 rounded border border-slate-800">
                  <div>nickname: <span className="text-cyan-300">{JSON.stringify(result.extracted?.nickname)}</span></div>
                  <div>rule_refs: <span className="text-purple-300">{JSON.stringify(result.extracted?.rule_refs)}</span></div>
                  <div>has_evidence: <span className={result.extracted?.has_evidence ? "text-emerald-400" : "text-slate-500"}>{String(result.extracted?.has_evidence)}</span></div>
                  <div>server: <span className="text-amber-300">{JSON.stringify(result.extracted?.server)}</span></div>
                </div>
              </div>

              {/* Draft Reply */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div className="text-slate-400 font-medium mb-1.5 flex items-center justify-between">
                  <span>Жауап жобасы (Draft Reply):</span>
                  <span className="text-purple-400 font-mono text-[11px]">
                    cited: {JSON.stringify(result.draft_reply?.cited || [])}
                  </span>
                </div>
                <div className="text-slate-200 leading-relaxed font-sans bg-slate-900/50 p-2.5 rounded border border-slate-800">
                  {result.draft_reply?.text}
                </div>
              </div>

              {/* Reasons */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div className="text-slate-400 font-medium mb-1">Негіздемелер (Reasons):</div>
                <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                  {result.reasons?.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs text-center">
              <Code className="w-8 h-8 text-slate-600 mb-2" />
              <span>Тестілеу үшін сол жақтағы батырманы басыңыз.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
