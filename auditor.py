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
    
    questions_md = f"# PRINCE2 Practitioner Question Paper ({timestamp})\n\n"
    answers_md = f"# PRINCE2 Practitioner Answer & Rationale Key ({timestamp})\n\n"

    for i, q in enumerate(data, 1):
        # Clean question text of artifacts
        q_text = q.get('question', '').replace("**", "").strip()
        q_text = re.sub(r"(Statement|Item|Action) \d+:\s*[._\-\s]+(?=\n|$)", "", q_text)
        q_text = re.sub(r"(?<!^)\s*((Statement|Item|Action) \d+:)", r"\n\n\1", q_text)
        q_text = re.sub(r"\n{3,}", "\n\n", q_text).strip()

        # 1. QUESTION PAPER (Clean for Tablet Use - No Spoilers)
        questions_md += f"### Question {i}\n\n{q_text}\n\n"
        options = q.get('options', {})
        for key in sorted(options.keys()):
            questions_md += f"- **{key})** {options[key]}\n"
        questions_md += "\n---\n\n"

        # 2. ANSWER KEY (Detailed for Post-Exam Review)
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

    # 3. ADD SYLLABUS TALLY
    answers_md += "## Performance Tally (Syllabus Breakdown)\n"
    answers_md += "Use this table to identify which chapters you need to re-read in the manual.\n\n"
    answers_md += "| Category | Questions | Your Score |\n|---|---|---|\n"
    answers_md += "| **Principles** | 1–7 | /7 |\n"
    answers_md += "| **People** | 8–13 | /6 |\n"
    answers_md += "| **Practices** | 14–49 | /36 |\n"
    answers_md += "| **Processes** | 50–70 | /21 |\n"

    with open(f"exports/questions_{timestamp}.md", "w") as f: f.write(questions_md)
    with open(f"exports/answers_{timestamp}.md", "w") as f: f.write(answers_md)
    
    print(f"\n📄 Tablet-ready Question Paper and Answer Key generated in 'exports/'.")

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

    total_q = len(data)
    issues = []
    repaired_count = 0
    unique_questions = set()

    print(f"--- Starting Audit of {total_q} Questions ---")
    
    if repair:
        print("[Mode] Repair enabled. Sorting chronological sequence and fixing structural issues...")
        original_order = [q.get('topic') for q in data]
        data.sort(key=lambda q: get_cat_id(q.get('category', '')))
        new_order = [q.get('topic') for q in data]
        
        if original_order != new_order:
            repaired_count += 1
            print("[Repair] Chronological sequence auto-sorted based on 'category' field.")

    # 1. Global Count Check
    if len(data) != 70:
        issues.append(f"Global: Exam has {len(data)} questions instead of exactly 70.")
        if repair and len(data) > 70:
            data = data[:70]
            repaired_count += 1
            print("[Repair] Truncated dataset to exactly 70 questions.")

    # 2. Sequence & Topic Audit
    topic_counts = Counter()
    sequence_errors = 0

    print("\n--- Sequence Integrity Audit ---")
    for i, q in enumerate(data):
        cat_name = q.get('category', 'Unknown')
        topic_counts[cat_name] += 1

        expected_cat = "Unknown"
        if 0 <= i < 7: expected_cat = "Intro/Principles"
        elif 7 <= i < 13: expected_cat = "People"
        elif 13 <= i < 49: expected_cat = "Practices"
        elif 49 <= i < 70: expected_cat = "Processes"

        if cat_name != expected_cat:
            sequence_errors += 1
            issues.append(f"Sequence: Q{i+1} has category '{cat_name}', but index {i+1} is reserved for {expected_cat}.")

    target_dist = {"Intro/Principles": 7, "People": 6, "Practices": 36, "Processes": 21}
    for category, target in target_dist.items():
        actual = topic_counts[category]
        status = "✅" if actual == target else "❌"
        print(f"  {status} {category}: {actual}/{target}")
    
    if topic_counts["Unknown"] > 0:
        print(f"  ⚠️ Unknown Categories: {topic_counts['Unknown']} questions have unrecognizable category labels.")

    if sequence_errors > 0:
        print(f"  ❌ Sequence: Found {sequence_errors} questions pushing past their chronological boundaries.")
    else:
        print("  ✅ Sequence: Chronological order is correct.")

    # --- LOAD SCENARIO BLACKLIST ONCE ---
    blacklist_path = Path("data/target_scenario/active_blacklist.json")
    prohibited_names = []
    if blacklist_path.exists():
        try:
            with open(blacklist_path, "r", encoding="utf-8") as bf:
                # Pre-convert to lowercase for fast matching
                prohibited_names = [name.lower() for name in json.load(bf)]
        except Exception as e:
            print(f"  ⚠️ Warning: Could not load active_blacklist.json: {e}")

    # 3. Individual Question Detail Audit
    for i, q in enumerate(data):
        required_keys = ['id', 'category', 'topic', 'type', 'scenario_reference', 'question', 'options', 'answer', 'rationale', 'bloom_level', 'difficulty']
        if not all(k in q for k in required_keys):
            missing = [k for k in required_keys if k not in q]
            issues.append(f"Q{i+1}: Missing structural keys: {missing}")
            continue

        topic = q.get('topic', '')
        category = q.get('category', '')
        if not topic.startswith(f"{category} - "):
            issues.append(f"Q{i+1}: Topic prefix mismatch. Expected '{category} - ', found '{topic}'")

        options = q.get('options', {})
        standard_keys = {'A', 'B', 'C', 'D'}
        current_keys = set(options.keys())
        
        if current_keys != standard_keys:
            if repair and current_keys.issuperset(standard_keys):
                for k in list(current_keys - standard_keys):
                    del q['options'][k]
                repaired_count += 1
            else:
                issues.append(f"Q{i+1}: Invalid options ({sorted(list(current_keys))})")

        # --- NEW GUARDRAIL: Trap 10 (RACI Codes) ---
        for opt_key, opt_text in options.items():
            # Matches pattern like A¹, R³, (A), (A/R)
            if re.search(r'\([ARCI]\)|\b[ARCI][¹²³⁴⁵]\b|\(A/R\)', str(opt_text)):
                issues.append(f"Q{i+1}: Option {opt_key} contains prohibited RACI matrix codes (Trap 10).")

        ans = str(q.get('answer', '')).strip()
        if ans not in standard_keys:
            issues.append(f"Q{i+1}: Invalid answer '{ans}'.")

        q_text = str(q.get('question', '')).strip()
        if q_text in unique_questions:
            issues.append(f"Q{i+1}: Duplicate question text detected.")
        unique_questions.add(q_text)

        # --- NEW GUARDRAIL: Entity Name Safety Sweep (Trap 12) ---
        if prohibited_names:
            q_text_lower = q_text.lower()
            for name in prohibited_names:
                if name in q_text_lower or any(name in str(opt).lower() for opt in options.values()):
                    issues.append(f"Q{i+1}: Hallucinated entity/role detected: '{name}' (Violates Continuity Mandate).")

