"""Artículos del blog (ES y EN). El cuerpo es HTML; {{week}} marca dónde va la
semana real dibujada (la misma que en la página por objetivo).

Reglas: cada artículo responde a una búsqueda concreta, enlaza a su página por
objetivo, cita fuentes cuando da cifras y no promete nada que la app no haga.
"""

PUBMED = "https://pubmed.ncbi.nlm.nih.gov/?term="

POSTS = [
    {
        "key": "hyrox", "date": "2026-11-02", "week": "hyrox", "photo": "blog-hyrox",
        "legal": {"es": "HYROX es una marca registrada de su titular. 2trAIn no está afiliada a HYROX ni cuenta con su patrocinio.",
                  "en": "HYROX is a registered trademark of its owner. 2trAIn is not affiliated with or sponsored by HYROX."},
        "es": {
            "slug": "semana-entrenamiento-hyrox", "cat": "HYROX",
            "title": "Cómo entrenar para HYROX: una semana real, sesión a sesión",
            "seo": "Plan de entrenamiento HYROX: una semana real, sesión a sesión · 2trAIn",
            "desc": "Qué entrenar para HYROX y cómo repartirlo en la semana: fuerza, carrera y gestos de la prueba. Con una semana real generada por 2trAIn, día a día.",
            "lead": "HYROX mezcla 8 km de carrera con 8 estaciones de fuerza. Para prepararlo no basta con correr ni con levantar: hay que hacer las dos cosas en la misma semana sin que una se coma a la otra. Así lo reparte un plan real.",
            "body": """
<h2>Qué te vas a encontrar el día de la prueba</h2>
<p>El formato es siempre el mismo: corres 1 km, haces una estación, y así ocho veces. Las estaciones, en orden, son SkiErg (1.000 m), empuje de trineo (50 m), arrastre de trineo (50 m), burpees con salto largo (80 m), remo (1.000 m), paseo del granjero (200 m), zancadas con saco (100 m) y wall balls (100 repeticiones). Los pesos cambian según la categoría.</p>
<p>De ahí salen tres necesidades: <strong>motor aeróbico</strong> para encadenar 8 km rompiendo el ritmo cada kilómetro, <strong>fuerza</strong> para mover el trineo y aguantar el agarre, y <strong>práctica de los gestos</strong> con las piernas ya cargadas.</p>
<h2>Las tres piezas de una semana de HYROX</h2>
<ul>
<li><strong>Fuerza con prioridad en pierna y tirón.</strong> Sentadilla, peso muerto y remos sostienen el trineo, las zancadas y el agarre del granjero.</li>
<li><strong>Dos sesiones de carrera con objetivos distintos:</strong> una de ritmo, para acostumbrarte a correr incómodo, y una tirada larga a ritmo de conversación para construir base.</li>
<li><strong>Gestos de la prueba al final de la fuerza:</strong> trineo, granjero, burpees o remoergómetro, en bloques cortos y con fatiga encima, como el día de la carrera.</li>
</ul>
<h2>Una semana real, día a día</h2>
<p>Esta es la semana que generó 2trAIn para un perfil de 29 años que viene de la fuerza, entrena 5 días y tiene su HYROX el 14 de marzo. No está retocada: son los títulos, tiempos, tramos y ejercicios que salieron del plan.</p>
{{week}}
<h2>Por qué está montada así</h2>
<p><strong>Tres días de fuerza y dos de carrera.</strong> Quien viene del gimnasio suele ir sobrado de fuerza y justo de carrera, así que la carrera tiene sus propios días y no se queda en «lo que sobre».</p>
<p><strong>Pierna y tirón pesan más que el empuje.</strong> En HYROX empujas el trineo con las piernas y tiras de él con la espalda; el press de banca apenas aparece en la prueba. Por eso hay más sentadilla, peso muerto y remo que press.</p>
<p><strong>Los gestos van al final.</strong> El arrastre de trineo, los golpes con balón o los burpees cierran las sesiones de fuerza en bloques de 30-40 segundos. Se practican con las piernas cansadas, que es como llegan en carrera, y no estropean la técnica de los básicos.</p>
<p><strong>La carrera de ritmo va por bloques.</strong> Tres bloques de 10 minutos en Zona 4 con 2 minutos suaves entre medias: un esfuerzo sostenido parecido al de la prueba, sin tener que hacerla entera.</p>
<p><strong>La tirada larga empieza con una prueba suave.</strong> Los primeros 30 minutos a ritmo de conversación sirven para medir distancia y pulso medio. Con ese dato, el plan ajusta los ritmos de las semanas siguientes en vez de suponerlos.</p>
<h2>Errores típicos al preparar HYROX</h2>
<ul>
<li><strong>Entrenar solo estaciones.</strong> Son lo que más se ve, pero buena parte del tiempo de la prueba se va corriendo.</li>
<li><strong>Hacer simulacros enteros cada semana.</strong> Acumulan mucha fatiga y dejan poco margen para mejorar fuerza y base. Mejor por partes.</li>
<li><strong>Olvidar el agarre.</strong> El granjero y el trineo lo castigan. Paseos con mancuernas y remos lo entrenan sin sesiones extra.</li>
<li><strong>Llegar cansado.</strong> Las últimas semanas bajan el volumen y mantienen algo de intensidad para que llegues fresco a la salida.</li>
</ul>
""",
            "faq": [("¿Cuántas semanas necesito para preparar un HYROX?", "Depende de dónde partas. Como referencia, unas 12 semanas dan tiempo a construir base, practicar las estaciones y afinar. Si tienes menos, el plan se adapta a las semanas que haya."),
                    ("¿Y si mi gimnasio no tiene trineo ni SkiErg?", "Se cambian por gestos parecidos con el material que tengas: empujes y arrastres con discos, remos, zancadas con mancuernas. 2trAIn lo recuerda para las semanas siguientes."),
                    ("¿Cuántos días a la semana hay que entrenar?", "Con 3 o 4 días se puede preparar bien. Esta semana usa 5 porque el perfil los tenía; con menos días se juntan fuerza y gestos en la misma sesión.")],
            "sources": [("Formato oficial de HYROX", "https://hyrox.com")],
            "cta": ("¿Quieres tu propia semana hacia tu fecha?", "Le dices el día de tu HYROX y el plan se construye hasta ahí, y se reescribe cada semana con lo que haces.", "/hyrox", "Ver cómo prepara HYROX 2trAIn"),
        },
        "en": {
            "slug": "hyrox-training-week", "cat": "HYROX",
            "title": "How to train for HYROX: a real week, session by session",
            "seo": "HYROX training plan: a real week, session by session · 2trAIn",
            "desc": "What to train for HYROX and how to spread it across the week: strength, running and race movements. With a real week generated by 2trAIn, day by day.",
            "lead": "HYROX mixes 8 km of running with 8 strength stations. Running alone won't do it, and neither will lifting: you need both in the same week without one eating the other. Here's how a real plan splits it.",
            "body": """
<h2>What race day looks like</h2>
<p>The format never changes: run 1 km, do a station, eight times over. The stations, in order, are SkiErg (1,000 m), sled push (50 m), sled pull (50 m), burpee broad jumps (80 m), rowing (1,000 m), farmers carry (200 m), sandbag lunges (100 m) and wall balls (100 reps). Weights depend on your division.</p>
<p>That leaves three needs: an <strong>aerobic engine</strong> to string together 8 km while breaking rhythm every kilometre, <strong>strength</strong> to move the sled and hold your grip, and <strong>practice of the movements</strong> on tired legs.</p>
<h2>The three pieces of a HYROX week</h2>
<ul>
<li><strong>Strength with legs and pulling first.</strong> Squats, deadlifts and rows carry the sled, the lunges and the farmers carry grip.</li>
<li><strong>Two runs with different goals:</strong> a tempo run to get used to running uncomfortable, and a conversational long run to build your base.</li>
<li><strong>Race movements at the end of strength days:</strong> sled, farmers carry, burpees or the rower, in short blocks and already tired, like on race day.</li>
</ul>
<h2>A real week, day by day</h2>
<p>This is the week 2trAIn generated for a 29-year-old profile coming from strength training, training 5 days, with a HYROX on March 14. Nothing touched up: these are the titles, times, segments and exercises the plan produced.</p>
{{week}}
<h2>Why it's built this way</h2>
<p><strong>Three strength days, two running days.</strong> People coming from the gym usually have strength to spare and not much running, so running gets its own days instead of whatever is left over.</p>
<p><strong>Legs and pulling outweigh pushing.</strong> In HYROX you push the sled with your legs and pull it with your back; the bench press barely shows up. So there's more squatting, deadlifting and rowing than pressing.</p>
<p><strong>Race movements go last.</strong> Sled drags, med ball slams or burpees close the strength sessions in 30-40 second blocks. You practise them on tired legs, as in the race, without spoiling your technique on the main lifts.</p>
<p><strong>The tempo run is split into blocks.</strong> Three 10-minute blocks in Zone 4 with 2 easy minutes between: sustained effort close to the race without running the whole thing.</p>
<p><strong>The long run starts with an easy test.</strong> The first 30 conversational minutes measure distance and average heart rate. With that, the plan sets the next weeks' paces instead of guessing them.</p>
<h2>Common HYROX prep mistakes</h2>
<ul>
<li><strong>Training only stations.</strong> They're the visible part, but a big share of race time is spent running.</li>
<li><strong>Full simulations every week.</strong> They pile up fatigue and leave little room to build strength and base. Train it in parts.</li>
<li><strong>Forgetting grip.</strong> The farmers carry and the sled punish it. Dumbbell carries and rows train it without extra sessions.</li>
<li><strong>Arriving tired.</strong> The last weeks drop the volume and keep some intensity so you reach the start line fresh.</li>
</ul>
""",
            "faq": [("How many weeks do I need to prepare for HYROX?", "It depends on where you start. As a reference, around 12 weeks gives you time to build a base, practise the stations and taper. With less, the plan adapts to the weeks you have."),
                    ("What if my gym has no sled or SkiErg?", "They're swapped for similar movements with the equipment you have: plate pushes and drags, rows, dumbbell lunges. 2trAIn remembers it for the following weeks."),
                    ("How many days a week do I need?", "You can prepare well with 3 or 4. This week uses 5 because the profile had them; with fewer days, strength and race movements share a session.")],
            "sources": [("Official HYROX format", "https://hyrox.com")],
            "cta": ("Want your own week toward your date?", "Tell it your HYROX date and the plan is built up to that day, rewritten every week from what you do.", "/en/hyrox/", "See how 2trAIn prepares HYROX"),
        },
    },
    {
        "key": "maraton", "date": "2026-11-02", "week": "maraton", "photo": "blog-maraton",
        "es": {
            "slug": "semana-entrenamiento-maraton", "cat": "Maratón y media",
            "title": "Plan de maratón y media maratón: así es una semana real",
            "seo": "Plan de entrenamiento de maratón y media maratón: una semana real · 2trAIn",
            "desc": "Cómo se reparte una semana para maratón o media: rodajes suaves, series, tirada larga y descanso. Con dos semanas reales generadas por 2trAIn, sesión a sesión.",
            "lead": "La mayoría de los kilómetros de un plan de maratón son suaves, y no es casualidad. Aquí tienes dos semanas reales, una de maratón y otra de media, con cada sesión dibujada por zonas y explicada.",
            "body": """
<h2>La regla que más se repite: casi todo suave</h2>
<p>Los estudios sobre cómo entrenan los corredores de fondo de nivel coinciden en un patrón: alrededor del 80 % de las sesiones son de intensidad baja y el resto, de calidad. Es lo que se conoce como entrenamiento polarizado o regla 80/20. Correr suave la mayor parte del tiempo construye base aeróbica sin acumular tanta fatiga, y deja piernas para que las series sean de verdad de calidad.</p>
<p>En la práctica, una semana de maratón o de media tiene cuatro tipos de sesión:</p>
<ul>
<li><strong>Rodajes suaves (Zona 2):</strong> a ritmo de conversación. Son la mayoría.</li>
<li><strong>Series o cambios de ritmo (Zona 4):</strong> cortas y con recuperación, para subir el techo.</li>
<li><strong>Tirada larga:</strong> la sesión clave de la semana, también suave.</li>
<li><strong>Descanso:</strong> sin él, lo demás no se asimila.</li>
</ul>
<h2>Dos semanas reales, sesión a sesión</h2>
<p>Abajo tienes dos semanas que generó 2trAIn. La de maratón es de un perfil de 45 años que entrena 5 días; la de media, de una corredora de 33 años que quiere bajar de 2:05 a 1:55. Cada gráfica muestra los tramos de la sesión: cuanto más alta y más oscura la barra, más intenso el tramo.</p>
{{week}}
<h2>Qué se ve en estas semanas</h2>
<p><strong>Solo dos días de calidad.</strong> En las dos semanas hay dos sesiones intensas (series, fartlek o cuestas) y el resto es suave. Mira la tira de arriba: los días oscuros son pocos.</p>
<p><strong>Las series son cortas y muchas.</strong> 11 × 90 segundos o 7 × 2 minutos, siempre con recuperación suave entre medias. Es más fácil mantener bien el esfuerzo en tramos cortos que en uno largo.</p>
<p><strong>La tirada larga va por bloques.</strong> 86 minutos en tramos de 15 con 2 minutos suaves entre medias. Da tiempo a beber, comprobar sensaciones y no pasarse de ritmo.</p>
<p><strong>Si fallas una sesión, se recoloca; no se acumula.</strong> El corredor de maratón se saltó la tirada larga de la semana anterior por un viaje. El plan no la metió doble: la mantuvo el sábado tal cual y sumó una serie más al lunes y al jueves.</p>
<p><strong>La media no es un maratón a escala.</strong> Su semana es más corta (3 h 45 min frente a 5 h 26 min) y cambia las series por fartlek y cuestas en tierra, que trabajan ritmo y fuerza de piernas con menos impacto.</p>
<h2>Las últimas semanas: el afinado</h2>
<p>Antes de la carrera se baja el volumen para llegar fresco. La revisión más citada sobre el tema (Bosquet y colaboradores, 2007) encontró los mejores resultados con unas dos semanas de afinado, reduciendo el volumen alrededor de un 40-60 % y manteniendo la intensidad y la frecuencia. Bajar volumen no es dejar de correr rápido: las series se acortan, pero no desaparecen.</p>
""",
            "faq": [("¿Cuántos días a la semana necesito para una media maratón?", "Con 3 o 4 días se puede preparar bien: dos sesiones de calidad, un rodaje suave y la tirada larga, como en la semana de media de arriba."),
                    ("¿A qué ritmo hago la tirada larga?", "Suave, a un ritmo en el que puedas hablar. Su objetivo es acumular tiempo corriendo, no la velocidad."),
                    ("¿Qué hago si me salto la tirada larga?", "No la recuperes metiendo dos en la misma semana. Sigue con el plan: 2trAIn la recoloca y ajusta el resto, como en la semana de maratón de arriba.")],
            "sources": [("Seiler S. (2010). What is best practice for training intensity and duration distribution in endurance athletes? International Journal of Sports Physiology and Performance.", PUBMED + "Seiler+2010+best+practice+training+intensity+duration+distribution+endurance+athletes"),
                        ("Bosquet L. y col. (2007). Effects of tapering on performance: a meta-analysis. Medicine & Science in Sports & Exercise.", PUBMED + "Bosquet+2007+effects+of+tapering+on+performance+meta-analysis")],
            "cta": ("¿Tienes fecha de carrera?", "Le dices la carrera y el día, y el plan reparte rodajes, series y tiradas largas hasta ahí, ajustándose a cómo respondes.", "/maraton", "Ver cómo prepara un maratón 2trAIn"),
        },
        "en": {
            "slug": "marathon-training-week", "cat": "Marathon and half",
            "title": "Marathon and half marathon training: what a real week looks like",
            "seo": "Marathon and half marathon training plan: a real week · 2trAIn",
            "desc": "How a marathon or half marathon week is split: easy runs, intervals, the long run and rest. With two real weeks generated by 2trAIn, session by session.",
            "lead": "Most of the kilometres in a marathon plan are easy, and that's no accident. Here are two real weeks, one for a marathon and one for a half, with every session drawn by zone and explained.",
            "body": """
<h2>The rule that keeps coming up: almost everything easy</h2>
<p>Studies on how well-trained endurance runners train agree on a pattern: around 80% of sessions are low intensity and the rest are quality. It's known as polarised training, or the 80/20 rule. Running easy most of the time builds your aerobic base without piling up fatigue, and leaves legs for intervals that are actually good.</p>
<p>In practice, a marathon or half marathon week has four kinds of session:</p>
<ul>
<li><strong>Easy runs (Zone 2):</strong> conversational pace. Most of the week.</li>
<li><strong>Intervals or surges (Zone 4):</strong> short and with recovery, to raise the ceiling.</li>
<li><strong>Long run:</strong> the key session of the week, also easy.</li>
<li><strong>Rest:</strong> without it, nothing else gets absorbed.</li>
</ul>
<h2>Two real weeks, session by session</h2>
<p>Below are two weeks 2trAIn generated. The marathon one is for a 45-year-old profile training 5 days; the half, for a 33-year-old runner who wants to go from 2:05 to 1:55. Each chart shows the session's segments: the taller and darker the bar, the harder the segment.</p>
{{week}}
<h2>What these weeks show</h2>
<p><strong>Only two quality days.</strong> Both weeks have two hard sessions (intervals, fartlek or hills) and the rest is easy. Look at the strip at the top: dark days are few.</p>
<p><strong>Intervals are short and many.</strong> 11 × 90 seconds or 7 × 2 minutes, always with easy recovery between. It's easier to hold good effort over short reps than one long one.</p>
<p><strong>The long run is split into blocks.</strong> 86 minutes in 15-minute segments with 2 easy minutes between. Time to drink, check how you feel and not drift too fast.</p>
<p><strong>Miss a session and it gets moved, not stacked.</strong> The marathon runner skipped the previous week's long run because of a trip. The plan didn't double it: it kept Saturday's long run as it was and added one rep to Monday and Thursday.</p>
<p><strong>A half isn't a scaled-down marathon.</strong> Its week is shorter (3 h 45 min vs 5 h 26 min) and swaps intervals for fartlek and trail hills, which work pace and leg strength with less impact.</p>
<h2>The last weeks: the taper</h2>
<p>Before the race, volume comes down so you arrive fresh. The most cited review on the subject (Bosquet et al., 2007) found the best results with a taper of about two weeks, cutting volume by roughly 40-60% while keeping intensity and frequency. Less volume doesn't mean no fast running: intervals get shorter, but they don't disappear.</p>
""",
            "faq": [("How many days a week do I need for a half marathon?", "You can prepare well with 3 or 4: two quality sessions, an easy run and the long run, like the half marathon week above."),
                    ("What pace should the long run be?", "Easy, at a pace where you can talk. Its goal is time on your feet, not speed."),
                    ("What if I skip the long run?", "Don't make it up by doing two in one week. Carry on with the plan: 2trAIn moves it and adjusts the rest, like in the marathon week above.")],
            "sources": [("Seiler S. (2010). What is best practice for training intensity and duration distribution in endurance athletes? International Journal of Sports Physiology and Performance.", PUBMED + "Seiler+2010+best+practice+training+intensity+duration+distribution+endurance+athletes"),
                        ("Bosquet L. et al. (2007). Effects of tapering on performance: a meta-analysis. Medicine & Science in Sports & Exercise.", PUBMED + "Bosquet+2007+effects+of+tapering+on+performance+meta-analysis")],
            "cta": ("Got a race date?", "Tell it the race and the day, and the plan spreads easy runs, intervals and long runs up to it, adjusting to how you respond.", "/en/marathon/", "See how 2trAIn prepares a marathon"),
        },
    },
    {
        "key": "descarga", "date": "2026-11-02", "week": "fuerza", "photo": "blog-descarga",
        "es": {
            "slug": "semana-de-descarga", "cat": "Fuerza",
            "title": "Semana de descarga: qué es, cuándo hacerla y cómo es una de verdad",
            "seo": "Semana de descarga en fuerza: qué es, cuándo y cómo hacerla · 2trAIn",
            "desc": "Qué es una semana de descarga en el entrenamiento de fuerza, las señales de que la necesitas y cómo se hace. Con la semana real que generó 2trAIn tras una semana al límite.",
            "lead": "Entrenar menos a propósito para luego rendir más. Suena raro, pero la semana de descarga es una de las herramientas más útiles para seguir progresando en fuerza. Así es una real.",
            "body": """
<h2>Qué es una semana de descarga</h2>
<p>Es un periodo corto, normalmente de una semana, en el que entrenas menos de lo habitual para recuperar y volver rindiendo mejor. No son vacaciones: sigues entrenando, pero con menos carga total.</p>
<p>Los trabajos recientes con entrenadores de fuerza (Bell y colaboradores) la describen como una reducción planificada de la exigencia del entrenamiento. Lo más habitual es hacerla cada pocas semanas, durante unos días, y bajar sobre todo el volumen (menos series) y el esfuerzo (más repeticiones en reserva), más que el peso de la barra.</p>
<h2>Señales de que te toca</h2>
<ul>
<li>Las series que antes salían con margen ahora te llevan al límite.</li>
<li>Los pesos se estancan o bajan varias sesiones seguidas.</li>
<li>Duermes peor, te cuesta arrancar o arrastras molestias.</li>
<li>Llevas muchas semanas subiendo carga sin parar.</li>
</ul>
<h2>Una semana de descarga real</h2>
<p>La semana anterior, este perfil de powerlifting (mujer de 27 años, 4 días) lo hizo todo, pero al límite: esfuerzo 9 sobre 10 en todas las sesiones. 2trAIn respondió con esta semana:</p>
{{week}}
<h2>Qué cambia y qué se mantiene</h2>
<p><strong>Se mantienen los cuatro días y los básicos.</strong> Sentadilla, banca, peso muerto y press militar siguen ahí. No hace falta dejar de hacerlos; lo que baja es cuánto te exigen.</p>
<p><strong>Baja el esfuerzo, no la técnica.</strong> La indicación del lunes es dejar 2-3 repeticiones en reserva; la del jueves, series técnicas y limpias. El peso muerto pasa a 4 × 3: pocas repeticiones y bien hechas.</p>
<p><strong>Se aprovecha para afinar.</strong> La banca del martes lleva pausa en el pecho. Con menos fatiga es buen momento para pulir la técnica.</p>
<p><strong>Llega con su porqué.</strong> El plan no baja la carga porque toque en el calendario, sino porque la semana anterior fue al límite. Si hubiera ido con margen, habría seguido subiendo.</p>
<h2>Cómo hacerla por tu cuenta</h2>
<ul>
<li>Mantén los ejercicios principales y tus días de entrenamiento.</li>
<li>Quita alguna serie por ejercicio (por ejemplo, de 4 a 3).</li>
<li>Termina cada serie con 2-3 repeticiones en reserva.</li>
<li>Después vuelve a tu semana normal, sin intentar recuperar lo «perdido».</li>
</ul>
""",
            "faq": [("¿Cada cuánto hay que hacer una descarga?", "No hay un número fijo. Muchos entrenadores la programan cada pocas semanas; otros esperan a ver señales de fatiga. 2trAIn la mete cuando tus sesiones lo piden."),
                    ("¿Pierdo fuerza o músculo por una semana de descarga?", "No. Una semana entrenando algo menos no basta para perder lo ganado, y lo normal es volver con mejores sensaciones."),
                    ("¿Descarga es lo mismo que descanso?", "No. En la descarga sigues entrenando, con menos volumen y menos esfuerzo; en el descanso no entrenas.")],
            "sources": [("Bell L. y col. (2023). Integrating deloading into strength and physique sports training programmes: an international Delphi consensus approach. Sports Medicine – Open.", PUBMED + "Bell+2023+integrating+deloading+strength+physique+Delphi+consensus")],
            "cta": ("¿Quieres que la descarga llegue cuando toca?", "2trAIn sube la carga cuando tus sesiones salen con margen y la baja cuando van al límite, y te explica cada cambio.", "/fuerza", "Ver cómo entrena la fuerza 2trAIn"),
        },
        "en": {
            "slug": "deload-week", "cat": "Strength",
            "title": "Deload week: what it is, when to do it and what a real one looks like",
            "seo": "Deload week for strength training: what, when and how · 2trAIn",
            "desc": "What a deload week is in strength training, the signs you need one and how to do it. With the real week 2trAIn generated after a week at the limit.",
            "lead": "Training less on purpose so you can perform better afterwards. It sounds odd, but the deload week is one of the most useful tools to keep making strength progress. Here's a real one.",
            "body": """
<h2>What a deload week is</h2>
<p>It's a short period, usually a week, where you train less than usual to recover and come back performing better. It's not a holiday: you still train, just with less total load.</p>
<p>Recent work with strength coaches (Bell et al.) describes it as a planned reduction in training demand. It's most often done every few weeks, for a few days, mainly by cutting volume (fewer sets) and effort (more reps in reserve) rather than the weight on the bar.</p>
<h2>Signs it's time</h2>
<ul>
<li>Sets that used to have reps to spare now take you to the limit.</li>
<li>Your weights stall or drop for several sessions in a row.</li>
<li>You sleep worse, struggle to get going or carry niggles.</li>
<li>You've been adding load for many weeks without a break.</li>
</ul>
<h2>A real deload week</h2>
<p>The week before, this powerlifting profile (woman, 27, 4 days) did everything, but at her limit: effort 9 out of 10 in every session. 2trAIn answered with this week:</p>
{{week}}
<h2>What changes and what stays</h2>
<p><strong>The four days and the main lifts stay.</strong> Squat, bench, deadlift and overhead press are all still there. No need to drop them; what comes down is how hard they push you.</p>
<p><strong>Effort drops, technique doesn't.</strong> Monday's cue is to leave 2-3 reps in reserve; Thursday's, clean technical sets. The deadlift goes to 4 × 3: few reps, done well.</p>
<p><strong>It's a chance to sharpen up.</strong> Tuesday's bench has a pause on the chest. With less fatigue, it's a good moment to polish technique.</p>
<p><strong>It comes with its why.</strong> The plan doesn't cut load because the calendar says so, but because the previous week was at the limit. Had it gone with room to spare, it would have kept going up.</p>
<h2>How to do one yourself</h2>
<ul>
<li>Keep your main lifts and your training days.</li>
<li>Drop a set per exercise (for example, from 4 to 3).</li>
<li>Finish every set with 2-3 reps in reserve.</li>
<li>Then go back to your normal week, without trying to make up for anything.</li>
</ul>
""",
            "faq": [("How often should I deload?", "There's no fixed number. Many coaches schedule one every few weeks; others wait for signs of fatigue. 2trAIn adds one when your sessions call for it."),
                    ("Will I lose strength or muscle in a deload week?", "No. One week of training a bit less isn't enough to lose what you've built, and you usually come back feeling better."),
                    ("Is a deload the same as rest?", "No. In a deload you keep training, with less volume and effort; when resting you don't train.")],
            "sources": [("Bell L. et al. (2023). Integrating deloading into strength and physique sports training programmes: an international Delphi consensus approach. Sports Medicine – Open.", PUBMED + "Bell+2023+integrating+deloading+strength+physique+Delphi+consensus")],
            "cta": ("Want deloads to land when they're due?", "2trAIn raises the load when your sessions have room to spare and lowers it when they're at the limit, and explains every change.", "/en/strength/", "See how 2trAIn trains strength"),
        },
    },
]

