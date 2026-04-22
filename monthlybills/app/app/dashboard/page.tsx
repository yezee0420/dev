"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import seedData from "@/data/seed-subscriptions.json";

type Period = "monthly" | "yearly";

type Category = {
  slug: string;
  label_ko: string;
  emoji: string;
  sort_order: number;
};

type SelectedSub = {
  slug: string;
  name_ko: string;
  plan_name: string;
  price: number;
  period: Period;
  payment_day?: number;
  payment_month?: number;
};

type FixedCost = {
  id: string;
  preset_slug: string;
  label: string;
  emoji: string;
  amount: number;
  period: Period;
  payment_day?: number;
  payment_month?: number;
  isCustom?: boolean;
};

type CustomSub = {
  id: string;
  name: string;
  category_slug: string;
  amount: number;
  period: Period;
  payment_day?: number;
  payment_month?: number;
};

const categories = seedData.categories as Category[];
const categoryBySlug = new Map(categories.map((c) => [c.slug, c]));

function formatKrw(amount: number) {
  return `₩${Math.round(amount).toLocaleString("ko-KR")}`;
}

function formatPaymentSchedule(
  period: Period,
  day?: number,
  month?: number
): string {
  if (!day) return "결제일 미설정";
  if (period === "yearly" && month) return `매년 ${month}월 ${day}일`;
  return `매월 ${day}일`;
}

function toMonthly(amount: number, period: Period) {
  return period === "yearly" ? amount / 12 : amount;
}

function toYearly(amount: number, period: Period) {
  return period === "yearly" ? amount : amount * 12;
}

function safeParse<T>(raw: string | null): T[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as T[]) : [];
  } catch {
    return [];
  }
}

