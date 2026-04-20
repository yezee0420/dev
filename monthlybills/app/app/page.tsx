import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col bg-zinc-50 font-sans">
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-16 text-center">
        <div className="mb-4 text-xs font-semibold text-sky-600 tracking-wider uppercase">
          monthlybills (가제)
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-zinc-900 leading-tight mb-4 max-w-md">
          내 구독과 고정비,
          <br />한 화면에.
        </h1>
        <p className="text-base text-zinc-600 mb-10 max-w-sm leading-relaxed">
          넷플릭스부터 월세·통신비까지.
          <br />
          매달 내가 얼마 쓰는지 60초 안에 확인해요.
        </p>

        <div className="w-full max-w-xs flex flex-col gap-3">
          <Link
            href="/login"
            className="w-full h-14 flex items-center justify-center rounded-2xl bg-zinc-900 text-white font-semibold text-base shadow-sm hover:bg-zinc-800 transition-colors"
          >
            내 월 고정비 계산하기
          </Link>
          <Link
            href="/onboarding/subscriptions"
            className="w-full h-12 flex items-center justify-center text-sm text-zinc-500 hover:text-zinc-800 transition-colors"
          >
            로그인 없이 둘러보기
          </Link>
        </div>
      </section>

      <footer className="border-t border-zinc-200 px-6 py-6 text-center text-xs text-zinc-400">
        © 2026 monthlybills
      </footer>
    </main>
  );
}
