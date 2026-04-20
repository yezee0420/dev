"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import seedData from "@/data/seed-subscriptions.json";

type Period = "monthly" | "yearly";

type Plan = {
  name: string;
  price: number;
};

type Subscription = {
  slug: string;
  name_ko: string;
  name_en: string;
  category: string;
  default_price_krw: number;
  default_period: Period;
  is_popular?: boolean;
  plans: Plan[];
};

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
};

type FixedCost = {
  slug: string;
  label: string;
  emoji: string;
  amount: number;
  period: Period;
  isCustom?: boolean;
};

const categories = seedData.categories as Category[];
const subscriptions = seedData.subscriptions as Subscription[];

const onboardingCategorySlugs = new Set([
  "delivery_shopping",
  "ott",
  "music",
  "reading",
  "edu_productivity",
  "cloud",
]);

const visibleCategories = categories
  .filter((c) => onboardingCategorySlugs.has(c.slug))
  .sort((a, b) => a.sort_order - b.sort_order);

const popularServices = subscriptions.filter((s) => s.is_popular);

const fixedCostPresets: Array<Omit<FixedCost, "amount" | "period">> = [
  { slug: "rent", label: "월세", emoji: "🏠" },
  { slug: "maintenance", label: "관리비", emoji: "🏢" },
  { slug: "loan_interest", label: "대출 이자", emoji: "💳" },
  { slug: "telecom", label: "통신비", emoji: "📞" },
  { slug: "internet", label: "인터넷", emoji: "🌐" },
  { slug: "card_fee", label: "카드 연회비", emoji: "💳" },
];

function formatKrw(amount: number) {
  return `₩${amount.toLocaleString("ko-KR")}`;
}