export default function DashboardPage() {
  const [hydrated, setHydrated] = useState(false);
  const [subs, setSubs] = useState<SelectedSub[]>([]);
  const [fixed, setFixed] = useState<FixedCost[]>([]);
  const [customs, setCustoms] = useState<CustomSub[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setSubs(
      safeParse<SelectedSub>(
        window.localStorage.getItem("onboarding.subscriptions")
      )
    );
    setFixed(
      safeParse<FixedCost>(
        window.localStorage.getItem("onboarding.fixedCosts")
      )
    );
    setCustoms(
      safeParse<CustomSub>(
        window.localStorage.getItem("onboarding.customSubscriptions")
      )
    );
    setHydrated(true);
  }, []);

  const { monthlyTotal, yearlyTotal, totalItems } = useMemo(() => {
    let m = 0;
    let y = 0;
    for (const s of subs) {
      m += toMonthly(s.price, s.period);
      y += toYearly(s.price, s.period);
    }
    for (const f of fixed) {
      m += toMonthly(f.amount, f.period);
      y += toYearly(f.amount, f.period);
    }
    for (const c of customs) {
      m += toMonthly(c.amount, c.period);
      y += toYearly(c.amount, c.period);
    }
    return {
      monthlyTotal: m,
      yearlyTotal: y,
      totalItems: subs.length + fixed.length + customs.length,
    };
  }, [subs, fixed, customs]);

  function clearAll() {
    if (!window.confirm("입력한 모든 항목을 지우고 처음부터 시작할까요?"))
      return;
    window.localStorage.removeItem("onboarding.subscriptions");
    window.localStorage.removeItem("onboarding.fixedCosts");
    window.localStorage.removeItem("onboarding.customSubscriptions");
    window.location.href = "/onboarding/subscriptions";
  }

  return (
    <div className="min-h-screen bg-zinc-50 pb-24">
      <header className="sticky top-0 z-10 border-b border-zinc-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-xl items-center justify-between px-5 py-4">
          <span className="text-sm font-semibold text-zinc-900">
            monthlybills
            <span className="ml-1 text-xs font-normal text-zinc-400">
              (가제)
            </span>
          </span>
          <button
            onClick={clearAll}
            className="text-xs text-zinc-400 hover:text-rose-600"
          >
            초기화
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-xl px-5 pt-6">
        <section className="mb-6 rounded-3xl bg-zinc-900 p-6 text-white shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
            월 합계
          </p>
          <p className="mt-1 text-4xl font-bold tracking-tight">
            {hydrated ? formatKrw(monthlyTotal) : "₩…"}
          </p>
          <div className="mt-3 flex items-center justify-between text-sm text-zinc-300">
            <span>
              연 합계{" "}
              <span className="font-semibold text-white">
                {hydrated ? formatKrw(yearlyTotal) : "₩…"}
              </span>
            </span>
            <span className="text-xs text-zinc-400">{totalItems}개 항목</span>
          </div>
        </section>

        {hydrated && totalItems === 0 ? (
          <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-8 text-center">
            <p className="mb-2 text-sm text-zinc-600">
              아직 등록된 항목이 없어요.
            </p>
            <Link
              href="/onboarding/subscriptions"
              className="inline-flex items-center rounded-xl bg-zinc-900 px-5 py-2 text-sm font-semibold text-white hover:bg-zinc-800"
            >
              첫 항목 추가하기
            </Link>
          </div>
        ) : (
          <>
            {subs.length > 0 && (
              <Section title={`구독 (${subs.length})`}>
                {subs.map((s) => (
                  <ItemRow
                    key={`sub-${s.slug}`}
                    title={s.name_ko}
                    subtitle={`${s.plan_name} · ${formatPaymentSchedule(
                      s.period,
                      s.payment_day,
                      s.payment_month
                    )}`}
                    amount={s.price}
                    period={s.period}
                  />
                ))}
              </Section>
            )}

            {fixed.length > 0 && (
              <Section title={`고정비 (${fixed.length})`}>
                {fixed.map((f) => (
                  <ItemRow
                    key={`fc-${f.id}`}
                    title={`${f.emoji} ${f.label}`}
                    subtitle={formatPaymentSchedule(
                      f.period,
                      f.payment_day,
                      f.payment_month
                    )}
                    amount={f.amount}
                    period={f.period}
                  />
                ))}
              </Section>
            )}

            {customs.length > 0 && (
              <Section title={`직접 추가 (${customs.length})`}>
                {customs.map((c) => {
                  const cat = categoryBySlug.get(c.category_slug);
                  return (
                    <ItemRow
                      key={`cs-${c.id}`}
                      title={`${cat?.emoji ?? ""} ${c.name}`.trim()}
                      subtitle={`${
                        cat?.label_ko ?? "기타"
                      } · ${formatPaymentSchedule(
                        c.period,
                        c.payment_day,
                        c.payment_month
                      )}`}
                      amount={c.amount}
                      period={c.period}
                    />
                  );
                })}
              </Section>
            )}
          </>
        )}
      </main>

      <div className="fixed inset-x-0 bottom-5 z-10 mx-auto flex max-w-xl justify-end px-5">
        <Link
          href="/onboarding/subscriptions"
          aria-label="추가"
          className="flex h-14 w-14 items-center justify-center rounded-full bg-zinc-900 text-2xl font-light text-white shadow-lg transition hover:bg-zinc-800"
        >
          +
        </Link>
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-6">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
        {title}
      </h2>
      <ul className="space-y-2">{children}</ul>
    </section>
  );
}

function ItemRow({
  title,
  subtitle,
  amount,
  period,
}: {
  title: string;
  subtitle: string;
  amount: number;
  period: Period;
}) {
  return (
    <li className="flex items-center justify-between rounded-2xl border border-zinc-100 bg-white px-4 py-3">
      <div className="min-w-0">
        <p className="text-sm font-medium text-zinc-900">{title}</p>
        <p className="truncate text-xs text-zinc-500">{subtitle}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-zinc-900">
          {formatKrw(amount)}
        </p>
        <p className="text-xs text-zinc-400">
          {period === "monthly" ? "/월" : "/년"}
        </p>
      </div>
    </li>
  );
}
