# References

What each computed output is based on. Garmin's own values (readiness, training status,
VO2max, HRV status, sleep score...) are passed through as Garmin reports them; the list below
covers what this server **calculates or interprets** itself.

None of this is a medical device. Wrist optical sensors have error against ECG; use trends
against your own data, not absolute values or comparisons with other people.

## HRV analysis — `garmin_hrv_analysis`

| Output | Method | Sources |
|---|---|---|
| Baseline | 7-day mean of ln rMSSD (Garmin nightly HRV), at least 3 nights | Plews 2012, 2013; Bellenger 2023 (AIS) |
| Normal range | mean of the last 60 days ± 0.5 SD (provisional under 42 nights, none under 21) | Vesterinen 2016 (mean ± 0.5 SD); Bellenger 2023 (60 days, SWC = 0.5 × CV); Altini (60-day normal range) |
| Decision | intensity only when the baseline is inside the range; low intensity or rest when it falls below; resume when it returns | Kiviniemi 2007; Vesterinen 2016; Javaloyes 2019 |
| Resting HR | same baseline/range logic | Buchheit 2014; Altini |
| Normalized HRV | ln rMSSD / mean RR (s), RR derived from Garmin's daily resting HR | Buchheit 2014; Plews 2017; Bulte 2025 |
| Day-to-day variation | 7-day CV of ln rMSSD against its own 60-day values (± 1 SD; no published consensus threshold) | Plews 2012; Altini |
| Parasympathetic saturation | low HRV with low HR and a weak (< 0.2) ln rMSSD–RR correlation over 2 or 6 weeks: flagged as possible, decided by context | Plews 2013, 2017; Buchheit 2014 |
| Patterns | HRV × resting HR × ratio matrix; HRV moderately above range with low HR = coping well, above mean + 1 SD with low HR = abnormally high (possible functional overreaching) | Buchheit 2014 (Table 2); Le Meur 2013 |
| Starting a loading block | a stable, in-range or rising baseline is a good moment; higher baseline vagal activity is associated with larger aerobic gains | Hautala 2003; Altini |
| Subjective override | how the runner feels overrides the data when they disagree | Alfonso 2025; Altini |
| Data quality note | nocturnal wrist HRV vs ECG | Dial 2025 |

