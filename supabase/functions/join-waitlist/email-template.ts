/**
 * Email de alta en la beta abierta (Resend): el acceso llega al momento.
 * Nada de plazas, waves ni referidos: descarga (iPhone o Android), crea tu cuenta y listo.
 *
 * Light (default): fondo claro + wordmark negro.
 * Dark (@media prefers-color-scheme: dark): fondo azul marca #2A6FDB + wordmark blanco.
 *
 * Los headers del logo son PNG OPACOS del mismo color que el fondo (Gmail rellena
 * la transparencia PNG con blanco y generaba la "caja" blanca).
 */

const BRAND = '#2A6FDB'
const BRAND_SOFT = '#5a8fe3'
const LIGHT_BG = '#eef1f6'
const LIGHT_CARD = '#ffffff'
const LIGHT_HERO = '#f7f8fb'
const LIGHT_BORDER = '#e2e5eb'
const LIGHT_TEXT = '#1a1a1a'
const LIGHT_MUTED = '#5b6270'
const CARD_W = '540'
const LOGO_LIGHT = 'https://2trainapp.com/assets/logo-header-light.png'
const LOGO_DARK = 'https://2trainapp.com/assets/logo-header-dark.png'
export const APP_STORE_URL = 'https://apps.apple.com/app/id6809469225'
export const PLAY_URL = 'https://play.google.com/store/apps/details?id=com.twotrain.two_train'
const FONT = `-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif`

function copy(isEn: boolean, shareLink: string) {
  return isEn
    ? {
        lang: 'en',
        subject: "You're in: start training with 2trAIn",
        preheader: 'Download 2trAIn, create your account and your first week is ready.',
        eyebrow: 'Open beta',
        hero: "You're in",
        sub: 'Your access to 2trAIn',
        intro: 'Thanks for signing up. 2trAIn is your AI coach: it builds your week, adjusts it to what you train and explains why every change happens.',
        start: 'To get started:',
        step1: 'Download 2trAIn on your phone: App Store for iPhone or Google Play for Android.',
        step2: 'Open the app, tap <strong>«Create account»</strong> and sign up with email and password. We recommend using this same email.',
        cta: 'App Store (iPhone) →',
        ctaPlay: 'Google Play (Android) →',
        feedback: 'If anything feels off while you try it, reply to this email: we read everything and it helps us a lot.',
        shareK: 'Share',
        shareT: 'Train with someone? Send them the link.',
        shareBtn: 'Share on WhatsApp →',
        wa: `I'm trying 2trAIn ⚡ An AI coach that builds your week and explains every change with your own data. Open beta 👉 ${shareLink}`,
        team: '— The 2trAIn team',
        signup: 'You signed up at',
        unsub: 'Unsubscribe',
        unsubSubject: 'Unsubscribe from 2trAIn emails',
        text: (link: string) =>
          'Thanks for signing up. 2trAIn is your AI coach: it builds your week, adjusts it to what you train and explains why every change happens.\n\n' +
          `1. Download 2trAIn. iPhone: ${APP_STORE_URL} · Android: ${PLAY_URL}\n` +
          '2. Open the app, tap «Create account» and sign up with email and password. We recommend using this same email.\n\n' +
          'If anything feels off while you try it, reply to this email: we read everything.\n\n' +
          `Train with someone? Send them the link: ${link}\n\n— The 2trAIn team`,
      }
    : {
        lang: 'es',
        subject: 'Ya puedes entrar en 2trAIn',
        preheader: 'Descarga 2trAIn, crea tu cuenta y tu primera semana está lista.',
        eyebrow: 'Beta abierta',
        hero: 'Ya puedes entrar',
        sub: 'Tu acceso a 2trAIn',
        intro: 'Gracias por apuntarte. 2trAIn es tu entrenador con IA: te prepara la semana, la ajusta a lo que entrenas y te explica por qué cambia cada cosa.',
        start: 'Para empezar:',
        step1: 'Descarga 2trAIn en tu móvil: App Store si tienes iPhone o Google Play si tienes Android.',
        step2: 'Abre la app, toca <strong>«Crear cuenta»</strong> y regístrate con email y contraseña. Te recomendamos usar este mismo email.',
        cta: 'App Store (iPhone) →',
        ctaPlay: 'Google Play (Android) →',
        feedback: 'Si algo no te cuadra mientras la pruebas, contesta a este correo: lo leemos todo y nos ayuda muchísimo.',
        shareK: 'Comparte',
        shareT: '¿Entrenas con alguien? Pásale el enlace.',
        shareBtn: 'Compartir por WhatsApp →',
        wa: `Estoy probando 2trAIn ⚡ Un coach con IA que te prepara la semana y te explica cada cambio con tus propios datos. Beta abierta 👉 ${shareLink}`,
        team: '— El equipo de 2trAIn',
        signup: 'Te apuntaste en',
        unsub: 'Darme de baja',
        unsubSubject: 'Baja emails 2trAIn',
        text: (link: string) =>
          'Gracias por apuntarte. 2trAIn es tu entrenador con IA: te prepara la semana, la ajusta a lo que entrenas y te explica por qué cambia cada cosa.\n\n' +
          `1. Descarga 2trAIn. iPhone: ${APP_STORE_URL} · Android: ${PLAY_URL}\n` +
          '2. Abre la app, toca «Crear cuenta» y regístrate con email y contraseña. Te recomendamos usar este mismo email.\n\n' +
          'Si algo no te cuadra mientras la pruebas, contesta a este correo: lo leemos todo.\n\n' +
          `¿Entrenas con alguien? Pásale el enlace: ${link}\n\n— El equipo de 2trAIn`,
      }
}

