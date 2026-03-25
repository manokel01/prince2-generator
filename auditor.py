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
    """Exports the JSON data into two clean Markdown files with timestamps."""
    # Ensure the exports directory exists
    Path("exports").mkdir(exist_ok=True)
    
    questions_md = f"# PRINCE2 Practitioner Mock Exam - Questions ({timestamp})\n\n"
    answers_md = f"# PRINCE2 Practitioner Mock Exam - Answers & Rationales ({timestamp})\n\n"

    for i, q in enumerate(data, 1):
        # 1. Clean the question text exactly like the TUI does
        q_text = q.get('question', '')
        q_text = q_text.replace("**", "")
        q_text = re.sub(r"(Statement|Item|Action) \d+:\s*[._\-\s]+(?=\n|$)", "", q_text)
        q_text = re.sub(r"(?<!^)\s*((Statement|Item|Action) \d+:)", r"\n\n\1", q_text)
        q_text = re.sub(r"\n{3,}", "\n\n", q_text).strip()

        # 2. Build Questions File
        questions_md += f"### Question {i}\n"
        questions_md += f"**Topic:** {q.get('topic', 'Unknown')}\n\n"
        questions_md += f"{q_text}\n\n"
        
        options = q.get('options', {})
        for key in sorted(options.keys()):
            questions_md += f"- **{key})** {options[key]}\n"
        questions_md += "\n---\n\n"

        # 3. Build Answers File
        correct_ans = q.get('answer', '')
        answers_md += f"### Question {i}\n"
        answers_md += f"**Correct Answer:** {correct_ans}\n\n"
        
        rationale = q.get('rationale', {})
        if isinstance(rationale, dict):
            answers_md += f"**Why Option {correct_ans} is correct:**\n{rationale.get('correct', '')}\n\n"
            answers_md += "**Why the other options are wrong:**\n"
            
            wrong_dict = rationale.get('wrong', {})
            for opt_key in sorted(wrong_dict.keys()):
                if opt_key != correct_ans and wrong_dict.get(opt_key, '').strip():
                    answers_md += f"- **Option {opt_key}:** {wrong_dict[opt_key]}\n"
            
            manual_ref = rationale.get('manual_reference', '')
            if manual_ref:
                answers_md += f"\n**Manual reference:** {manual_ref}\n"
        else:
            # Fallback just in case
            answers_md += f"{rationale}\n"
        
        answers_md += "\n---\n\n"

    # 4. Write to disk with timestamped filenames
    q_file = f"exports/questions_{timestamp}.md"
    a_file = f"exports/answers_{timestamp}.md"
    
    with open(q_file, "w", encoding="utf-8") as f:
        f.write(questions_md)
    with open(a_file, "w", encoding="utf-8") as f:
        f.write(answers_md)
        
    print(f"\n📄 Export Complete: '{q_file}' and '{a_file}' generated successfully.")


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
        
        # Auto-Sort by chronological PRINCE2 syllabus categories using the explicit category field
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

    # Print Distribution Summary
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

    # 3. Individual Question Detail Audit
    for i, q in enumerate(data):
        # V0.2 Strict Schema Keys
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

        ans = str(q.get('answer', '')).strip()
        if ans not in standard_keys:
            issues.append(f"Q{i+1}: Invalid answer '{ans}'.")

        q_text = q.get('question', '').strip()
        if q_text in unique_questions:
            issues.append(f"Q{i+1}: Duplicate question text detected.")
        unique_questions.add(q_text)

        # V0.2 Nested Rationale Audit
        rationale = q.get('rationale', {})
        if isinstance(rationale, dict):
            if 'correct' not in rationale or len(rationale.get('correct', '')) < 10:
                issues.append(f"Q{i+1}: Rationale missing or dangerously short 'correct' explanation.")
            
            wrong_dict = rationale.get('wrong', {})
            if not isinstance(wrong_dict, dict) or len(wrong_dict) < 3:
                issues.append(f"Q{i+1}: Rationale 'wrong' dictionary is malformed or missing distractors.")
        else:
            # Fallback check just in case the LLM output a flat string despite instructions
            if len(str(rationale)) < 50:
                issues.append(f"Q{i+1}: Flat rationale is dangerously short.")

    if repair and repaired_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\n✅ Repaired {repaired_count} structural/sequence issues and saved JSON.")

    if not issues:
        print("\n✅ 100% CONFIDENCE: Exam is sequenced, V0.2 schema-compliant, and proctor-ready.")
        
        # --- NEW: Snapshot and Export Logic ---
        Path("exams").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        snapshot_path = f"exams/exam_{ts}.json"
        
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        print(f"📦 Final exam snapshot saved to {snapshot_path}")
        export_to_markdown(data, ts)
        
    else:
        print(f"\n❌ AUDIT FAILED: Found {len(issues)} issues.")
        for issue in issues[:15]:
            print(f"  - {issue}")
        print("\n⚠️ Note: Markdown export and JSON snapshot skipped due to audit failures.")

if __name__ == "__main__":
    repair_mode = "--repair" in sys.argv
    audit_exam_data(repair=repair_mode)
