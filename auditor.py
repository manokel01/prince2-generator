import json
import sys
from pathlib import Path

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
        print("[Mode] Repair enabled. Fixing structural issues...")

    for i, q in enumerate(data):
        # 1. Structural Check
        required_keys = ['topic', 'question', 'options', 'answer', 'rationale']
        missing = [k for k in required_keys if k not in q]
        if missing:
            issues.append(f"Q{i}: Missing keys: {missing}")
            continue

        # 2. Options Check & Repair
        options = q.get('options', {})
        current_keys = set(options.keys())
        standard_keys = {'A', 'B', 'C', 'D'}
        
        if current_keys != standard_keys:
            if repair and current_keys.issuperset(standard_keys):
                # Has A, B, C, D plus extra (like 'E'). Strip the extra.
                extra_keys = current_keys - standard_keys
                for k in list(extra_keys):
                    del q['options'][k]
                repaired_count += 1
            else:
                issues.append(f"Q{i}: Invalid options structure. Keys found: {sorted(list(current_keys))}")

        # 3. Answer Consistency
        ans = q.get('answer')
        if ans not in standard_keys:
            issues.append(f"Q{i}: Invalid answer '{ans}'. Must be A, B, C, or D.")

        # 4. Content Uniqueness
        q_text = q.get('question', '').strip()
        if q_text in unique_questions:
            issues.append(f"Q{i}: Duplicate question detected.")
        unique_questions.add(q_text)

        # 5. Rationale Check
        rat = q.get('rationale', '')
        if len(rat) < 50:
            issues.append(f"Q{i}: Rationale too short.")

    if repair and repaired_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\n✅ Repaired and saved {repaired_count} questions.")

    if not issues:
        print("\n✅ 100% CONFIDENCE: Dataset is valid and proctor-ready.")
    else:
        print(f"\n❌ AUDIT FAILED: Found {len(issues)} unresolvable issues.")
        for issue in issues[:10]:
            print(f"  - {issue}")

if __name__ == "__main__":
    repair_mode = "--repair" in sys.argv
    audit_exam_data(repair=repair_mode)
