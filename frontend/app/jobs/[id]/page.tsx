"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getJobDetail, getJobFilePreview, getJobActivity, retryJob, retryPublishing, regenerateJobStep, forceFinalizeJob, reviseJob } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { formatTimeOnly } from "@/lib/formatters";
import { FileText, CheckCircle2, AlertCircle, RefreshCw, Layers, ArrowLeft, ExternalLink, RotateCcw, Sparkles, X, ShieldAlert, FileSearch, Wrench } from "lucide-react";

const FILE_TABS = [
  { key: "01-research.md", label: "01 Research" },
  { key: "02-content-brief.md", label: "02 Brief" },
  { key: "03-draft.md", label: "03 Draft" },
  { key: "04-quality-seo.md", label: "04 Quality/SEO" },
  { key: "05-final.md", label: "05 Final Article" },
];

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<string>("01-research.md");
  const [fileContent, setFileContent] = useState<string>("");
  const [fileLoading, setFileLoading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [regeneratingStep, setRegeneratingStep] = useState<string | null>(null);

  // Modal State
  const [showReportModal, setShowReportModal] = useState<boolean>(false);
  const [reportData, setReportData] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState<boolean>(false);

  const [showPublishedModal, setShowPublishedModal] = useState<boolean>(false);
  const [publishedArticleText, setPublishedArticleText] = useState<string>("");
  const [publishedLoading, setPublishedLoading] = useState<boolean>(false);

  const handleViewPublishedArticle = async (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    setShowPublishedModal(true);
    setPublishedLoading(true);
    try {
      const res = await getJobFilePreview(jobId, "05-final.md");
      setPublishedArticleText(res.content || "");
    } catch {
      setPublishedArticleText(fileContent || "# Published Article\n\nContent details not loaded.");
    } finally {
      setPublishedLoading(false);
    }
  };

  const handleReviseDraft = async () => {
    try {
      setRegeneratingStep("revising");
      await reviseJob(jobId);
      await loadJob();
    } catch (err: any) {
      alert(`Failed to trigger revision: ${err.message}`);
    } finally {
      setRegeneratingStep(null);
    }
  };

  const handleOpenReportModal = async () => {
    setShowReportModal(true);
    setReportLoading(true);
    try {
      // Try dedicated structured JSON first
      try {
        const jsonRes = await getJobFilePreview(jobId, "04-quality-seo.json");
        const parsed = JSON.parse(jsonRes.content);
        setReportData(parsed);
        setReportLoading(false);
        return;
      } catch {}

      // Fallback to extracting embedded json block from markdown
      const res = await getJobFilePreview(jobId, "04-quality-seo.md");
      const text = res.content || "";
      const match = text.match(/```json\s*(\{[\s\S]*?\})\s*```/);
      if (match && match[1]) {
        try {
          const parsed = JSON.parse(match[1]);
          setReportData(parsed);
        } catch {
          setReportData({ raw: text });
        }
      } else {
        setReportData({ raw: text });
      }
    } catch (e: any) {
      setReportData({ error: "Quality Audit report not available." });
    } finally {
      setReportLoading(false);
    }
  };


  const handleRegenerateStep = async (stepFilename: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      setRegeneratingStep(stepFilename);
      await regenerateJobStep(jobId, stepFilename);
      await loadJob();
    } catch (err: any) {
      alert(`Failed to regenerate step: ${err.message}`);
    } finally {
      setRegeneratingStep(null);
    }
  };

  const handleForceFinalize = async () => {
    try {
      setRegeneratingStep("05-final.md");
      await forceFinalizeJob(jobId);
      await loadJob();
    } catch (err: any) {
      alert(`Failed to force finalize: ${err.message}`);
    } finally {
      setRegeneratingStep(null);
    }
  };

  const loadJob = async () => {
    try {
      const [jData, aData] = await Promise.all([
        getJobDetail(jobId),
        getJobActivity(jobId).catch(() => []),
      ]);
      setJob(jData);
      setActivity(aData);
      // Auto refresh active file tab content
      getJobFilePreview(jobId, activeTab)
        .then((res) => {
          const text = res.content || "";
          const cleanText = text.replace(/^\s*```json\s*\{[\s\S]*?\}\s*```\s*/, "").trim();
          setFileContent(cleanText);
        })
        .catch(() => {});
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadFile = async (tabKey: string) => {
    setActiveTab(tabKey);
    setFileLoading(true);
    try {
      const res = await getJobFilePreview(jobId, tabKey);
      const text = res.content || "";
      const cleanText = text.replace(/^\s*```json\s*\{[\s\S]*?\}\s*```\s*/, "").trim();
      setFileContent(cleanText);
    } catch (e) {
      setFileContent(`*File ${tabKey} is not yet generated in the workflow storage.*`);
    } finally {
      setFileLoading(false);
    }
  };

  useEffect(() => {
    loadJob();
    const interval = setInterval(loadJob, 2000); // Live polling every 2 seconds
    return () => clearInterval(interval);
  }, [jobId, activeTab]);

  useEffect(() => {
    if (job) {
      loadFile(activeTab);
    }
  }, [activeTab, jobId]);

  if (loading && !job) {
    return (
      <div className="p-12 text-center text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
        <span>Loading content job details...</span>
      </div>
    );
  }

  if (!job) {
    return <div className="p-12 text-center text-rose-400">Content Job not found.</div>;
  }

  const steps = [
    { label: "Research", file: "01-research.md" },
    { label: "Brief", file: "02-content-brief.md" },
    { label: "Draft", file: "03-draft.md" },
    { label: "Quality Audit", file: "04-quality-seo.md" },
    { label: "Final Article", file: "05-final.md" },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <Link href={`/batches/${job.batch_id}`} className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Batch
        </Link>
        <div className="flex items-center space-x-2">
          {job.status === "FAILED" && (
            <button
              onClick={async () => {
                await retryJob(jobId);
                loadJob();
              }}
              className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 text-xs font-semibold"
            >
              Retry Job
            </button>
          )}
          {job.publishing_info?.status === "FAILED" && (
            <button
              onClick={async () => {
                await retryPublishing(jobId);
                loadJob();
              }}
              className="px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400 hover:bg-sky-500/20 text-xs font-semibold"
            >
              Retry Strapi Publishing
            </button>
          )}
        </div>
      </div>

      {/* Main Metadata Card */}
      <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs uppercase font-semibold text-sky-400">Content Job #{jobId.slice(0, 8)}</span>
              <StatusBadge status={job.status} />
            </div>
            <h1 className="text-2xl font-bold text-white mt-1">{job.topic}</h1>
            <p className="text-xs text-slate-400 mt-1">
              Primary Keyword: <strong className="text-sky-300">{job.primary_keyword}</strong> &bull; Volume: {job.search_volume ?? "N/A"} &bull; KD: {job.keyword_difficulty ?? "N/A"} &bull; Density: {job.target_density ?? "N/A"}
            </p>
          </div>

          {job.publishing_info?.published_url && (
            <button
              onClick={handleViewPublishedArticle}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-semibold rounded-xl transition cursor-pointer shadow"
            >
              <span>View Published Article</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Quality Audit Revision / Manual Review Warning Banners */}
        {job.status === "REVISION_REQUIRED" || (!job.markdown_files?.["05-final.md"] && job.markdown_files?.["04-quality-seo.md"] && job.status !== "MANUAL_REVIEW_REQUIRED" && job.status !== "AWAITING_APPROVAL" && job.status !== "PUBLISHED") ? (
          <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 my-3">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-bold text-white text-sm">Quality Audit — Revision Required</p>
                  <span className="px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 text-[10px] font-semibold border border-orange-500/30">
                    Attempt {job.retry_count || 1} / 3
                  </span>
                </div>
                <p className="text-slate-300 mt-0.5">
                  The Quality Inspector evaluated 03-draft.md and flagged issues (e.g. low keyword density or unsourced claims).
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0">
              <button
                onClick={handleOpenReportModal}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold transition flex items-center gap-1.5 shadow"
              >
                <FileSearch className="w-3.5 h-3.5 text-sky-400" />
                <span>View Quality Report</span>
              </button>
              <button
                onClick={handleReviseDraft}
                disabled={regeneratingStep === "revising"}
                className="px-3.5 py-2 rounded-xl bg-orange-500/20 hover:bg-orange-500/30 text-orange-200 border border-orange-500/40 font-semibold transition disabled:opacity-50 flex items-center gap-1.5 shadow"
              >
                <Wrench className={`w-3.5 h-3.5 ${regeneratingStep === "revising" ? "animate-spin" : ""}`} />
                <span>{regeneratingStep === "revising" ? "Revising Draft..." : "Revise Draft"}</span>
              </button>
            </div>
          </div>
        ) : job.status === "MANUAL_REVIEW_REQUIRED" ? (
          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 my-3">
            <div className="flex items-start gap-2.5">
              <ShieldAlert className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-white text-sm">Quality Audit — Manual Review Required</p>
                <p className="text-slate-300 mt-0.5">
                  Quality audit findings remained unresolved after 3 automated revision attempts. Manual editor review required.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0">
              <button
                onClick={handleOpenReportModal}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold transition flex items-center gap-1.5 shadow"
              >
                <FileSearch className="w-3.5 h-3.5 text-purple-400" />
                <span>View Quality Report</span>
              </button>
              <button
                onClick={handleForceFinalize}
                disabled={regeneratingStep === "05-final.md"}
                className="px-3.5 py-2 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 font-semibold transition disabled:opacity-50 flex items-center gap-1.5 shadow"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Force Generate Final Article</span>
              </button>
            </div>
          </div>
        ) : null}


        {/* Workflow Stepper */}
        <div className="pt-4 border-t border-slate-800/80">
          <div className="grid grid-cols-5 gap-2 text-center text-xs">
            {steps.map((s, idx) => {
              const hasFile = job.markdown_files?.[s.file];
              const isRegenerating = regeneratingStep === s.file;
              return (
                <div
                  key={s.label}
                  onClick={() => loadFile(s.file)}
                  className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                    activeTab === s.file
                      ? "bg-sky-500/10 border-sky-500/50 text-sky-300 font-semibold"
                      : hasFile
                      ? "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                      : "bg-slate-950/40 border-slate-900 text-slate-600 opacity-60"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                      {hasFile ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <span className="w-3.5 h-3.5 rounded-full border border-slate-700 text-[10px] inline-flex items-center justify-center">
                          {idx + 1}
                        </span>
                      )}
                      <span>{s.label}</span>
                    </div>
                    <span className="text-[10px] block text-slate-500 truncate">{s.file}</span>
                  </div>

                  <button
                    onClick={(e) => handleRegenerateStep(s.file, e)}
                    disabled={isRegenerating}
                    className="mt-2 text-[10px] px-2 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center gap-1 transition disabled:opacity-50 font-normal"
                    title={`Regenerate ${s.label}`}
                  >
                    <RotateCcw className={`w-2.5 h-2.5 ${isRegenerating ? "animate-spin" : ""}`} />
                    <span>{isRegenerating ? "Running..." : "Regenerate"}</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tabs & File Preview */}
      <div className="bg-slate-900/80 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/80 px-4 overflow-x-auto">
          <div className="flex items-center">
            {FILE_TABS.map((tab) => {
              const exists = job.markdown_files?.[tab.key];
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => loadFile(tab.key)}
                  className={`px-4 py-3 text-xs font-semibold border-b-2 transition flex items-center gap-2 whitespace-nowrap ${
                    isActive
                      ? "border-sky-500 text-sky-400 bg-sky-500/5"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <span>{tab.label}</span>
                  {exists && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => handleRegenerateStep(activeTab)}
            disabled={regeneratingStep === activeTab}
            className="px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50 whitespace-nowrap ml-4 my-2"
            title={`Regenerate ${activeTab}`}
          >
            <RotateCcw className={`w-3 h-3 ${regeneratingStep === activeTab ? "animate-spin" : ""}`} />
            <span>{regeneratingStep === activeTab ? "Regenerating..." : `Regenerate Step`}</span>
          </button>
        </div>

        <div className="p-6">
          {fileLoading ? (
            <div className="p-8 text-center text-slate-500">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-sky-400" />
              Loading markdown content...
            </div>
          ) : (
            <pre className="whitespace-pre-wrap font-mono text-xs text-slate-300 bg-slate-950 p-6 rounded-xl border border-slate-800 leading-relaxed overflow-x-auto max-h-[600px]">
              {fileContent}
            </pre>
          )}
        </div>
      </div>

      {/* Activity Timeline */}
      <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span>Activity & Execution Log</span>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live Sync (2s)
            </span>
          </h3>
          <span className="text-xs text-slate-500">{activity.length} events logged</span>
        </div>
        <div className="space-y-3">
          {activity.map((log: any) => (
            <div key={log.id} className="flex items-start space-x-3 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800/80">
              <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${log.status === "SUCCESS" ? "bg-emerald-400" : log.status === "FAILED" ? "bg-rose-400" : "bg-sky-400 animate-pulse"}`} />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white">{log.step_name}</span>
                  <span className="text-slate-500 text-[10px]">{formatTimeOnly(log.timestamp)}</span>
                </div>
                <p className="text-slate-400 mt-0.5">{log.message}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quality Audit Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
              <div className="flex items-center gap-2.5">
                <ShieldAlert className="w-5 h-5 text-orange-400" />
                <h2 className="text-base font-bold text-white">Quality Audit Structured Report</h2>
              </div>
              <button
                onClick={() => setShowReportModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-300">
              {reportLoading ? (
                <div className="p-8 text-center text-slate-400">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
                  Loading Quality Audit Report...
                </div>
              ) : reportData?.error ? (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
                  {reportData.error}
                </div>
              ) : reportData?.raw ? (
                <pre className="whitespace-pre-wrap font-mono bg-slate-950 p-4 rounded-xl border border-slate-800 text-slate-300 leading-relaxed overflow-x-auto">
                  {reportData.raw}
                </pre>
              ) : (
                <div className="space-y-5">
                  {/* Status Banner */}
                  <div className={`p-4 rounded-xl border flex items-center justify-between ${
                    reportData?.passed
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                      : "bg-orange-500/10 border-orange-500/30 text-orange-300"
                  }`}>
                    <div>
                      <p className="font-bold text-white text-sm">
                        Audit Outcome: {reportData?.passed ? "PASS" : "REVISION REQUIRED"}
                      </p>
                      <p className="text-[11px] opacity-80 mt-0.5">
                        Target keyword: <strong className="text-white">{job?.primary_keyword}</strong> &bull; Target Density: {job?.target_density || "2.0"}%
                      </p>
                    </div>
                    {reportData?.scores?.overall !== undefined && (
                      <div className="text-right">
                        <span className="text-2xl font-extrabold text-white">{reportData.scores.overall}</span>
                        <span className="text-xs text-slate-400 block">Overall Score</span>
                      </div>
                    )}
                  </div>

                  {/* Metrics Cards Grid */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-400">SEO Density</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          reportData?.seo?.status === "PASS" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                        }`}>
                          {reportData?.seo?.status || "N/A"}
                        </span>
                      </div>
                      <div className="text-lg font-bold text-white mt-1">
                        {reportData?.seo?.density !== undefined ? `${reportData.seo.density}%` : "N/A"}
                      </div>
                      <span className="text-[10px] text-slate-500 block">Target: {reportData?.seo?.target ?? job?.target_density ?? 2.0}%</span>
                    </div>

                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-400">Fact Checking</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          reportData?.fact_check?.status === "PASS" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                        }`}>
                          {reportData?.fact_check?.status || "N/A"}
                        </span>
                      </div>
                      <div className="text-lg font-bold text-white mt-1">
                        {reportData?.fact_check?.unsupported_claims !== undefined ? `${reportData.fact_check.unsupported_claims} issues` : "0 issues"}
                      </div>
                      <span className="text-[10px] text-slate-500 block">Unsupported claims</span>
                    </div>

                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-400">Editorial Quality</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          reportData?.editorial?.status === "PASS" ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"
                        }`}>
                          {reportData?.editorial?.status || "N/A"}
                        </span>
                      </div>
                      <div className="text-lg font-bold text-white mt-1">
                        {reportData?.editorial?.score !== undefined ? `${reportData.editorial.score}/100` : "N/A"}
                      </div>
                      <span className="text-[10px] text-slate-500 block">Readability score</span>
                    </div>
                  </div>

                  {/* Issues List */}
                  {reportData?.issues && reportData.issues.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-bold text-white uppercase text-[10px] tracking-wider text-slate-400">
                        Flagged Revision Issues ({reportData.issues.length})
                      </h4>
                      <div className="space-y-1.5 bg-slate-950 p-3 rounded-xl border border-slate-800">
                        {reportData.issues.map((iss: any, idx: number) => {
                          const isObj = typeof iss === "object" && iss !== null;
                          const issueText = isObj ? (iss.issue || JSON.stringify(iss)) : String(iss);
                          const issueType = isObj ? iss.type : null;
                          const severity = isObj ? iss.severity : null;
                          const recAction = isObj ? iss.recommended_action : null;

                          return (
                            <div key={idx} className="flex items-start gap-2 text-slate-300">
                              <span className="text-orange-400 font-bold mt-0.5">•</span>
                              <div className="flex-1">
                                <div className="flex items-center flex-wrap gap-1.5">
                                  {issueType && (
                                    <span className="px-1.5 py-0.5 rounded bg-sky-500/10 border border-sky-500/30 text-sky-300 text-[10px] font-mono font-bold uppercase">
                                      {issueType}
                                    </span>
                                  )}
                                  {severity && (
                                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                                      severity === "HIGH" ? "bg-rose-500/20 text-rose-300 border border-rose-500/30" : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    }`}>
                                      {severity}
                                    </span>
                                  )}
                                  <span className="font-medium text-white">{issueText}</span>
                                </div>
                                {recAction && (
                                  <p className="text-slate-400 text-[11px] mt-1 pl-0.5">
                                    <strong className="text-slate-300">Action:</strong> {recAction}
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowReportModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold transition"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowReportModal(false);
                  handleReviseDraft();
                }}
                className="px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold transition flex items-center gap-1.5 shadow-lg shadow-orange-500/20"
              >
                <Wrench className="w-3.5 h-3.5" />
                <span>Revise Draft Now</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Published Article Reader Modal */}
      {showPublishedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs uppercase font-semibold text-emerald-400 tracking-wide">Published Article</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
                      {job?.publishing_info?.cms || "Strapi"} CMS
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white mt-0.5">{job?.topic}</h3>
                </div>
              </div>
              <button
                onClick={() => setShowPublishedModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Publishing Metadata Bar */}
            <div className="px-5 py-2.5 bg-slate-950/80 border-b border-slate-800/80 text-xs flex flex-wrap items-center justify-between gap-3 text-slate-400">
              <div className="flex items-center space-x-4">
                <span>CMS Entry ID: <strong className="text-slate-200 font-mono">{job?.publishing_info?.cms_entry_id || "N/A"}</strong></span>
                {job?.publishing_info?.published_at && (
                  <span>Published: <strong className="text-slate-200">{new Date(job.publishing_info.published_at).toLocaleString()}</strong></span>
                )}
              </div>
              {job?.publishing_info?.published_url && (
                <a
                  href={job.publishing_info.published_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sky-400 hover:text-sky-300 underline inline-flex items-center gap-1 font-medium"
                >
                  <span>Open External CMS Link</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {publishedLoading ? (
                <div className="p-12 text-center text-slate-400 flex flex-col items-center">
                  <RefreshCw className="w-6 h-6 animate-spin mb-2 text-emerald-400" />
                  <span>Loading published article content...</span>
                </div>
              ) : (
                <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 text-slate-200 text-sm leading-relaxed font-sans whitespace-pre-wrap">
                  {publishedArticleText}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowPublishedModal(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold transition"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

