-- Esquema para el visor propio (CustomJewelryViewer.tsx + GlbUploader.tsx).
-- Pégalo en el SQL editor de tu proyecto Supabase (el que Lovable conecta).

-- 1) Tabla de metadatos de cada modelo subido.
create table if not exists public.jewelry_models (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  storage_path text not null,
  width_morph_name text not null default 'Width',
  created_at timestamptz not null default now()
);

alter table public.jewelry_models enable row level security;

-- Lectura pública (el visor necesita listar/leer sin sesión).
create policy "jewelry_models_public_read"
  on public.jewelry_models for select
  using (true);

-- Solo usuarios autenticados pueden subir metadatos.
create policy "jewelry_models_authenticated_insert"
  on public.jewelry_models for insert
  to authenticated
  with check (true);

-- 2) Bucket de almacenamiento para los .glb.
insert into storage.buckets (id, name, public)
values ('jewelry-models', 'jewelry-models', true)
on conflict (id) do nothing;

-- Lectura pública de los archivos (para que useGLTF los cargue por URL).
create policy "jewelry_models_storage_public_read"
  on storage.objects for select
  using (bucket_id = 'jewelry-models');

-- Solo usuarios autenticados pueden subir archivos.
create policy "jewelry_models_storage_authenticated_insert"
  on storage.objects for insert
  to authenticated
  with check (bucket_id = 'jewelry-models');
