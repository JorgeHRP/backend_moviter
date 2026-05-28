-- Tabela de ligacao utilizador <-> maquina
-- SEM foreign keys — relacao gerida apenas no backend
-- user_id referencia users.id  (sem constraint)
-- num_maquina referencia machines.num_maquina (sem constraint)

create table if not exists user_machines (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null,
    num_maquina text not null,
    created_at  timestamptz default now(),
    unique (user_id, num_maquina)
);

create index if not exists idx_user_machines_user_id     on user_machines(user_id);
create index if not exists idx_user_machines_num_maquina on user_machines(num_maquina);
