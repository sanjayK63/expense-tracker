import axios from "axios";
import { supabase } from "./supabase";

const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL });

// Attach Supabase JWT to every request automatically
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;

// ── Typed API helpers ─────────────────────────────────────────────────────────

export type Expense = {
  id: string;
  date: string;
  amount: number;
  category: string;
  description: string;
  payment_method: string;
  source: string;
  type: "Debit" | "Credit";
};

export type Budget = {
  category: string;
  monthly_limit: number;
};

export const expensesApi = {
  list: (params?: { month?: number; year?: number; category?: string; source?: string }) =>
    api.get<Expense[]>("/expenses", { params }),

  create: (data: Omit<Expense, "id">) =>
    api.post<Expense>("/expenses", data),

  update: (id: string, data: Partial<Expense>) =>
    api.patch<Expense>(`/expenses/${id}`, data),

  delete: (id: string) =>
    api.delete(`/expenses/${id}`),

  deleteBySource: (source: string) =>
    api.delete(`/expenses/batch/by-source`, { params: { source } }),
};

export const budgetsApi = {
  list: () => api.get<Budget[]>("/budgets"),
  upsert: (budgets: Budget[]) => api.put<Budget[]>("/budgets", budgets),
};

export const importApi = {
  uploadPdf: (file: File, accountName: string, password = "") => {
    const form = new FormData();
    form.append("file", file);
    form.append("account_name", accountName);
    form.append("password", password);
    return api.post("/import/pdf", form);
  },
  confirmPdf: (rows: Expense[]) =>
    api.post("/import/pdf/confirm", { rows }),

  uploadSheet: (file: File, accountName: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("account_name", accountName);
    return api.post("/import/csv", form);
  },
  confirmSheet: (rows: Expense[]) =>
    api.post("/import/csv/confirm", { rows }),
};

export const reportsApi = {
  monthlySummary: (year: number, month: number) =>
    api.get("/reports/monthly-summary", { params: { year, month } }),
  yearOverYear: () => api.get("/reports/year-over-year"),
  recurring: () => api.get("/reports/recurring"),
  exportExcel: (year: number, month: number) =>
    api.get("/reports/export/excel", { params: { year, month }, responseType: "blob" }),
};
