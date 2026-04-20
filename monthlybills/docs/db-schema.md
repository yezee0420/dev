# DB Schema (Phase 1)

> Postgres via Supabase. Auth 테이블은 Supabase가 관리(`auth.users`), 도메인 테이블은 `public` 스키마에.

## ERD 요약

```
auth.users (Supabase 관리)
   │
   └──< profiles (1:1) ─── display_name, notification_prefs
          │
          ├──< user_subscriptions (N:1 ─> subscription_catalog, nullable)
          │
          └──< user_fixed_costs
```

- `subscription_catalog`: 넷플릭스·유튜브 프리미엄 같은 공통 서비스 마스터
- `user_subscriptions`: 사용자가 선택한 구독 (카탈로그 기반이거나 직접 입력)
- `user_fixed_costs`: 카탈로그 없이 자유 입력 (월세, 관리비, 대출이자 등)
- `categories`: 카탈로그·사용자 항목 공통 카테고리

## 테이블

### `categories`

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | smallint PK | |
| slug | text unique | `ott`, `music`, `delivery_shopping`, `reading`, `edu_productivity`, `cloud`, `telecom`, `housing`, `insurance`, `loan`, `card_fee`, `etc` |
| label_ko | text | "OTT", "음악", ... |
| emoji | text | UI 아이콘 |
| sort_order | smallint | |

### `subscription_catalog`

공통 서비스 마스터. 시드 JSON에서 초기 적재.

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | uuid PK | |
| slug | text unique | `netflix`, `youtube_premium`, ... |
| name_ko | text | "넷플릭스" |
| name_en | text nullable | |
| category_id | smallint FK→categories | |
| default_price_krw | int | 대표 요금 (기본 플랜) |
| default_period | text | `monthly` / `yearly` |
| plans | jsonb | `[{name:"베이직", price:9500}, ...]` |
| icon_url | text nullable | |
| homepage_url | text nullable | |
| is_popular | boolean default false | 상단 "인기 서비스" 노출 |
| created_at | timestamptz default now() | |

### `profiles`

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | uuid PK, FK→auth.users | Supabase Auth 연동 |
| display_name | text | |
| avatar_url | text nullable | |
| provider | text | `kakao`, `naver`, `email` |
| notification_prefs | jsonb | `{channels:["push","email"], lead_days:[3,1]}` |
| onboarding_completed | boolean default false | |
| created_at | timestamptz default now() | |

### `user_subscriptions`

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK→profiles | |
| catalog_id | uuid FK→subscription_catalog nullable | null이면 사용자 직접 입력 |
| custom_name | text nullable | catalog_id가 null일 때 사용 |
| category_id | smallint FK→categories | |
| plan_label | text nullable | "프리미엄", "가족 요금제" 등 |
| price_krw | int | 실제 사용자가 지불하는 금액 |
| billing_period | text | `monthly` / `yearly` |
| billing_day | smallint nullable | 1~31 (monthly일 때), yearly면 `billing_date` 별도 |
| billing_date | date nullable | yearly용 |
| started_at | date nullable | |
| memo | text nullable | |
| is_active | boolean default true | 해지 시 false |
| created_at | timestamptz default now() | |
| updated_at | timestamptz default now() | |

### `user_fixed_costs`

구독이 아닌 월 고정비. 카탈로그 없이 자유 입력.

| 컬럼 | 타입 | 비고 |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK→profiles | |
| name | text | "전세자금대출 이자", "월세", "KT 인터넷" |
| category_id | smallint FK→categories | `housing`/`telecom`/`loan`/`card_fee`/`etc` |
| price_krw | int | |
| billing_period | text | `monthly`/`yearly`/`quarterly` |
| billing_day | smallint nullable | |
| billing_date | date nullable | |
| memo | text nullable | |
| is_active | boolean default true | |
| created_at | timestamptz default now() | |
| updated_at | timestamptz default now() | |

## RLS 정책 (중요)

Supabase는 기본으로 public 스키마에도 접근 가능 — **반드시 RLS 활성화**.

- `profiles`: `user_id = auth.uid()`
- `user_subscriptions`: `user_id = auth.uid()`
- `user_fixed_costs`: `user_id = auth.uid()`
- `subscription_catalog`, `categories`: SELECT 전체 허용, INSERT/UPDATE는 service role만

## 파생 뷰 (Phase 2에서 추가)

- `v_user_monthly_total`: 사용자별 월 환산 합계
  - yearly → /12, quarterly → /3
- `v_upcoming_payments`: 다가오는 14일 내 결제 예정 항목 (알림 쿼리용)

## 마이그레이션 관리

Supabase CLI + `supabase/migrations/` 디렉토리. Phase 1 시작 시 `app/supabase/`에 세팅.
