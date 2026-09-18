"use client";

import { useEffect, useState } from "react";
import { getSystemConfig, updateSystemConfig } from "@/lib/api";
import { Settings, Save, CheckCircle2, AlertCircle, RefreshCw, Key, Globe, Sparkles } from "lucide-react";

export default function SettingsPage() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const [form, setForm] = useState({
    strapi_url: "",
    strapi_api_token: "",
    strapi_content_type: "",
    openrouter_api_key: "",
    default_research_model: "",
    default_writer_model: "",
    default_quality_model: "",
    demo_mode: true,
  });

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await getSystemConfig();
      setConfig(data);
      setForm({
        strapi_url: data.strapi_url || "http://localhost:1337",
        strapi_api_token: "",
        strapi_content_type: data.strapi_content_type || "articles",
        openrouter_api_key: "",
        default_research_model: data.default_research_model || "google/gemini-2.5-pro-flash",
        default_writer_model: data.default_writer_model || "anthropic/claude-3.5-sonnet",
        default_quality_model: data.default_quality_model || "openai/gpt-4o-mini",
        demo_mode: data.demo_mode ?? true,
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setMessage(null);
      
      const payload: any = {
        strapi_url: form.strapi_url,
        strapi_content_type: form.strapi_content_type,
        default_research_model: form.default_research_model,
        default_writer_model: form.default_writer_model,
        default_quality_model: form.default_quality_model,
        demo_mode: form.demo_mode,
      };

      if (form.strapi_api_token.trim()) {
        payload.strapi_api_token = form.strapi_api_token;
      }
      if (form.openrouter_api_key.trim()) {
        payload.openrouter_api_key = form.openrouter_api_key;
      }

      await updateSystemConfig(payload);
      setMessage("Configuration saved successfully!");
      loadConfig();
    } catch (err: any) {
      alert(err.message || "Failed to update configuration");
    } finally {
      setSaving(false);
    }
  };

  if (loading && !config) {
    return (
      <div className="p-12 text-center text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
        <span>Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-sky-400" />
          <span>System Settings & API Configurations</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure OpenRouter AI models, Strapi CMS API tokens, and offline DEMO mode settings.
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Operating Mode */}
        <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Operating Mode</span>
          </h2>

          <div className="flex items-center justify-between bg-slate-950 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-sm font-bold text-white block">DEMO Mode (Offline Mock Mode)</span>
              <span className="text-xs text-slate-400">
                When enabled, system operates without requiring live OpenRouter or Strapi API keys.
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={form.demo_mode}
                onChange={(e) => setForm({ ...form, demo_mode: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-sky-500"></div>
            </label>
          </div>
        </div>

        {/* AI Provider Config */}
        <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Key className="w-4 h-4 text-sky-400" />
            <span>OpenRouter AI Configuration</span>
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">OpenRouter API Key</label>
              <input
                type="password"
                placeholder={config?.openrouter_api_key_configured ? "••••••••••••••••" : "sk-or-v1-..."}
                value={form.openrouter_api_key}
                onChange={(e) => setForm({ ...form, openrouter_api_key: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-sky-500 font-mono"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                {config?.openrouter_api_key_configured ? "✓ API Key Configured" : "⚠ Key missing (Falling back to DEMO mode)"}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Research Agent Model</label>
                <input
                  type="text"
                  value={form.default_research_model}
                  onChange={(e) => setForm({ ...form, default_research_model: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Writer Agent Model</label>
                <input
                  type="text"
                  value={form.default_writer_model}
                  onChange={(e) => setForm({ ...form, default_writer_model: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Quality Check Model</label>
                <input
                  type="text"
                  value={form.default_quality_model}
                  onChange={(e) => setForm({ ...form, default_quality_model: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-3 py-2 text-xs font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Strapi CMS Integration */}
        <div className="bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Globe className="w-4 h-4 text-emerald-400" />
            <span>Strapi CMS Integration Settings</span>
          </h2>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Strapi Base URL</label>
                <input
                  type="text"
                  value={form.strapi_url}
                  onChange={(e) => setForm({ ...form, strapi_url: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-xs font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Content Type Endpoint</label>
                <input
                  type="text"
                  value={form.strapi_content_type}
                  onChange={(e) => setForm({ ...form, strapi_content_type: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-xs font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Strapi API Token (Bearer Token)</label>
              <input
                type="password"
                placeholder={config?.strapi_api_token_configured ? "••••••••••••••••" : "Bearer Token..."}
                value={form.strapi_api_token}
                onChange={(e) => setForm({ ...form, strapi_api_token: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-xs font-mono focus:outline-none focus:border-emerald-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                {config?.strapi_api_token_configured ? "✓ Token Configured" : "⚠ Token missing"}
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white px-6 py-2.5 rounded-xl font-semibold text-sm shadow-lg shadow-sky-500/20 transition disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
}
