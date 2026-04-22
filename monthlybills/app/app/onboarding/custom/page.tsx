"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import seedData from "@/data/seed-subscriptions.json";

type Period = "monthly" | "yearly";

type Category = {
  slug: string;
  label_ko: string;
  emoji: string;
  sort_order: number;
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

const categories = (seedData.categories as Category[])
  .slice()
  .sort((a, b) => a.sort_order - b.sort_order);

function formatKrw(amount: number) {
  return `₩${amount.toLocaleString("ko-KR")}`;
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

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function CustomPage() {
  const [items, setItems] = useState<Record<string, CustomSub>>({});
  const [editingId, setEditingId] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [categorySlug, setCategorySlug] = useState<string>(
    categories[0]?.slug ?? "etc"
  );
  const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState<Period>("monthly");
  const [paymentDay, setPaymentDay] = useState("");
  const [paymentMonth, setPaymentMonth] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem("onboarding.customSubscriptions");
    if (!raw) return;
    try {
      const list = JSON.parse(raw) as CustomSub[];
      const map: Record<string, CustomSub> = {};
      for (const x of list) map[x.id] = x;
      setItems(map);
    } catch {
      // ignore
    }
  }, []);

  function resetForm() {
    setName("");
    setCategorySlug(categories[0]?.slug ?? "etc");
    setAmount("");
    setPeriod("monthly");
    setPaymentDay("");
    setPaymentMonth("");
    setEditingId(null);
  }

  function buildItem(): CustomSub | null {
    if (!name.trim()) return null;
    const n = Number(amount);
    if (!Number.isFinite(n) || n <= 0) return null;

    let day: number | undefined;
    if (paymentDay.trim()) {
      const d = Number(paymentDay);
      if (!Number.isFinite(d) || d < 1 || d > 31) return null;
      day = d;
    }
    let month: number | undefined;
    if (period === "yearly" && paymentMonth.trim()) {
      const m = Number(paymentMonth);
      if (!Number.isFinite(m) || m < 1 || m > 12) return null;
      month = m;
    }

    return {
      id: editingId ?? newId(),
      name: name.trim(),
      category_slug: categorySlug,
      amount: n,
      period,
      payment_day: day,
      payment_month: month,
    };
  }

  const canSubmit = buildItem() !== null;

  function submitItem() {
    const item = buildItem();
    if (!item) return;
    setItems({ ...items, [item.id]: item });
    resetForm();
  }

  function startEdit(item: CustomSub) {
    setEditingId(item.id);
    setName(item.name);
    setCategorySlug(item.category_slug);
    setAmount(String(item.amount));
    setPeriod(item.period);
    setPaymentDay(item.payment_day ? String(item.payment_day) : "");
    setPaymentMonth(item.payment_month ? String(item.payment_month) : "");
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  function removeItem(id: string) {
    const next = { ...items };
    delete next[id];
    setItems(next);
    if (editingId === id) resetForm();
  }

  function persist() {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(
      "onboarding.customSubscriptions",
      JSON.stringify(Object.values(items))
    );
  }

  function handleNext() {
    persist();
    window.location.href = "/dashboard";
  }

  function handleSkip() {
    persist();
    window.location.href = "/dashboard";
  }

  const list = Object.values(items);
  const categoryBySlug = new Map(categories.map((c) => [c.slug, c]));

  return (
    <div className="min-h-screen bg-white pb-28">
      <header className="sticky top-0 z-10 border-b border-zinc-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-xl items-center justify-between px-5 py-4">
          <Link
            href="/onboarding/subscriptions"
            className="text-sm text-zinc-500 hover:text-zinc-800"
          >
            ← 뒤로
          </Link>
          <span className="text-sm font-medium text-zinc-800">직접 추가</span>
          <button
            onClick={handleSkip}
            className="text-sm text-zinc-400 hover:text-zinc-700"
          >
            건너뛰기
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-xl px-5 pt-6">
        <h1 className="mb-1 text-xl font-bold text-zinc-900">
          빠진 구독이 있나요?
        </h1>
        <p className="mb-6 text-sm text-zinc-500">
          카탈로그에 없는 서비스나 개인적인 구독·정기 결제를 직접 추가할 수
          있어요.
        </p>

        <div className="mb-6 rounded-2xl border border-zinc-200 bg-zinc-50 p-4">
          <div className="mb-3">
            <label className="mb-1 block text-xs text-zinc-500">
              서비스명 <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: 리멤버 커리어, 콴다 과외"
              className="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
            />
          </div>

          <div className="mb-3">
            <label className="mb-1 block text-xs text-zinc-500">카테고리</label>
            <select
              value={categorySlug}
              onChange={(e) => setCategorySlug(e.target.value)}
              className="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-zinc-400"
            >
              {categories.map((c) => (
                <option key={c.slug} value={c.slug}>
                  {c.emoji} {c.label_ko}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-3">
            <label className="mb-1 block text-xs text-zinc-500">
              금액 (원) <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              inputMode="numeric"
              value={amount}
              onChange={(e) =>
                setAmount(e.target.value.replace(/[^0-9]/g, ""))
              }
              placeholder="예: 9900"
              className="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm font-medium text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
            />
          </div>

          <div className="mb-3">
            <label className="mb-1 block text-xs text-zinc-500">결제 주기</label>
            <div className="flex gap-2">
              {(["monthly", "yearly"] as Period[]).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`flex-1 rounded-xl border px-3 py-2 text-sm transition ${
                    period === p
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-700"
                  }`}
                >
                  {p === "monthly" ? "월간" : "연간"}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-xs text-zinc-500">
              결제일
              <span className="ml-1 text-zinc-400">
                (선택, 나중에 수정 가능)
              </span>
            </label>
            {period === "monthly" ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-zinc-600">매월</span>
                <input
                  type="text"
                  inputMode="numeric"
                  value={paymentDay}
                  onChange={(e) =>
                    setPaymentDay(e.target.value.replace(/[^0-9]/g, ""))
                  }
                  placeholder="15"
                  maxLength={2}
                  className="w-16 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-center text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
                />
                <span className="text-sm text-zinc-600">일</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-zinc-600">매년</span>
                <input
                  type="text"
                  inputMode="numeric"
                  value={paymentMonth}
                  onChange={(e) =>
                    setPaymentMonth(e.target.value.replace(/[^0-9]/g, ""))
                  }
                  placeholder="1"
                  maxLength={2}
                  className="w-14 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-center text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
                />
                <span className="text-sm text-zinc-600">월</span>
                <input
                  type="text"
                  inputMode="numeric"
                  value={paymentDay}
                  onChange={(e) =>
                    setPaymentDay(e.target.value.replace(/[^0-9]/g, ""))
                  }
                  placeholder="15"
                  maxLength={2}
                  className="w-14 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-center text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
                />
                <span className="text-sm text-zinc-600">일</span>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            {editingId && (
              <button
                onClick={resetForm}
                className="flex-1 rounded-xl border border-zinc-200 bg-white py-3 text-sm text-zinc-700 hover:border-zinc-400"
              >
                취소
              </button>
            )}
            <button
              onClick={submitItem}
              disabled={!canSubmit}
              className="flex-1 rounded-xl bg-zinc-900 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {editingId ? "수정 저장" : "+ 추가"}
            </button>
          </div>
        </div>

        {list.length > 0 && (
          <section>
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
              추가한 항목 ({list.length})
            </h2>
            <ul className="space-y-2">
              {list.map((item) => {
                const cat = categoryBySlug.get(item.category_slug);
                return (
                  <li
                    key={item.id}
                    className="flex items-center justify-between rounded-2xl border border-zinc-100 bg-white px-4 py-3"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-zinc-900">
                        {cat?.emoji ?? ""} {item.name}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {cat?.label_ko ?? "기타"} ·{" "}
                        {formatPaymentSchedule(
                          item.period,
                          item.payment_day,
                          item.payment_month
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-zinc-900">
                        {formatKrw(item.amount)}
                      </span>
                      <button
                        onClick={() => startEdit(item)}
                        className="text-xs text-zinc-500 hover:text-zinc-800"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="text-xs text-zinc-400 hover:text-rose-600"
                        aria-label={`${item.name} 삭제`}
                      >
                        삭제
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {list.length === 0 && (
          <p className="py-4 text-center text-xs text-zinc-400">
            아직 직접 추가한 항목이 없어요. 건너뛰어도 괜찮아요.
          </p>
        )}
      </main>

      <footer className="fixed inset-x-0 bottom-0 border-t border-zinc-100 bg-white/95 backdrop-blur">
        <div className="mx-auto max-w-xl px-5 py-4">
          <button
            onClick={handleNext}
            className="w-full rounded-xl bg-zinc-900 py-4 text-sm font-semibold text-white transition hover:bg-zinc-800"
          >
            다음{list.length > 0 ? ` (${list.length})` : ""}
          </button>
        </div>
      </footer>
    </div>
  );
}
