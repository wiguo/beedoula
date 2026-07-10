"""Golden evaluation set: the Task 1 questions with reference answers.

kind:
  corpus  - answerable from the guideline PDFs
  memory  - depends on the seeded baby profile / family notes
  web     - needs live web search (Tavily); references describe expected behavior
"""
from __future__ import annotations

GOLDEN_EXAMPLES: list[dict] = [
    {
        "question": "How much formula should a 6-month-old drink per feeding?",
        "reference": "Around 180-240 ml of formula per feeding, roughly 4-5 feedings per day at 6 months; exact amounts vary with the baby's appetite and whether solids have started.",
        "kind": "corpus",
    },
    {
        "question": "When can babies start eating solid foods?",
        "reference": "Complementary (solid) foods should start at about 6 months of age, alongside continued breastfeeding or formula. Signs of readiness include sitting with support, good head control, and interest in food.",
        "kind": "corpus",
    },
    {
        "question": "Is honey safe for a 10-month-old?",
        "reference": "No. Honey is not safe before 12 months of age because it can contain Clostridium botulinum spores that cause infant botulism. Avoid honey in all forms, including baked goods, until after the first birthday.",
        "kind": "corpus",
    },
    {
        "question": "My baby is 4 months old with a 38.2 C fever - what should I do?",
        "reference": "Contact the pediatrician promptly for a fever of 38.2 C in a 4-month-old. (In a baby under 3 months, any fever of 38 C or higher is an emergency.) Watch for warning signs like trouble breathing, poor feeding, unusual sleepiness, or rash, and seek emergency care if they appear.",
        "kind": "corpus",
    },
    {
        "question": "How should I put the baby down to sleep safely?",
        "reference": "Always place the baby on their back, on a firm flat sleep surface such as a safety-approved crib mattress with a fitted sheet, in their own sleep space. No blankets, pillows, bumpers, or soft toys in the crib. Keep the room a comfortable temperature and avoid overheating.",
        "kind": "corpus",
    },
    {
        "question": "How many naps does a 9-month-old typically take?",
        "reference": "Typically two naps per day (morning and afternoon) at 9 months, with total daytime sleep of roughly 2-3 hours; babies usually move to one nap between 12 and 18 months.",
        "kind": "corpus",
    },
    {
        "question": "What do I do if the baby is choking?",
        "reference": "For an infant under 1 year who cannot cough, cry, or breathe: give sets of 5 back blows between the shoulder blades followed by 5 chest thrusts, repeating until the object comes out or the baby becomes unresponsive. If unresponsive, call 911 and start infant CPR. Do not use abdominal thrusts on an infant.",
        "kind": "corpus",
    },
    {
        "question": "What foods are choking hazards for a 1-year-old?",
        "reference": "Common choking hazards include whole grapes, nuts and seeds, popcorn, hot dogs or sausage rounds, hard candy, chunks of raw hard vegetables or apple, spoonfuls of nut butter, and marshmallows. Food should be cut into small pieces no larger than about 1 cm.",
        "kind": "corpus",
    },
    {
        "question": "When should a baby be able to sit up on their own?",
        "reference": "Most babies sit without support at around 6 months (per CDC milestones, sitting without support is a 6-month milestone; some take until about 9 months). Talk to the pediatrician if the baby is not sitting with support by 9 months.",
        "kind": "corpus",
    },
    {
        "question": "Is it normal that my 8-month-old isn't crawling yet?",
        "reference": "Yes, usually. Crawling typically emerges between about 7 and 10 months, and some healthy babies skip crawling entirely. Discuss with the pediatrician if the baby also is not sitting without support or shows other missed milestones.",
        "kind": "corpus",
    },
    {
        "question": "How do I safely warm a bottle of breast milk?",
        "reference": "Warm the bottle by standing it in a bowl of warm water or holding it under warm running water, then swirl and test a few drops on your wrist. Never microwave breast milk or formula - it heats unevenly and creates hot spots that can burn the baby's mouth.",
        "kind": "corpus",
    },
    {
        "question": "How long can prepared formula sit out before it's unsafe?",
        "reference": "Prepared formula should be used within about 2 hours at room temperature, and within 1 hour once the baby has started drinking from the bottle; discard leftovers after that because bacteria multiply quickly.",
        "kind": "corpus",
    },
    {
        "question": "What's a good bedtime routine for a 1-year-old?",
        "reference": "A short, consistent, calming routine at the same time each night: for example bath, pajamas, brushing teeth, a book or song, then into the crib awake, on their back, in a sleep sack. Consistency matters more than the exact steps; avoid screens before bed.",
        "kind": "corpus",
    },
    {
        "question": "The baby has a diaper rash - what should I do?",
        "reference": "Change diapers frequently, gently clean and pat dry, give diaper-free air time, and apply a thick barrier cream such as zinc oxide at each change. Contact the pediatrician if the rash is severe, blistered, bleeding, spreading, or accompanied by fever, or if it does not improve in a few days.",
        "kind": "corpus",
    },
    {
        "question": "Does this baby have any food allergies I should know about?",
        "reference": "Yes - Mia is allergic to eggs (confirmed by an allergist). Avoid egg in all forms and check labels for egg ingredients such as albumin. No other known food allergies; peanut has been introduced without reaction.",
        "kind": "memory",
    },
    {
        "question": "What is the baby's usual nap schedule?",
        "reference": "Mia takes two naps a day, roughly 09:30-11:00 in the morning and 14:30-16:00 in the afternoon.",
        "kind": "memory",
    },
    {
        "question": "Have there been any recent baby formula recalls I should know about?",
        "reference": "The assistant should search the live web for current formula recall information and report any recent recalls with sources, or state clearly that no recent recalls were found in the search results.",
        "kind": "web",
    },
    {
        "question": "What's the current guidance on introducing peanut to babies?",
        "reference": "Current guidance recommends early introduction: peanut-containing foods (never whole peanuts) can be introduced around 4-6 months for high-risk infants after medical advice, and around 6 months for most infants, then kept in the diet regularly. Whole peanuts remain a choking hazard until at least age 4.",
        "kind": "web",
    },
    {
        "question": "Can a 15-month-old drink cow's milk?",
        "reference": "Yes. After 12 months, children can drink whole cow's milk as a main drink, typically around 350-500 ml per day; before 12 months cow's milk should not replace breast milk or formula.",
        "kind": "corpus",
    },
    {
        "question": "The baby fell off the couch and is crying - what should I check?",
        "reference": "Comfort the baby and check for warning signs: loss of consciousness, vomiting, unusual drowsiness or irritability, a bulging soft spot, unequal pupils, fluid from ears or nose, or a misshapen skull area. Call 911 or seek emergency care for any of these; otherwise watch closely for 24 hours and call the pediatrician - and per this family's house rules, call the parents right away after any fall.",
        "kind": "memory",
    },
]
