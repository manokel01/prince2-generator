# PRINCE2 7 Practitioner Exam Generation Specification

## Golden Dataset — Generation Rules, Trap Logic, Scenario Profiles, and Quality Standards

> **Role of this document:** This is an authoritative reference injected as RAG context at generation time. All rules herein are non-negotiable constraints on output quality. When this document conflicts with general LLM priors about exam design, this document wins.

---

## PART 1 — EXAM STRUCTURE: AUTHORITATIVE RULES

### 1.1 Total Composition

| Parameter | Value |
|---|---|
| Total marks / questions | 70 |
| Classic questions | ~60 (1 mark each) |
| Matching questions | ~10 (1 mark each via Combination format) |
| Pass mark | 60% = 42 correct marks |
| Time allowed | 150 minutes |
| Open book | Yes — official PRINCE2 7 manual only |

### 1.2 Question Type Definitions

**CLASSIC**

- Stem + 4 options (A, B, C, D)
- Exactly one option is correct
- All three wrong options (distractors) must be plausible management actions
- The reasoning structure `"Yes/No, because..."` is the required format for most classic questions.

**MATCHING — Implemented as Combination Multiple-Choice**

- *Note: While real exams score matching out of 3, this simulator requires 1-mark combination questions to maintain system parity.*
- One stem presents 3 labelled items (e.g., three actions, three statements).
- The four answer options (A–D) each provide a *different complete mapping* of all three items.
- Only one answer option contains the correct mapping for all three items.
- Worth 1 mark total (all-or-nothing per the combination format).
- **Matching stems belong strictly inside the Practices section.**
- **CRITICAL LOGIC RULE:** Exactly one option (A, B, C, or D) MUST contain the 100% correct mapping for all three items. You must verify that the correct mapping actually exists in the options provided. Furthermore, the 3 items must be mutually exclusive (e.g., do not blend "Probability" and "Impact" into a single item if they are meant to be mapped separately).

### 1.3 Section Distribution

The 70 questions are distributed across four sections in this exact ratio. The Kill Switch enforces this programmatically.

| Section | Questions | % |
|---|---|---|
| Principles | 7 | 10% |
| People | 6 | 9% |
| Practices | 36 | 51% |
| Processes | 21 | 30% |

---

## PART 2 — QUESTION CONSTRUCTION RULES

### 2.1 Bloom's Taxonomy Requirement

**ALL questions must operate at Bloom's Level 3 (Application) or Level 4 (Analysis). Level 1 (Recall) and Level 2 (Comprehension) questions are banned.**

- Banned: "What is the purpose of the Business Case?"
- Required: "Given *scenario/event*, which action should the Project Manager take and why?"

### 2.2 The Rigid PeopleCert Stem Structure

You MUST use one of the following exact, formulaic question stems for all classic Yes/No reasoning questions. You are STRICTLY FORBIDDEN from writing "natural" or conversational questions (e.g., "Should the project manager do X?"). You must explicitly name the syllabus element being tested in the stem.

**Approved Stem Templates:**
- "Is this an appropriate application of the '[Topic Name]' [principle/practice/activity], and why?"
- "How well does this apply the '[Topic Name]' [principle/element], and why?"
- "Which [principle/practice/process] is being applied by this action, and why?"

**Template Structure:**

[Scenario reference + specific situation]
[One of the Approved Stem Templates above]

A. [Yes / It applies it well], because [plausible but incorrect PRINCE2 reasoning]
B. [Yes / It applies it well], because [correct PRINCE2 reasoning]
C. [No / It applies it poorly], because [plausible but incorrect PRINCE2 reasoning]
D. [No / It applies it poorly], because [plausible but incorrect PRINCE2 reasoning]

### 2.3 Distractor Construction Rules

All distractors must:
1. **Be plausible management actions**
2. **Use correct PRINCE2 terminology**
3. **Contain exactly one flaw**: wrong conclusion, wrong reasoning, or right action in the wrong context.
4. **Never be obviously absurd.**
5. **STRICT SCENARIO RELEVANCE:** Every distractor must be directly relevant to the management problem described in the stem. You are STRICTLY FORBIDDEN from using "generic" distractors or recycling distractors that belong to other questions (e.g., if a question is about job-sharing the Project Executive role, do not use a distractor about combining the Project Manager and Project Executive roles).

### 2.4 Stem Construction Rules

