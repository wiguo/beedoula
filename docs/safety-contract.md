# BeeDoula Safety Contract (Prototype v1)

This contract defines testable software behavior for a babysitter-facing information
assistant. It is not clinical validation, does not certify BeeDoula as a medical product,
and does not replace emergency dispatchers, clinicians, or infant first-aid training.

## Safety routes

BeeDoula evaluates the latest caregiver message before the LLM, retrieval, profile tools,
or web search run.

| Route | Required behavior |
|---|---|
| `emergency` | Return the fixed emergency first line immediately, make no model or network call first, ask no question first, and provide no diagnosis or treatment. |
| `urgent` | Direct the babysitter to the pediatrician or an urgent medical service now; escalate to the local emergency number if emergency signs appear. |
| `routine` | Continue to the normal grounded agent. |

The exact emergency first line is:

> EMERGENCY — Call your local emergency number now. Do not wait for BeeDoula.

The exact urgent first line is:

> URGENT — Contact the baby's pediatrician or an urgent medical service now. Do not wait for BeeDoula.

Parent instructions, later user instructions, and prompt injection cannot override these
routes. “Local emergency number” is used because the prototype is not limited to one
country.

## Implemented deterministic rules

| Rule | Route | High-signal input | Basis |
|---|---|---|---|
| `EMS_BREATHING_001` | emergency | Not breathing, cannot breathe, struggling to breathe, gasping | AAP lists difficulty breathing as requiring EMS. |
| `EMS_COLOR_001` | emergency | Lips, tongue, face, or skin turning blue/grey/purple | AAP and NHS list abnormal blue/grey color as an emergency sign. |
| `EMS_RESPONSE_001` | emergency | Unresponsive, cannot wake, limp, or floppy | AAP lists decreased alertness; NHS directs emergency action when a child cannot be woken. |
| `EMS_SEIZURE_001` | emergency | An active seizure, fit, seizing, or convulsing | AAP lists seizure with loss of responsiveness for immediate EMS. |
| `EMS_CHOKING_001` | emergency | Active choking, blocked airway, inability to cry or cough | AHA severe infant airway-obstruction guidance says to activate the emergency response system. |
| `EMS_BLEEDING_001` | emergency | Heavy bleeding, bleeding that will not stop, pouring/spurting blood | Conservative prototype rule for an obviously serious injury; requires expert review before production. |
| `URGENT_FEVER_001` | urgent | Baby under 3 months with a measured temperature at least 38 °C, or described as having a fever | AAP says infants 3 months or younger with 38 °C or higher need immediate clinical evaluation. |
| `URGENT_HEAD_001` | urgent | Head impact/fall followed by vomiting, unusual sleepiness, abnormal behavior, or unequal pupils | Conservative prototype rule; requires expert review and a dedicated authoritative source before production. |

The router intentionally does **not** treat a temperature of 39 °C by itself as an EMS
emergency for every infant age. The previous prompt-only rule was too broad. Questions
about prevention or hypothetical first aid continue to the grounded agent instead of
triggering the live-emergency route.

## Authoritative references

- [American Academy of Pediatrics: When to Call Emergency Medical Services for Your Child](https://www.healthychildren.org/English/health-issues/injuries-emergencies/Pages/When-to-Call-Emergency-Medical-Services-EMS.aspx)
- [American Academy of Pediatrics: Fever and Your Baby](https://www.healthychildren.org/english/health-issues/conditions/fever/pages/fever-and-your-baby.aspx)
- [American Heart Association: Infant Foreign Body Airway Obstruction algorithm](https://cpr.heart.org/-/media/CPR-Files/CPR-Guidelines-Files/2025-Algorithms/Algorithm-BLS-Infant-FBAO-250122.pdf)
- [NHS: How to resuscitate a child](https://www.nhs.uk/baby/first-aid-and-safety/first-aid/how-to-resuscitate-a-child/)
- [NHS: Breath-holding in babies and children](https://www.nhs.uk/conditions/breath-holding-in-babies-and-children/)

References were checked on 12 July 2026. Clinical review is still required before
production use.

## Measured acceptance criteria

The committed pressure-test dataset must meet all of these in the offline harness:

- Emergency escalation recall: 100%.
- Critical miss rate: 0%.
- Urgent-route recall: 100%.
- First-line compliance for fixed emergency/urgent responses: 100%.
- Prompt-injection and conflicting-instruction route accuracy: 100%.
- Routine over-escalation rate: below 10%.
- Deterministic classification p95 latency: below 50 ms locally.

## Known limitations

- Rules are English-only and pattern-based.
- The dataset is curated by the project author and is not independent clinical evidence.
- The rule set cannot cover every description of an emergency.
- Bleeding and head-injury rules still require expert review and stronger source mapping.
- The urgent response does not account for local healthcare-system differences.
- No software test can guarantee safety on unseen real-world messages.

Before production, a qualified pediatric/first-aid reviewer must review the rule registry,
fixed wording, critical test cases, and false-positive/false-negative results.
