"use client";

import { useEffect, useState } from "react";
import { getReviewQueue, approveArticle, requestRevision, rejectArticle, editArticle, humanizeArticle } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { CheckCircle2, XCircle, AlertCircle, Edit3, Eye, FileText, RefreshCw, Check, Sparkles } from "lucide-react";

export default function ReviewQueuePage() {
  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeModal, setActiveModal] = useState<{
    type: "preview" | "research" | "quality" | "edit" | "revision";
    item: any;
  } | null>(null);

  const [editContent, setEditContent] = useState<string>("");
  const [revisionNotes, setRevisionNotes] = useState<string>("");
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const data = await getReviewQueue();
      setQueue(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
    const interval = setInterval(loadQueue, 2000); // Live polling review queue every 2s
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (jobId: string) => {
    try {
      setActionLoading(true);
      await approveArticle(jobId);
      loadQueue();
      setActiveModal(null);
    } catch (e: any) {
      alert(e.message || "Failed to approve article");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (jobId: string) => {
    if (!confirm("Are you sure you want to reject and cancel this article?")) return;
    try {
      setActionLoading(true);
      await rejectArticle(jobId);
      loadQueue();
      setActiveModal(null);
    } catch (e: any) {
      alert(e.message || "Failed to reject article");
    } finally {
      setActionLoading(false);
    }
  };

  const handleHumanize = async (jobId: string) => {
    try {
      setActionLoading(true);
      await humanizeArticle(jobId);
      alert("Article text successfully humanized!");
      loadQueue();
    } catch (e: any) {
      alert(e.message || "Failed to humanize article text");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRequestRevisionSubmit = async () => {
    if (!activeModal || !revisionNotes.trim()) return;
    try {
      setActionLoading(true);
      await requestRevision(activeModal.item.job_id, revisionNotes);
      loadQueue();
      setActiveModal(null);
      setRevisionNotes("");
    } catch (e: any) {
      alert(e.message || "Failed to request revision");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveEditSubmit = async () => {
    if (!activeModal) return;
    try {
      setActionLoading(true);
      await editArticle(activeModal.item.job_id, editContent);
      loadQueue();
      setActiveModal(null);
    } catch (e: any) {
      alert(e.message || "Failed to save article edits");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-6 h-6 text-amber-400" />
            <span>Human Review Queue</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review quality reports, research data, and article previews before approving for Strapi publication.
          </p>
        </div>
        <button
          onClick={loadQueue}
          className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          title="Refresh queue"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {loading && queue.length === 0 ? (
        <div className="p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
          <span>Loading review queue...</span>
        </div>
      ) : queue.length === 0 ? (
        <div className="bg-slate-900/80 p-12 rounded-2xl border border-slate-800 text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Review Queue is Empty</h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All generated articles have been processed, approved, or published to Strapi CMS.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map((item) => (
            <div key={item.job_id} className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <StatusBadge status={item.status} />
                    <span className="text-xs text-slate-400">Topic ID: #{item.job_id.slice(0, 8)}</span>
                  </div>
                  <h2 className="text-xl font-bold text-white mt-1">{item.topic}</h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Primary Keyword: <strong className="text-sky-300">{item.primary_keyword}</strong> &bull; Volume: {item.search_volume ?? "N/A"} &bull; KD: {item.keyword_difficulty ?? "N/A"} &bull; Density: {item.target_density ?? "N/A"}
                  </p>
                </div>

                {/* Score Pills */}
                <div className="flex items-center space-x-2 text-xs">
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-emerald-500/30 text-center min-w-[90px]">
                    <span className="block text-[10px] text-slate-400 uppercase font-semibold">Fact Check</span>
                    <span className="text-sm font-bold text-emerald-400">{item.scores.fact_check}%</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-sky-500/30 text-center min-w-[90px]">
                    <span className="block text-[10px] text-slate-400 uppercase font-semibold">SEO Score</span>
                    <span className="text-sm font-bold text-sky-400">{item.scores.seo}%</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-indigo-500/30 text-center min-w-[90px]">
                    <span className="block text-[10px] text-slate-400 uppercase font-semibold">Editorial</span>
                    <span className="text-sm font-bold text-indigo-400">{item.scores.editorial}%</span>
                  </div>
                </div>
              </div>

              {/* Preview Snippet */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 text-xs text-slate-300 font-mono">
                <p className="line-clamp-3 italic opacity-90">{item.preview_snippet}...</p>
              </div>

              {/* Action Buttons Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => setActiveModal({ type: "preview", item })}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5 text-sky-400" /> Preview Article
                  </button>
                  <button
                    onClick={() => setActiveModal({ type: "research", item })}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5 text-indigo-400" /> View Research
                  </button>
                  <button
                    onClick={() => setActiveModal({ type: "quality", item })}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Quality Report
                  </button>
                  <button
                    onClick={() => {
                      setEditContent(item.final_article_text);
                      setActiveModal({ type: "edit", item });
                    }}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-amber-400" /> Edit
                  </button>
                  <button
                    onClick={() => handleHumanize(item.job_id)}
                    disabled={actionLoading}
                    className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 text-purple-300 text-xs font-semibold flex items-center gap-1.5 transition"
                    title="Humanize text to remove AI voice and clichés"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Humanize Text
                  </button>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setActiveModal({ type: "revision", item })}
                    className="px-3 py-2 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-400 hover:bg-orange-500/20 text-xs font-semibold transition"
                  >
                    Request Revision
                  </button>
                  <button
                    onClick={() => handleReject(item.job_id)}
                    className="px-3 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 text-xs font-semibold transition"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleApprove(item.job_id)}
                    disabled={actionLoading}
                    className="flex items-center space-x-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white px-5 py-2 rounded-xl font-semibold text-xs shadow-lg shadow-emerald-500/20 transition"
                  >
                    <Check className="w-4 h-4" />
                    <span>Approve & Publish</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Dialog */}
      {activeModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <h3 className="font-bold text-white text-sm">
                {activeModal.type === "preview" && "Article Preview"}
                {activeModal.type === "research" && "01-research.md View"}
                {activeModal.type === "quality" && "04-quality-seo.md View"}
                {activeModal.type === "edit" && "Edit 05-final.md Content"}
                {activeModal.type === "revision" && "Request Article Revision"}
              </h3>
              <button
                onClick={() => setActiveModal(null)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                Close ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {activeModal.type === "preview" && (
                <pre className="whitespace-pre-wrap font-sans text-sm text-slate-200 leading-relaxed">
                  {activeModal.item.final_article_text}
                </pre>
              )}

              {activeModal.type === "research" && (
                <p className="text-xs text-slate-400 italic">
                  Displays raw Markdown data captured in 01-research.md for this article.
                </p>
              )}

              {activeModal.type === "quality" && (
                <pre className="whitespace-pre-wrap font-mono text-xs text-slate-300 bg-slate-950 p-4 rounded-xl">
                  {(activeModal.item.quality_report_text || "").replace(/^\s*```json\s*\{[\s\S]*?\}\s*```\s*/, "").trim()}
                </pre>
              )}

              {activeModal.type === "edit" && (
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={16}
                  className="w-full bg-slate-950 border border-slate-700 text-white font-mono text-xs p-4 rounded-xl focus:outline-none focus:border-sky-500"
                />
              )}

              {activeModal.type === "revision" && (
                <div className="space-y-3">
                  <p className="text-xs text-slate-400">
                    Provide instructions for the Writer Agent on what specific claims or sections to fix:
                  </p>
                  <textarea
                    value={revisionNotes}
                    onChange={(e) => setRevisionNotes(e.target.value)}
                    placeholder="e.g. Include more recent 2025 statistics for career growth and refine H2 subheadings..."
                    rows={6}
                    className="w-full bg-slate-950 border border-slate-700 text-white text-xs p-4 rounded-xl focus:outline-none focus:border-amber-500"
                  />
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950 flex justify-end space-x-3">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>

              {activeModal.type === "edit" && (
                <button
                  onClick={handleSaveEditSubmit}
                  disabled={actionLoading}
                  className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs"
                >
                  Save Edits
                </button>
              )}

              {activeModal.type === "revision" && (
                <button
                  onClick={handleRequestRevisionSubmit}
                  disabled={actionLoading || !revisionNotes.trim()}
                  className="px-5 py-2 rounded-xl bg-orange-500 hover:bg-orange-400 text-white font-bold text-xs disabled:opacity-50"
                >
                  Send Revision Request
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
