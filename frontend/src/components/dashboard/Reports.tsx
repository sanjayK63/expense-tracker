"use client";
import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line, CartesianGrid,
} from "recharts";
import { reportsApi } from "@/lib/api";
import toast from "react-hot-toast";

const now = new Date();
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const COLORS = ["#6366f1","#f59e0b","#10b981","#ef4444","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f97316"];
const NON_SPEND = ["contra","transfer","repayment","refund","cashback","reversal","interest received"];
const isNonSpend = (c: string) => NON_SPEND.some((p) => c.toLowerCase().includes(p));

type YoyData  = Record<string, Record<string, number>>;
type RecurRow = { description: string; avg_amount: number; months: string[] };

export default function Reports() {
  const [year,      setYear]      = useState(now.getFullYear());
  const [month,     setMonth]     = useState(now.getMonth() + 1);
  const [yoy,       setYoy]       = useState<YoyData | null>(null);
  const [recurring, setRecurring] = useState<RecurRow[]>([]);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    reportsApi.yearOverYear().then(({ data }) => setYoy(data));
    reportsApi.recurring().then(({ data }) => setRecurring(data));
  }, []);

  const fmt = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  // ── Year-over-year monthly totals ──────────────────────────────────────
  const trendRows = yoy
    ? Object.entries(yoy).slice(-24).map(([ym, cats]) => ({
        month: ym,
        total: Object.entries(cats)
          .filter(([c]) => !isNonSpend(c))
          .reduce((s, [, v]) => s + v, 0),
      }))
    : [];

  // ── Category breakdown across the last 12 months ──────────────────────
  const last12 = yoy ? Object.entries(yoy).slice(-12) : [];
  const catTotals: Record<string, number> = {};
  last12.forEach(([, cats]) => {
    Object.entries(cats).forEach(([c, v]) => {
      if (!isNonSpend(c)) catTotals[c] = (catTotals[c] ?? 0) + v;
    });
  });
  const topCats = Object.entries(catTotals)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  // Build stacked bar data month × category
  const stackedData = last12.map(([ym, cats]) => {
    const row: Record<string, any> = { month: ym };
    topCats.forEach(([cat]) => { row[cat] = cats[cat] ?? 0; });
    return row;
  });

  const handleExport = async () => {
    setExporting(true);
    try {
      const { data } = await reportsApi.exportExcel(year, month);
      const url = URL.createObjectURL(new Blob([data]));
      const a   = document.createElement("a");
      a.href    = url;
      a.download = `expenses_${year}_${String(month).padStart(2,"0")}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Export failed");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Export row */}
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold mr-2">Reports</h2>
        <select value={month} onChange={(e) => setMonth(+e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
        </select>
        <select value={year} onChange={(e) => setYear(+e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {[2023,2024,2025,2026].map((y) => <option key={y}>{y}</option>)}
        </select>
        <button onClick={handleExport} disabled={exporting}
          className="px-4 py-2 bg-emerald-700 hover:bg-emerald-600 rounded-lg text-sm font-medium transition disabled:opacity-50 flex items-center gap-2">
          {exporting ? "Exporting…" : "⬇ Export Excel"}
        </button>
      </div>

      {/* Monthly trend */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Monthly Spend Trend (24 months)</h3>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={trendRows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `₹${(v/1000).toFixed(0)}K`} tick={{ fontSize: 10 }} />
            <Tooltip formatter={(v: any) => fmt(v)} />
            <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Category breakdown — stacked bar */}
      {stackedData.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Category Breakdown — Last 12 Months</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stackedData}>
              <XAxis dataKey="month" tick={{ fontSize: 10 }} />
              <YAxis tickFormatter={(v) => `₹${(v/1000).toFixed(0)}K`} tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: any) => fmt(v)} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {topCats.map(([cat], i) => (
                <Bar key={cat} dataKey={cat} stackId="a" fill={COLORS[i % COLORS.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recurring expenses */}
      {recurring.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">
            Recurring Expenses
            <span className="text-gray-600 font-normal ml-2">(same merchant 3+ months)</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b border-gray-800">
                  <th className="pb-2 text-left">Description</th>
                  <th className="pb-2 text-right">Avg / month</th>
                  <th className="pb-2 text-right">Occurrences</th>
                  <th className="pb-2 text-left pl-4">Months seen</th>
                </tr>
              </thead>
              <tbody>
                {recurring.map((r, i) => (
                  <tr key={i} className="border-t border-gray-800">
                    <td className="py-2.5 text-gray-200">{r.description}</td>
                    <td className="py-2.5 text-right font-medium">{fmt(r.avg_amount)}</td>
                    <td className="py-2.5 text-right text-gray-400">{r.months.length}</td>
                    <td className="py-2.5 pl-4 text-gray-500 text-xs">{r.months.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
