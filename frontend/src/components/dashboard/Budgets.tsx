"use client";
import { useEffect, useState } from "react";
import { budgetsApi, type Budget } from "@/lib/api";
import toast from "react-hot-toast";

const CATEGORIES = [
  "Food","Groceries","Shopping","Transport","Travel to Chennai","Trip",
  "Utilities","Health","Entertainment","Rent","EMI","Subscriptions",
  "Insurance","Education","Investments","Others",
];

export default function Budgets() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [dirty,   setDirty]   = useState(false);
  const [saving,  setSaving]  = useState(false);

  useEffect(() => {
    budgetsApi.list().then(({ data }) => {
      const map = new Map(data.map((b) => [b.category, b.monthly_limit]));
      setBudgets(CATEGORIES.map((cat) => ({ category: cat, monthly_limit: map.get(cat) ?? 0 })));
    });
  }, []);

  const handleChange = (cat: string, val: string) => {
    setBudgets((prev) =>
      prev.map((b) => b.category === cat ? { ...b, monthly_limit: Number(val) || 0 } : b)
    );
    setDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await budgetsApi.upsert(budgets.filter((b) => b.monthly_limit > 0));
      toast.success("Budgets saved");
      setDirty(false);
    } catch {
      toast.error("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const totalBudget = budgets.reduce((s, b) => s + b.monthly_limit, 0);
  const fmt = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Monthly Budgets</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Set 0 to exclude a category from budget tracking.
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Total budget</div>
          <div className="text-xl font-bold text-indigo-400">{fmt(totalBudget)}</div>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-800/50 text-xs text-gray-500 uppercase">
              <th className="px-5 py-3 text-left">Category</th>
              <th className="px-5 py-3 text-right">Monthly limit (₹)</th>
            </tr>
          </thead>
          <tbody>
            {budgets.map((b) => (
              <tr key={b.category} className="border-t border-gray-800">
                <td className="px-5 py-3 text-sm">{b.category}</td>
                <td className="px-5 py-3">
                  <input
                    type="number"
                    min={0}
                    step={500}
                    value={b.monthly_limit || ""}
                    placeholder="0"
                    onChange={(e) => handleChange(b.category, e.target.value)}
                    className="w-36 text-right bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-indigo-500 float-right"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button
        onClick={handleSave}
        disabled={!dirty || saving}
        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm font-medium transition disabled:opacity-40"
      >
        {saving ? "Saving…" : "Save budgets"}
      </button>
    </div>
  );
}
