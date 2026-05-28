-- Tabela de utilizadores — login mobile (email + password)
-- Executar no Supabase SQL Editor ou via scripts/create_users_table.py

create table if not exists users (
    id              uuid primary key default gen_random_uuid(),
    email           text unique not null,
    password_hash   text not null,
    full_name       text,
    phone           text,
    role            text not null default 'user',   -- 'user' | 'admin'
    is_active       boolean not null default true,
    last_login_at   timestamptz,
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

create index if not exists idx_users_email on users(email);

-- Tabela de refresh tokens (sessoes persistentes no mobile)
create table if not exists refresh_tokens (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid not null references users(id) on delete cascade,
    token           text unique not null,
    device_info     text,
    expires_at      timestamptz not null,
    created_at      timestamptz default now()
);

create index if not exists idx_refresh_tokens_token   on refresh_tokens(token);
create index if not exists idx_refresh_tokens_user_id on refresh_tokens(user_id);

-- Trigger updated_at para users (reutiliza a função criada na tabela machines)
create trigger users_updated_at
    before update on users
    for each row execute function update_updated_at();