# --- NEW GUARDRAIL: Rigid Stem Structure (Rule 2.2) ---
        q_type = q.get('type', 'classic').lower()
        if q_type == 'classic':
            # Check if it's a Yes/No/Because question by looking at the options
            is_yes_no = any(str(opt).startswith("Yes,") or str(opt).startswith("No,") or 
                            str(opt).startswith("It applies it well,") or str(opt).startswith("It applies it poorly,") 
                            for opt in options.values())
            
            if is_yes_no and not re.search(r'and why\?$', q_text.lower().strip()):
                issues.append(f"Q{i+1}: Stem violates Rigid Structure (Rule 2.2). Classic Yes/No questions MUST end with ', and why?'.")

        # --- NEW GUARDRAIL: Passive Ending Check (NotebookLM Fix) ---
        # A valid practitioner question must evaluate a hard action.
        action_verbs = ['decided', 'approved', 'authorized', 'rejected', 'escalated', 'submitted', 'created', 'updated', 'instructed', 'closed', 'accepted']
        if not any(verb in q_text.lower() for verb in action_verbs):
            issues.append(f"Q{i+1}: Stem lacks a definitive management action verb. Ends too passively.")

        # --- NEW GUARDRAIL: Yes/No Logic Contradiction Check (NotebookLM Fix) ---
        # Prevents options from saying "Yes" but providing a reason why the action was bad.
        for opt_key, opt_text in options.items():
            opt_lower = str(opt_text).lower()
            if opt_lower.startswith("yes, because") and any(phrase in opt_lower for phrase in ["should always", "must instead", "failed to"]):
                issues.append(f"Q{i+1}: Option {opt_key} contains a logical contradiction ('Yes' followed by negative rationale).")

        # V0.2 Nested Rationale Audit
        rationale = q.get('rationale', {})
        if isinstance(rationale, dict):
            if 'correct' not in rationale or len(rationale.get('correct', '')) < 10:
                issues.append(f"Q{i+1}: Rationale missing or dangerously short 'correct' explanation.")
            
            wrong_dict = rationale.get('wrong', {})
            if not isinstance(wrong_dict, dict) or len(wrong_dict) < 3:
                issues.append(f"Q{i+1}: Rationale 'wrong' dictionary is malformed or missing distractors.")
        else:
            if len(str(rationale)) < 50:
                issues.append(f"Q{i+1}: Flat rationale is dangerously short.")

    if repair and repaired_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\n✅ Repaired {repaired_count} structural/sequence issues and saved JSON.")

    if not issues:
        print("\n✅ 100% CONFIDENCE: Exam is sequenced, V0.2 schema-compliant, and proctor-ready.")
        
        Path("exams").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        snapshot_path = f"exams/exam_{ts}.json"
        
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        print(f"📦 Final exam snapshot saved to {snapshot_path}")
        export_to_markdown(data, ts)
        
    else:
        print(f"\n❌ AUDIT FAILED: Found {len(issues)} issues.")
        for issue in issues[:20]:
            print(f"  - {issue}")
        print("\n⚠️ Note: Markdown export and JSON snapshot skipped due to audit failures.")

if __name__ == "__main__":
    repair_mode = "--repair" in sys.argv
    audit_exam_data(repair=repair_mode)
