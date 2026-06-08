"use client";

import Link from "next/link";
import { useState } from "react";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signInWithKakao() {
    setLoading(true);
    setError(null);
    const supabase = createSupabaseBrowserClient();
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "kakao",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) {
      setError(error.message);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col bg-zinc-50 font-sans">
      <header className="px-4 py-3">
        <Link
          href="/"
          className="inline-flex items-center text-sm text-zinc-500 hover:text-zinc-700"
          aria-label="뒤로"
        >
          ← 뒤로
        </Link>
      </header>

      <section className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <h1 className="text-2xl font-bold text-zinc-900 mb-2 text-center">
          간편하게 시작해보세요
        </h1>
        <p className="text-sm text-zinc-500 mb-10 text-center max-w-xs">
          소셜 로그인으로 3초 안에 가입할 수 있어요.
        </p>

        <div className="w-full max-w-xs flex flex-col gap-3">
          <button
            type="button"
            onClick={signInWithKakao}
            disabled={loading}
            className="w-full h-14 flex items-center justify-center rounded-2xl bg-[#FEE500] text-[#191919] font-semibold text-base transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "연결 중..." : "카카오로 시작하기"}
          </button>
          <button
            type="button"
            disabled
            className="w-full h-14 flex items-center justify-center rounded-2xl bg-[#03C75A] text-white font-semibold text-base cursor-not-allowed opacity-60"
          >
            네이버로 시작하기 (준비 중)
          </button>
          {error && (
            <p className="text-xs text-rose-600 text-center mt-2">
              로그인 실패: {error}
            </p>
          )}
          <p className="text-xs text-zinc-400 text-center mt-4">
            카카오 계정으로 간편 로그인. 네이버는 Phase 1 후반 지원 예정.
          </p>
        </div>
      </section>
    </main>
  );
}
