<<<<<<< HEAD
import Image from "next/image";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            To get started, edit the page.tsx file.
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Looking for a starting point or more instructions? Head over to{" "}
            <a
              href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
              className="font-medium text-zinc-950 dark:text-zinc-50"
            >
              Templates
            </a>{" "}
            or the{" "}
            <a
              href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
              className="font-medium text-zinc-950 dark:text-zinc-50"
            >
              Learning
            </a>{" "}
            center.
          </p>
        </div>
        <div className="flex flex-col gap-4 text-base font-medium sm:flex-row">
          <a
            className="flex h-12 w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 text-background transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc] md:w-[158px]"
            href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Image
              className="dark:invert"
              src="/vercel.svg"
              alt="Vercel logomark"
              width={16}
              height={16}
            />
            Deploy Now
          </a>
          <a
            className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-5 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] md:w-[158px]"
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            Documentation
          </a>
        </div>
      </main>
    </div>
=======
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
        <p className="text-base text-zinc-600 mb-10 max-w-sm">
          넷플릭스부터 월세·통신비까지. 매달 내가 얼마 쓰는지 60초 안에 확인해요.
        </p>

        <div className="w-full max-w-xs flex flex-col gap-3">
          <Link
            href="/login"
            className="w-full h-14 flex items-center justify-center rounded-2xl bg-zinc-900 text-white font-semibold text-base shadow-sm hover:bg-zinc-800 transition-colors"
          >
            내 월 고정비 계산하기
          </Link>
          <button
            type="button"
            disabled
            className="w-full h-12 flex items-center justify-center text-sm text-zinc-400 cursor-not-allowed"
          >
            로그인 없이 둘러보기 (준비 중)
          </button>
        </div>
      </section>

      <footer className="border-t border-zinc-200 px-6 py-6 text-center text-xs text-zinc-400">
        © 2026 monthlybills
      </footer>
    </main>
>>>>>>> b8d83c31 (Add 프로젝트 한 줄 and 라우팅 — 상황별 읽을 md and 새 규칙·결정이 생겼을 때)
  );
}
