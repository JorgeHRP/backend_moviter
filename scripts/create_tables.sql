-- Tabela principal de máquinas
-- Executar no Supabase SQL Editor

create table if not exists machines (
    id              integer primary key,
    chassis         text,
    num_maquina     text unique not null,
    designacao      text,
    cod_cliente     text not null,
    nome_cliente    text,
    localidade      text,
    marca           text,
    familia         text,
    cod_marca       text,
    cod_modelo      text,
    modelo          text,
    email           text,
    telefone1       text,
    synced_at       timestamptz,
    raw_json        jsonb,
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

-- Índices para queries frequentes
create index if not exists idx_machines_cod_cliente on machines(cod_cliente);
create index if not exists idx_machines_marca       on machines(marca);
create index if not exists idx_machines_chassis     on machines(chassis);

-- RLS — habilitar Row Level Security (ajustar policies conforme autenticação)
alter table machines enable row level security;

-- Policy de leitura aberta (ajustar em produção)
drop policy if exists "Leitura pública de máquinas" on machines;
create policy "Leitura pública de máquinas"
    on machines for select
    using (true);

-- Trigger para updated_at automático
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger machines_updated_at
    before update on machines
    for each row execute function update_updated_at();
