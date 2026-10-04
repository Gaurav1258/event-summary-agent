import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  ShieldAlert, 
  Globe, 
  ExternalLink, 
  Play, 
  AlertCircle, 
  Layers, 
  Zap, 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronUp, 
  Search, 
  Sparkles, 
  FileText 
} from 'lucide-react';
import type { CandidateProfile, SummaryResponse } from './types';
import { DEFAULT_CANDIDATES } from './mockCandidates';

export function App() {
  const [candidates, setCandidates] = useState<CandidateProfile[]>(DEFAULT_CANDIDATES);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateProfile | null>(DEFAULT_CANDIDATES[0] || null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendHealth, setBackendHealth] = useState<'checking' | 'healthy' | 'offline'>('checking');
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [linksDrawerOpen, setLinksDrawerOpen] = useState<boolean>(true);
  const [linkFilter, setLinkFilter] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  // Check Backend Health
  useEffect(() => {
    fetch('/health')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(() => setBackendHealth('healthy'))
      .catch(() => setBackendHealth('offline'));
  }, []);

  // Fetch Candidate Hits Directory (with fallback to DEFAULT_CANDIDATES)
  useEffect(() => {
    fetch('/api/v1/candidates')
      .then(res => res.ok ? res.json() : null)
      .then((data: CandidateProfile[] | null) => {
        if (Array.isArray(data) && data.length > 0) {
          setCandidates(data);
          setSelectedCandidate(prev => prev || data[0]);
        }
      })
      .catch(() => {
        // Fallback already pre-loaded into state
      });
  }, []);

  // Timer while analyzing
  useEffect(() => {
    let interval: any;
    if (loading) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleRunInvestigation = async () => {
    if (!selectedCandidate) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const payload = {
      candidate_id: selectedCandidate.candidate_id,
      hit_id: selectedCandidate.hit_id,
      entity_name: selectedCandidate.entity_name,
      events: selectedCandidate.events
    };

    try {
      const response = await fetch('/api/v1/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server error: ${response.statusText}`);
      }

      const data: SummaryResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error('Investigation error:', err);
      setError(err.message || 'An unexpected error occurred during summarization.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.summary_report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredLinks = selectedCandidate?.events.filter(e => 
    e.url.toLowerCase().includes(linkFilter.toLowerCase()) || 
    (e.title && e.title.toLowerCase().includes(linkFilter.toLowerCase())) ||
    (e.source_name && e.source_name.toLowerCase().includes(linkFilter.toLowerCase()))
  ) || [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600/20 text-blue-400 p-2 rounded-lg border border-blue-500/30">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Namelist Screening Event Summary Agent
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v1.0.0
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              GCP Vertex AI Map-Reduce Adverse Media & Sanctions Investigator
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800/80 border border-slate-700/60">
            <span className={`w-2 h-2 rounded-full ${backendHealth === 'healthy' ? 'bg-emerald-400 animate-pulse' : backendHealth === 'checking' ? 'bg-amber-400' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-medium">
              {backendHealth === 'healthy' ? 'Cloud Run: Connected (mlops2215)' : backendHealth === 'checking' ? 'Connecting...' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Candidate Hits Directory */}
        <aside className="w-80 border-r border-slate-800 bg-slate-900/30 flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Screening Hits Directory ({candidates.length})
            </h2>
          </div>

          <div className="overflow-y-auto flex-1 divide-y divide-slate-800/60 p-2 space-y-1">
            {candidates.map((c) => {
              const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
              const isHighRisk = c.risk_category.toLowerCase().includes('high');
              const isFalsePositive = c.risk_category.toLowerCase().includes('false');

              return (
                <button
                  key={c.candidate_id}
                  onClick={() => {
                    setSelectedCandidate(c);
                    setResult(null);
                    setError(null);
                  }}
                  className={`w-full text-left p-3.5 rounded-lg transition-all border ${
                    isSelected 
                      ? 'bg-blue-600/15 border-blue-500/50 shadow-sm shadow-blue-500/10' 
                      : 'hover:bg-slate-800/50 border-transparent text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="font-semibold text-sm text-white truncate">{c.entity_name}</span>
                    <span className="text-[10px] font-mono text-slate-400">{c.total_events} events</span>
                  </div>

                  <div className="flex items-center gap-1.5 mb-2">
                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                      isHighRisk 
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/20' 
                        : isFalsePositive 
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' 
                        : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                    }`}>
                      {c.risk_category.split(' - ')[0]}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {c.description}
                  </p>
                </button>
              );
            })}
          </div>
        </aside>

        {/* Right Main Panel: Investigation & Results */}
        <main className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {selectedCandidate ? (
            <>
              {/* Candidate Info Card */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-lg">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h2 className="text-2xl font-bold text-white tracking-tight">
                        {selectedCandidate.entity_name}
                      </h2>
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
                        {selectedCandidate.candidate_id}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 max-w-2xl mt-1 leading-relaxed">
                      {selectedCandidate.description}
                    </p>
                    <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Globe className="w-3.5 h-3.5 text-slate-500" />
                        {selectedCandidate.country}
                      </span>
                      <span>•</span>
                      <span>Hit ID: <strong className="text-slate-200">{selectedCandidate.hit_id}</strong></span>
                      <span>•</span>
                      <span>Total Events: <strong className="text-blue-400">{selectedCandidate.total_events} links</strong></span>
                    </div>
                  </div>

                  {/* Mode Badge & Run Button */}
                  <div className="flex flex-col items-end gap-3">
                    {/* Adaptive Threshold Mode Indicator */}
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border bg-slate-800/80 border-slate-700 text-slate-300">
                      {selectedCandidate.total_events <= 3 ? (
                        <>
                          <Zap className="w-3.5 h-3.5 text-amber-400" />
                          <span>Direct Mode (Gemini 2.5 Pro)</span>
                        </>
                      ) : (
                        <>
                          <Layers className="w-3.5 h-3.5 text-blue-400" />
                          <span>Map-Reduce Mode (Flash + Pro)</span>
                        </>
                      )}
                    </div>

                    <button
                      onClick={handleRunInvestigation}
                      disabled={loading}
                      className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all shadow-md ${
                        loading 
                          ? 'bg-blue-600/50 text-blue-200 cursor-not-allowed' 
                          : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/25 hover:shadow-blue-500/35 active:scale-95'
                      }`}
                    >
                      {loading ? (
                        <>
                          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          <span>Analyzing Events ({elapsedTime}s)...</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 fill-white" />
                          <span>Run Agent Investigation</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Event Links Drawer (Collapsible) */}
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl overflow-hidden">
                <button
                  onClick={() => setLinksDrawerOpen(!linksDrawerOpen)}
                  className="w-full px-5 py-3.5 bg-slate-900/70 border-b border-slate-800/80 flex items-center justify-between text-xs font-semibold text-slate-300 hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <span>Associated Event Links ({selectedCandidate.events.length})</span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-400">
                    <span>{linksDrawerOpen ? 'Collapse' : 'Expand'}</span>
                    {linksDrawerOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {linksDrawerOpen && (
                  <div className="p-4 space-y-3">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
                      <input
                        type="text"
                        placeholder="Search event links by title or domain..."
                        value={linkFilter}
                        onChange={e => setLinkFilter(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                      />
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                      {filteredLinks.map((event, idx) => (
                        <div 
                          key={idx}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/50 text-xs hover:border-slate-700 transition-colors"
                        >
                          <div className="flex-1 min-w-0 pr-4">
                            <p className="text-slate-200 font-medium truncate">{event.title || 'Adverse Media Event'}</p>
                            <span className="text-[11px] text-slate-500 truncate block mt-0.5">{event.url}</span>
                          </div>
                          <a
                            href={event.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-[11px] font-medium flex-shrink-0"
                          >
                            <span>Visit</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Error Alert */}
              {error && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3 text-rose-300 text-sm">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong className="font-semibold">Investigation Error:</strong>
                    <p className="mt-0.5 text-xs text-rose-200/90">{error}</p>
                  </div>
                </div>
              )}

              {/* Results & Statistics Section */}
              {result && (
                <div className="space-y-6">
                  {/* Stats Bar */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-xs text-slate-400 font-medium">Total Events Evaluated</span>
                      <p className="text-2xl font-bold text-white mt-1">{result.stats.total_links}</p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-xs text-emerald-400 font-medium">Successfully Scraped</span>
                      <p className="text-2xl font-bold text-emerald-400 mt-1">{result.stats.successful_scrapes}</p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-xs text-rose-400 font-medium">Failed / 404 Links</span>
                      <p className="text-2xl font-bold text-rose-400 mt-1">{result.stats.failed_scrapes}</p>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                      <span className="text-xs text-blue-400 font-medium">Elapsed Execution Time</span>
                      <p className="text-2xl font-bold text-blue-400 mt-1">{elapsedTime}s</p>
                    </div>
                  </div>

                  {/* Final Markdown Report Viewer */}
                  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 shadow-xl relative">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-amber-400" />
                        <h3 className="text-lg font-bold text-white">Synthesized Compliance Summary Report</h3>
                      </div>

                      <button
                        onClick={copyToClipboard}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
                      </button>
                    </div>

                    {/* Markdown Renderer */}
                    <div className="prose prose-invert prose-blue max-w-none text-slate-200 text-sm leading-relaxed space-y-4">
                      <ReactMarkdown>
                        {result.summary_report}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-3">
              <ShieldAlert className="w-12 h-12 stroke-[1.5]" />
              <p className="text-sm font-medium">Select a screening candidate to begin investigation.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
