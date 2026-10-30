import React, { useState } from 'react';
import { TicketItem, TriageResult } from '../types';
import { 
  AlertTriangle, CheckCircle, ShieldAlert, Clock, UserCheck, 
  Send, CornerUpRight, RefreshCw, MessageSquare, Tag, Eye,
  AlertCircle, Sparkles, Filter, Check, Paperclip, ChevronRight
} from 'lucide-react';

interface QueueViewProps {
  tickets: TicketItem[];
  onUpdateTicketStatus: (ticketId: string, status: TicketItem['status'], draftText?: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const QueueView: React.FC<QueueViewProps> = ({
  tickets,
  onUpdateTicketStatus,
  onRefresh,
  isLoading
}) => {
  const [selectedTicketId, setSelectedTicketId] = useState<string>(tickets[0]?.ticket_id || '');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [langFilter, setLangFilter] = useState<string>('all');
  const [needsHumanOnly, setNeedsHumanOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [editableReply, setEditableReply] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('standard');
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const selectedTicket = tickets.find(t => t.ticket_id === selectedTicketId) || tickets[0];

  // Sync draft reply when selected ticket changes
  React.useEffect(() => {
    if (selectedTicket?.triage?.draft_reply?.text) {
      setEditableReply(selectedTicket.triage.draft_reply.text);
    } else {
      setEditableReply('');
    }
    setActionSuccess(null);
  }, [selectedTicketId, selectedTicket]);

  const filteredTickets = tickets.filter(t => {
    if (priorityFilter !== 'all' && t.triage?.priority !== priorityFilter) return false;
    if (langFilter !== 'all' && t.triage?.lang !== langFilter) return false;
    if (needsHumanOnly && !t.triage?.needs_human) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const inText = t.text.toLowerCase().includes(q);
      const inId = t.ticket_id.toLowerCase().includes(q);
      const inCat = (t.triage?.category || '').toLowerCase().includes(q);
      const inNick = (t.triage?.extracted?.nicknames || []).some(n => n.toLowerCase().includes(q));
      if (!inText && !inId && !inCat && !inNick) return false;
    }
    return true;
  });

  const handleAction = (status: TicketItem['status'], note?: string) => {
    if (!selectedTicket) return;
    onUpdateTicketStatus(selectedTicket.ticket_id, status, editableReply);
    setActionSuccess(`Өтініш #${selectedTicket.ticket_id} мәртебесі жаңартылды: ${status?.toUpperCase()}`);
    setTimeout(() => setActionSuccess(null), 3000);
  };

  const priorityColor = (p?: string) => {
    switch (p) {
      case 'p0': return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'p1': return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'p2': return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'p3': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      default: return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  const langFlag = (lang?: string) => {
    switch (lang) {
      case 'kk': return '🇰🇿 KK';
      case 'ru': return '🇷🇺 RU';
      case 'uz': return '🇺🇿 UZ';
      case 'en': return '🇬🇧 EN';
      case 'es': return '🇪🇸 ES';
      case 'pt': return '🇵🇹 PT';
      default: return '🌐 ' + (lang || 'RU');
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Top Filter Bar */}
      <div className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
            <Filter className="w-3.5 h-3.5 mr-2 text-slate-400" />
            <span className="font-semibold mr-2 text-slate-400">Басымдық:</span>
            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value)}
              className="bg-transparent border-0 text-amber-400 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-slate-200">Барлығы (All)</option>
              <option value="p0" className="bg-slate-900 text-rose-400">p0 (Критикалық / Hack)</option>
              <option value="p1" className="bg-slate-900 text-amber-400">p1 (Жоғары / Донат, Чит)</option>
              <option value="p2" className="bg-slate-900 text-blue-400">p2 (Орташа / DM, DB)</option>
              <option value="p3" className="bg-slate-900 text-emerald-400">p3 (Төмен / Сұрақ)</option>
            </select>
          </div>

          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
            <span className="font-semibold mr-2 text-slate-400">Тіл:</span>
            <select
              value={langFilter}
              onChange={e => setLangFilter(e.target.value)}
              className="bg-transparent border-0 text-cyan-400 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-slate-200">Барлық тілдер</option>
              <option value="kk" className="bg-slate-900 text-cyan-300">🇰🇿 Қазақша (KK)</option>
              <option value="ru" className="bg-slate-900 text-cyan-300">🇷🇺 Орысша (RU)</option>
              <option value="uz" className="bg-slate-900 text-cyan-300">🇺🇿 Өзбекше (UZ)</option>
              <option value="en" className="bg-slate-900 text-cyan-300">🇬🇧 Ағылшын (EN)</option>
            </select>
          </div>

          <button
            onClick={() => setNeedsHumanOnly(!needsHumanOnly)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
              needsHumanOnly 
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' 
                : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Адамға жіберілген (Needs Human)
          </button>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Іздеу (ID, никнейм, сөздер)..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none w-56 placeholder-slate-500"
          />
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
            title="Жаңарту"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="bg-emerald-950/80 border-b border-emerald-600/40 text-emerald-300 px-6 py-2 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Main Two-Column View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Ticket List Queue */}
        <div className="w-1/3 min-w-[320px] max-w-[420px] border-r border-slate-800 bg-slate-950/50 flex flex-col overflow-y-auto divide-y divide-slate-800/60">
          <div className="px-4 py-2.5 bg-slate-900/60 text-xs font-semibold text-slate-400 flex justify-between items-center sticky top-0 backdrop-blur z-10">
            <span>Өтініштер кезегі ({filteredTickets.length})</span>
            <span className="text-[11px] text-cyan-400">Offline CPU Triage</span>
          </div>

          {filteredTickets.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              Сүзгіге сәйкес келетін өтініштер табылмады.
            </div>
          ) : (
            filteredTickets.map(ticket => {
              const isSelected = ticket.ticket_id === selectedTicketId;
              const tr = ticket.triage;
              const isDup = tr?.is_spam_or_duplicate;
              return (
                <div
                  key={ticket.ticket_id}
                  onClick={() => setSelectedTicketId(ticket.ticket_id)}
                  className={`p-3.5 cursor-pointer transition-all border-l-4 text-left ${
                    isSelected
                      ? 'bg-slate-900/90 border-l-cyan-400'
                      : 'hover:bg-slate-900/40 border-l-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                      #{ticket.ticket_id}
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-sans">
                        {langFlag(tr?.lang || ticket.lang)}
                      </span>
                    </span>
                    <div className="flex items-center gap-1.5">
                      {isDup && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-950 text-red-300 border border-red-700/50">
                          Қайталанған
                        </span>
                      )}
                      <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold border ${priorityColor(tr?.priority)}`}>
                        {tr?.priority?.toUpperCase() || 'P2'}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 line-clamp-2 mb-2 leading-relaxed font-normal">
                    {ticket.text}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span className="truncate max-w-[180px] text-cyan-300/80 font-medium">
                      {tr?.category ? tr.category.replace('player_report_', '') : 'Талдануда...'}
                    </span>
                    {tr?.needs_human ? (
                      <span className="flex items-center gap-1 text-rose-400 text-[10px] font-semibold">
                        <ShieldAlert className="w-3 h-3" /> Адамға
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-emerald-400 text-[10px]">
                        <Check className="w-3 h-3" /> Авто-дайын
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right: Active Ticket Inspector & Draft Response Workbench */}
        {selectedTicket ? (
          <div className="flex-1 flex flex-col overflow-y-auto bg-slate-900/30">
            {/* Header info card */}
            <div className="p-6 border-b border-slate-800 bg-slate-900/60">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm font-bold text-white">#{selectedTicket.ticket_id}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      Тілі: {langFlag(selectedTicket.triage?.lang)}
                    </span>
                    {selectedTicket.reporter_hash && (
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                        Ойыншы: {selectedTicket.reporter_hash}
                      </span>
                    )}
                    {selectedTicket.created_at && (
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(selectedTicket.created_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <h2 className="text-sm font-semibold text-slate-200">
                    {selectedTicket.triage?.reasons?.[0] || 'Өтініш мәліметтері'}
                  </h2>
                </div>

                <div className="flex items-center gap-2">
                  <div className={`px-3 py-1 rounded-lg border font-mono font-bold text-xs ${priorityColor(selectedTicket.triage?.priority)}`}>
                    Басымдық: {selectedTicket.triage?.priority?.toUpperCase()}
                  </div>
                  {selectedTicket.triage?.needs_human && (
                    <div className="px-3 py-1 rounded-lg border border-rose-500/40 bg-rose-500/10 text-rose-300 font-semibold text-xs flex items-center gap-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                      Міндетті бақылау
                    </div>
                  )}
                </div>
              </div>

              {/* Player Message Box with extracted entities */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-4">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>Ойыншының бастапқы мәтіні (Preserved Raw Text):</span>
                  {selectedTicket.triage?.extracted?.has_attachments && (
                    <span className="text-amber-400 text-xs flex items-center gap-1 font-normal">
                      <Paperclip className="w-3.5 h-3.5" />
                      Тіркеме бар ({selectedTicket.images_count || 1})
                    </span>
                  )}
                </div>
                <div className="text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-wrap selection:bg-cyan-500/30">
                  {selectedTicket.text}
                </div>

                {/* Extracted Badges */}
                <div className="mt-3 pt-3 border-t border-slate-900 flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-slate-500 font-medium">Анықталған деректер:</span>
                  {(selectedTicket.triage?.extracted?.nicknames || []).map(n => (
                    <span key={n} className="px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800/40 font-mono text-[11px]">
                      Ник: {n}
                    </span>
                  ))}
                  {(selectedTicket.triage?.extracted?.rule_refs_raw || []).map(r => (
                    <span key={r} className="px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-800/40 font-mono text-[11px]">
                      Ереже сілтемесі: {r}
                    </span>
                  ))}
                  {(selectedTicket.triage?.extracted?.ids || []).map(id => (
                    <span key={id} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                      ID: {id}
                    </span>
                  ))}
                </div>
              </div>

              {/* Copilot NLP Analysis Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-slate-400 font-medium mb-1">Санат (14 Taxonomy):</div>
                  <div className="text-cyan-300 font-semibold">{selectedTicket.triage?.category}</div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Ұқсастық ұпайы: {(Number(selectedTicket.triage?.confidence || 0) * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-slate-400 font-medium mb-1">Цитаталар (draft_reply.cited):</div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(selectedTicket.triage?.draft_reply?.cited || []).length > 0 ? (
                      selectedTicket.triage?.draft_reply.cited.map(c => (
                        <span key={c} className="px-1.5 py-0.5 rounded bg-purple-900/60 text-purple-200 border border-purple-700/40 font-mono font-bold">
                          {c}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 italic">Нақты тармақ жоқ</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-3">
                  <div className="text-slate-400 font-medium mb-1">Дедупликация (1 сағат):</div>
                  {selectedTicket.triage?.is_spam_or_duplicate ? (
                    <span className="text-rose-400 font-semibold flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Қайталанған өтініш
                    </span>
                  ) : (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Бірегей өтініш
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Matched Server Rules Section */}
            {selectedTicket.triage?.matched_rules && selectedTicket.triage.matched_rules.length > 0 && (
              <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/40">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  Сәйкестендірілген ережелер (11 бөлім, 266 тармақтан):
                </div>
                <div className="space-y-2">
                  {selectedTicket.triage.matched_rules.slice(0, 3).map((r, i) => (
                    <div key={r.internal_key || i} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-amber-300">
                          {r.section_name} &bull; <span className="font-mono text-cyan-300">{r.ref}</span>
                        </span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          Ұқсастық: {r.score}
                        </span>
                      </div>
                      <p className="text-slate-300 font-normal leading-relaxed">{r.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Draft Reply Editor & Human Actions Workbench */}
            <div className="p-6 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5 text-cyan-400" />
                    Дайындалған жауап жобасы (Draft Reply):
                  </label>
                  <span className="text-[11px] text-slate-500">
                    Қауіпсіз, тексерілген шаблон &bull; Жалған уәдесіз
                  </span>
                </div>

                <textarea
                  value={editableReply}
                  onChange={e => setEditableReply(e.target.value)}
                  rows={4}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-sm text-slate-100 font-sans focus:border-cyan-500 focus:outline-none resize-none leading-relaxed selection:bg-cyan-500/30"
                  placeholder="Жауап жобасы осында көрсетіледі..."
                />
              </div>

              {/* Action Buttons */}
              <div className="mt-6 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAction('approved')}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-950 transition-all cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Бекіту және жауапты жіберу
                  </button>

                  <button
                    onClick={() => handleAction('escalated')}
                    className="px-3.5 py-2 rounded-lg bg-amber-600/30 hover:bg-amber-600/40 text-amber-200 border border-amber-500/40 text-xs font-medium flex items-center gap-2 transition-all cursor-pointer"
                  >
                    <CornerUpRight className="w-3.5 h-3.5" />
                    Аға әкімшілікке эскалациялау
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleAction('clarification')}
                    className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all cursor-pointer"
                  >
                    Нақтылау сұрау (/time)
                  </button>

                  <button
                    onClick={() => handleAction('rejected')}
                    className="px-3 py-2 rounded-lg bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-medium transition-all cursor-pointer"
                  >
                    Қайталанған / Спам
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500 text-xs">
            Өтінішті таңдаңыз
          </div>
        )}
      </div>
    </div>
  );
};
