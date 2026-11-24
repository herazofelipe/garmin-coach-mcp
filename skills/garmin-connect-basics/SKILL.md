---
name: garmin-connect-basics
description: "Use the garmin-coach-mcp tools correctly: analyze runs on the active block, read HRV and readiness against the runner's own range, read long trends, and create, move or delete Garmin workouts without duplicates. Use for any Garmin Connect data or workout task on this server."
---

# Garmin Connect basics (garmin-coach-mcp)

How to use this server's tools well. Answer in the user's language. Heart-rate, HRV and cycle
outputs are training indicators: **not a medical device**. For chest pain, fainting,
palpitations at rest or anything that sounds medical, tell the user to see a clinician.

## Analyze a run

- `garmin_get_activity_analysis` gives the summary, laps, typed workout blocks and minutes per
  zone. Add `include_weather=true` for Open-Meteo weather at the run's GPS point; if Garmin's
  station is more than 15 km away, trust the Open-Meteo values.
- `garmin_get_activity_dynamics` gives Pa:HR / Pw:HR decoupling, cardiac drift and 60 s HR
  recovery, computed on the active block only. Decoupling is only meaningful for continuous
  steady runs; for intervals, say it is not interpretable.
- Hot, humid conditions raise HR at the same pace: check the weather before calling a high HR
  a fitness drop.

## Readiness

- `garmin_morning_check` for the day's snapshot; `garmin_hrv_analysis` before a quality
  session or when planning the week.
- Decide on the 7-day HRV baseline against the runner's own normal range, never on one night
  or on population values. HRV mainly holds back: a high value is not a green light.
- How the runner feels overrides the data. Ask about it only before quality sessions.

## Trends

Use `garmin_get_trend` for any multi-day series (HRV, resting HR, sleep, stress, VO2max,
Body Battery...) instead of calling a daily tool many times. It reaches up to 3 years.

## Plans and workouts

- Before planning, ask whether a race is coming (date, distance, goal, terrain).
- Before creating any workout, call `garmin_get_training_calibration` and set every target
  from the runner's current lactate threshold, VO2max and their 5 Garmin HR zones
  (`hr_zones`), never from memory or age formulas.
- Workout names: 30 characters or fewer. Strength: find exact names with
  `garmin_search_exercises`; unilateral exercises need one step per side.
- To move a session: `garmin_unschedule_workout` + `garmin_schedule_workout`, do not recreate
  it. To fix one: confirm with the user, delete the old one, create the new one.
- **Always confirm with the user before deleting anything.** Never delete activities.

## Menstrual cycle

If the user tracks her cycle, `garmin_cycle_insights` gives the phase and training
considerations: adjust by symptoms and individual response, not by calendar phase. Ovulation
and fertile-window outputs are estimates: never present them as contraception or a diagnosis.

## The full coaching method

The complete method (readiness decision flow, race and weekly plans by experience level,
workout structure, metric thresholds, with references) is the **Garmin Run Coach** skill:
https://agensi.io/skills/garmin-run-coach-decoupling-real-weather-workouts
