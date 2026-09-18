"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { parseCsvFile, validateCsvMapping, confirmBatchImport } from "@/lib/api";
import { FileSpreadsheet, Upload, CheckCircle2, AlertCircle, ArrowRight, Layers, Sparkles } from "lucide-react";

const LOGICAL_FIELDS = [
  { key: "topic", label: "Blog topic", required: true },
  { key: "primary_keyword", label: "Primary keyword", required: true },
  { key: "search_volume", label: "Search volume (Volume / Vol)", required: false },
  { key: "keyword_difficulty", label: "Keyword difficulty (KD)", required: false },
  { key: "target_density", label: "Target density", required: false },
  { key: "category", label: "Category", required: false },
  { key: "audience", label: "Target Audience", required: false },
  { key: "notes", label: "Notes / Instructions", required: false },
];

export default function NewBatchPage() {
  const router = useRouter();
  const [step, setStep] = useState<"upload" | "map_preview">("upload");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filename, setFilename] = useState<string>("");
  const [headers, setHeaders] = useState<string[]>([]);
  const [rawRows, setRawRows] = useState<Record<string, string>[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<any>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      const res = await parseCsvFile(file);

      setFilename(res.filename);
      setHeaders(res.headers);
      setRawRows(res.rows);

      // Auto-detected mapping matching headers to logical fields
      const autoMap: Record<string, string> = {};
      res.headers.forEach((h: string) => {
        if (res.detected_mapping[h]) {
          autoMap[h] = res.detected_mapping[h];
        }
      });
      setMapping(autoMap);
      setPreview(res.preview);
      setStep("map_preview");
    } catch (err: any) {
      setError(err.message || "Failed to parse CSV file");
    } finally {
      setLoading(false);
    }
  };

  const handleMappingChange = async (csvHeader: string, logicalField: string) => {
    const updated = { ...mapping };
    if (logicalField === "") {
      delete updated[csvHeader];
    } else {
      updated[csvHeader] = logicalField;
    }
    setMapping(updated);

    try {
      const updatedPreview = await validateCsvMapping({
        headers,
        rows: rawRows,
        column_mapping: updated,
      });
      setPreview(updatedPreview);
    } catch (err: any) {
      console.error("Mapping re-validation error:", err);
    }
  };

  const handleConfirmImport = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await confirmBatchImport({
        filename,
        headers,
        rows: rawRows,
        column_mapping: mapping,
      });
      router.push(`/batches/${res.batch_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to confirm batch import.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <FileSpreadsheet className="w-6 h-6 text-sky-400" />
          <span>Upload CSV Batch</span>
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Upload a CSV containing blog topics and SEO metadata to initiate automated research and writing.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {step === "upload" && (
        <div className="bg-slate-900/80 p-8 rounded-2xl border border-slate-800 shadow-xl text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mx-auto text-sky-400">
            <Upload className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-lg font-bold text-white">Select a CSV File to Upload</h2>
            <p className="text-xs text-slate-400 mt-1">
              File must contain at minimum columns for <strong>Blog topic</strong> and <strong>Primary keyword</strong>.
            </p>
          </div>

          <label className="inline-flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white px-6 py-3 rounded-xl font-semibold text-sm cursor-pointer shadow-lg shadow-sky-500/20 transition">
            <Upload className="w-4 h-4" />
            <span>Choose CSV File</span>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
              disabled={loading}
            />
          </label>

          <div className="pt-4 border-t border-slate-800 text-left text-xs text-slate-400 space-y-2">
            <p className="font-semibold text-slate-300">Expected CSV Format Example:</p>
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
              Blog topic,Primary keyword,Vol.,KD,Target density<br />
              Career Options: How to Choose the Right Career Path,career options,4400,35,0.8–1.0%<br />
              Career Opportunities in India: Best Paths for Students & Graduates,career opportunities,18100,57,0.7–0.9%
            </div>
          </div>
        </div>
      )}

      {step === "map_preview" && preview && (
        <div className="space-y-6">
          {/* File summary bar */}
          <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-sky-400" />
                <span>{filename}</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                {preview.total_rows} topics detected from CSV
              </p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
                ✓ {preview.valid_rows_count} Valid Rows
              </span>
              {preview.invalid_rows_count > 0 && (
                <span className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                  ⚠ {preview.invalid_rows_count} Invalid
                </span>
              )}
              {preview.duplicate_count > 0 && (
                <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold">
                  ! {preview.duplicate_count} Duplicates
                </span>
              )}
            </div>
          </div>

          {/* Column Mapping Section */}
          <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              1. Column Mapping Configuration
            </h3>
            <p className="text-xs text-slate-400">
              Map detected CSV headers to ContentEngine logical fields. Required fields must be mapped.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {headers.map((header) => {
                const currentMapped = mapping[header] || "";
                const isRequiredField = ["topic", "primary_keyword"].includes(currentMapped);
                return (
                  <div key={header} className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold text-slate-400 block">CSV Header</span>
                      <span className="text-sm font-bold text-white">{header}</span>
                    </div>
                    <div className="w-1/2">
                      <select
                        value={currentMapped}
                        onChange={(e) => handleMappingChange(header, e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-sky-500"
                      >
                        <option value="">-- Unmapped --</option>
                        {LOGICAL_FIELDS.map((lf) => (
                          <option key={lf.key} value={lf.key}>
                            {lf.label} {lf.required ? "*" : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Table Preview */}
          <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              2. Data Rows Validation Preview
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="text-slate-400 uppercase bg-slate-950/60 border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2">Row</th>
                    <th className="px-3 py-2">Blog Topic</th>
                    <th className="px-3 py-2">Primary Keyword</th>
                    <th className="px-3 py-2">Vol</th>
                    <th className="px-3 py-2">KD</th>
                    <th className="px-3 py-2">Density</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {preview.rows.map((r: any) => (
                    <tr key={r.row_index} className={r.is_valid ? "hover:bg-slate-800/40" : "bg-rose-500/5"}>
                      <td className="px-3 py-2 font-mono text-slate-500">#{r.row_index}</td>
                      <td className="px-3 py-2 font-semibold text-white max-w-xs truncate">
                        {r.topic || <span className="text-rose-400 italic">[Empty]</span>}
                      </td>
                      <td className="px-3 py-2 font-medium text-slate-300">
                        {r.primary_keyword || <span className="text-rose-400 italic">[Empty]</span>}
                      </td>
                      <td className="px-3 py-2">{r.search_volume ?? "N/A"}</td>
                      <td className="px-3 py-2">{r.keyword_difficulty ?? "N/A"}</td>
                      <td className="px-3 py-2">{r.target_density ?? "N/A"}</td>
                      <td className="px-3 py-2">
                        {r.is_valid ? (
                          <span className="text-emerald-400 font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Valid
                          </span>
                        ) : (
                          <span className="text-rose-400 font-semibold flex items-center gap-1" title={r.errors.join("; ")}>
                            <AlertCircle className="w-3.5 h-3.5" /> Invalid
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl">
            <button
              onClick={() => setStep("upload")}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
            >
              Cancel & Upload New
            </button>

            <button
              onClick={handleConfirmImport}
              disabled={loading || preview.valid_rows_count === 0}
              className="flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white px-6 py-2.5 rounded-xl font-semibold text-sm shadow-lg shadow-sky-500/20 disabled:opacity-50 transition"
            >
              <span>Import {preview.valid_rows_count} Topics</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
