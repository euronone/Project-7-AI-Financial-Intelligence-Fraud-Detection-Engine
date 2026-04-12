"use client";

/**
 * Data Schema Mapping page (/dashboard/data-schema)
 *
 * Enhanced 3-column layout per table:
 *   Col 1 — FinShield column name (+ type badge + description)
 *   Col 2 — "Consider this column" toggle (grant/deny FinShield access)
 *   Col 3 — Customer's column name (text input; disabled when toggle is off)
 *
 * Two table sections: Customers and Transactions (tab-switched).
 * Users can append custom columns (not in FinShield's canonical schema).
 */

import { useAuthStore, isAdmin } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
  Shield, Database, Table, Save, RefreshCw, CheckCircle2,
  Info, Users, ArrowRightLeft, AlertTriangle, LogOut,
  Settings, Activity, TrendingUp, FlaskConical, Plus, Trash2, Brain,
} from "lucide-react";
import Link from "next/link";
import { apiClient, type SchemaField, type FieldMapping, type CustomColumn } from "@/lib/api-client";

// ── Types ─────────────────────────────────────────────────────────────────────
type SchemaTab = "customers" | "transactions";

/** One row in the canonical schema table. */
interface CanonicalRow {
  field: SchemaField;
  clientColumn: string;
  enabled: boolean;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const TYPE_COLOR: Record<string, string> = {
  UUID:        "text-[#8B5CF6]",
  STRING:      "text-[#3B82F6]",
  "STRING(2)": "text-[#3B82F6]",
  "STRING(3)": "text-[#3B82F6]",
  "STRING(4)": "text-[#3B82F6]",
  DECIMAL:     "text-[#F59E0B]",
  INTEGER:     "text-[#F59E0B]",
  BOOLEAN:     "text-[#00FF87]",
  DATE:        "text-[#F97316]",
  TIMESTAMP:   "text-[#F97316]",
  ENUM:        "text-[#EC4899]",
  JSON:        "text-gray-400",
};
const typeColor = (t: string) => TYPE_COLOR[t] ?? "text-gray-400";

const FIELD_TYPES = ["STRING", "UUID", "DECIMAL", "INTEGER", "BOOLEAN", "DATE", "TIMESTAMP", "ENUM", "JSON"];

// ── Toggle component ──────────────────────────────────────────────────────────
function Toggle({
  enabled,
  onChange,
  disabled = false,
}: {
  enabled: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={() => !disabled && onChange(!enabled)}
      title={enabled ? "FinShield can access this column" : "Column excluded from FinShield"}
      className={`relative inline-flex h-5 w-9 flex-shrink-0 rounded-full border-2 transition-colors duration-200 focus:outline-none ${
        disabled
          ? "cursor-not-allowed opacity-40 border-[#2E2E3E] bg-[#2E2E3E]"
          : enabled
          ? "cursor-pointer border-[#00FF87] bg-[#00FF87]/20"
          : "cursor-pointer border-[#2E2E3E] bg-[#1E1E2E]"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-3.5 w-3.5 rounded-full shadow-sm transition-transform duration-200 ${
          enabled ? "translate-x-4 bg-[#00FF87]" : "translate-x-0 bg-[#4E4E5E]"
        }`}
      />
    </button>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
const NAV = [
  { href: "/dashboard",              icon: Activity,      label: "Overview",      active: false, adminOnly: false },
  { href: "/dashboard/transactions", icon: TrendingUp,    label: "Transactions",  active: false, adminOnly: false },
  { href: "/dashboard/alerts",       icon: AlertTriangle, label: "Fraud Alerts",  active: false, adminOnly: false },
  { href: "/dashboard/test-me",      icon: FlaskConical,  label: "Test Me",       active: false, adminOnly: true },
  { href: "/dashboard/customers",    icon: Users,         label: "Customers",     active: false, adminOnly: false },
  { href: "/dashboard/data-sources", icon: Database,      label: "Data Sources",  active: false, adminOnly: false },
  { href: "/dashboard/data-schema",  icon: Table,         label: "Data Schema",   active: true,  adminOnly: false },
  { href: "/dashboard/ml-training",  icon: Brain,         label: "ML Training",   active: false, adminOnly: false },
  { href: "/dashboard/settings",     icon: Settings,      label: "Settings",      active: false, adminOnly: false },
];

// ── Page ──────────────────────────────────────────────────────────────────────
export default function DataSchemaPage() {
  const { isAuthenticated, token, user, clearAuth } = useAuthStore();
  const router = useRouter();

  const [tab, setTab] = useState<SchemaTab>("customers");

  // Canonical (FinShield-defined) rows
  const [custRows, setCustRows]   = useState<CanonicalRow[]>([]);
  const [txnRows, setTxnRows]     = useState<CanonicalRow[]>([]);

  // Custom (user-defined extra) columns
  const [custCustom, setCustCustom] = useState<CustomColumn[]>([]);
  const [txnCustom, setTxnCustom]   = useState<CustomColumn[]>([]);

  const [saving, setSaving]         = useState(false);
  const [saved, setSaved]           = useState(false);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login");
  }, [isAuthenticated, router]);

  const buildCanonicalRows = useCallback(
    (
      fields: SchemaField[],
      mapping: Record<string, FieldMapping>
    ): CanonicalRow[] =>
      fields.map((f) => {
        const entry = mapping[f.field];
        return {
          field: f,
          clientColumn: entry?.client_column ?? "",
          enabled: entry?.enabled ?? true,
        };
      }),
    []
  );

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    Promise.all([
      apiClient.getSchemaDefinition(token),
      apiClient.getSchemaMapping(token),
    ])
      .then(([def, mapping]) => {
        setCustRows(buildCanonicalRows(def.customers, mapping.customers));
        setTxnRows(buildCanonicalRows(def.transactions, mapping.transactions));
        setCustCustom(mapping.customers_custom ?? []);
        setTxnCustom(mapping.transactions_custom ?? []);
        setLastUpdated(mapping.last_updated ?? null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, buildCanonicalRows]);

  // ── Auto-fill: set every clientColumn = FinShield field name ─────────────
  function handleAutoFill() {
    const setter = tab === "customers" ? setCustRows : setTxnRows;
    setter((rows) => rows.map((r) => ({ ...r, clientColumn: r.field.field })));
    setSaved(false);
  }

  // ── Canonical row updaters ─────────────────────────────────────────────────
  function updateCanonical(
    which: SchemaTab,
    fieldName: string,
    patch: Partial<Pick<CanonicalRow, "clientColumn" | "enabled">>
  ) {
    const setter = which === "customers" ? setCustRows : setTxnRows;
    setter((rows) =>
      rows.map((r) =>
        r.field.field === fieldName ? { ...r, ...patch } : r
      )
    );
    setSaved(false);
  }

  // ── Custom column updaters ─────────────────────────────────────────────────
  function updateCustom(
    which: SchemaTab,
    idx: number,
    patch: Partial<CustomColumn>
  ) {
    const setter = which === "customers" ? setCustCustom : setTxnCustom;
    setter((cols) =>
      cols.map((c, i) => (i === idx ? { ...c, ...patch } : c))
    );
    setSaved(false);
  }

  function addCustomColumn(which: SchemaTab) {
    const blank: CustomColumn = {
      field: "",
      type: "STRING",
      description: "",
      client_column: "",
      enabled: true,
    };
    if (which === "customers") setCustCustom((c) => [...c, blank]);
    else setTxnCustom((c) => [...c, blank]);
    setSaved(false);
  }

  function removeCustomColumn(which: SchemaTab, idx: number) {
    const setter = which === "customers" ? setCustCustom : setTxnCustom;
    setter((cols) => cols.filter((_, i) => i !== idx));
    setSaved(false);
  }

  // ── Save ───────────────────────────────────────────────────────────────────
  async function handleSave() {
    if (!token) return;
    setSaving(true);
    setError(null);
    try {
      const toMappingRecord = (rows: CanonicalRow[]): Record<string, FieldMapping> =>
        Object.fromEntries(
          rows.map((r) => [
            r.field.field,
            { client_column: r.clientColumn.trim(), enabled: r.enabled },
          ])
        );

      await apiClient.saveSchemaMapping(
        {
          customers:           toMappingRecord(custRows),
          transactions:        toMappingRecord(txnRows),
          customers_custom:    custCustom,
          transactions_custom: txnCustom,
        },
        token
      );
      setSaved(true);
      setLastUpdated(new Date().toISOString());
      setTimeout(() => setSaved(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  function handleLogout() {
    clearAuth();
    router.replace("/login");
  }

  // ── Derived stats ──────────────────────────────────────────────────────────
  const canonRows   = tab === "customers" ? custRows : txnRows;
  const customCols  = tab === "customers" ? custCustom : txnCustom;
  const mappedCount = canonRows.filter((r) => r.clientColumn.trim() !== "").length;
  const enabledCount = canonRows.filter((r) => r.enabled).length + customCols.filter((c) => c.enabled).length;

  const isWrittenByFS = (desc: string) => desc.startsWith("[FinShield writes]");

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex">

      {/* ── Sidebar ── */}
      <aside className="w-64 bg-[#0D0D15] border-r border-[#1E1E2E] flex flex-col">
        <div className="p-6 border-b border-[#1E1E2E]">
          <div className="flex items-center gap-2">
            <Shield size={22} className="text-[#00FF87]" />
            <span className="font-bold text-lg">FinShield AI</span>
          </div>
          <div className="text-xs text-gray-500 mt-1">{user?.institution_name || "Dashboard"}</div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {NAV.filter(({ adminOnly }) => !adminOnly || isAdmin(user))
            .map(({ href, icon: Icon, label, active }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                active
                  ? "bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20"
                  : "text-gray-400 hover:text-white hover:bg-[#1E1E2E]"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-[#1E1E2E]">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-red-400 hover:bg-red-900/10 rounded-xl text-sm transition-all"
          >
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 flex flex-col overflow-hidden">

        {/* Header */}
        <header className="px-8 py-5 border-b border-[#1E1E2E] flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <ArrowRightLeft size={18} className="text-[#3B82F6]" />
              <h1 className="text-xl font-bold">Data Schema Mapping</h1>
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              Map your database columns to FinShield&apos;s schema and control access per field
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                Last saved: {new Date(lastUpdated).toLocaleString()}
              </span>
            )}
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 bg-[#3B82F6] hover:bg-[#2563EB] disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-all"
            >
              {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
              {saving ? "Saving…" : saved ? "Saved ✓" : "Save Mapping"}
            </button>
          </div>
        </header>

        {/* Info banner */}
        <div className="mx-8 mt-6 bg-[#3B82F6]/5 border border-[#3B82F6]/20 rounded-2xl p-4 flex gap-3">
          <Info size={16} className="text-[#3B82F6] mt-0.5 flex-shrink-0" />
          <div className="text-sm text-gray-300 leading-relaxed">
            <span className="font-semibold text-white">How to use: </span>
            Use the toggle to grant or deny FinShield access to each column.
            Enter your database&apos;s actual column name in the third column — leave blank if it already matches FinShield&apos;s name.
            Use <span className="text-[#00FF87] font-semibold">Add Custom Column</span> to include extra fields not in the standard schema.
            {" "}<span className="text-[#F59E0B]">✦ columns are written back by FinShield</span> — they must exist in your schema.
          </div>
        </div>

        {/* Tabs */}
        <div className="px-8 mt-6 flex gap-2">
          {(["customers", "transactions"] as SchemaTab[]).map((t) => {
            const Icon = t === "customers" ? Users : Database;
            const rows = t === "customers" ? custRows : txnRows;
            const custom = t === "customers" ? custCustom : txnCustom;
            const on = rows.filter((r) => r.enabled).length + custom.filter((c) => c.enabled).length;
            return (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold border transition-all ${
                  tab === t
                    ? "bg-[#3B82F6]/10 border-[#3B82F6]/40 text-[#3B82F6]"
                    : "border-[#1E1E2E] text-gray-400 hover:text-white hover:bg-[#1E1E2E]"
                }`}
              >
                <Icon size={15} />
                {t === "customers" ? "Customer Schema" : "Transaction Schema"}
                <span className="bg-[#00FF87]/10 text-[#00FF87] text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  {on} on
                </span>
              </button>
            );
          })}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-8 mt-4 bg-red-900/20 border border-red-500/30 rounded-xl p-3 text-sm text-red-400 flex gap-2">
            <AlertTriangle size={14} className="mt-0.5 flex-shrink-0" /> {error}
          </div>
        )}

        {/* Table area */}
        <div className="flex-1 overflow-auto px-8 mt-4 pb-8">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <RefreshCw size={20} className="animate-spin text-gray-500" />
              <span className="ml-2 text-gray-500">Loading schema…</span>
            </div>
          ) : (
            <>
              {/* Stats + Auto-fill */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{canonRows.length + customCols.length} columns total</span>
                  <span>·</span>
                  <span className="text-[#00FF87]">{enabledCount} accessible to FinShield</span>
                  <span>·</span>
                  <span className="text-[#3B82F6]">{mappedCount} renamed</span>
                  {customCols.length > 0 && (
                    <>
                      <span>·</span>
                      <span className="text-[#F59E0B]">{customCols.length} custom</span>
                    </>
                  )}
                </div>
                <button
                  onClick={handleAutoFill}
                  className="flex items-center gap-1.5 text-xs font-semibold text-[#F59E0B] border border-[#F59E0B]/30 bg-[#F59E0B]/5 hover:bg-[#F59E0B]/10 px-3 py-1.5 rounded-lg transition-all"
                  title="Auto-fill all &quot;Your Column Name&quot; fields with the FinShield column name"
                >
                  <RefreshCw size={12} />
                  Auto-fill column names
                </button>
              </div>

              <div className="bg-[#0D0D15] border border-[#1E1E2E] rounded-2xl overflow-hidden">

                {/* ── Column header ── */}
                <div className="grid grid-cols-[1fr_130px_1fr] border-b border-[#1E1E2E] px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  <div>FinShield Column</div>
                  <div className="text-center">Consider this column</div>
                  <div>Your Column Name</div>
                </div>

                {/* ── Canonical rows ── */}
                {canonRows.map((row, idx) => {
                  const fsWrites  = isWrittenByFS(row.field.description);
                  const isMapped  = row.clientColumn.trim() !== "";
                  const isOff     = !row.enabled;
                  const descText  = fsWrites
                    ? row.field.description.replace("[FinShield writes] ", "")
                    : row.field.description;

                  return (
                    <div
                      key={row.field.field}
                      className={`grid grid-cols-[1fr_130px_1fr] px-4 py-3.5 border-b border-[#1E1E2E]/40 items-center gap-4 transition-opacity ${
                        idx % 2 === 0 ? "bg-[#0D0D15]" : "bg-[#111118]"
                      } ${isOff ? "opacity-50" : ""}`}
                    >
                      {/* Col 1 — FinShield field info */}
                      <div className="flex items-start gap-2">
                        <div className="min-w-0">
                          <div className="font-mono text-white text-xs flex items-center gap-1.5 flex-wrap">
                            {fsWrites && (
                              <span className="text-[#F59E0B] text-[10px] font-bold">✦</span>
                            )}
                            <span>{row.field.field}</span>
                            <span className={`font-mono text-[10px] font-semibold ${typeColor(row.field.type)}`}>
                              {row.field.type}
                            </span>
                            {row.field.required && (
                              <span className="text-[10px] font-bold text-red-400 bg-red-900/20 px-1 py-0.5 rounded">
                                req
                              </span>
                            )}
                            {isMapped && row.enabled && (
                              <CheckCircle2 size={10} className="text-[#00FF87]" />
                            )}
                          </div>
                          <div className="text-[11px] text-gray-500 mt-0.5 leading-snug">{descText}</div>
                        </div>
                      </div>

                      {/* Col 2 — Toggle */}
                      <div className="flex flex-col items-center gap-1">
                        <Toggle
                          enabled={row.enabled}
                          onChange={(v) => updateCanonical(tab, row.field.field, { enabled: v })}
                        />
                        <span className={`text-[9px] font-semibold tracking-wide uppercase ${
                          row.enabled ? "text-[#00FF87]" : "text-gray-600"
                        }`}>
                          {row.enabled ? "Granted" : "Denied"}
                        </span>
                      </div>

                      {/* Col 3 — Client column name */}
                      <div>
                        <input
                          type="text"
                          value={row.clientColumn}
                          onChange={(e) =>
                            updateCanonical(tab, row.field.field, { clientColumn: e.target.value })
                          }
                          placeholder={`e.g. ${row.field.field}`}
                          disabled={!row.enabled}
                          className={`w-full bg-[#0A0A0F] border rounded-lg px-3 py-1.5 text-xs font-mono outline-none transition-all
                            ${!row.enabled
                              ? "border-[#1E1E2E] text-gray-600 cursor-not-allowed"
                              : isMapped
                              ? "border-[#00FF87]/30 text-[#00FF87] focus:border-[#00FF87]/60"
                              : "border-[#2E2E3E] text-gray-300 focus:border-[#3B82F6]/50 focus:text-white"
                            } placeholder:text-gray-600`}
                        />
                        {isMapped && row.enabled && (
                          <div className="text-[10px] text-gray-600 mt-0.5 font-mono truncate">
                            {row.field.field} ← {row.clientColumn}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* ── Custom columns ── */}
                {customCols.length > 0 && (
                  <>
                    <div className="px-4 py-2 bg-[#0A0A0F] border-t border-[#1E1E2E] text-[10px] font-bold uppercase tracking-widest text-[#F59E0B] flex items-center gap-2">
                      <Plus size={10} /> Custom Columns
                    </div>
                    {customCols.map((col, idx) => (
                      <div
                        key={idx}
                        className={`grid grid-cols-[1fr_130px_1fr] px-4 py-3.5 border-b border-[#1E1E2E]/40 items-start gap-4 ${
                          idx % 2 === 0 ? "bg-[#0D0D15]" : "bg-[#111118]"
                        } ${!col.enabled ? "opacity-50" : ""}`}
                      >
                        {/* Col 1 — Editable field name + type */}
                        <div className="flex flex-col gap-1.5">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="text"
                              value={col.field}
                              onChange={(e) => updateCustom(tab, idx, { field: e.target.value })}
                              placeholder="column_name"
                              className="flex-1 bg-[#0A0A0F] border border-[#2E2E3E] rounded-lg px-2.5 py-1 text-xs font-mono text-white outline-none focus:border-[#F59E0B]/50 placeholder:text-gray-600"
                            />
                            <select
                              value={col.type}
                              onChange={(e) => updateCustom(tab, idx, { type: e.target.value })}
                              className="bg-[#0A0A0F] border border-[#2E2E3E] rounded-lg px-2 py-1 text-[11px] font-mono outline-none focus:border-[#F59E0B]/50 text-gray-300"
                            >
                              {FIELD_TYPES.map((t) => (
                                <option key={t} value={t}>{t}</option>
                              ))}
                            </select>
                            <button
                              onClick={() => removeCustomColumn(tab, idx)}
                              className="text-gray-600 hover:text-red-400 transition-colors p-1 rounded"
                              title="Remove custom column"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                          <input
                            type="text"
                            value={col.description}
                            onChange={(e) => updateCustom(tab, idx, { description: e.target.value })}
                            placeholder="Optional description…"
                            className="bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg px-2.5 py-1 text-[11px] text-gray-500 outline-none focus:border-[#2E2E3E] placeholder:text-gray-700"
                          />
                        </div>

                        {/* Col 2 — Toggle */}
                        <div className="flex flex-col items-center gap-1 pt-1">
                          <Toggle
                            enabled={col.enabled}
                            onChange={(v) => updateCustom(tab, idx, { enabled: v })}
                          />
                          <span className={`text-[9px] font-semibold tracking-wide uppercase ${
                            col.enabled ? "text-[#00FF87]" : "text-gray-600"
                          }`}>
                            {col.enabled ? "Granted" : "Denied"}
                          </span>
                        </div>

                        {/* Col 3 — Client column name */}
                        <div className="pt-1">
                          <input
                            type="text"
                            value={col.client_column}
                            onChange={(e) => updateCustom(tab, idx, { client_column: e.target.value })}
                            placeholder={col.field || "your_db_column"}
                            disabled={!col.enabled}
                            className={`w-full bg-[#0A0A0F] border rounded-lg px-3 py-1.5 text-xs font-mono outline-none transition-all
                              ${!col.enabled
                                ? "border-[#1E1E2E] text-gray-600 cursor-not-allowed"
                                : col.client_column.trim()
                                ? "border-[#F59E0B]/30 text-[#F59E0B] focus:border-[#F59E0B]/60"
                                : "border-[#2E2E3E] text-gray-300 focus:border-[#3B82F6]/50 focus:text-white"
                              } placeholder:text-gray-600`}
                          />
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {/* Add Custom Column button */}
                <div className="px-4 py-3 flex items-center gap-3 border-t border-[#1E1E2E]">
                  <button
                    onClick={() => addCustomColumn(tab)}
                    className="flex items-center gap-2 text-xs text-[#F59E0B] hover:text-white border border-[#F59E0B]/20 hover:border-[#F59E0B]/50 hover:bg-[#F59E0B]/5 px-3 py-1.5 rounded-lg transition-all font-semibold"
                  >
                    <Plus size={12} />
                    Add Custom Column
                  </button>
                  <span className="text-xs text-gray-600">
                    Add columns from your DB that aren&apos;t in FinShield&apos;s standard schema
                  </span>
                </div>
              </div>

              {/* Quick reset */}
              <div className="mt-4 flex gap-3 items-center">
                <button
                  onClick={() => {
                    const setter = tab === "customers" ? setCustRows : setTxnRows;
                    setter((rs) =>
                      rs.map((r) => ({ ...r, clientColumn: "", enabled: true }))
                    );
                    if (tab === "customers") setCustCustom([]);
                    else setTxnCustom([]);
                    setSaved(false);
                  }}
                  className="text-xs text-gray-500 hover:text-red-400 border border-[#2E2E3E] hover:border-red-500/30 px-3 py-1.5 rounded-lg transition-all"
                >
                  Reset to defaults
                </button>
                <button
                  onClick={() => {
                    const setter = tab === "customers" ? setCustRows : setTxnRows;
                    setter((rs) => rs.map((r) => ({ ...r, enabled: true })));
                    setSaved(false);
                  }}
                  className="text-xs text-gray-500 hover:text-[#00FF87] border border-[#2E2E3E] hover:border-[#00FF87]/30 px-3 py-1.5 rounded-lg transition-all"
                >
                  Grant access to all
                </button>
                <button
                  onClick={() => {
                    const setter = tab === "customers" ? setCustRows : setTxnRows;
                    setter((rs) =>
                      rs.map((r) => {
                        const fsWrites = isWrittenByFS(r.field.description);
                        return { ...r, enabled: fsWrites ? true : false };
                      })
                    );
                    setSaved(false);
                  }}
                  className="text-xs text-gray-500 hover:text-[#EF4444] border border-[#2E2E3E] hover:border-red-500/30 px-3 py-1.5 rounded-lg transition-all"
                >
                  Deny all (keep FS writes)
                </button>
              </div>
            </>
          )}
        </div>

        {/* Sticky save footer */}
        {!loading && (
          <div className="border-t border-[#1E1E2E] px-8 py-4 flex items-center justify-between bg-[#0D0D15]">
            <div className="text-sm text-gray-500">
              <span className="text-[#00FF87] font-semibold">{enabledCount}</span> columns accessible
              {" · "}
              <span className="text-[#3B82F6] font-semibold">{mappedCount}</span> renamed
              {customCols.length > 0 && (
                <>
                  {" · "}
                  <span className="text-[#F59E0B] font-semibold">{customCols.length}</span> custom
                </>
              )}
            </div>
            <div className="flex items-center gap-3">
              {saved && (
                <span className="text-[#00FF87] text-sm flex items-center gap-1">
                  <CheckCircle2 size={14} /> Saved successfully
                </span>
              )}
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 bg-[#3B82F6] hover:bg-[#2563EB] disabled:opacity-60 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-all"
              >
                {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                {saving ? "Saving…" : "Save Mapping"}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
