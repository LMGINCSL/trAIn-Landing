import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { buildEmail, buildText, emailSubject } from './email-template.ts'
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

    // ── Enlaces ?spot=CODE de los emails antiguos de la waitlist: abren el modal
    //    ya confirmado con el enlace para compartir. Ya no hay posición que enseñar.
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
        return json({ error: isEn ? 'Link not found' : 'Enlace no encontrado' }, 404, corsHeaders)
      }

      return json({ referral_code: row.referral_code, already_registered: true, from_spot_link: true }, 200, corsHeaders)
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

    // Beta abierta: el email lleva el acceso (App Store y cómo crear la cuenta).
    // También a quien ya estaba apuntado: los de la antigua lista de espera que
    // vuelven a dejar su email reciben ahora el acceso.
    const shareLink = `https://2trainapp.com${isEn ? '/en/' : ''}?ref=${referralCode}`

    // Tope diario de emails: backstop anti-flood para no quemar Resend / la reputación
    // del dominio. (Resend gratis = 100/día; sube/baja DAILY_EMAIL_CAP según tu plan.)
    const dayStart = new Date(); dayStart.setUTCHours(0, 0, 0, 0)
    const dc = await supabase.from('signup_log')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', dayStart.toISOString())
    const DAILY_EMAIL_CAP = 300

    if ((dc.count ?? 0) <= DAILY_EMAIL_CAP) {
      const sent = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${Deno.env.get('RESEND_API_KEY')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: '2trAIn <waitlist@2trainapp.com>',
          // waitlist@ no recibe correo: las respuestas (dudas, fallos) van al buzón real
          reply_to: 'contact@2trainapp.com',
          to: email,
          subject: emailSubject(isEn),
          html: buildEmail(shareLink, isEn),
          text: buildText(shareLink, isEn),
        }),
      })
      if (!sent.ok) console.error('Resend', sent.status, await sent.text())
    }

    return json({ referral_code: referralCode, already_registered: alreadyRegistered }, 200, corsHeaders)
  } catch (err) {
    console.error(err)
    return json({ error: 'Error interno' }, 500, corsHeaders)
  }
})
