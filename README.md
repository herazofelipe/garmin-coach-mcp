# garmin-coach-mcp

A remote MCP server that connects Claude (or any MCP client) to **your own** Garmin Connect
account: activities, splits, HR and power zones, aerobic decoupling, HRV against your own
normal range, sleep, stress, readiness, training status, gear, personal records, session weather, skin temperature and
menstrual-cycle context for planning training — and it can create,
schedule and delete running, strength and swim workouts on your watch.

It runs in the cloud, so it also works from the Claude mobile app.

![Session analysis](docs/screenshot-2.png)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/herazofelipe/garmin-coach-mcp)

> **Español:** instrucciones al final.

**Prefer a guided setup?** The [Garmin Connect MCP Setup](https://agensi.io/skills/garmin-connect-mcp-setup-deploy-connect-verify) skill walks your agent
through deploying, connecting and verifying this server, and fixes the usual errors.

**Want coach-grade analysis on top of the data?** The
[Garmin Run Coach](https://agensi.io/skills/garmin-run-coach-decoupling-real-weather-workouts) skill on Agensi teaches your agent to
use these tools well: decoupling on the steady block, weather-corrected heart rate, readiness
calls and workouts that upload cleanly.

**Both together:** the [Garmin AI Running Kit: Setup & Coach](https://agensi.io/bundles/garmin-ai-running-kit-setup-coach)
bundle includes the two skills for $8 instead of $10.

## How it stays private

- **Everyone deploys their own copy.** Your Garmin credentials live only in *your* Render
  account's environment variables. This repo contains no credentials and no personal data.
- **The connector URL is the key.** Render generates a random `MCP_SECRET`; the endpoint is
  `https://<your-service>.onrender.com/mcp/<secret>`. Without it, the server answers nothing
  but `/health`. The server refuses to start in the cloud without a secret.
- **Nothing is sent anywhere else**, except Open-Meteo (coordinates and time only) when you
  ask for session weather.

## Setup (about 10 minutes)

1. **Deploy.** Click *Deploy to Render* (free account). Render asks for:
   - `GARMIN_EMAIL`, `GARMIN_PASSWORD` — your Garmin Connect login. Works directly if your
     account has no two-factor authentication (MFA).
   - `GARMIN_TOKENS` — leave empty, unless your account uses MFA (see below).
   - `LOCAL_TZ_OFFSET_HOURS` — your offset from UTC (e.g. `-5`, `-6`, `1`).
   - `MCP_SECRET` is generated for you.
2. **Get your connector URL.** When the deploy is *Live*, open the service's **Logs**: the
   server prints `Conector MCP: https://<tu-servicio>.onrender.com/mcp/...`. Replace
   `<tu-servicio>` with your service's address (shown at the top of the Render page).
   Keep this URL private.
3. **Add it to Claude.** claude.ai (web) → Settings → Connectors → *Add custom connector* →
   paste the URL. It then works in the web, desktop and mobile apps. Test with
   *"check my Garmin connection"*.
4. **Keep it awake (recommended).** Render's free plan sleeps after 15 minutes without traffic.
   Create a free [UptimeRobot](https://uptimerobot.com) HTTP(s) monitor on
   `https://<your-service>.onrender.com/health` every 5 minutes. Use only `/health` there,
   never the URL with your secret. One always-on service fits Render's 750 free hours a month.

**Accounts with MFA:** run `garmin_login.py` on your computer, or open
`garmin_login_colab.ipynb` in Google Colab from your phone. Paste the printed value into
`GARMIN_TOKENS` in Render. Treat it like a password.

## Tools (45)

| Group | Tools |
|---|---|
| Activities | list, by date, last, full analysis (summary, laps, workout blocks, zones in minutes, optional weather; compact, ~5-10 KB), compare, progress summary, personal records |
| Derived metrics | aerobic decoupling Pa:HR / Pw:HR on the active block, cardiac drift, HR recovery, HR curve |
| HRV analysis | `garmin_hrv_analysis`: 7-day HRV baseline against your 60-day normal range, resting HR, HR-normalized HRV, day-to-day variation and a parasympathetic-saturation check, with a pattern and today's intensity |
| Daily physiology | morning check, HRV (+detail), sleep, stress, Body Battery events, daily summary, altitude vitals, body composition, hydration |
| Cycle & skin temperature | nightly skin-temperature deviation with biphasic shift detection, Garmin menstrual-cycle day/phase, `garmin_cycle_insights` (phase, ovulation and fertile-window estimates, evidence-based training considerations) |
| Trends | `garmin_get_trend` for HRV, sleep, resting HR, stress, VO2max, SpO2, respiration, skin temperature, Body Battery, intensity minutes, hill and endurance score, up to 3 years (long ranges are split into chunks and merged; daily up to 62 days, weekly up to 400, monthly beyond); readiness range up to 366 days |
| Intraday | heart rate and stress for a time window |
| Status | training status (load, ACWR, load balance, acclimation, race predictions), calibration (LTHR, threshold pace/power, VO2max, the runner's 5 Garmin HR zones) |
| Strength & swim | session detail, exercise search and validation |
| Writing | create running/strength/swim workouts, inspect, delete, calendar, schedule/unschedule, gear, set activity gear |

**Session weather** (`include_weather=true` in the activity analysis): Garmin uses its nearest
weather station, which can be tens of km away. The server also queries Open-Meteo at the run's
GPS point for the hours nearest start and end, and warns when Garmin's station is > 15 km away.

**HRV analysis.** `garmin_hrv_analysis` reads the last 66 nights and compares your 7-day HRV
baseline (ln rMSSD) with your own normal range (60-day mean ± 0.5 SD), together with resting HR,
HR-normalized HRV and day-to-day variation. It returns a pattern (stable, accumulated fatigue,
major stressor, saturation or fatigue, abnormally high HRV...) and today's intensity. It is
built for any runner: every number is compared with the runner's own data, never with
population values. HRV is used mainly to hold back (a high value is not a green light), and
how the runner feels overrides the data. Methods and sources: [REFERENCES.md](REFERENCES.md).

**Cycle and skin temperature.** Skin temperature needs a watch with Garmin's Elevate Gen 5
sensor (fēnix 7 Pro/8, epix Pro, Venu 3/4, Venu X1, Forerunner 570/970); the Forerunner 965/265
don't have it. Cycle data needs cycle tracking turned on in Garmin Connect. The server reads
both, detects the post-ovulation temperature shift (3-over-6 rule) and returns training
considerations with references (symptoms first, heat tolerance and HRV in the luteal phase). The
morning check and the calibration add a short cycle block only when the account tracks it.
Ovulation and fertile-window outputs are wellness estimates: **not a medical device and not a
contraceptive method.** Sexual-activity entries and free-text notes are never returned.

Tool descriptions are in Spanish; Claude answers in your language anyway. What each
calculation is based on is in [REFERENCES.md](REFERENCES.md).

## Updating

Your copy does **not** update by itself when this repo changes.

1. **Get the new code.** In Render, open your service → **Manual Deploy** → **Deploy latest
   commit**. Wait until it shows *Live*. Fixes and improvements to existing tools work right
   away, with nothing to change in Claude.
2. **Refresh Claude only when tools are added or changed.** Claude keeps the list of tools and
   their parameters it saw when you connected. If a release adds tools or parameters
   ([commits](https://github.com/herazofelipe/garmin-coach-mcp/commits/main)), go to claude.ai
   (web) → Settings → Connectors, update the Garmin connector's tool list, and open a new chat.
   Only if the new tools still don't show, remove the connector and add it again with the
   same URL.

Your URL, credentials and secret stay the same across updates.

## Important

- **Unofficial access.** This uses [`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect),
  which talks to Garmin Connect the way the website does. It is not affiliated with or endorsed
  by Garmin, and Garmin can change or block it at any time. Use it with your own account only.
  Garmin also offers an official [Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-faq/)
  (read-only, your own data).
- **Not a medical device.** Heart-rate metrics are training indicators, not clinical measurements.
- **Exercise catalog.** Strength exercise names are validated against a catalog generated at
  build time from Garmin's official `garmin-fit-sdk` package (FIT Protocol License). It is not
  included in this repo.
- **Open-Meteo** is free for non-commercial use; personal analysis of your own runs fits that.

## Run locally

```bash
pip install -r requirements.txt "garmin-fit-sdk>=21,<22"
python build_exercise_catalog.py
export GARMIN_EMAIL="..." GARMIN_PASSWORD="..."      # or GARMIN_TOKENS
HOST=127.0.0.1 PORT=8000 python garmin_mcp_server.py # MCP at http://127.0.0.1:8000/mcp
```

## License

MIT for the code in this repo. See `LICENSE`.

---

## Español

Servidor MCP para conectar Claude con **tu propia** cuenta de Garmin Connect. Cada persona
despliega su copia; tus credenciales quedan solo en tu cuenta de Render. Si prefieres una instalación
guiada, está el skill [Garmin Connect MCP Setup](https://agensi.io/skills/garmin-connect-mcp-setup-deploy-connect-verify). Para análisis de
entrenador sobre estos datos, existe el skill
[Garmin Run Coach](https://agensi.io/skills/garmin-run-coach-decoupling-real-weather-workouts) en Agensi. Los dos juntos
cuestan $8 en lugar de $10 en el pack
[Garmin AI Running Kit: Setup & Coach](https://agensi.io/bundles/garmin-ai-running-kit-setup-coach).

1. Pulsa **Deploy to Render**. Escribe tu correo y contraseña de Garmin (cuentas sin
   verificación en dos pasos) y tu desfase horario (Bogotá/Lima `-5`, Ciudad de México `-6`).
   El secreto `MCP_SECRET` se genera solo.
2. Cuando diga *Live*, abre **Logs** y copia la línea `Conector MCP: ...`. Cambia
   `<tu-servicio>` por la dirección de tu servicio. Esa URL es tu llave: no la compartas.
3. En claude.ai (web) → Ajustes → Conectores → *Agregar conector personalizado* → pega la URL.
4. Opcional: un monitor gratis de UptimeRobot a `.../health` cada 5 minutos para que no se duerma.

Incluye análisis de VFC frente a tu propio rango normal (`garmin_hrv_analysis`: línea base de 7
días frente a 60 días, FC en reposo, VFC normalizada y variación día a día, con la intensidad
recomendada para hoy), temperatura de la piel (relojes con sensor Elevate Gen 5; no el Forerunner 965/265) y
ciclo menstrual (si está activado en Garmin Connect) para organizar entrenamientos por fase y
síntomas. Las estimaciones de ovulación y ventana fértil son orientativas: no es un dispositivo
médico ni un método anticonceptivo. Las referencias de cada cálculo están en
[REFERENCES.md](REFERENCES.md).

Si tu cuenta usa verificación en dos pasos, genera `GARMIN_TOKENS` con
`garmin_login_colab.ipynb` (Google Colab, funciona desde el celular).

**Actualizar.** Tu copia no se actualiza sola cuando cambia este repositorio.

1. En Render: tu servicio → **Manual Deploy** → **Deploy latest commit**, y espera a que diga
   *Live*. Las mejoras de las herramientas que ya tenías funcionan de inmediato.
2. Solo si la versión agrega herramientas o parámetros nuevos: en claude.ai (web) → Ajustes →
   Conectores, actualiza la lista de herramientas del conector de Garmin y abre un chat nuevo.
   Únicamente si aun así no aparecen, quítalo y agrégalo otra vez con la misma URL.

La URL, las credenciales y el secreto no cambian al actualizar.
