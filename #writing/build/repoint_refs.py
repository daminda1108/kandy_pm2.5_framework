"""Repoint chapter-level {{ref:}} tokens to the specific section each one means.

A reference to a whole old chapter lands, in a thesis that split that chapter, on only the part
it kept. Each occurrence below was read in context (2026-09-18) and assigned the section it
actually refers to. Keyed by (file, occurrence index of that label in the file) so a repeated
label in one file is repointed individually. Occurrences not listed keep the chapter label,
which was judged correct in context.

Usage: python repoint_refs.py <mapping-name>
"""
import os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

MAPS = {
 "validation": ("ch-validation-without-local-ground", {
    ("pool/ch01_weather_and_air/04-s-aim-approach.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch01_weather_and_air/04-s-aim-approach.md", 1): "s-summary-established-results",
    ("pool/ch02_why_not_kandy/02-s-existing-measurement-record.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch02_why_not_kandy/03-s-health-policy-stakes.md", 0): "s-exposure-weighting",
    ("pool/ch02_why_not_kandy/04-s-question-ministry-actually-asks.md", 0): "s-recommendation-inverts-tropics",
    ("pool/ch03_what_is_known/01-s-two-decades-measurement.md", 1): "s-checks-kandy-carry-weight",
    ("pool/ch03_what_is_known/03-s-capabilities-limits-modelling.md", 0): "s-dependence-estimator",
    ("pool/ch03_what_is_known/04-s-position-literature-claims-novelty.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch04_what_there_was/02-s-data-streams-their-uses.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch04_what_there_was/03-s-borrowed-panel.md", 0): "s-borrowed-ground-truth",
    ("pool/ch04_what_there_was/03-s-borrowed-panel.md", 1): "s-summary-established-results",
    ("pool/ch04_what_there_was/04-s-data-requested-but-obtained.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch04_what_there_was/06-s-construction-follows.md", 1): "s-marginal-predictive-value-each",
    ("pool/ch05_what_failed/07-s-defects-found-audit-rather.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch05_what_failed/09-s-pattern-across-eight.md", 0): "s-pre-registration-working-practice",
    ("pool/ch06_the_model/00-ch-model.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch06_the_model/03-s-information-budget.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch06_the_model/03-s-information-budget.md", 1): "s-dependence-estimator",
    ("pool/ch06_the_model/04-s-guarantees-enforced-mechanisms-discharged.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch09_what_next/00-ch-measure-next.md", 0): "s-marginal-predictive-value-each",
    ("pool/ch09_what_next/01-s-measurement-priority-ordering.md", 0): "s-checks-kandy-carry-weight",
    ("pool/front/acknowledgements.md", 0): "s-checks-kandy-carry-weight",
 }),
 "stops": ("ch-model-stops", {
    ("pool/ch03_what_is_known/03-s-capabilities-limits-modelling.md", 2): "s-six-negative-results-their",
    ("pool/ch03_what_is_known/03-s-capabilities-limits-modelling.md", 3): "s-six-negative-results-their",
    ("pool/ch06_the_model/07-s-excluded-processes-known-limits.md", 0): "s-six-negative-results-their",
    ("pool/ch09_what_next/03-s-construction-step-most-worth.md", 0): "s-spatial-contrast-lost",
    ("pool/ch09_what_next/04-s-implications-radius-result.md", 0): "s-reason-change-support",
    ("pool/ch09_what_next/04-s-implications-radius-result.md", 1): "s-reason-change-support",
    ("theses/a/discussion.md", 0): "s-reason-change-support",
 }),
 "next": ("ch-measure-next", {
    ("pool/ch04_what_there_was/02-s-data-streams-their-uses.md", 0): "s-implications-radius-result",
    ("pool/ch04_what_there_was/04-s-data-requested-but-obtained.md", 0): "s-measurement-priority-ordering",
    ("pool/ch06_the_model/01-s-decomposition-conserves.md", 0): "s-construction-step-most-worth",
    ("pool/ch06_the_model/06-s-partition-constraint-rather-than.md", 0): "s-measurement-would-settle-most",
    ("pool/ch07_making_sure/01-s-borrowed-ground-truth.md", 0): "s-measurement-priority-ordering",
    ("pool/ch07_making_sure/01-s-borrowed-ground-truth.md", 1): "s-measurement-would-settle-most",
    ("pool/ch07_making_sure/02-s-marginal-predictive-value-each.md", 0): "s-measurement-would-settle-most",
    ("pool/ch07_making_sure/03-s-recommendation-inverts-tropics.md", 0): "s-measurement-would-settle-most",
    ("pool/ch07_making_sure/10-s-independent-chemical-check.md", 0): "s-measurement-would-settle-most",
    ("pool/ch08_where_it_stops/04-s-spatial-contrast-lost.md", 0): "s-construction-step-most-worth",
    ("pool/ch08_where_it_stops/06-s-reason-change-support.md", 0): "s-implications-radius-result",
    ("pool/ch08_where_it_stops/08-s-spatial-results-support.md", 0): "s-construction-step-most-worth",
    ("theses/a/aims.md", 0): "s-measurement-priority-ordering",
 }),
 "model": ("ch-model", {
    ("pool/ch02_why_not_kandy/03-s-health-policy-stakes.md", 1): "s-partition-constraint-rather-than",
    ("pool/ch03_what_is_known/04-s-position-literature-claims-novelty.md", 0): "s-information-budget",
    ("pool/ch05_what_failed/00-ch-eight-approaches-did-work.md", 1): "s-information-budget",
    ("pool/ch05_what_failed/02-s-rigid-physical-form-fitted.md", 0): "s-guarantees-enforced-mechanisms-discharged",
    ("pool/ch05_what_failed/04-s-fine-tuning-two-sensors.md", 0): "s-admissibility-asserted-code",
    ("pool/ch05_what_failed/06-s-five-reconstructions-regional-background.md", 1): "s-partition-constraint-rather-than",
    ("pool/ch10_software/05-s-admissibility-asserted-code.md", 0): "s-information-budget",
 }),
 "data": ("ch-available-data-deliberate-constraint", {
    ("pool/ch07_making_sure/01-s-borrowed-ground-truth.md", 0): "s-borrowed-panel",
 }),
 "prior": ("ch-prior-measurement-gap-leaves", {
    ("pool/ch05_what_failed/05-s-five-attempts-find-spatial.md", 0): "s-two-decades-measurement",
    ("pool/ch08_where_it_stops/01-s-observation-sets-problem.md", 0): "s-two-decades-measurement",
    ("pool/ch08_where_it_stops/06-s-reason-change-support.md", 0): "s-two-decades-measurement",
 }),
}

def main():
    label, table = MAPS[sys.argv[1]]
    pat = re.compile(r"\{\{ref:%s\}\}" % re.escape(label))
    done = 0
    for (rel, _), _ in sorted(table.items()):
        pass
    files = sorted({rel for rel, _ in table})
    for rel in files:
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        k = -1
        def sub(m):
            nonlocal k, done
            k += 1
            new = table.get((rel, k))
            if new:
                done += 1
                return "{{ref:%s}}" % new
            return m.group(0)
        t = pat.sub(sub, s)
        if t != s:
            tmp = p.with_suffix(".md.tmp"); tmp.write_text(t, encoding="utf-8", newline="\n"); os.replace(tmp, p)
    print(f"repointed {done} of {len(table)} listed")
    return 0 if done == len(table) else 1

if __name__ == "__main__":
    sys.exit(main())