export function emailSubject(isEn: boolean): string {
  return copy(isEn, '').subject
}

export function buildText(shareLink: string, isEn: boolean): string {
  return copy(isEn, shareLink).text(shareLink)
}

const sep = `<tr><td class="divider" bgcolor="${LIGHT_CARD}" style="background-color:${LIGHT_CARD};padding:0;border-top:1px solid ${LIGHT_BORDER};font-size:0;line-height:0;height:1px;">&nbsp;</td></tr>`

function p(text: string, opts: { muted?: boolean; size?: string; margin?: string } = {}) {
  const color = opts.muted ? LIGHT_MUTED : LIGHT_TEXT
  const cls = opts.muted ? 'text-mut' : 'text-pri'
  return `<p class="${cls}" style="margin:${opts.margin ?? '0 0 14px'};font-size:${opts.size ?? '15px'};color:${color};line-height:1.55;">${text}</p>`
}

function step(n: number, text: string) {
  return `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 14px;"><tr>
      <td valign="top" style="width:30px;vertical-align:top;"><span class="accent" style="display:inline-block;font-size:13px;font-weight:800;color:${BRAND};line-height:1.55;">${n}.</span></td>
      <td valign="top" style="vertical-align:top;">${p(text, { margin: '0' })}</td>
    </tr></table>`
}

function body(inner: string, padding = '24px 28px 10px') {
  return `<tr><td class="body" bgcolor="${LIGHT_CARD}" style="background-color:${LIGHT_CARD};padding:${padding};">${inner}</td></tr>`
}

export function buildEmail(shareLink: string, isEn: boolean): string {
  const t = copy(isEn, shareLink)
  const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(t.wa)}`
  const unsubUrl = `mailto:contact@2trainapp.com?subject=${encodeURIComponent(t.unsubSubject)}`
  const siteRoot = isEn ? 'https://2trainapp.com/en/' : 'https://2trainapp.com'

  return `<!DOCTYPE html>
