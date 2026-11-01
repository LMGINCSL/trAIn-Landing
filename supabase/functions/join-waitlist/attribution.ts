// Origen del alta: UTM, identificadores de clic de anuncios y páginas.
// Todo llega del navegador, así que se limpia: solo claves conocidas, texto
// corto y sin caracteres raros. Lo que no pasa el filtro se descarta en
// silencio; nunca bloquea un alta.

const TEXT_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'] as const
const CLICK_KEYS = ['gclid', 'fbclid'] as const
const PATH_KEYS = ['landing_path', 'signup_path'] as const

export function cleanAttribution(raw: unknown): Record<string, string> {
  const out: Record<string, string> = {}
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return out
  const r = raw as Record<string, unknown>

  for (const k of TEXT_KEYS) {
    const v = r[k]
    if (typeof v !== 'string') continue
    const t = v.trim().slice(0, 150).toLowerCase()
    if (t && /^[\p{L}\p{N} ._~+:/@|-]+$/u.test(t)) out[k] = t
  }
  for (const k of CLICK_KEYS) {
    const v = r[k]
    if (typeof v === 'string' && /^[A-Za-z0-9_-]{8,255}$/.test(v.trim())) out[k] = v.trim()
  }
  for (const k of PATH_KEYS) {
    const v = r[k]
    if (typeof v === 'string' && /^\/[A-Za-z0-9/._-]{0,199}$/.test(v)) out[k] = v
  }
  const h = r.referrer_host
  if (typeof h === 'string') {
    const host = h.trim().toLowerCase()
    if (/^[a-z0-9-]+(\.[a-z0-9-]+)+$/.test(host) && host.length <= 253) out.referrer_host = host
  }
  return out
}