export default function SubscriptionsPage() {
  const [selected, setSelected] = useState<Record<string, SelectedSub>>({});
  const [fixedCosts, setFixedCosts] = useState<Record<string, FixedCost>>({});
  const [expandedFixed, setExpandedFixed] = useState<string | null>(null);
  const [customName, setCustomName] = useState("");
  const [query, setQuery] = useState("");
  const [openCategory, setOpenCategory] = useState<string | null>(
    visibleCategories[0]?.slug ?? null
  );
  const [tab, setTab] = useState<"browse" | "mine">("browse");
  const [modalSub, setModalSub] = useState<Subscription | null>(null);

  const subCount = Object.keys(selected).length;
  const fixedCount = Object.keys(fixedCosts).length;
  const totalCount = subCount + fixedCount;

  const filteredBySearch = useMemo(() => {
    if (!query.trim()) return null;
    const q = query.trim().toLowerCase();
    return subscriptions.filter(
      (s) =>
        s.name_ko.toLowerCase().includes(q) ||
        s.name_en.toLowerCase().includes(q)
    );
  }, [query]);

  function toggleSubscription(sub: Subscription) {
    if (selected[sub.slug]) {
      const next = { ...selected };
      delete next[sub.slug];
      setSelected(next);
      return;
    }
    if (sub.plans.length > 1) {
      setModalSub(sub);
      return;
    }
    const plan = sub.plans[0];
    setSelected({
      ...selected,
      [sub.slug]: {
        slug: sub.slug,
        name_ko: sub.name_ko,
        plan_name: plan.name,
        price: plan.price,
        period: sub.default_period,
      },
    });
  }

  function confirmPlan(sub: Subscription, plan: Plan) {
    setSelected({
      ...selected,
      [sub.slug]: {
        slug: sub.slug,
        name_ko: sub.name_ko,
        plan_name: plan.name,
        price: plan.price,
        period: sub.default_period,
      },
    });
    setModalSub(null);
  }

  function upsertFixedCost(partial: FixedCost) {
    setFixedCosts({ ...fixedCosts, [partial.slug]: partial });
  }

  function removeFixedCost(slug: string) {
    const next = { ...fixedCosts };
    delete next[slug];
    setFixedCosts(next);
    if (expandedFixed === slug) setExpandedFixed(null);
  }

  function addCustomFixedCost() {
    const name = customName.trim();
    if (!name) return;
    const slug = `custom_${Date.now()}`;
    upsertFixedCost({
      slug,
      label: name,
      emoji: "📌",
      amount: 0,
      period: "monthly",
      isCustom: true,
    });
    setExpandedFixed(slug);
    setCustomName("");
  }

  function handleNext() {
    if (totalCount === 0) {
      const ok = window.confirm(
        "선택한 항목이 없어요. 그래도 진행할까요?"
      );
      if (!ok) return;
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        "onboarding.subscriptions",
        JSON.stringify(Object.values(selected))
      );
      window.localStorage.setItem(
        "onboarding.fixedCosts",
        JSON.stringify(Object.values(fixedCosts))
      );
    }
    window.location.href = "/onboarding/custom";
  }

  return (
    <div className="min-h-screen bg-white pb-28">
      <header className="sticky top-0 z-10 border-b border-zinc-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-xl items-center justify-between px-5 py-4">
          <Link
            href="/login"
            className="text-sm text-zinc-500 hover:text-zinc-800"
            aria-label="이전 화면으로"
          >
            ← 뒤로
          </Link>
          <span className="text-sm font-medium text-zinc-800">
            구독 · 고정비 입력
          </span>
          <Link
            href="/onboarding/custom"
            className="text-sm text-zinc-400 hover:text-zinc-700"
          >
            건너뛰기
          </Link>
        </div>
        <nav className="mx-auto flex max-w-xl px-5">
          <button
            onClick={() => setTab("browse")}
            className={`flex-1 py-3 text-sm font-medium transition ${
              tab === "browse"
                ? "border-b-2 border-zinc-900 text-zinc-900"
                : "border-b-2 border-transparent text-zinc-400"
            }`}
          >
            둘러보기
          </button>
          <button
            onClick={() => setTab("mine")}
            className={`flex-1 py-3 text-sm font-medium transition ${
              tab === "mine"
                ? "border-b-2 border-zinc-900 text-zinc-900"
                : "border-b-2 border-transparent text-zinc-400"
            }`}
          >
            내 항목 ({totalCount})
          </button>
        </nav>
      </header>

      <main className="mx-auto max-w-xl px-5 pt-5">
        {tab === "browse" ? (
          <>
            <div className="mb-5">
              <input
                type="search"
                placeholder="서비스명으로 검색"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm outline-none transition placeholder:text-zinc-400 focus:border-zinc-400 focus:bg-white"
              />
            </div>

            {filteredBySearch ? (
              <section>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  검색 결과 ({filteredBySearch.length})
                </h2>
                {filteredBySearch.length === 0 ? (
                  <p className="py-8 text-center text-sm text-zinc-400">
                    일치하는 서비스가 없어요. 다음 단계에서 직접 추가할 수
                    있어요.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {filteredBySearch.map((sub) => (
                      <SubscriptionCard
                        key={sub.slug}
                        sub={sub}
                        isSelected={Boolean(selected[sub.slug])}
                        selectedPlanName={selected[sub.slug]?.plan_name}
                        onClick={() => toggleSubscription(sub)}
                      />
                    ))}
                  </ul>
                )}
              </section>
            ) : (
              <>
                <section className="mb-8">
                  <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    인기 서비스
                  </h2>
                  <div className="-mx-5 overflow-x-auto px-5">
                    <div className="flex gap-2">
                      {popularServices.map((sub) => {
                        const isSel = Boolean(selected[sub.slug]);
                        return (
                          <button
                            key={sub.slug}
                            onClick={() => toggleSubscription(sub)}
                            className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition ${
                              isSel
                                ? "border-zinc-900 bg-zinc-900 text-white"
                                : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400"
                            }`}
                          >
                            {isSel ? "✓ " : ""}
                            {sub.name_ko}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </section>

                <section className="mb-8">
                  <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    카테고리
                  </h2>
                  <div className="space-y-2">
                    {visibleCategories.map((cat) => {
                      const catSubs = subscriptions.filter(
                        (s) => s.category === cat.slug
                      );
                      if (catSubs.length === 0) return null;
                      const isOpen = openCategory === cat.slug;
                      const catSelectedCount = catSubs.filter(
                        (s) => selected[s.slug]
                      ).length;

                      return (
                        <div
                          key={cat.slug}
                          className="overflow-hidden rounded-2xl border border-zinc-100"
                        >
                          <button
                            onClick={() =>
                              setOpenCategory(isOpen ? null : cat.slug)
                            }
                            className="flex w-full items-center justify-between bg-zinc-50 px-4 py-4 text-left transition hover:bg-zinc-100"
                            aria-expanded={isOpen}
                          >
                            <span className="flex items-center gap-2 text-sm font-medium text-zinc-800">
                              <span aria-hidden>{cat.emoji}</span>
                              {cat.label_ko}
                              {catSelectedCount > 0 && (
                                <span className="rounded-full bg-zinc-900 px-2 py-0.5 text-xs font-semibold text-white">
                                  {catSelectedCount}
                                </span>
                              )}
                            </span>
                            <span
                              className={`text-xs text-zinc-400 transition ${
                                isOpen ? "rotate-180" : ""
                              }`}
                            >
                              ▾
                            </span>
                          </button>
                          {isOpen && (
                            <ul className="space-y-2 bg-white p-3">
                              {catSubs.map((sub) => (
                                <SubscriptionCard
                                  key={sub.slug}
                                  sub={sub}
                                  isSelected={Boolean(selected[sub.slug])}
                                  selectedPlanName={
                                    selected[sub.slug]?.plan_name
                                  }
                                  onClick={() => toggleSubscription(sub)}
                                />
                              ))}
                            </ul>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>

                <section className="mb-4">
                  <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                    고정비
                  </h2>
                  <p className="mb-4 text-sm text-zinc-500">
                    그 외 매달 나가는 돈, 같이 넣어두면 총액이 더 정확해져요.
                  </p>

                  <div className="mb-3 flex flex-wrap gap-2">
                    {fixedCostPresets.map((preset) => {
                      const existing = fixedCosts[preset.slug];
                      const isSelected = Boolean(existing);
                      const isExpanded = expandedFixed === preset.slug;
                      return (
                        <button
                          key={preset.slug}
                          onClick={() =>
                            setExpandedFixed(
                              isExpanded ? null : preset.slug
                            )
                          }
                          className={`rounded-full border px-3 py-2 text-sm font-medium transition ${
                            isSelected
                              ? "border-zinc-900 bg-zinc-900 text-white"
                              : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-400"
                          }`}
                        >
                          <span aria-hidden className="mr-1">
                            {preset.emoji}
                          </span>
                          {preset.label}
                          {existing && existing.amount > 0 && (
                            <span className="ml-1 text-xs opacity-80">
                              {formatKrw(existing.amount)}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {expandedFixed &&
                    fixedCostPresets.some((p) => p.slug === expandedFixed) && (
                      <FixedCostForm
                        preset={
                          fixedCostPresets.find(
                            (p) => p.slug === expandedFixed
                          )!
                        }
                        existing={fixedCosts[expandedFixed]}
                        onSave={(fc) => {
                          upsertFixedCost(fc);
                          setExpandedFixed(null);
                        }}
                        onRemove={() => removeFixedCost(expandedFixed)}
                        onCancel={() => setExpandedFixed(null)}
                      />
                    )}

                  <div className="mt-3 rounded-2xl border border-dashed border-zinc-200 bg-zinc-50 p-4">
                    <label className="mb-2 block text-xs font-medium text-zinc-600">
                      ➕ 기타 — 이름을 입력하고 추가
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={customName}
                        onChange={(e) => setCustomName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") addCustomFixedCost();
                        }}
                        placeholder="예: 헬스장, 자동차 할부"
                        className="flex-1 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
                      />
                      <button
                        onClick={addCustomFixedCost}
                        disabled={!customName.trim()}
                        className="rounded-xl bg-zinc-900 px-4 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        추가
                      </button>
                    </div>
                  </div>

                  {Object.values(fixedCosts).filter((fc) => fc.isCustom).length >
                    0 && (
                    <ul className="mt-3 space-y-2">
                      {Object.values(fixedCosts)
                        .filter((fc) => fc.isCustom)
                        .map((fc) => (
                          <li key={fc.slug}>
                            {expandedFixed === fc.slug ? (
                              <FixedCostForm
                                preset={{
                                  slug: fc.slug,
                                  label: fc.label,
                                  emoji: fc.emoji,
                                }}
                                existing={fc}
                                onSave={(updated) => {
                                  upsertFixedCost({
                                    ...updated,
                                    isCustom: true,
                                  });
                                  setExpandedFixed(null);
                                }}
                                onRemove={() => removeFixedCost(fc.slug)}
                                onCancel={() => setExpandedFixed(null)}
                              />
                            ) : (
                              <button
                                onClick={() => setExpandedFixed(fc.slug)}
                                className="flex w-full items-center justify-between rounded-xl border border-zinc-100 bg-white px-4 py-3 text-left transition hover:border-zinc-300"
                              >
                                <span className="text-sm font-medium text-zinc-900">
                                  {fc.emoji} {fc.label}
                                </span>
                                <span className="text-sm text-zinc-700">
                                  {fc.amount > 0
                                    ? `${formatKrw(fc.amount)} / ${
                                        fc.period === "monthly" ? "월" : "년"
                                      }`
                                    : "금액 입력"}
                                </span>
                              </button>
                            )}
                          </li>
                        ))}
                    </ul>
                  )}
                </section>
              </>
            )}
          </>
        ) : (
          <section className="space-y-6">
            {subCount > 0 && (
              <div>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  구독 ({subCount})
                </h2>
                <ul className="space-y-2">
                  {Object.values(selected).map((item) => (
                    <li
                      key={item.slug}
                      className="flex items-center justify-between rounded-2xl border border-zinc-100 bg-white px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-zinc-900">
                          {item.name_ko}
                        </p>
                        <p className="text-xs text-zinc-500">
                          {item.plan_name} ·{" "}
                          {item.period === "monthly" ? "월간" : "연간"}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-zinc-900">
                          {formatKrw(item.price)}
                        </span>
                        <button
                          onClick={() => {
                            const next = { ...selected };
                            delete next[item.slug];
                            setSelected(next);
                          }}
                          className="text-xs text-zinc-400 hover:text-zinc-700"
                          aria-label={`${item.name_ko} 삭제`}
                        >
                          삭제
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {fixedCount > 0 && (
              <div>
                <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  고정비 ({fixedCount})
                </h2>
                <ul className="space-y-2">
                  {Object.values(fixedCosts).map((fc) => (
                    <li
                      key={fc.slug}
                      className="flex items-center justify-between rounded-2xl border border-zinc-100 bg-white px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-zinc-900">
                          {fc.emoji} {fc.label}
                        </p>
                        <p className="text-xs text-zinc-500">
                          {fc.period === "monthly" ? "월간" : "연간"}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-zinc-900">
                          {fc.amount > 0 ? formatKrw(fc.amount) : "미입력"}
                        </span>
                        <button
                          onClick={() => removeFixedCost(fc.slug)}
                          className="text-xs text-zinc-400 hover:text-zinc-700"
                          aria-label={`${fc.label} 삭제`}
                        >
                          삭제
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {totalCount === 0 && (
              <p className="py-16 text-center text-sm text-zinc-400">
                아직 선택한 항목이 없어요.
                <br />
                둘러보기 탭에서 구독·고정비를 입력해보세요.
              </p>
            )}
          </section>
        )}
      </main>

      <footer className="fixed inset-x-0 bottom-0 border-t border-zinc-100 bg-white/95 backdrop-blur">
        <div className="mx-auto max-w-xl px-5 py-4">
          <button
            onClick={handleNext}
            className="w-full rounded-xl bg-zinc-900 py-4 text-sm font-semibold text-white transition hover:bg-zinc-800"
          >
            다음{totalCount > 0 ? ` (${totalCount})` : ""}
          </button>
        </div>
      </footer>

      {modalSub && (
        <PlanModal
          sub={modalSub}
          onClose={() => setModalSub(null)}
          onConfirm={(plan) => confirmPlan(modalSub, plan)}
        />
      )}
    </div>
  );
}

function SubscriptionCard({
  sub,
  isSelected,
  selectedPlanName,
  onClick,
}: {
  sub: Subscription;
  isSelected: boolean;
  selectedPlanName?: string;
  onClick: () => void;
}) {
  return (
    <li>
      <button
        onClick={onClick}
        className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left transition ${
          isSelected
            ? "border-zinc-900 bg-zinc-50"
            : "border-zinc-100 bg-white hover:border-zinc-300"
        }`}
      >
        <div>
          <p className="text-sm font-medium text-zinc-900">{sub.name_ko}</p>
          <p className="mt-0.5 text-xs text-zinc-500">
            {isSelected && selectedPlanName
              ? selectedPlanName
              : `${formatKrw(sub.default_price_krw)} ${
                  sub.default_period === "monthly" ? "/월" : "/년"
                }`}
          </p>
        </div>
        <span
          className={`flex h-6 w-6 items-center justify-center rounded-full border text-xs ${
            isSelected
              ? "border-zinc-900 bg-zinc-900 text-white"
              : "border-zinc-300 bg-white text-transparent"
          }`}
          aria-hidden
        >
          ✓
        </span>
      </button>
    </li>
  );
}

function FixedCostForm({
  preset,
  existing,
  onSave,
  onRemove,
  onCancel,
}: {
  preset: { slug: string; label: string; emoji: string };
  existing?: FixedCost;
  onSave: (fc: FixedCost) => void;
  onRemove: () => void;
  onCancel: () => void;
}) {
  const [amount, setAmount] = useState<string>(
    existing && existing.amount > 0 ? String(existing.amount) : ""
  );
  const [period, setPeriod] = useState<Period>(existing?.period ?? "monthly");

  function handleSave() {
    const num = Number(amount.replace(/[^0-9]/g, ""));
    if (!Number.isFinite(num) || num <= 0) return;
    onSave({
      slug: preset.slug,
      label: preset.label,
      emoji: preset.emoji,
      amount: num,
      period,
    });
  }

  return (
    <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-medium text-zinc-900">
          {preset.emoji} {preset.label}
        </span>
        {existing && (
          <button
            onClick={onRemove}
            className="text-xs text-zinc-400 hover:text-rose-600"
          >
            삭제
          </button>
        )}
      </div>
      <div className="mb-3">
        <label className="mb-1 block text-xs text-zinc-500">금액 (원)</label>
        <input
          type="text"
          inputMode="numeric"
          value={amount}
          onChange={(e) =>
            setAmount(e.target.value.replace(/[^0-9]/g, ""))
          }
          placeholder="예: 600000"
          className="w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm outline-none transition placeholder:text-zinc-400 focus:border-zinc-400"
          autoFocus
        />
      </div>
      <div className="mb-4">
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
      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className="flex-1 rounded-xl border border-zinc-200 bg-white py-2 text-sm text-zinc-700 hover:border-zinc-400"
        >
          취소
        </button>
        <button
          onClick={handleSave}
          disabled={!amount || Number(amount) <= 0}
          className="flex-1 rounded-xl bg-zinc-900 py-2 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          저장
        </button>
      </div>
    </div>
  );
}

function PlanModal({
  sub,
  onClose,
  onConfirm,
}: {
  sub: Subscription;
  onClose: () => void;
  onConfirm: (plan: Plan) => void;
}) {
  return (
    <div
      className="fixed inset-0 z-20 flex items-end justify-center bg-black/40 sm:items-center"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-t-2xl bg-white p-6 sm:rounded-2xl"
      >
        <h3 className="mb-1 text-base font-semibold text-zinc-900">
          {sub.name_ko}
        </h3>
        <p className="mb-5 text-xs text-zinc-500">요금제를 선택해주세요</p>
        <ul className="space-y-2">
          {sub.plans.map((plan) => (
            <li key={plan.name}>
              <button
                onClick={() => onConfirm(plan)}
                className="flex w-full items-center justify-between rounded-xl border border-zinc-200 px-4 py-3 text-left transition hover:border-zinc-900 hover:bg-zinc-50"
              >
                <span className="text-sm font-medium text-zinc-900">
                  {plan.name}
                </span>
                <span className="text-sm font-semibold text-zinc-900">
                  {formatKrw(plan.price)}
                </span>
              </button>
            </li>
          ))}
        </ul>
        <button
          onClick={onClose}
          className="mt-4 w-full py-3 text-sm text-zinc-500 hover:text-zinc-800"
        >
          취소
        </button>
      </div>
    </div>
  );
}
