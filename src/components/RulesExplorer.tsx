import React, { useState, useEffect } from 'react';
import { BookOpen, Search, Shield, ChevronDown, ChevronRight, Hash } from 'lucide-react';

interface RulePoint {
  ref: string;
  text: string;
}

interface RPDefinition {
  term: string;
  text: string;
}

interface Section {
  id: string;
  name: string;
  description: string;
  rp_definitions?: RPDefinition[];
  points: RulePoint[];
}

export const RulesExplorer: React.FC = () => {
  const [sections, setSections] = useState<Section[]>([]);
  const [expandedSection, setExpandedSection] = useState<string>('sec_combat');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/rules')
      .then(res => res.json())
      .then(data => {
        setSections(data.rules || data.sections || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Failed to load rules:', err);
        setIsLoading(false);
      });
  }, []);

  const totalPoints = sections.reduce((acc, s) => acc + (s.points?.length || 0), 0);

  const filteredSections = sections.map(sec => {
    if (!searchQuery) return sec;
    const q = searchQuery.toLowerCase();
    const matchedPoints = (sec.points || []).filter(p => 
      p.ref.toLowerCase().includes(q) || p.text.toLowerCase().includes(q)
    );
    const matchedRp = (sec.rp_definitions || []).filter(rp =>
      rp.term.toLowerCase().includes(q) || rp.text.toLowerCase().includes(q)
    );
    return {
      ...sec,
      points: matchedPoints,
      rp_definitions: matchedRp
    };
  }).filter(sec => sec.points.length > 0 || (sec.rp_definitions && sec.rp_definitions.length > 0));

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-7xl mx-auto w-full">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            Сервер ережелерінің базасы (Grand Mobile Official Rules)
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            11 бөлім, 266 тармақ &bull; Бірегей кілт: <code className="bg-slate-900 px-1.5 py-0.5 rounded text-amber-300">section_id + "::" + ref</code>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-300">
            Барлығы: <span className="font-bold text-cyan-400">{sections.length}</span> бөлім, <span className="font-bold text-cyan-400">{totalPoints}</span> тармақ
          </div>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Ереже бойынша іздеу (DM, GZ, 2.1)..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none w-64 placeholder-slate-500"
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-500 text-xs">Ережелер жүктелуде...</div>
      ) : (
        <div className="space-y-4">
          {filteredSections.map(sec => {
            const isExpanded = expandedSection === sec.id || Boolean(searchQuery);
            return (
              <div key={sec.id} className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden transition-all">
                <button
                  onClick={() => setExpandedSection(isExpanded ? '' : sec.id)}
                  className="w-full px-5 py-3.5 bg-slate-900/60 hover:bg-slate-900 flex items-center justify-between text-left cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="p-1 rounded bg-slate-800 text-cyan-400">
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </span>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-200">{sec.name}</h3>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{sec.description}</p>
                    </div>
                  </div>
                  <div className="text-xs font-mono text-slate-500 flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                      {sec.points.length} тармақ
                    </span>
                    <span className="text-[11px] text-slate-600">ID: {sec.id}</span>
                  </div>
                </button>

                {isExpanded && (
                  <div className="p-5 border-t border-slate-800/80 bg-slate-950/40 space-y-4">
                    {/* RP definitions */}
                    {sec.rp_definitions && sec.rp_definitions.length > 0 && (
                      <div>
                        <div className="text-[11px] font-semibold text-amber-400/90 uppercase tracking-wider mb-2">
                          Рөлдік ойын анықтамалары (RP Definitions):
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {sec.rp_definitions.map((rp, i) => (
                            <div key={i} className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5 text-xs">
                              <span className="font-bold text-amber-300 mr-2">{rp.term}:</span>
                              <span className="text-slate-300 font-normal">{rp.text}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Points */}
                    <div>
                      <div className="text-[11px] font-semibold text-cyan-400/90 uppercase tracking-wider mb-2">
                        Нақты тармақтар (Official Points):
                      </div>
                      <div className="space-y-2">
                        {sec.points.map((pt, i) => (
                          <div key={pt.ref || i} className="bg-slate-900/60 border border-slate-800/60 rounded-lg p-3 text-xs flex items-start gap-3">
                            <span className="font-mono font-bold text-cyan-300 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded text-[11px] shrink-0">
                              {pt.ref}
                            </span>
                            <div className="flex-1">
                              <p className="text-slate-200 leading-relaxed font-sans">{pt.text}</p>
                              <div className="mt-1 text-[10px] font-mono text-slate-500">
                                Ішкі бірегей кілт: <span className="text-slate-400">{sec.id}::{pt.ref}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
