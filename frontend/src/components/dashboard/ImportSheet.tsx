"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { importApi, type Expense } from "@/lib/api";
import toast from "react-hot-toast";

const PDF_EXTS  = ["pdf"];
const SHEET_EXTS = ["xlsx", "xls", "xlsb", "csv"];
const getExt = (name: string) => name.split(".").pop()?.toLowerCase() ?? "";

type PreviewRow = Expense & { _selected?: boolean };

const CATEGORIES = [
  "Food","Groceries","Shopping","Transport","Travel to Chennai","Trip",
  "Utilities","Health","Entertainment","Rent","EMI","Subscriptions",
  "Insurance","Education","Investments","Contra","Transfer","Repayment",
  "Refund","Cashback","Others",
];

export default function ImportSheet() {
  const [accountName, setAccountName] = useState("");
  const [password,    setPassword]    = useState("");
  const [stage,       setStage]       = useState<"upload" | "preview" | "done">("upload");
  const [rows,        setRows]        = useState<PreviewRow[]>([]);
  const [loading,     setLoading]     = useState(false);
  const [message,     setMessage]     = useState("");
  const [fileType,    setFileType]    = useState<"pdf" | "sheet">("pdf");

  const onDrop = useCallback(async (accepted: File[]) => {
    if (!accepted.length) return;
    const file = accepted[0];
    if (!accountName.trim()) { toast.error("Enter account name first"); return; }
    setLoading(true);
    setMessage("");
    try {
      const ext = getExt(file.name);
      let data: any;
      if (PDF_EXTS.includes(ext)) {
        ({ data } = await importApi.uploadPdf(file, accountName.trim(), password));
        setFileType("pdf");
      } else if (SHEET_EXTS.includes(ext)) {
        ({ data } = await importApi.uploadSheet(file, accountName.trim()));
        setFileType("sheet");
      } else {
        toast.error("Unsupported file type. Use PDF, XLSX, XLS, XLSB, or CSV.");
        return;
      }
      const preview: PreviewRow[] = (data.rows ?? []).map((r: Expense) => ({ ...r, _selected: true }));
      setRows(preview);
      setMessage(`${preview.length} transactions detected from ${file.name}`);
      setStage("preview");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Parse failed");
    } finally {
      setLoading(false);
    }
  }, [accountName, password]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel.sheet.binary.macroEnabled.12": [".xlsb"],
      "text/csv": [".csv"],
    },
    multiple: false,
  });

  const toggleRow  = (idx: number) =>
    setRows((prev) => prev.map((r, i) => i === idx ? { ...r, _selected: !r._selected } : r));

  const toggleAll  = (val: boolean) =>
    setRows((prev) => prev.map((r) => ({ ...r, _selected: val })));

  const updateCategory = (idx: number, cat: string) =>
    setRows((prev) => prev.map((r, i) => i === idx ? { ...r, category: cat } : r));

  const handleConfirm = async () => {
    const selected = rows.filter((r) => r._selected).map(({ _selected, ...r }) => r);
    if (!selected.length) { toast.error("No rows selected"); return; }
    setLoading(true);
    try {
      if (fileType === "pdf") {
        await importApi.confirmPdf(selected);
      } else {
        await importApi.confirmSheet(selected);
      }
      toast.success(`${selected.length} transactions imported`);
      setStage("done");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Import failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setStage("upload"); setRows([]); setMessage(""); setPassword(""); };

  const fmt = (n: number) => `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

  return (
    <div className="space-y-6 max-w-5xl">
      <h2 className="text-lg font-semibold">Import Statement</h2>

      {/* ── Upload stage ─────────────────────────────────────────── */}
      {stage === "upload" && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">
              Account / Card Name *
            </label>
            <input
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              placeholder="e.g. AU Savings, Slice CC, HDFC Salary"
              className="w-full max-w-sm bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">
              PDF Password (if protected)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Leave blank if not password-protected"
              className="w-full max-w-sm bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition ${
              isDragActive ? "border-indigo-500 bg-indigo-950/30" : "border-gray-700 hover:border-gray-600"
            }`}
          >
            <input {...getInputProps()} />
            {loading ? (
              <p className="text-gray-400">Parsing statement…</p>
            ) : (
              <>
                <div className="text-4xl mb-3">📄</div>
                <p className="text-gray-300 font-medium">
                  {isDragActive ? "Drop the file here" : "Drag & drop or click to upload"}
                </p>
                <p className="text-xs text-gray-600 mt-1">Supports PDF, XLSX, XLS, XLSB, CSV</p>
                <p className="text-xs text-gray-600 mt-1">
                  Detected parsers: Slice CC • BOB CC • AU Bank • Generic
                </p>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Preview stage ────────────────────────────────────────── */}
      {stage === "preview" && (
        <div className="space-y-4">
          {/* datalist for category suggestions */}
          <datalist id="cat-suggestions">
            {CATEGORIES.map((c) => <option key={c} value={c} />)}
          </datalist>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-300">{message}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {rows.filter((r) => r._selected).length} / {rows.length} selected
                <span className="ml-3 text-gray-600">· Click category to edit · Ctrl+C / Ctrl+V supported</span>
              </p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => toggleAll(true)}
                className="text-xs text-indigo-400 hover:text-indigo-300">Select all</button>
              <span className="text-gray-600">|</span>
              <button onClick={() => toggleAll(false)}
                className="text-xs text-gray-500 hover:text-gray-400">Deselect all</button>
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-gray-800 max-h-[60vh] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-900 z-10">
                <tr className="text-gray-500 uppercase text-xs">
                  <th className="px-3 py-3 text-left w-8">✓</th>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-left">Description</th>
                  <th className="px-4 py-3 text-left w-44">Category</th>
                  <th className="px-4 py-3 text-left">Amount</th>
                  <th className="px-4 py-3 text-left">Type</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr
                    key={i}
                    className={`border-t border-gray-800 transition ${
                      row._selected ? "hover:bg-gray-800/40" : "opacity-40"
                    }`}
                  >
                    {/* Checkbox — clicking anywhere except the input toggles row */}
                    <td className="px-3 py-1.5">
                      <input
                        type="checkbox"
                        checked={!!row._selected}
                        onChange={() => toggleRow(i)}
                        className="accent-indigo-500 cursor-pointer"
                      />
                    </td>
                    <td className="px-4 py-1.5 text-gray-400 whitespace-nowrap">{row.date}</td>
                    <td className="px-4 py-1.5 max-w-xs truncate text-gray-200">{row.description}</td>

                    {/* Editable category */}
                    <td className="px-4 py-1.5">
                      <input
                        type="text"
                        list="cat-suggestions"
                        value={row.category}
                        onChange={(e) => updateCategory(i, e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        onKeyDown={(e) => e.stopPropagation()}
                        className="w-full bg-gray-800 border border-gray-700 rounded-md px-2 py-1 text-xs text-indigo-300 focus:outline-none focus:border-indigo-500 focus:bg-gray-750 cursor-text"
                        spellCheck={false}
                      />
                    </td>

                    <td className={`px-4 py-1.5 font-medium whitespace-nowrap ${
                      row.type === "Credit" ? "text-emerald-400" : "text-white"
                    }`}>
                      {row.type === "Credit" ? "+" : ""}{fmt(row.amount)}
                    </td>
                    <td className="px-4 py-1.5 text-gray-500 text-xs">{row.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3 items-center">
            <button
              onClick={reset}
              className="px-5 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition disabled:opacity-50"
            >
              {loading ? "Importing…" : `Import ${rows.filter((r) => r._selected).length} transactions`}
            </button>
          </div>
        </div>
      )}

      {/* ── Done stage ───────────────────────────────────────────── */}
      {stage === "done" && (
        <div className="text-center py-16 space-y-4">
          <div className="text-5xl">✅</div>
          <p className="text-xl font-semibold">Import complete!</p>
          <p className="text-gray-400 text-sm">Transactions are now visible in the Transactions tab.</p>
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-sm font-medium transition"
          >
            Import another file
          </button>
        </div>
      )}
    </div>
  );
}
