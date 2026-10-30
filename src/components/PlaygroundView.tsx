import React, { useState } from 'react';
import { TriageResult } from '../types';
import { Play, Sparkles, Copy, Check, ShieldAlert, AlertTriangle, Code, ArrowRight } from 'lucide-react';

export const PlaygroundView: React.FC = () => {
  const [inputText, setInputText] = useState<string>(
    'Сәлеметсіз бе! Мен спавнда тыныш тұрғанда Arman_Kaspi деген ойыншы келіп еш себепсіз диглмен атып өлтірді (DM). 2.1 ережесін бұзды. Жазалаңыздаршы!'
  );
  const [reporterHash, setReporterHash] = useState<string>('player_test_kz');
  const [imagesCount, setImagesCount] = useState<number>(1);
  const [result, setResult] = useState<TriageResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const presets = [
    {
      title: '🇰🇿 Қазақша DM шағымы',
      text: 'Сәлеметсіз бе! Мен спавнда тыныш тұрғанда Arman_Kaspi деген ойыншы келіп еш себепсіз диглмен атып өлтірді (DM). 2.1 ережесін бұзды. Жазалаңыздаршы!',
      rep: 'rep_kz_001',
      img: 1
    },
    {
      title: '🇰🇿 Қазақша CP1251 қате кодировка',
      text: 'Сєлеметсіз бе! Бўл ойыншы автобазарда мені кґлікпен ќасаќана басып ґлтірді, ДБ жасады! Скрин бар.',
      rep: 'rep_kz_002',
      img: 1
    },
    {
      title: '🇺🇿 Өзбекше Донат мәселесі (p1, Human)',
      text: "Salom adminlar. Men Click orqali 50000 so'mga donat qildim, kartamdan pul yechildi lekin Grand Coins hisobimga tushmadi. Chek ilova qildim, yordam bering.",
      rep: 'rep_uz_001',
      img: 1
    },
    {
      title: '🇷🇺 Аккаунт ұрлануы / Взлом (p0, Human)',
      text: 'Срочно помогите, меня взломали! Захожу на сервер, пишет неверный пароль, почта отвязана и 2FA сброшен. Ник Sergei_Gromov, номер аккаунта 184920.',
      rep: 'rep_ru_001',
      img: 0
    },
    {
      title: '🇷🇺 Зеленая Зона (GZ 3.1 контексті)',
      text: 'Игрок Vanya_Shooter устроил массовую стрельбу прямо в здании ЦБ в Зеленой Зоне (GZ 3.1). Накажите за DM в ЗЗ!',
      rep: 'rep_ru_002',
      img: 2
    },
    {
      title: '🇬🇧 English Speedhack Cheats',
      text: 'Player Dark_Rider is using speedhack and flying car on server 2. He is crashing into everyone and teleporting around.',
      rep: 'rep_en_001',
      img: 0
    }
  ];

  const handleRunTriage = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticket_id: `PLAYGROUND_${Date.now()}`,
          reporter_hash: reporterHash,
          created_at: new Date().toISOString(),
          text: inputText,
          images_count: imagesCount
        })
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error('Triage error:', err);
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
          Interactive Triage Playground
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Мәтінді тікелей енгізіп, Offline CPU TF-IDF моделінің тілді, санатты, басымдықты және ереже цитаталарын қалай анықтайтынын тексеріңіз.
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="mb-6">
        <div className="text-xs font-semibold text-slate-400 mb-2">Дайын тесттік сценарийлер (Presets):</div>
        <div className="flex flex-wrap gap-2">
          {presets.map((p, i) => (
            <button
              key={i}
              onClick={() => {
                setInputText(p.text);
                setReporterHash(p.rep);
                setImagesCount(p.img);
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
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Өтініш мәтіні (Ticket Raw Text):
            </label>
            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              rows={6}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-sans focus:border-cyan-500 focus:outline-none resize-none leading-relaxed"
              placeholder="Өтініш мәтінін осында жазыңыз немесе қойыңыз..."
            />

            <div className="grid grid-cols-2 gap-4 mt-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">
                  Reporter Hash (Ойыншы ID):
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
                  Тіркеме саны (Images / Attachments):
                </label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={imagesCount}
                  onChange={e => setImagesCount(parseInt(e.target.value) || 0)}
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

        {/* Right: Results or empty */}
        <div>
          {result ? (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  Triage нәтижесі (HTTP 200 OK):
                </span>
                <button
                  onClick={handleCopyJson}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Көшірілді!' : 'JSON көшіру'}
                </button>
              </div>

              {/* Badges */}
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
                  <div className="text-slate-500 text-[10px]">НЕЕДС ХУМАН</div>
                  <div className="font-bold text-xs mt-0.5">
                    {result.needs_human ? (
                      <span className="text-rose-400">ИӘ (Human)</span>
                    ) : (
                      <span className="text-emerald-400">ЖОҚ (Auto)</span>
                    )}
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px]">CONFIDENCE</div>
                  <div className="text-amber-400 font-bold font-mono text-sm mt-0.5">{result.confidence}</div>
                </div>
              </div>

              {/* Category */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div className="text-slate-500 font-medium">Санат (14 Taxonomy):</div>
                <div className="text-sm font-semibold text-cyan-300 mt-0.5">{result.category}</div>
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
              <span>Нәтижені көру үшін сол жақтағы батырманы басыңыз.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
