---
paths:
  - "supabase/**"
---

# Supabase: todo es producción

- No hay entorno local ni de pruebas: no hay `supabase/config.toml` ni migración base de la tabla
  `waitlist` (se dan por hechas). La función y la base de datos que se ven aquí son las de producción.
- **Migraciones aplicadas: no se editan** (el guard lo deniega). Un cambio de esquema es un fichero
  nuevo `supabase/migrations/YYYYMMDDHHMMSS_<nombre>.sql` (pide permiso) y lo aplica una persona.
- **Nada se despliega ni se aplica desde la sesión:** `supabase functions deploy`, `supabase db`,
  `supabase link` y `supabase secrets` están en `deny`. Tampoco `supabase/seed-waitlist-test.sql`:
  inserta filas directamente y solo vale para un entorno de pruebas que no existe.
- **El alta desde `localhost` llama a la función de producción** (CORS admite `localhost:8000`) y envía
  un email real por Resend. No se envía el formulario para probar; nada de `curl` a `join-waitlist`.
- El navegador solo habla con la función, nunca con las tablas: RLS activo sin políticas y sin
  `EXECUTE` para `anon` (`20260616110000_security_lockdown.sql`). Una migración nueva no lo abre.
- Variables de la función (solo nombres; los valores viven en el panel de Supabase, nunca aquí):
  `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `RESEND_API_KEY`. La clave anon de `app.js` es pública
  por diseño (`role=anon`); ninguna otra clave entra en el repo.
- `join-waitlist`: honeypot, límite por IP (`signup_log`), tope diario de emails y atribución
  (`attribution.ts`). El email de acceso ES/EN está en `email-template.ts`.