INDEX = {
    "es": {"title": "Blog de entrenamiento: planes reales, sesión a sesión · 2trAIn",
           "desc": "Guías de entrenamiento con semanas reales generadas por 2trAIn: HYROX, maratón y media, fuerza. Cada sesión dibujada y explicada.",
           "eyebrow": "Blog", "h1": 'Planes reales, <span class="accent">explicados.</span>',
           "lead": "Guías para entrenar mejor, con semanas que generó 2trAIn tal cual: sesión a sesión, con su porqué.",
           "read": "Leer", "min": "min de lectura", "crumb": "Blog"},
    "en": {"title": "Training blog: real plans, session by session · 2trAIn",
           "desc": "Training guides with real weeks generated by 2trAIn: HYROX, marathon and half, strength. Every session drawn and explained.",
           "eyebrow": "Blog", "h1": 'Real plans, <span class="accent">explained.</span>',
           "lead": "Guides to train better, with weeks 2trAIn generated as they came out: session by session, with their why.",
           "read": "Read", "min": "min read", "crumb": "Blog"},
}
UI = {
    "es": {"faq": "Preguntas frecuentes", "sources": "Fuentes", "related": "Sigue leyendo", "blog": "Blog",
           "months": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"], "cta_beta": "Unirme a la beta"},
    "en": {"faq": "FAQ", "sources": "Sources", "related": "Keep reading", "blog": "Blog",
           "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "cta_beta": "Join the beta"},
}
