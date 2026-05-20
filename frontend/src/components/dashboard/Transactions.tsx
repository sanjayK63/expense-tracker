"use client";
import { useEffect, useState, useCallback } from "react";
import { expensesApi, type Expense } from "@/lib/api";
import toast from "react-hot-toast";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const now = new Date();

export default function Transactions() {
  const [expenses,  setExpenses]  = useState<Expense[]>([]);
  const [loading,   setLoading]   = useState(false);
  const [year,      setYear]      = useState(now.getFullYear());
  const [month,     setMonth]     = useState(now.getMonth() + 1);
  const [category,  setCategory]  = useState("");
  const [source,    setSource]    = useState("");
  const [sources,   setSources]   = useState<string[]>([]);
  const [categories,setCategories]= useState<string[]>([]);
  const [editing,   setEditing]   = useState<Expense | null>(null);
  const [deleteSource, setDeleteSource] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { year, month };
      if (category) params.category = category;
      if (source)   params.source   = source;
      const { data } = await expensesApi.list(params);
      setExpenses(data);
      const allSrcs = [...new Set(data.map((e) => e.source).filter(Boolean))].sort();
      const allCats = [...new Set(data.map((e) => e.category))].sort();
      if (!source) setSources(allSrcs);
      if (!category) setCategories(allCats);
    } finally {
      setLoading(false);
    }
  }, [year, month, category, source]);

  useEffect(() => { load(); }, [load]);

  const fmt = (n: number) =>
    `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this transaction?")) return;
    await expensesApi.delete(id);
    toast.success("Deleted");
    load();
  };

  const handleDeleteBatch = async () => {
    if (!deleteSource) return;
    if (!confirm(`Delete ALL transactions from "${deleteSource}"?`)) return;
    await expensesApi.deleteBySource(deleteSource);
    toast.success(`Deleted all transactions from ${deleteSource}`);
    setDeleteSource(null);
    load();
  };

  const handleSaveEdit = async () => {
    if (!editing) return;
    await expensesApi.update(editing.id, {
      date: editing.date,
      amount: editing.amount,
      category: editing.category,
      description: editing.description,
      payment_method: editing.payment_method,
    });
    toast.success("Saved");
    setEditing(null);
    load();
  };

  const total = expenses.reduce((s, e) => s + (e.type === "Debit" ? e.amount : 0), 0);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <select value={month} onChange={(e) => setMonth(+e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
        </select>
        <select value={year} onChange={(e) => setYear(+e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          {[2023,2024,2025,2026].map((y) => <option key={y}>{y}</option>)}
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select value={source} onChange={(e) => setSource(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
          <option value="">All accounts</option>
          {sources.map((s) => <option key={s}>{s}</option>)}
        </select>

        {/* Batch delete trigger */}
        {sources.length > 0 && (
          <div className="ml-auto flex gap-2 items-center">
            <select value={deleteSource ?? ""} onChange={(e) => setDeleteSource(e.target.value || null)}
              className="bg-gray-800 border border-red-800 rounded-lg px-3 py-2 text-sm text-red-400">
              <option value="">Delete by account…</option>
              {sources.map((s) => <option key={s}>{s}</option>)}
            </select>
            {deleteSource && (
              <button onClick={handleDeleteBatch}
                className="px-3 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-medium transition">
                Delete batch
              </button>
            )}
          </div>
        )}
      </div>

      {/* Summary bar */}
      <div className="flex justify-between text-sm text-gray-400">
        <span>{expenses.length} transactions</span>
        <span className="font-semibold text-white">Total debits: {fmt(total)}</span>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center text-gray-500 py-16">Loading…</div>
      ) : expenses.length === 0 ? (
        <div className="text-center text-gray-600 py-16">No transactions found</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-900 text-gray-500 uppercase text-xs">
                {["Date","Description","Category","Amount","Method","Account",""].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {expenses.map((e) => (
                <tr key={e.id} className="border-t border-gray-800 hover:bg-gray-900/50 transition">
                  <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{e.date}</td>
                  <td className="px-4 py-3 max-w-xs truncate">{e.description}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 text-xs">
                      {e.category}
                    </span>
                  </td>
                  <td className={`px-4 py-3 font-medium whitespace-nowrap ${
                    e.type === "Credit" ? "text-emerald-400" : "text-white"
                  }`}>
                    {e.type === "Credit" ? "+" : ""}{fmt(e.amount)}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{e.payment_method || "—"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{e.source || "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button onClick={() => setEditing(e)}
                        className="text-gray-500 hover:text-indigo-400 text-xs transition">Edit</button>
                      <button onClick={() => handleDelete(e.id)}
                        className="text-gray-500 hover:text-red-400 text-xs transition">Del</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit modal */}
      {editing && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
          onClick={() => setEditing(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md space-y-4"
            onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-lg">Edit Transaction</h3>
            {(["date","description","category","payment_method"] as const).map((field) => (
              <div key={field}>
                <label className="text-xs text-gray-500 uppercase mb-1 block">
                  {field.replace("_", " ")}
                </label>
                <input
                  value={(editing as any)[field] ?? ""}
                  onChange={(e) => setEditing({ ...editing, [field]: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
                />
              </div>
            ))}
            <div>
              <label className="text-xs text-gray-500 uppercase mb-1 block">Amount</label>
              <input type="number"
                value={editing.amount}
                onChange={(e) => setEditing({ ...editing, amount: +e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div className="flex gap-3 justify-end pt-2">
              <button onClick={() => setEditing(null)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-white transition">Cancel</button>
              <button onClick={handleSaveEdit}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition">
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
