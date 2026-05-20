"use client";
/**
 * Main dashboard shell.
 * Tabs: Overview | Transactions | Import | Budgets | Reports | Settings
 */
import { useState } from "react";
import Overview from "./Overview";
import Transactions from "./Transactions";
import ImportSheet from "./ImportSheet";
import Budgets from "./Budgets";
import Reports from "./Reports";
import { supabase } from "@/lib/supabase";

const TABS = ["Overview", "Transactions", "Import", "Budgets", "Reports"] as const;
type Tab = (typeof TABS)[number];

export default function Dashboard() {
  const [tab, setTab] = useState<Tab>("Overview");

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* ── Top nav ──────────────────────────────────────────── */}
      <nav className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-900">
        <span className="font-bold text-lg">💰 Expense Tracker</span>
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                tab === t
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <button
          onClick={() => supabase.auth.signOut()}
          className="text-gray-500 hover:text-white text-sm transition"
        >
          Sign out
        </button>
      </nav>

      {/* ── Tab content ──────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === "Overview"      && <Overview />}
        {tab === "Transactions"  && <Transactions />}
        {tab === "Import"        && <ImportSheet />}
        {tab === "Budgets"       && <Budgets />}
        {tab === "Reports"       && <Reports />}
      </main>
    </div>
  );
}
