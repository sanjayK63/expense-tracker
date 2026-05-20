import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "Expense Tracker",
  description: "Smart personal finance for India",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster position="top-right" toastOptions={{ style: { background: "#1f2937", color: "#f9fafb", border: "1px solid #374151" } }} />
      </body>
    </html>
  );
}
