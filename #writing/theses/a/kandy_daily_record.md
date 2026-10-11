### A daily record at Kandy, and a held-out sensor {#s-kandy-daily-record}

Two further tests use Kandy data that played no part in building the field. Both are exploratory.

**The national research organisation's daily record.** Nirmani and colleagues published daily
PM2.5 for the organisation's Kandy station for 2021 and 2022 as a figure, from data they obtained on
request [@Nirmani2025]. The daily values were recovered by digitising that figure: the axes were
calibrated from the figure's own gridlines and the two years' lines separated by colour. Days
hidden behind other plotted symbols are lost, leaving {{claim:nbrod.digit.2021.days}} days in 2021
and {{claim:nbrod.digit.2022.days}} in 2022. As a check, the digitised annual means differ from the
published annual means by {{claim:nbrod.digit.2021.diff_pct}} and
{{claim:nbrod.digit.2022.diff_pct}} per cent. The record is compared with the delivered field at the
station's cell over {{claim:nbrod.days}} matched days.

{{tbl:T3_nbro_daily}}

Three results follow. The **seasonal shape** is supported: across the twelve calendar months the
model and the record correlate at {{claim:nbrod.climatology_r}}, and within 2021 at
{{claim:nbrod.monthly_r_2021}}. The **year 2022 is missed**: within that year the monthly
correlation is {{claim:nbrod.monthly_r_2022}}. The field is too high from January to April, during
the national economic crisis, fuel shortages and power cuts, and too low from September to December,
when the published record shows high values at several stations across the island. Neither event is
represented in the model's inputs. The **day-to-day sequence** is weak: once each month's mean is
removed, the daily correlation is {{claim:nbrod.anomaly_daily_r}}. Over all days the model's daily
correlation, {{claim:nbrod.all.model_cell.r}}, is below that of the record's own monthly
climatology, {{claim:nbrod.all.monthly_climatology_benchmark.r}}, a benchmark that flatters itself
because it is computed from the record being scored.

The split by whether the city's two low-cost sensors were reporting reproduces, at Kandy, the
pattern found on the ladder ({{ref:s-kandy-model-rung}}). On the {{claim:nbrod.sensors_reported.model_cell.n}}
days when they reported, the daily correlation is {{claim:nbrod.sensors_reported.model_cell.r}}. On the
{{claim:nbrod.sensors_absent.model_cell.n}} days when they did not, it is
{{claim:nbrod.sensors_absent.model_cell.r}}. Most of Kandy's record falls in the second case.

**A sensor the model never saw.** The temporal anchor was retrained on one of the two Kandy sensors
and scored on the other, with every predictor that identifies the site removed and with the held-out
sensor's own level withheld. The two records share only a few weeks, so the test is close to a
held-out period as well as a held-out site. On the held-out sensor the hourly correlation is
{{claim:loso.akurana.hourly.pred.r}} and {{claim:loso.hantana.hourly.pred.r}} in the two directions,
against {{claim:loso.akurana.hourly.prior_only.r}} and {{claim:loso.hantana.hourly.prior_only.r}}
for the composition prior alone. The daily correlation is {{claim:loso.akurana.daily.pred.r}} and
{{claim:loso.hantana.daily.pred.r}} (prior alone {{claim:loso.akurana.daily.prior_only.r}} and
{{claim:loso.hantana.daily.prior_only.r}}), and the mean daily cycle correlates at
{{claim:loso.akurana.diurnal_r}} and {{claim:loso.hantana.diurnal_r}}. The learned correction
therefore roughly doubles the skill of the prior at a site it was not trained on. Both sensors are
low-cost units with the same calibration, so this tests transfer between two points, not agreement
with a reference instrument.
