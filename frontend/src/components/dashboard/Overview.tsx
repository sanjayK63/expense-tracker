"use client";
import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Legend } from "recharts";
import { reportsApi, budgetsApi, type Budget } from "@/lib/api";

const COLORS = ["#6366f1","#f59e0b","#10b981","#ef4444","#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f97316"];
const NON_SPEND = ["contra","transfer","repayment","refund","cashback","reversal","interest received"];
const isNonSpend = (c: string) => NON_SPEND.some((p) => c.toLowerCase().includes(p));

export default function Overview() {
  const now = new Date();
  const [year,  setYear]    = useState(now.getFullYear());
  const [month, setMonth]   = useState(now.getMonth() + 1);
  const [summary, setSummary] = useState<any>(null);
  const [yoy,    setYoy]    = useState<any>(null);
  const [budgets, setBudgets] = useState<Budget[]>([]);

  useEffect(() => {
    reportsApi.monthlySummary(year, month).then((r) => setSummary(r.data));
    reportsApi.yearOverYear().then((r) => setYoy(r.data));
    budgetsApi.list().then((r) => setBudgets(r.data));
  }, [year, month]);

  const fmt = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  const spendCats = summary
    ? Object.entries(summary.by_category as Record<string, number>)
        .filter(([cat]) => !isNonSpend(cat))
        .sort((a, b) => (b[1] as number) - (a[1] as number))
    : [];

  const budgetedTotal = budgets.reduce((s, b) => s + b.monthly_limit, 0);
  const budgetedSpent = spendCats
    .filter(([cat]) => budgets.find((b) => b.category === cat && b.monthly_limit > 0))
    .reduce((s, [, v]) => s + (v as number), 0);
  const totalSpent = spendCats.reduce((s, [, v]) => s + (v as number), 0);

  // Build trend data from YoY
  const trendData = yoy
    ? Object.entries(yoy as Record<string, Record<string, number>>)
        .slice(-12)
        .map(([ym, cats]) => ({
          month: ym,
          total: Object.entries(cats)
            .filter(([c]) => !isNonSpend(c))
            .reduce((s, [, v]) => s + v, 0),
        }))
    : [];

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  return (
    <div className="space-y-6">
      {/* Month/Year picker */}
      <div className="flex gap-3 items-center">
        <select value={month} onChange={(e) => setMonth(+e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {MONTHS.map((m, i) => <option key={m} value={i+1}>{m}</option>)}
        </select>
        <select value={year} onChange={(e) => setYear(+e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {[2023,2024,2025,2026].map((y) => <option key={y}>{y}</option>)}
        </select>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Spent",     value: fmt(totalSpent) },
          { label: "Budget (tracked)", value: budgetedTotal > 0 ? fmt(budgetedTotal) : "Not set" },
          { label: "Remaining",
            value: budgetedTotal > 0 ? fmt(budgetedTotal - budgetedSpent) : "Set budget",
            color: budgetedTotal > 0 && budgetedTotal - budgetedSpent >= 0 ? "text-emerald-400" : "text-red-400" },
          { label: "Transactions",    value: summary?.transactions ?? "—" },
        ].map((k) => (
          <div key={k.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{k.label}</div>
            <div className={`text-2xl font-bold ${(k as any).color ?? ""}`}>{String(k.value)}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={spendCats.map(([name, value]) => ({ name, value }))}
                cx="50%" cy="50%" innerRadius={70} outerRadius={110}
                dataKey="value" nameKey="name">
                {spendCats.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v: any) => fmt(v)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">12-Month Trend</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={trendData}>
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `₹${(v/1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: any) => fmt(v)} />
              <Bar dataKey="total" fill="#6366f1" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Budget vs actual bars */}
      {budgets.filter((b) => b.monthly_limit > 0).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-semibold mb-4 text-gray-300">Budget vs Actual</h3>
          <div className="space-y-3">
            {budgets.filter((b) => b.monthly_limit > 0).map((b) => {
              const spent = (summary?.by_category?.[b.category] ?? 0) as number;
              const pct   = Math.min((spent / b.monthly_limit) * 100, 100);
              const over  = spent > b.monthly_limit;
              return (
                <div key={b.category}>
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>{b.category}</span>
                    <span>{fmt(spent)} / {fmt(b.monthly_limit)}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${over ? "bg-red-500" : "bg-emerald-400"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
