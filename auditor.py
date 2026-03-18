import json
import sys
from pathlib import Path
from collections import Counter

def get_cat(topic_str):
    t = topic_str.lower()
    # Syllabus 1.0 (Intro/Principles)
    if any(m in t for m in ["intro", "principle", "overview", "context"]): 
        return 0, "Intro/Principles"
    # Syllabus 2.0 (People)
    elif any(m in t for m in ["people", "stakeholder", "culture", "communication", "leadership"]): 
        return 1, "People"
    # Syllabus 3.0 (Practices)
    elif any(m in t for m in ["practice", "prac", "business case", "organizing", "plan", "quality", "risk", "issue", "progress"]): 
        return 2, "Practices"
    # Syllabus 4.0 (Processes)
    elif any(m in t for m in ["process", "proc", "starting up", "directing", "initiating", "controlling", "managing product", "stage boundary", "closing", "delivery"]): 
        return 3, "Processes"
    return 4, "Unknown"

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
        
        # Auto-Sort by chronological PRINCE2 syllabus categories
        original_order = [q.get('topic') for q in data]
        data.sort(key=lambda q: get_cat(q.get('topic', ''))[0])
        new_order = [q.get('topic') for q in data]
        
        if original_order != new_order:
            repaired_count += 1
            print("[Repair] Chronological sequence auto-sorted.")

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
        topic = q.get('topic', '')
        cat_id, cat_name = get_cat(topic)
        topic_counts[cat_name] += 1

        # Expected layout based on exact official 70 question split (Syllabus Page 10)
        expected_cat = "Unknown"
        if 0 <= i < 7: expected_cat = "Intro/Principles"
        elif 7 <= i < 13: expected_cat = "People"
        elif 13 <= i < 49: expected_cat = "Practices"
        elif 49 <= i < 70: expected_cat = "Processes"

        if cat_name != expected_cat and cat_name != "Unknown":
            sequence_errors += 1
            issues.append(f"Sequence: Q{i+1} is '{topic}' ({cat_name}), but index {i+1} is reserved for {expected_cat}.")

    # Print Distribution Summary (Updated to official Syllabus weights)
    target_dist = {"Intro/Principles": 7, "People": 6, "Practices": 36, "Processes": 21}
    for category, target in target_dist.items():
        actual = topic_counts[category]
        status = "✅" if actual == target else "❌"
        print(f"  {status} {category}: {actual}/{target}")
    
    if topic_counts["Unknown"] > 0:
        print(f"  ⚠️ Unknown Topics: {topic_counts['Unknown']} questions have unrecognizable topic names.")

    if sequence_errors > 0:
        print(f"  ❌ Sequence: Found {sequence_errors} questions pushing past their chronological boundaries.")
    else:
        print("  ✅ Sequence: Chronological order is correct.")

    # 3. Individual Question Detail Audit
    for i, q in enumerate(data):
        required_keys = ['topic', 'question', 'options', 'answer', 'rationale']
        if not all(k in q for k in required_keys):
            issues.append(f"Q{i+1}: Missing structural keys.")
            continue

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
            if any(char in ans for char in [":", "=", "Action", "Item", "-"]):
                issues.append(f"Q{i+1}: Hallucinated 'Matching' logic in answer field. Fix manually.")
            else:
                issues.append(f"Q{i+1}: Invalid answer '{ans}'.")

        q_text = q.get('question', '').strip()
        if q_text in unique_questions:
            issues.append(f"Q{i+1}: Duplicate question text.")
        unique_questions.add(q_text)

        if len(q.get('rationale', '')) < 50:
            issues.append(f"Q{i+1}: Rationale is too short/low quality.")

    if repair and repaired_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\n✅ Repaired {repaired_count} structural/sequence issues and saved JSON.")

    if not issues:
        print("\n✅ 100% CONFIDENCE: Exam is sequenced and proctor-ready.")
    else:
        print(f"\n❌ AUDIT FAILED: Found {len(issues)} issues.")
        for issue in issues[:15]:
            print(f"  - {issue}")

if __name__ == "__main__":
    repair_mode = "--repair" in sys.argv
    audit_exam_data(repair=repair_mode)
