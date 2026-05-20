"use client";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const loginGoogle = () =>
    supabase.auth.signInWithOAuth({ provider: "google",
      options: { redirectTo: window.location.origin } });

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white gap-6">
      <div className="text-4xl">💰</div>
      <h1 className="text-3xl font-bold">Expense Tracker</h1>
      <p className="text-gray-400 text-sm">Smart personal finance for India</p>
      <button
        onClick={loginGoogle}
        className="flex items-center gap-3 px-6 py-3 bg-white text-gray-900 rounded-xl font-medium hover:bg-gray-100 transition"
      >
        <img src="https://www.google.com/favicon.ico" className="w-5 h-5" alt="" />
        Continue with Google
      </button>
      <p className="text-gray-600 text-xs mt-4">Your data is private and encrypted.</p>
    </div>
  );
}