<html lang="${t.lang}" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>${t.subject}</title>
  <style>
    :root { color-scheme: light dark; }
    body { margin:0; padding:0; }
    .logo-dark { display:none !important; max-height:0 !important; overflow:hidden !important; mso-hide:all; }
    @media (prefers-color-scheme: dark) {
      .logo-light { display:none !important; max-height:0 !important; overflow:hidden !important; }
      .logo-dark { display:block !important; max-height:none !important; overflow:visible !important; }
      .page { background-color:${BRAND} !important; }
      .card, .hero, .body { background-color:${BRAND} !important; border-color:${BRAND_SOFT} !important; }
      .text-pri { color:#ffffff !important; }
      .text-mut { color:#d6e4f8 !important; }
      .accent { color:#ffffff !important; }
      .btn-pri { background-color:#ffffff !important; color:${BRAND} !important; }
      .divider { border-color:${BRAND_SOFT} !important; }
      .footer a { color:#ffffff !important; }
    }
  </style>
</head>
<body class="page" style="margin:0;padding:0;background-color:${LIGHT_BG};font-family:${FONT};" bgcolor="${LIGHT_BG}">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">${t.preheader}</div>
<table role="presentation" class="page" width="100%" cellpadding="0" cellspacing="0" bgcolor="${LIGHT_BG}" style="background-color:${LIGHT_BG};padding:24px 12px;">
<tr><td align="center">
<table role="presentation" class="card" width="${CARD_W}" cellpadding="0" cellspacing="0" bgcolor="${LIGHT_CARD}" style="width:${CARD_W}px;max-width:100%;background-color:${LIGHT_CARD};border:1px solid ${LIGHT_BORDER};border-radius:16px;overflow:hidden;">

  <!-- LOGO: light default / dark via media query. Opaque headers = no white box in Gmail. -->
  <tr><td class="card" bgcolor="${LIGHT_CARD}" style="background-color:${LIGHT_CARD};padding:0;line-height:0;font-size:0;">
    <div class="logo-light" style="line-height:0;font-size:0;">
      <img src="${LOGO_LIGHT}" width="540" alt="2trAIn" style="display:block;width:100%;max-width:540px;height:auto;border:0;outline:none;">
    </div>
    <!--[if !mso]><!-->
    <div class="logo-dark" style="display:none;max-height:0;overflow:hidden;line-height:0;font-size:0;">
      <img src="${LOGO_DARK}" width="540" alt="2trAIn" style="display:block;width:100%;max-width:540px;height:auto;border:0;outline:none;">
    </div>
    <!--<![endif]-->
  </td></tr>

  <!-- HERO -->
  <tr><td class="hero" bgcolor="${LIGHT_HERO}" style="background-color:${LIGHT_HERO};border-top:1px solid ${LIGHT_BORDER};border-bottom:1px solid ${LIGHT_BORDER};padding:34px 32px 28px;text-align:center;">
    <p class="accent" style="margin:0 0 10px;font-size:11px;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:${BRAND};">${t.eyebrow}</p>
    <p class="text-pri" style="margin:0;font-size:40px;font-weight:800;letter-spacing:-1.5px;color:${LIGHT_TEXT};line-height:1.1;">${t.hero}</p>
    <p class="text-mut" style="margin:12px 0 0;font-size:14px;color:${LIGHT_MUTED};line-height:1.5;">${t.sub}</p>
  </td></tr>

  <!-- Cómo entrar -->
  ${body(
    p(t.intro) +
    p(t.start, { margin: '6px 0 12px' }) +
    step(1, t.step1) +
    step(2, t.step2),
  )}
  ${body(
    `<a class="btn-pri" href="${APP_STORE_URL}" style="display:block;background:${BRAND};color:#ffffff;font-size:15px;font-weight:700;padding:15px 0;border-radius:8px;text-decoration:none;text-align:center;line-height:1.2;margin-bottom:10px;">${t.cta}</a>` +
    `<a class="btn-pri" href="${PLAY_URL}" style="display:block;background:${BRAND};color:#ffffff;font-size:15px;font-weight:700;padding:15px 0;border-radius:8px;text-decoration:none;text-align:center;line-height:1.2;">${t.ctaPlay}</a>`,
    '0 28px 26px',
  )}

  ${sep}

  <!-- Feedback -->
  ${body(p(t.feedback, { muted: true, size: '14px' }), '22px 28px 12px')}

  ${sep}

  <!-- Compartir -->
  ${body(
    `<p class="accent" style="margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:${BRAND};line-height:1.4;">${t.shareK}</p>` +
    p(t.shareT, { muted: true, size: '14px' }) +
    `<a class="btn-pri" href="${whatsappUrl}" style="display:block;background:${BRAND};color:#ffffff;font-size:14px;font-weight:700;padding:14px 0;border-radius:8px;text-decoration:none;text-align:center;line-height:1.2;">${t.shareBtn}</a>`,
    '22px 28px 26px',
  )}
</table>

  <table role="presentation" class="footer" width="${CARD_W}" cellpadding="0" cellspacing="0" style="width:${CARD_W}px;max-width:100%;">
  <tr><td style="padding:18px 0 24px;text-align:center;">
    <p class="text-mut" style="margin:0 0 3px;font-size:12px;color:#8a9099;">${t.team}</p>
    <p class="text-mut" style="margin:0 0 10px;font-size:11px;color:#8a9099;">${t.signup} <a href="${siteRoot}" style="color:${BRAND};text-decoration:none;">2trainapp.com</a></p>
    <p class="text-mut" style="margin:0;font-size:11px;color:#8a9099;"><a href="${unsubUrl}" style="color:#8a9099;text-decoration:underline;">${t.unsub}</a></p>
  </td></tr>
  </table>

</td></tr>
</table>
</body>
</html>`
}