- The stem must contain **at least one specific reference to the scenario**.
- **CRITICAL ACTION RULE:** The stem MUST describe a specific **decision or action** taken by a character. You are strictly forbidden from ending a stem with a passive situation (e.g., "A risk occurred. How well does this apply the principle?"). You must include the character's response (e.g., "A risk occurred, so the Project Manager decided to do X. How well does this action apply the principle?").
- The final sentence of the stem is the actual question.
- Never ask two questions in one stem.
- **NO DUPLICATION:** You must never test the exact same PRINCE2 concept twice in the same exam. Furthermore, you are FORBIDDEN from using the same scenario trigger (e.g., the discovery of archaeological artifacts) for more than one question. Every question must use a unique management problem or scenario event to ensure broad syllabus coverage.- **SCENARIO MANDATE:** Every single question MUST begin with a 2-3 sentence scenario paragraph establishing the context and the specific action taken. You must NEVER start a question directly with the stem (e.g., "Is this action appropriate...").
- **PERSPECTIVE ALIGNMENT:** The action being evaluated in the stem must belong to the role accountable for the specific Process being tested. For example, if testing 'Directing a Project', you must evaluate a Project Board action, not a Project Manager action.
- **RACI INTEGRITY MANDATE:** When describing a character taking an action (e.g., 'The Project Manager drafted the Quality Management Approach'), you MUST cross-reference the official PRINCE2 RACI tables for that Process. You are STRICTLY FORBIDDEN from assigning an 'Accountable' role (like the Executive) to perform a task that the manual assigns as 'Responsible' to a different role (like the Project Manager). If the Executive is involved, they should 'approve', 'decide', or 'be consulted', not 'convene', 'draft', or 'document'.

---

## PART 3 — THE HIDDEN STATE PRINCIPLE (Scenario Usage Rules)

The live exam scenario strips PRINCE2 titles from characters. Candidates must infer roles from business function. Your generated questions must replicate this.

**BANNED — explicitly naming PRINCE2 roles in question stems:**

- "The Senior User decides to..."
- "The Executive approves..."

**REQUIRED — using scenario-native language:**

- "The Operations Director decides to..."
- "*Character name from scenario* reviews..."

- **ENTITY & CHARACTER CONTINUITY MANDATE:**
  - You MUST ONLY use the specific job titles, character names, and company names (e.g., BuildyBrick, Louistown City Council) defined in the `<project_context>`. 
  - You are STRICTLY FORBIDDEN from inventing new company names (like 'BuildTech') or senior management titles (like 'Director of Finance'). 
  - If a role is not explicitly named, you must select the most logical predefined character (e.g., for user/business quality reviews, use the 'Heritage Director' or 'Chair, Louistown Business Association').  You MUST ONLY use the specific job titles and characters explicitly defined in the provided `<project_context>` scenario (e.g., Head of Regeneration, Portfolio Director, Contracts Director). You are STRICTLY FORBIDDEN from inventing new senior management titles (like 'Director of Finance' or 'Chief Executive') to act as project board members. If the scenario defines the 'Head of Regeneration' as having ultimate accountability, they are the Project Executive. Do not contradict the scenario.

---

## PART 4 — DYNAMIC SCENARIO PROFILING (THE CONSTRAINT HUNTER)

You will be provided with a specific project scenario inside the `<project_context>` tags. You MUST automatically analyze this text, extract its unique constraints, and weaponize them into Practitioner-level traps. 

You are STRICTLY FORBIDDEN from writing generic PRINCE2 questions. Every question must feel like it belongs exclusively to the active scenario.

**Mandatory Extraction & Weaponization Directives:**
1. **Identify the Project/Programme Boundary:** Scan the scenario for the overarching governance structure. If the scenario defines a Programme Board, a Portfolio Director, or an Investment Committee, you MUST build escalation traps that test whether the Project Board should handle a deviation or escalate it to these higher bodies based on the scenario's specific tolerance rules.
2. **Weaponize Local Procedures:** Scan the scenario for customized management approaches. 
   - *Example:* If the scenario mentions a "Unified Risk Register" or an "Automated Issue Form", you must use those specific tools in your distractors when testing the Risk or Issues practices.
   - *Example:* If the scenario mandates a "1-month stage limit" due to agile delivery, use that specific time constraint to test the 'Manage by Stages' principle.
3. **Weaponize Strategic Drivers:** Identify the core commercial or regulatory drivers. 
   - *Example:* If the scenario is driven by "public-sector sustainability," use carbon limits in your Business Case traps. 
   - *Example:* If the scenario is a "FinTech pivot to direct-to-consumer," use time-to-market pressure and consumer protection compliance as the triggers for your Quality and Scope change traps.
4. **Tone & Language Alignment:** Mirror the sector of the scenario. Bureaucratic and formal for public-sector; cutthroat, agile, and profit-driven for commercial tech.

---

## PART 5 — TRAP PATTERNS AND ANTI-PATTERNS

### 5.1 The Six Primary Trap Patterns

