"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboardMetrics, getBatchesList } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { formatDate } from "@/lib/formatters";
import { FileSpreadsheet, CheckCircle2, ArrowRight, RefreshCw, AlertCircle, Layers, Sparkles } from "lucide-react";

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [batches, setBatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [mRes, bRes] = await Promise.all([
        getDashboardMetrics().catch(() => null),
        getBatchesList().catch(() => []),
      ]);
      setMetrics(mRes);
      setBatches(bRes || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Live polling dashboard every 5s
    return () => clearInterval(interval);
  }, []);

  const p = metrics?.pipeline || {};

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800/80 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <span>AI CONTENT ENGINE</span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 font-semibold tracking-normal">
              Production Dashboard
            </span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            CSV-driven autonomous article research, multi-agent drafting, quality audits, human approval & Strapi publishing.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadData}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700"
            title="Refresh metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <Link
            href="/batches/new"
            className="flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white px-4 py-2.5 rounded-xl font-semibold text-sm shadow-lg shadow-sky-500/20 transition"
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Upload New CSV</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800/80 shadow-md">
          <p className="text-xs uppercase font-semibold text-slate-400">Total Batches</p>
          <p className="text-3xl font-bold text-white mt-2">{metrics?.total_batches ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Uploaded CSV files</p>
        </div>
        <div className="bg-slate-900/80 p-5 rounded-2xl border border-slate-800/80 shadow-md">
          <p className="text-xs uppercase font-semibold text-slate-400">Total Articles</p>
          <p className="text-3xl font-bold text-white mt-2">{metrics?.total_articles ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Processed content jobs</p>
        </div>
        <div className="bg-slate-900/80 p-5 rounded-2xl border border-amber-500/20 shadow-md">
          <p className="text-xs uppercase font-semibold text-amber-400">Awaiting Review</p>
          <p className="text-3xl font-bold text-amber-400 mt-2">{p.awaiting_review ?? 0}</p>
          <Link href="/review" className="inline-flex items-center text-xs text-amber-400/80 hover:underline mt-1">
            Review articles <ArrowRight className="w-3 h-3 ml-1" />
          </Link>
        </div>
        <div className="bg-slate-900/80 p-5 rounded-2xl border border-emerald-500/20 shadow-md">
          <p className="text-xs uppercase font-semibold text-emerald-400">Published to Strapi</p>
          <p className="text-3xl font-bold text-emerald-400 mt-2">{p.published ?? 0}</p>
          <p className="text-xs text-slate-500 mt-1">Verified CMS entries</p>
        </div>
      </div>

      {/* Content Pipeline Status Overview */}
      <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center justify-between">
          <span>Content Pipeline Status</span>
          <span className="text-xs text-slate-400 font-normal">Real-time status breakdown</span>
        </h2>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-center">
            <span className="block text-xs text-slate-400 uppercase font-semibold">Queued</span>
            <span className="text-xl font-bold text-slate-200 mt-1 block">{p.queued ?? 0}</span>
          </div>
          <div className="bg-slate-950 p-3.5 rounded-xl border border-indigo-500/20 text-center">
            <span className="block text-xs text-indigo-400 uppercase font-semibold">Researching</span>
            <span className="text-xl font-bold text-indigo-400 mt-1 block">{p.researching ?? 0}</span>
          </div>
          <div className="bg-slate-950 p-3.5 rounded-xl border border-indigo-500/20 text-center">
            <span className="block text-xs text-indigo-300 uppercase font-semibold">Writing</span>
            <span className="text-xl font-bold text-indigo-300 mt-1 block">{p.writing ?? 0}</span>
          </div>
          <div className="bg-slate-950 p-3.5 rounded-xl border border-amber-500/20 text-center">
            <span className="block text-xs text-amber-400 uppercase font-semibold">Review</span>
            <span className="text-xl font-bold text-amber-400 mt-1 block">{p.awaiting_review ?? 0}</span>
          </div>
          <div className="bg-slate-950 p-3.5 rounded-xl border border-emerald-500/20 text-center">
            <span className="block text-xs text-emerald-400 uppercase font-semibold">Published</span>
            <span className="text-xl font-bold text-emerald-400 mt-1 block">{p.published ?? 0}</span>
          </div>
          <div className="bg-slate-950 p-3.5 rounded-xl border border-rose-500/20 text-center">
            <span className="block text-xs text-rose-400 uppercase font-semibold">Failed</span>
            <span className="text-xl font-bold text-rose-400 mt-1 block">{p.failed ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Recent Batches List */}
      <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Recent Batches</h2>
          <Link href="/batches/new" className="text-xs text-sky-400 hover:underline flex items-center gap-1">
            <span>+ Create Batch</span>
          </Link>
        </div>

        {batches.length === 0 ? (
          <div className="p-8 text-center bg-slate-950/60 rounded-xl border border-slate-800/60">
            <FileSpreadsheet className="w-10 h-10 mx-auto text-slate-600 mb-3" />
            <p className="text-slate-300 font-semibold">No batches created yet</p>
            <p className="text-slate-500 text-xs mt-1">Upload a CSV containing blog topics to begin processing.</p>
            <Link
              href="/batches/new"
              className="inline-flex items-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-xl text-xs font-semibold mt-4 transition"
            >
              Upload First CSV
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Filename</th>
                  <th className="px-4 py-3">Total Rows</th>
                  <th className="px-4 py-3">Valid / Invalid</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {batches.map((batch) => (
                  <tr key={batch.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-semibold text-white flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-sky-400 flex-shrink-0" />
                      <span className="truncate max-w-xs">{batch.filename}</span>
                    </td>
                    <td className="px-4 py-3 font-medium">{batch.total_rows}</td>
                    <td className="px-4 py-3 text-xs">
                      <span className="text-emerald-400 font-semibold">{batch.valid_rows} valid</span>
                      {batch.invalid_rows > 0 && (
                        <span className="text-rose-400 ml-2 font-semibold">{batch.invalid_rows} invalid</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={batch.status} />
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {formatDate(batch.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/batches/${batch.id}`}
                        className="inline-flex items-center text-xs font-semibold text-sky-400 hover:text-sky-300"
                      >
                        View Batch <ArrowRight className="w-3 h-3 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
