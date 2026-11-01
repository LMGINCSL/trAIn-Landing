import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { buildEmail } from './email-template.ts'
import { cleanAttribution } from './attribution.ts'

const ALLOWED_ORIGINS = new Set([
  'https://2trainapp.com',
  'https://www.2trainapp.com',
  'http://localhost:8000',
  'http://127.0.0.1:8000',
  'http://localhost:5501',
  'http://127.0.0.1:5501',
])

function buildCors(origin: string | null) {
  const allow = origin && ALLOWED_ORIGINS.has(origin) ? origin : 'https://2trainapp.com'
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Vary': 'Origin',
  }
}

function json(data: unknown, status: number, cors: Record<string, string>) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...cors, 'Content-Type': 'application/json' },
  })
}

// deno-lint-ignore no-explicit-any
async function rateLimitOrReject(supabase: any, req: Request, isEn: boolean, cors: Record<string, string>) {
  const ip = (req.headers.get('x-forwarded-for') || '').split(',')[0].trim() || 'unknown'
  const rlSince = new Date(Date.now() - 60 * 60 * 1000).toISOString()
  const rl = await supabase.from('signup_log')
    .select('*', { count: 'exact', head: true })
    .eq('ip', ip).gte('created_at', rlSince)
  if ((rl.count ?? 0) >= 10) {
    return json(
      { error: isEn ? 'Too many attempts. Please try again later.' : 'Demasiados intentos. Inténtalo más tarde.' },
      429,
      cors,
    )
  }
  await supabase.from('signup_log').insert({ ip })
  return null
}

/** Stats + posición para el modal (signup o ?spot=). */
// deno-lint-ignore no-explicit-any
async function buildSpotPayload(supabase: any, email: string, referralCode: string) {
  const { data: posData } = await supabase.rpc('get_waitlist_position', { p_email: email })
  const position: number = posData ?? 0

  const [r1, r2, r3] = await Promise.all([
    supabase.rpc('project_waitlist_position', { p_email: email, p_extra_referrals: 1 }),
    supabase.rpc('project_waitlist_position', { p_email: email, p_extra_referrals: 2 }),
    supabase.rpc('project_waitlist_position', { p_email: email, p_extra_referrals: 3 }),
  ])
  const projection = { '1': r1.data ?? position, '2': r2.data ?? position, '3': r3.data ?? position }

  const totalRes = await supabase.from('waitlist').select('*', { count: 'exact', head: true })
  const total = totalRes.count ?? 0
  const lockedRes = await supabase.from('waitlist').select('*', { count: 'exact', head: true }).not('locked_position', 'is', null)
  const lockedCount = lockedRes.count ?? 0
  const refRes = await supabase.from('waitlist').select('*', { count: 'exact', head: true }).eq('referred_by', referralCode)
  const referrals = refRes.count ?? 0
  const lockedRowRes = await supabase.from('waitlist').select('locked_position').eq('email', email).maybeSingle()
  const lockedPosition = (lockedRowRes.data as { locked_position?: number } | null)?.locked_position ?? null

  return {
    referral_code: referralCode,
    position,
    projection,
    total,
    locked: lockedCount,
    referrals,
    locked_position: lockedPosition,
  }
}

Deno.serve(async (req) => {
  const corsHeaders = buildCors(req.headers.get('origin'))

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const body = await req.json()
    const { email, referred_by, lang, hp, referral_code: spotCode, attribution } = body
    const isEn = lang === 'en'

    // Honeypot: campo oculto que solo rellenan los bots → respondemos OK sin registrar nada.
    if (hp && String(hp).trim() !== '') {
      return json({ ok: true }, 200, corsHeaders)
    }

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    )

    // ── Lookup por código (CTA "Ver mi posición" del email → ?spot=CODE) ──
    if (spotCode && typeof spotCode === 'string' && !email) {
      const code = spotCode.trim()
      if (!/^[A-Za-z0-9_-]{4,64}$/.test(code)) {
        return json({ error: isEn ? 'Invalid code' : 'Código inválido' }, 400, corsHeaders)
      }

      const limited = await rateLimitOrReject(supabase, req, isEn, corsHeaders)
      if (limited) return limited

      const { data: row } = await supabase
        .from('waitlist')
        .select('email, referral_code')
        .eq('referral_code', code)
        .maybeSingle()

      if (!row?.email || !row.referral_code) {
        return json({ error: isEn ? 'Spot not found' : 'Plaza no encontrada' }, 404, corsHeaders)
      }

      const payload = await buildSpotPayload(supabase, row.email, row.referral_code)
      return json({ ...payload, already_registered: true, from_spot_link: true }, 200, corsHeaders)
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return json({ error: 'Email inválido' }, 400, corsHeaders)
    }

    const limited = await rateLimitOrReject(supabase, req, isEn, corsHeaders)
    if (limited) return limited

    // Insert — if duplicate, fetch existing record. El origen (UTM, gclid…)
    // solo se guarda en el primer alta. Si la migración de atribución aún no
    // está aplicada (columna inexistente, 42703), se repite sin esos campos
    // para que el alta nunca falle por ello.
    const row = { email, referred_by: referred_by || null, ...cleanAttribution(attribution) }
    let { data: inserted, error: insertError } = await supabase
      .from('waitlist')
      .insert(row)
      .select('referral_code')
      .single()
    if (insertError?.code === '42703') {
      console.warn('waitlist sin columnas de atribución: falta aplicar 20261101090000_waitlist_attribution.sql')
      ;({ data: inserted, error: insertError } = await supabase
        .from('waitlist')
        .insert({ email, referred_by: referred_by || null })
        .select('referral_code')
        .single())
    }

    let referralCode: string
    let alreadyRegistered = false

    if (insertError) {
      if (insertError.code === '23505') {
        alreadyRegistered = true
        const { data: existing } = await supabase
          .from('waitlist')
          .select('referral_code')
          .eq('email', email)
          .single()
        referralCode = existing!.referral_code
      } else {
        throw insertError
      }
    } else {
      referralCode = inserted!.referral_code
    }

    const payload = await buildSpotPayload(supabase, email, referralCode)
    const { position, referrals } = payload

    const siteUrl = 'https://2trainapp.com'
    const referralLink = `${siteUrl}?ref=${referralCode}`
    const spotLink = isEn
      ? `${siteUrl}/en/?spot=${encodeURIComponent(referralCode)}`
      : `${siteUrl}/?spot=${encodeURIComponent(referralCode)}`

    // Tope diario de emails: backstop anti-flood para no quemar Resend / la reputación
    // del dominio. (Resend gratis = 100/día; sube/baja DAILY_EMAIL_CAP según tu plan.)
    const dayStart = new Date(); dayStart.setUTCHours(0, 0, 0, 0)
    const dc = await supabase.from('waitlist')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', dayStart.toISOString())
    const dailyCount = dc.count ?? 0
    const DAILY_EMAIL_CAP = 300

    // Send email only on first signup (y por debajo del tope diario)
    if (!alreadyRegistered && dailyCount <= DAILY_EMAIL_CAP) {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${Deno.env.get('RESEND_API_KEY')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: '2trAIn Waitlist <waitlist@2trainapp.com>',
          to: email,
          subject: isEn ? `You're #${position} on the 2trAIn waitlist` : `Eres el #${position} en la waitlist de 2trAIn`,
          html: buildEmail(position, referralLink, isEn, referrals, spotLink),
        }),
      })
    }

    return json({ ...payload, already_registered: alreadyRegistered }, 200, corsHeaders)
  } catch (err) {
    console.error(err)
    return json({ error: 'Error interno' }, 500, corsHeaders)
  }
})