**Trap 1: Correct Statement, Wrong Answer.** The distractor contains a 100% accurate PRINCE2 statement that does not address what the question is asking. 
**Trap 2: Right Action, Wrong Stage/Process.** Correct action, but deployed at the wrong time. 
**Trap 3: Right Role, Wrong Responsibility.** Assumes the PM does something the Board should do. 
**Trap 4: Absolute Language.** Using "always" or "never" incorrectly in a tailorable method.
**Trap 5: RACI Verb Hallucination (AVOID THIS).** When testing roles and responsibilities, you MUST use the exact verbs from the PRINCE2 manual RACI tables. Do not substitute "Approve" if a role is only accountable to "Agree" or "Review". A question is flawed if the verb contradicts the manual.
**Trap 6: The Broken Premise (AVOID THIS).** - If a question stem asks "Which action triggers an exception?", you must not describe a scenario that is within tolerance. 
- **PHRASING MANDATE:** When describing deviations, you must reference the "target" or "plan," not the "tolerance." 
- **BANNED:** "The project manager forecast that the stage would overrun its tolerance by 3%." (This implies a breach).
- **REQUIRED:** "The project manager forecast that the stage would exceed its target completion time by 3%." (This clearly places the 3% deviation against the 20% tolerance limit).
**Trap 7: Assurance Hallucination (AVOID THIS).** Do not state that Project Board members cannot perform their own Project Assurance. They CAN. The restriction is that a board member cannot perform assurance for the *other* board interests (e.g., the Executive cannot perform User Assurance), and Assurance can NEVER be delegated to the Project Manager or Project Support.
**Trap 8: The Compound Action Fallacy (AVOID THIS).** If a scenario features a character performing two distinct actions (e.g., Approving a document AND conducting a review), and one action is RACI-correct but the other is RACI-incorrect, the correct 'No, because...' option MUST specifically isolate and target the incorrect action. It must not falsely claim the correct action was also wrong.
**Trap 9: Conflated Tolerances (AVOID THIS).** Do not mix up the six tolerance types. If a product is delivered late, that is a Time tolerance issue, NOT a Quality tolerance issue. Furthermore, failing a quality test does not immediately trigger an off-specification if it can be fixed within tolerances. The correct option must accurately reflect the specific tolerance being breached.
**Trap 10: Lazy RACI Formatting (AVOID THIS).** When testing RACI responsibilities, you must use plain role names ONLY (e.g., 'Project Manager', 'Project Executive'). You are STRICTLY FORBIDDEN from including raw RACI table codes, brackets, or superscripts (e.g., A¹, R³, C, I) in the question text or the options.
**Trap 11: The Unsolvable RACI Matrix (AVOID THIS).** When generating combination matching questions for RACI tables, you MUST ensure that a definitively correct option actually exists among A, B, C, and D. If you ask for the 'Accountable' role for a process where a single role (e.g., the Project Executive) holds all accountability, the correct option MUST list that role for all items. Do not provide options that make the question mathematically impossible to answer correctly based on the official manual.
**Trap 12: The Generic Entity Error (AVOID THIS).** Do not use generic industry names (e.g., 'The Contractor', 'The Tech Firm'). Use the specific entity name provided in the scenario (e.g., 'BuildyBrick').
**Trap 13: Role/Title Conflation in Matching (AVOID THIS).** Never combine a PRINCE2 role name and a scenario job title in the same option (e.g., "Project Executive (Head of Regeneration)"). 
- If the stem asks "Which *role* is responsible...", the options MUST use standard PRINCE2 role names ONLY (e.g., "Project Executive", "Senior User").
- If the stem asks "Which *individual* is appropriate...", the options MUST use scenario-specific job titles ONLY (e.g., "Head of Regeneration", "Sustainability Manager").
**Trap 14: The Compound Error (REQUIRED FOR 'NO' DISTRACTORS).** To prevent lazy or fabricated distractors, you must frequently use "Compound Errors" for your 'No' options. Rather than inventing a fake rule, take a factually correct PRINCE2 concept and misapply it.
- *Wrong Phase/Process:* Describe a correct action but place it in the wrong project phase (e.g., updating the benefits management approach during 'starting up a project').
- *Wrong RACI Accountability:* Correctly identify a management product or action but assign it to the wrong role (e.g., stating the Project Manager should authorise the stage instead of the Project Board).

### 5.2 Anti-Patterns — What NOT to Generate

- **Definition questions**
- **List completion** ("Which is NOT...")
- **Scenario-free stems**
- **Compound questions** ("Which TWO of the following...")

---

## PART 6 — JSON OUTPUT SCHEMA REMINDER

Each generated question must conform to this exact schema.

```json
{
  "id": "Q[nn]",
  "category": "[Principles|People|Practices|Processes]",
  "topic": "[specific principle/practice/process name]",
  "type": "[classic|matching]",
  "scenario_reference": "[character or event from scenario used in stem]",
  "question": "[question text]",
  "options": {
    "A": "[option text]",
    "B": "[option text]",
    "C": "[option text]",
    "D": "[option text]"
  },
  "answer": "[A|B|C|D]",
  "rationale": {
    "correct": "[why correct option is right]",
    "wrong": {
      "A": "[why wrong, if not correct]",
      "B": "[why wrong, if not correct]",
      "C": "[why wrong, if not correct]",
      "D": "[why wrong, if not correct]"
    },
    "manual_reference": "[section and page range]"
  },
  "bloom_level": "[3|4]",
  "difficulty": "[easy|medium|hard]"
}
