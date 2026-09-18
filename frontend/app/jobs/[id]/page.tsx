"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getJobDetail, getJobFilePreview, getJobActivity, retryJob, retryPublishing } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { formatTimeOnly } from "@/lib/formatters";
import { FileText, CheckCircle2, AlertCircle, RefreshCw, Layers, ArrowLeft, ExternalLink } from "lucide-react";

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

  const loadJob = async () => {
    try {
      const [jData, aData] = await Promise.all([
        getJobDetail(jobId),
        getJobActivity(jobId).catch(() => []),
      ]);
      setJob(jData);
      setActivity(aData);
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
      setFileContent(res.content);
    } catch (e) {
      setFileContent(`*File ${tabKey} is not yet generated in the workflow storage.*`);
    } finally {
      setFileLoading(false);
    }
  };

  useEffect(() => {
    loadJob();
    const interval = setInterval(loadJob, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

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
            <a
              href={job.publishing_info.published_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-semibold rounded-xl"
            >
              <span>View Published Article</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>

        {/* Workflow Stepper */}
        <div className="pt-4 border-t border-slate-800/80">
          <div className="grid grid-cols-5 gap-2 text-center text-xs">
            {steps.map((s, idx) => {
              const hasFile = job.markdown_files?.[s.file];
              return (
                <div
                  key={s.label}
                  onClick={() => loadFile(s.file)}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    activeTab === s.file
                      ? "bg-sky-500/10 border-sky-500/50 text-sky-300 font-semibold"
                      : hasFile
                      ? "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700"
                      : "bg-slate-950/40 border-slate-900 text-slate-600 opacity-60"
                  }`}
                >
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
              );
            })}
          </div>
        </div>
      </div>

      {/* Tabs & File Preview */}
      <div className="bg-slate-900/80 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
        <div className="flex items-center border-b border-slate-800 bg-slate-950/80 px-4 overflow-x-auto">
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
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Activity & Execution Log</h3>
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
    </div>
  );
}
