"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getBatchDetail } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { formatDate } from "@/lib/formatters";
import { FileSpreadsheet, ArrowRight, RefreshCw, Layers } from "lucide-react";

export default function BatchDetailPage() {
  const params = useParams();
  const batchId = params.id as string;

  const [batch, setBatch] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await getBatchDetail(batchId);
      setBatch(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000); // Poll batch progress
    return () => clearInterval(interval);
  }, [batchId]);

  if (loading && !batch) {
    return (
      <div className="p-12 text-center text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
        <span>Loading batch details...</span>
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="p-12 text-center text-rose-400 bg-slate-900 rounded-2xl border border-slate-800">
        Batch not found.
      </div>
    );
  }

  const jobs = batch.jobs || [];
  const publishedCount = jobs.filter((j: any) => j.status === "PUBLISHED").length;
  const reviewCount = jobs.filter((j: any) => j.status === "AWAITING_APPROVAL").length;
  const failedCount = jobs.filter((j: any) => j.status === "FAILED").length;
  const totalCount = jobs.length;
  const progressPct = totalCount > 0 ? Math.round(((publishedCount + reviewCount) / totalCount) * 100) : 0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs uppercase tracking-wider font-semibold text-sky-400">Content Batch</span>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2 mt-1">
              <FileSpreadsheet className="w-6 h-6 text-sky-400" />
              <span>{batch.filename}</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Created {formatDate(batch.created_at)} &bull; {totalCount} total jobs queued
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
              {publishedCount} Published
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold">
              {reviewCount} Awaiting Review
            </span>
            {failedCount > 0 && (
              <span className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                {failedCount} Failed
              </span>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5 pt-2">
          <div className="flex justify-between text-xs font-semibold text-slate-300">
            <span>Overall Batch Progress</span>
            <span>{progressPct}%</span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-sky-500 to-emerald-500 h-3 transition-all duration-500 rounded-full"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white">Batch Topics & Content Jobs</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Topic</th>
                <th className="px-4 py-3">Keyword</th>
                <th className="px-4 py-3">Volume</th>
                <th className="px-4 py-3">KD</th>
                <th className="px-4 py-3">Target Density</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {jobs.map((job: any) => (
                <tr key={job.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-4 py-3 font-semibold text-white max-w-xs truncate">
                    {job.topic}
                  </td>
                  <td className="px-4 py-3 text-slate-300 font-medium">{job.primary_keyword}</td>
                  <td className="px-4 py-3">{job.search_volume ?? "N/A"}</td>
                  <td className="px-4 py-3">{job.keyword_difficulty ?? "N/A"}</td>
                  <td className="px-4 py-3">{job.target_density ?? "N/A"}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/jobs/${job.id}`}
                      className="inline-flex items-center text-xs font-semibold text-sky-400 hover:text-sky-300"
                    >
                      View Details <ArrowRight className="w-3 h-3 ml-1" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
