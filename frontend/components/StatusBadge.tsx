import React from "react";

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = (status || "QUEUED").toUpperCase();

  const getStyle = () => {
    switch (normalized) {
      case "PUBLISHED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "AWAITING_APPROVAL":
      case "FINAL_READY":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "APPROVED":
      case "PUBLISHING":
        return "bg-sky-500/10 text-sky-400 border-sky-500/30 animate-pulse";
      case "RESEARCHING":
      case "BRIEF_GENERATING":
      case "WRITING":
      case "QUALITY_CHECK":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/30";
      case "REVISION_REQUIRED":
        return "bg-orange-500/10 text-orange-400 border-orange-500/30";
      case "FAILED":
      case "CANCELLED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border tracking-wide uppercase ${getStyle()}`}
    >
      {normalized.replace(/_/g, " ")}
    </span>
  );
}
