import json
import sys
import re
from datetime import datetime
from pathlib import Path
from collections import Counter

def get_cat_id(cat_name):
    """Maps category names to chronological IDs for sorting."""
    mapping = {
        "Intro/Principles": 0,
        "People": 1,
        "Practices": 2,
        "Processes": 3
    }
    return mapping.get(cat_name, 4)

def export_to_markdown(data, timestamp):
    """Exports the JSON data into a clean Question Paper and a detailed Answer Key."""
    Path("exports").mkdir(exist_ok=True)
    Path("exports/answers").mkdir(exist_ok=True, parents=True)
    
    questions_md = f"# PRINCE2 Practitioner Question Paper ({timestamp})\n\n"
    answers_md = f"# PRINCE2 Practitioner Answer & Rationale Key ({timestamp})\n\n"

    for i, q in enumerate(data, 1):
        q_text = q.get('question', '').replace("**", "").strip()
        q_text = re.sub(r"(Statement|Item|Action) \d+:\s*[._\-\s]+(?=\n|$)", "", q_text)
        q_text = re.sub(r"(?<!^)\s*((Statement|Item|Action) \d+:)", r"\n\n\1", q_text)
        q_text = re.sub(r"\n{3,}", "\n\n", q_text).strip()

        questions_md += f"### Question {i}\n\n{q_text}\n\n"
        options = q.get('options', {})
        for key in sorted(options.keys()):
            questions_md += f"- **{key})** {options[key]}\n"
        questions_md += "\n---\n\n"

        correct_ans = q.get('answer', '')
        answers_md += f"### Question {i}\n"
        answers_md += f"**Topic Area:** {q.get('topic', 'Unknown')}\n" 
        answers_md += f"**Correct Answer:** {correct_ans}\n\n"
        
        rationale = q.get('rationale', {})
        if isinstance(rationale, dict):
            answers_md += f"**Why Option {correct_ans} is correct:**\n{rationale.get('correct', '')}\n\n"
            answers_md += "**Why the other options are wrong:**\n"
            for opt_key in sorted(rationale.get('wrong', {}).keys()):
                if opt_key != correct_ans:
                    answers_md += f"- **Option {opt_key}:** {rationale['wrong'].get(opt_key, '')}\n"
            
            if rationale.get('manual_reference'):
                answers_md += f"\n**Manual reference:** {rationale['manual_reference']}\n"
        
        answers_md += "\n---\n\n"

    answers_md += "## Performance Tally (Syllabus Breakdown)\n"
    answers_md += "| Category | Questions | Your Score |\n|---|---|---|\n"
    answers_md += "| **Principles** | 1–7 | /7 |\n"
    answers_md += "| **People** | 8–13 | /6 |\n"
    answers_md += "| **Practices** | 14–49 | /36 |\n"
    answers_md += "| **Processes** | 50–70 | /21 |\n"

    with open(f"exports/questions_{timestamp}.md", "w") as f: f.write(questions_md)
    with open(f"exports/answers/answers_{timestamp}.md", "w") as f: f.write(answers_md)
    print(f"\n📄 Question Paper generated in 'exports/' and Answer Key in 'exports/answers/'.")

def audit_exam_data(repair=False):
    file_path = Path("exam_data.json")
    if not file_path.exists():
        print("[!] Error: exam_data.json not found.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[!] Critical: JSON is malformed. {e}")
        return

    issues = []
    repaired_count = 0
    unique_questions = set()

    print(f"--- Starting Audit of {len(data)} Questions ---")
    
    if repair:
        data.sort(key=lambda q: get_cat_id(q.get('category', '')))

    # 1. Global Count Check
    if len(data) != 70:
        issues.append(f"Global: Exam has {len(data)} questions instead of 70.")
        if repair and len(data) > 70: data = data[:70]

    # --- NEW GUARDRAIL: Semantic Redundancy Check ---
    scenario_keywords = ["groupthink", "external risk adviser", "hard disk", "logotype", "compliance officer"]
    scenario_tally = Counter()

    for i, q in enumerate(data):
        ref = q.get('scenario_reference', '').lower()
        for kw in scenario_keywords:
            if kw in ref:
                scenario_tally[kw] += 1
                if scenario_tally[kw] > 1:
                    issues.append(f"Q{i+1}: Redundancy Warning! Scenario anchor '{kw}' used {scenario_tally[kw]} times.")

    # 2. Individual Question Detail Audit
    for i, q in enumerate(data):
        q_id = f"Q{i+1}"
        ans = str(q.get('answer', '')).strip()
        rationale = q.get('rationale', {})
        options = q.get('options', {})

        # --- SELF-CORRECTION HOOK: Rationale Letter Mismatch ---
        if isinstance(rationale, dict) and 'correct' in rationale:
            correct_text = rationale['correct']
            match = re.search(r"Option ([A-D]) is correct", correct_text, re.IGNORECASE)
            if match:
                found_letter = match.group(1).upper()
                if found_letter != ans:
                    issues.append(f"{q_id}: Rationale Header Mismatch (Key is {ans}, Rationale says {found_letter})")
                    if repair:
                        new_text = re.sub(r"Option [A-D] is correct", f"Option {ans} is correct", correct_text, flags=re.IGNORECASE)
                        q['rationale']['correct'] = new_text
                        repaired_count += 1
                        print(f"  [Repair] Fixed Rationale Letter Drift for {q_id}")

        # --- LOGIC POLARITY CHECK ---
        if isinstance(rationale, dict) and 'correct' in rationale:
            correct_text = rationale['correct'].lower()
            if ans in ['A', 'B'] and (correct_text.startswith('no') or 'incorrect' in correct_text[:20]):
                issues.append(f"{q_id}: Logic Polarity Warning! Answer is '{ans}' (Yes), but rationale text indicates 'No'.")
            if ans in ['C', 'D'] and (correct_text.startswith('yes') or 'correct' in correct_text[:20]):
                if "is correct" not in correct_text[:25]:
                     issues.append(f"{q_id}: Logic Polarity Warning! Answer is '{ans}' (No), but rationale text indicates 'Yes'.")

        # 3. Standard Guardrails
        signpost_pattern = re.compile(r'\b(however|obviously|because of this)\b', re.IGNORECASE)
        for opt_key, opt_text in options.items():
            if signpost_pattern.search(str(opt_text)):
                issues.append(f"{q_id}: Option {opt_key} contains a banned transition word (Rule 6).")

        q_text = str(q.get('question', '')).strip()
        if q_text in unique_questions: issues.append(f"{q_id}: Duplicate question detected.")
        unique_questions.add(q_text)

    if repair and repaired_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\n✅ Repaired {repaired_count} structural issues.")

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    snapshot_path = f"exams/exam_{ts}.json"
    with open(snapshot_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

    if not issues:
        print("\n✅ 100% CONFIDENCE: Exam is proctor-ready.")
    else:
        print(f"\n❌ AUDIT FOUND {len(issues)} ISSUES:")
        for issue in issues[:30]: print(f"  - {issue}")

    export_to_markdown(data, ts)

if __name__ == "__main__":
    repair_mode = "--repair" in sys.argv
    audit_exam_data(repair=repair_mode)
