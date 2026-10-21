-- Run once in the Supabase SQL Editor.
create table if not exists public.learner_progress (
    user_id uuid primary key references auth.users(id) on delete cascade,
    progress jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

alter table public.learner_progress enable row level security;

drop policy if exists "Learners can read their progress" on public.learner_progress;
create policy "Learners can read their progress"
    on public.learner_progress for select to authenticated
    using (auth.uid() = user_id);

drop policy if exists "Learners can create their progress" on public.learner_progress;
create policy "Learners can create their progress"
    on public.learner_progress for insert to authenticated
    with check (auth.uid() = user_id);

drop policy if exists "Learners can update their progress" on public.learner_progress;
create policy "Learners can update their progress"
    on public.learner_progress for update to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

grant select, insert, update on public.learner_progress to authenticated;
revoke all on public.learner_progress from anon;

create or replace function public.set_learner_progress_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists set_learner_progress_updated_at on public.learner_progress;
create trigger set_learner_progress_updated_at
    before update on public.learner_progress
    for each row execute function public.set_learner_progress_updated_at();
