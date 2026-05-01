# Schema design — node types and edges per subject

The bio app uses 16 node types tuned for biology. Other subjects need different types. Here's how to choose.

## The universal core (always include)

These 8 types apply to almost any educational subject. Always include them:

| Type | What it captures | Example |
|---|---|---|
| `chapter` | A unit of source material (chapter, lecture, module) | "Chapter 9 — Meiosis" |
| `exam_topic` | A study-guide bullet, learning objective, or test target | "Describe the steps of meiosis I" |
| `concept` | A broad idea | "Central dogma" |
| `term` | A vocabulary term | "Allele", "Mitosis" |
| `principle` | A law, rule, theorem, or stated principle | "Mendel's law of segregation" |
| `person` | A named individual | "Gregor Mendel" |
| `comparison` | An explicit X vs Y discussion | "Mitosis vs. meiosis" |
| `source` | A raw source file (mostly for citation links) | The chapter PPTX |

## Domain-specific extensions

Add 3–8 of these depending on the subject. Pick types that match what's actually in the source material — if you don't see a single instance of a type in chapter 1, you probably don't need it.

### Biology / life sciences
- `process` — meiosis, transcription, translation, glycolysis
- `structure` — chromosome, ribosome, organelle
- `molecule` — DNA, mRNA, glucose, ATP
- `enzyme` — DNA polymerase, helicase, ATP synthase
- `inheritance_pattern` — autosomal recessive, codominance, X-linked
- `experiment` — Mendel's pea cross, Hershey-Chase, Meselson-Stahl
- `disease` — sickle cell, cystic fibrosis, Huntington's
- `technique` — PCR, gel electrophoresis, CRISPR

### Mathematics
- `theorem` — Pythagorean theorem, fundamental theorem of calculus
- `formula` / `equation` — quadratic formula, integration by parts
- `proof` — proof of derivative power rule
- `function` — sine, cosine, exponential
- `definition` — limit, continuity, derivative
- `example` — worked example problems

### Chemistry
- `element` — carbon, oxygen, sodium
- `compound` — H₂O, NaCl, glucose
- `reaction` — combustion, neutralization, redox
- `mechanism` — SN1, SN2, electrophilic addition
- `principle` (already universal) — Le Chatelier's, Hund's rule

### Physics
- `law` — Newton's laws, conservation of energy
- `equation` — F=ma, E=mc²
- `phenomenon` — gravity, refraction, interference
- `particle` — electron, photon, quark
- `experiment` — double-slit, Michelson-Morley

### History / political science
- `event` — French Revolution, Battle of Hastings, Civil Rights Act
- `era` — Renaissance, Cold War, Industrial Revolution
- `place` — Constantinople, Berlin Wall
- `document` — Magna Carta, Declaration of Independence
- `treaty` — Treaty of Versailles
- `policy` — New Deal, Truman Doctrine

### Programming / CS
- `algorithm` — quicksort, Dijkstra's, gradient descent
- `data_structure` — array, hash map, B-tree
- `pattern` — observer, factory, MVC
- `language_feature` — closures, generics, async
- `tool` — git, Docker, npm
- `complexity` — O(n log n), polynomial-time class

### Law / regulation
- `case` — Marbury v. Madison, Roe v. Wade
- `statute` — Sherman Act, GDPR
- `doctrine` — strict liability, fair use
- `jurisdiction` — federal, state, EU
- `procedure` — discovery, motion to dismiss

### Medicine / clinical
- `condition` — diabetes mellitus, MI, sepsis
- `symptom` — fever, hyperglycemia
- `medication` — metformin, lisinopril
- `procedure` — appendectomy, intubation
- `pathophysiology` — beta-cell destruction
- `assessment` — APGAR, Glasgow Coma Scale

### Languages
- `vocabulary` — words and phrases (use type=`term` for these)
- `grammar_rule` — verb conjugation, passive voice
- `tense` — preterite, subjunctive
- `idiom` — culturally specific phrases
- `dialogue` — example exchange

### Business / finance
- `concept` (universal) — supply, demand, opportunity cost
- `model` — DCF, CAPM, Porter's Five Forces
- `metric` — EBITDA, NPV, ROIC
- `case_study` — Enron, GameStop, ARM IPO
- `regulation` — Sarbanes-Oxley, MiFID II

## Edge relations

Most subjects use the same universal edge set. The default 27-relation enum from `tools/build_kg.py` works for almost everything:

```
part_of, consists_of, produces, produced_by, catalyzes, catalyzed_by,
precedes, follows, pairs_with, complement_of, transcribes_to,
translates_to, compared_to, discovered_by, demonstrates,
demonstrated_by, causes, caused_by, regulates, regulated_by,
located_in, mentioned_in, example_of, instance_of, inherits_as,
requires, contradicts, supersedes, cites, related_to, covers
```

Some are clearly biology-leaning (`catalyzes`, `transcribes_to`). They cause no harm if unused — they're just never emitted. You can prune them or leave them.

For a math/CS skew, you might add: `proves`, `proven_by`, `solves`, `applied_in`, `generalizes`, `specializes`.

For history, you might add: `preceded_by`, `succeeded_by`, `signed_at`, `participants`, `caused_by`.

## How to choose for a new subject

1. **Read 1–2 sample chapters carefully.**
2. **Make a list** of every kind of "thing" the material talks about — the ontology.
3. **Cluster** similar things into types. If you have <3 examples of a type, merge it into another. If you have >50 of one type, consider splitting it.
4. **Sanity-check** with the sources — does every important thing have exactly one type?
5. **Show the user** the proposed list and get sign-off before authoring 200+ pages.

Avoid premature generalization. Pick the types your specific source material actually demands; you can always add types later by editing `tools/build_kg.py`'s `NODE_TYPES` constant and `kg/schema/node.base.schema.json`'s enum, then re-running `tools/build_kg.py`.

## Examples of what fits where

| Subject | Universal | Domain-specific (4–8) | Total types |
|---|---|---|---|
| Biology Bio 1320 | 8 | process, structure, molecule, enzyme, inheritance_pattern, experiment, disease, technique | 16 |
| Calc II | 8 | theorem, formula, function, definition, example, proof | 14 |
| AP US History | 8 | event, era, place, document, treaty, policy | 14 |
| Algorithms 101 | 8 | algorithm, data_structure, pattern, complexity, language_feature | 13 |
| MCAT chem | 8 | element, compound, reaction, mechanism, experiment, technique | 14 |
| Bar exam (Crim Law) | 8 | case, statute, doctrine, procedure, element_of_crime | 13 |

A typical study tutor uses **12–18 node types**. Less than 10 is usually too coarse; more than 20 is usually too fragmented.
