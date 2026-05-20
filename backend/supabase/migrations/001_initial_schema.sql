-- ═══════════════════════════════════════════════════════════
--  Expense Tracker — Initial Schema
--  Run this in Supabase → SQL Editor
-- ═══════════════════════════════════════════════════════════

-- ── Extensions ──────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ── Users (mirrors auth.users — for profile data) ───────────
create table if not exists public.profiles (
  id             uuid primary key references auth.users(id) on delete cascade,
  display_name   text,
  whatsapp_phone text unique,
  currency       text default 'INR',
  created_at     timestamptz default now()
);

-- ── Expenses ────────────────────────────────────────────────
create table if not exists public.expenses (
  id             uuid primary key default uuid_generate_v4(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  date           date not null,
  amount         numeric(12,2) not null check (amount >= 0),
  category       text not null default 'Others',
  description    text default '',
  payment_method text default 'UPI',
  source         text default '',      -- import batch tag
  type           text default 'Debit', -- Debit | Credit
  attachment_url text default '',      -- Supabase Storage URL
  created_at     timestamptz default now()
);

create index idx_expenses_user_date on public.expenses(user_id, date desc);
create index idx_expenses_user_cat  on public.expenses(user_id, category);
create index idx_expenses_source    on public.expenses(user_id, source);

-- ── Budgets ─────────────────────────────────────────────────
create table if not exists public.budgets (
  id             uuid primary key default uuid_generate_v4(),
  user_id        uuid not null references auth.users(id) on delete cascade,
  category       text not null,
  monthly_limit  numeric(12,2) not null default 0,
  updated_at     timestamptz default now(),
  unique(user_id, category)
);

-- ── Custom keyword mappings ──────────────────────────────────
create table if not exists public.keyword_mappings (
  id         uuid primary key default uuid_generate_v4(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  keyword    text not null,
  category   text not null,
  unique(user_id, keyword)
);

-- ── WhatsApp phone → user link ───────────────────────────────
create table if not exists public.whatsapp_users (
  phone    text primary key,
  user_id  uuid not null references auth.users(id) on delete cascade,
  linked_at timestamptz default now()
);

-- ── Row Level Security ───────────────────────────────────────
alter table public.profiles        enable row level security;
alter table public.expenses        enable row level security;
alter table public.budgets         enable row level security;
alter table public.keyword_mappings enable row level security;

-- profiles: own row only
create policy "own profile" on public.profiles
  for all using (auth.uid() = id);

-- expenses: own rows only
create policy "own expenses" on public.expenses
  for all using (auth.uid() = user_id);

-- budgets: own rows only
create policy "own budgets" on public.budgets
  for all using (auth.uid() = user_id);

-- keyword_mappings: own rows only
create policy "own keywords" on public.keyword_mappings
  for all using (auth.uid() = user_id);

-- ── Auto-create profile on signup ───────────────────────────
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$;

create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
