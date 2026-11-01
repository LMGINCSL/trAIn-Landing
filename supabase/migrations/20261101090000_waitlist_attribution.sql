-- Origen de cada alta: UTM, identificadores de clic de anuncios (gclid para
-- importar conversiones en Google Ads, fbclid para Meta), página de entrada,
-- web de procedencia y página donde se apuntó. Lo rellena la edge function
-- join-waitlist solo en el primer alta; RLS ya deja la tabla fuera de anon.

alter table public.waitlist
  add column if not exists utm_source text,
  add column if not exists utm_medium text,
  add column if not exists utm_campaign text,
  add column if not exists utm_term text,
  add column if not exists utm_content text,
  add column if not exists gclid text,
  add column if not exists fbclid text,
  add column if not exists landing_path text,
  add column if not exists referrer_host text,
  add column if not exists signup_path text;

create index if not exists waitlist_utm_campaign_idx on public.waitlist (utm_campaign);

-- Altas por semana y canal. Sin UTM, el canal es «referido» (enlace de otro
-- usuario), la web de procedencia o «(directo)».
create or replace view public.waitlist_by_source
  with (security_invoker = true) as
select
  date_trunc('week', created_at)::date as semana,
  coalesce(
    utm_source,
    case when referred_by is not null then 'referido' end,
    referrer_host,
    '(directo)'
  ) as origen,
  utm_medium as medio,
  utm_campaign as campana,
  coalesce(signup_path, landing_path) as pagina,
  count(*) as altas,
  count(gclid) as con_gclid
from public.waitlist
group by 1, 2, 3, 4, 5;

revoke all on public.waitlist_by_source from anon, authenticated;