- Kiviniemi AM et al. Endurance training guided individually by daily heart rate variability measurements. Eur J Appl Physiol 2007;101:743-51. [doi:10.1007/s00421-007-0552-2](https://doi.org/10.1007/s00421-007-0552-2)
- Plews DJ et al. Heart rate variability in elite triathletes, is variation in variability the key to effective training? Eur J Appl Physiol 2012;112:3729-41. [doi:10.1007/s00421-012-2354-4](https://doi.org/10.1007/s00421-012-2354-4)
- Plews DJ et al. Training adaptation and heart rate variability in elite endurance athletes. Sports Med 2013;43:773-81. [doi:10.1007/s40279-013-0071-8](https://doi.org/10.1007/s40279-013-0071-8)
- Hautala AJ et al. Cardiovascular autonomic function correlates with the response to aerobic training in healthy sedentary subjects. Am J Physiol Heart Circ Physiol 2003;285:H1747-52. [doi:10.1152/ajpheart.00202.2003](https://doi.org/10.1152/ajpheart.00202.2003)
- Le Meur Y et al. Evidence of parasympathetic hyperactivity in functionally overreached athletes. Med Sci Sports Exerc 2013;45:2061-71. [doi:10.1249/MSS.0b013e3182980125](https://doi.org/10.1249/MSS.0b013e3182980125)
- Buchheit M. Monitoring training status with HR measures: do all roads lead to Rome? Front Physiol 2014;5:73. [doi:10.3389/fphys.2014.00073](https://doi.org/10.3389/fphys.2014.00073)
- Vesterinen V et al. Individual endurance training prescription with heart rate variability. Med Sci Sports Exerc 2016;48:1347-54. [doi:10.1249/MSS.0000000000000910](https://doi.org/10.1249/MSS.0000000000000910)
- Plews DJ et al. Day-to-day heart-rate variability recordings in world-champion rowers. Int J Sports Physiol Perform 2017;12:697-703. [doi:10.1123/ijspp.2016-0343](https://doi.org/10.1123/ijspp.2016-0343)
- Javaloyes A et al. Training prescription guided by heart-rate variability in cycling. Int J Sports Physiol Perform 2019;14:23-32. [doi:10.1123/ijspp.2018-0122](https://doi.org/10.1123/ijspp.2018-0122)
- Bellenger C, Siegel R, Stanley J, McGibbon K. Best practice guidelines: measurement, analysis and interpretation of resting heart rate and heart rate variability in athletes. Australian Institute of Sport, 2023. [PDF](https://www.ais.gov.au/__data/assets/pdf_file/0013/1130260/HRV-BPG_FINAL.pdf)
- Bulte KR et al. Use of heart-rate variability to examine readiness to perform in response to overload and taper in swimmers. Int J Sports Physiol Perform 2025;20:918-24. [doi:10.1123/ijspp.2024-0362](https://doi.org/10.1123/ijspp.2024-0362)
- Alfonso C et al. Individual training prescribed by heart rate variability, heart rate and well-being scores in experienced cyclists. Sci Rep 2025;15:34023. [doi:10.1038/s41598-025-13540-z](https://doi.org/10.1038/s41598-025-13540-z)
- Dial MB et al. Validation of nocturnal resting heart rate and heart rate variability in consumer wearables. Physiol Rep 2025;13:e70527. [doi:10.14814/phy2.70527](https://doi.org/10.14814/phy2.70527)
- Altini M. HRV4Training newsletter: normal range, normalized HRV, coefficient of variation, parasympathetic saturation. [hrv4training.substack.com](https://hrv4training.substack.com)

## Aerobic decoupling, cardiac drift, HR recovery — `garmin_get_activity_dynamics`

| Output | Method |
|---|---|
| Pa:HR / Pw:HR decoupling | efficiency factor (speed or power / HR) of the second half of the active block vs the first half, in %; warm-up and cool-down excluded |
| Cardiac drift | mean HR, second half minus first half of the active block (bpm) |
| HR recovery | HR drop from the last 10 s of the final active block to 60 s later (window 50-70 s), anchored to absolute timestamps; "not measurable" when anchoring fails |

These follow the common coaching definitions (Friel, *The Triathlete's Training Bible*; Allen &
Coggan, *Training and Racing with a Power Meter*). HR recovery after exercise as a marker of
parasympathetic reactivation: Buchheit 2014 (above).

## Session weather — `garmin_get_activity_analysis(include_weather=true)`

Open-Meteo hourly data at the run's start point (rounded to ~1 km), at the hours nearest start
and end: temperature, relative humidity, dew point, apparent temperature, 10 m wind.
[open-meteo.com](https://open-meteo.com) (forecast API for the last 5 days, ERA5-based archive
for older sessions). Garmin's station distance is computed with the haversine formula.

## Menstrual cycle and skin temperature — `garmin_cycle_insights`, `garmin_get_skin_temperature`

| Output | Method | Sources |
|---|---|---|
| Temperature shift | 3 nights above the highest of the previous 6, the third ≥ 0.2 °C over it, within 4 days; ovulation ≈ the day before the first high night | Shilaih 2018 |
| Fertile window | 6 days ending on the estimated ovulation day | Wilcox 1995 |
| Calendar estimate | mean cycle length of up to 6 past cycles; luteal phase 14 days by default, personalized from past shifts | Wilcox 1995 |
| Training considerations | no periodization by calendar phase; symptoms first; luteal heat and HRV | McNulty 2020; Colenso-Semple 2023; Giersch 2020; Schmalenberger 2020 |

- McNulty KL et al. Sports Med 2020;50:1813-27. [doi:10.1007/s40279-020-01319-3](https://doi.org/10.1007/s40279-020-01319-3)
- Colenso-Semple LM et al. Front Sports Act Living 2023;5:1054542. [doi:10.3389/fspor.2023.1054542](https://doi.org/10.3389/fspor.2023.1054542)
- Giersch GEW et al. J Sci Med Sport 2020;23:1134-40. [doi:10.1016/j.jsams.2020.05.014](https://doi.org/10.1016/j.jsams.2020.05.014)
- Schmalenberger KM et al. J Clin Med 2020;9:617. [doi:10.3390/jcm9030617](https://doi.org/10.3390/jcm9030617)
- Shilaih M et al. Biosci Rep 2018;38:BSR20171279. [doi:10.1042/BSR20171279](https://doi.org/10.1042/BSR20171279)
- Wilcox AJ et al. N Engl J Med 1995;333:1517-21. [doi:10.1056/NEJM199512073332301](https://doi.org/10.1056/NEJM199512073332301)

Wellness estimates only: **not a medical device and not a contraceptive method.**

## Data access

[python-garminconnect](https://github.com/cyberjunky/python-garminconnect) (unofficial; Garmin
may change or block it). Not affiliated with Garmin.
