import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=180.0
)

# RE-BALANCED BATCHES
BATCH_CONFIGS = [
    {"name": "B1: Intro", "files": ["01_intro_principles.md"], "count": 7},
    {"name": "B2: People", "files": ["02_people.md"], "count": 6},
    {"name": "B3: Prac P1-A", "files": ["03_practices_p1.md"], "count": 4},
    {"name": "B4: Prac P1-B", "files": ["03_practices_p1.md"], "count": 4},
    {"name": "B5: Prac P2-A", "files": ["04_practices_p2.md"], "count": 4},
    {"name": "B6: Prac P2-B", "files": ["04_practices_p2.md"], "count": 4},
    {"name": "B7: Prac P3-A", "files": ["05_practices_p3.md"], "count": 4},
    {"name": "B8: Prac P3-B", "files": ["05_practices_p3.md"], "count": 4},
    {"name": "B9: Prac P4-A", "files": ["06_practices_p4.md"], "count": 4},
    {"name": "B10: Prac P4-B", "files": ["06_practices_p4.md"], "count": 4},
    {"name": "B11: Proc P1-A", "files": ["07_processes_p1.md"], "count": 5},
    {"name": "B12: Proc P1-B", "files": ["07_processes_p1.md"], "count": 5},
    {"name": "B13: Proc P2-A", "files": ["08_processes_p2.md"], "count": 4},
    {"name": "B14: Proc P2-B", "files": ["08_processes_p2.md"], "count": 4},
    {"name": "B15: Proc P3-A", "files": ["09_processes_p3.md"], "count": 4},
    {"name": "B16: Proc P3-B", "files": ["09_processes_p3.md"], "count": 5}
]

DATA_FILE = Path("exam_data.json")

def load_data(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""

def get_existing_progress():
    """Load existing questions to avoid re-running successful batches."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def generate_exam():
    scenario = load_data("data/target_scenario/Louistown_scenario.md")
    roles_outline = load_data("data/target_scenario/Louistown_roles.md")
    golden_q = load_data("data/golden_datasets/NowByou_question_set_1.md")
    golden_a = load_data("data/golden_datasets/NowByou_answer_set_1.md")

    full_exam = get_existing_progress()
    
    # Simple checkpoint logic: track which batches we've already finished
    # We use 'topic' or index to determine if we should skip
    finished_count = len(full_exam)
    print(f"Found {finished_count} existing questions. Resuming...")

    total_input = 0
    total_output = 0
    current_q_count = 0

    for idx, batch in enumerate(BATCH_CONFIGS):
        # Skip logic: if the cumulative count of previous batches covers this one, skip it
        target_q_range_end = sum(b['count'] for b in BATCH_CONFIGS[:idx+1])
        
        if finished_count >= target_q_range_end:
            print(f"--- Skipping {batch['name']} (Already mined) ---")
            current_q_count = target_q_range_end
            continue

        print(f"\n--- Running {batch['name']} ---")
        syllabus_context = "\n".join([load_data(f"data/syllabus/{f}") for f in batch['files']])

        prompt = f"""
        Act as a PRINCE2 7th Edition Lead Examiner. Generate {batch['count']} Practitioner-level questions.
        
        SYLLABUS DATA:
        {syllabus_context}

        SCENARIO:
        {scenario}

        ROLE MAPPING:
        {roles_outline}

        STYLE REFERENCE:
        {golden_q[:1000]}
        {golden_a[:1000]}

        CONSTRAINTS:
        1. NO PRINCE2 ROLES: Use internal scenario titles (e.g. 'Mayor').
        2. RATIONALES: Provide a detailed rationale for all 4 options.
        3. OUTPUT: Strictly valid JSON list.
        """

        max_retries = 3
        batch_success = False
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system="JSON ONLY. Format: [{'id':int, 'topic':str, 'question':str, 'options':{'A':str,'B':str,'C':str,'D':str}, 'answer':str, 'rationale':str}]",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                raw_text = response.content[0].text
                start_idx = raw_text.find('[')
                end_idx = raw_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    clean_json = raw_text[start_idx:end_idx]
                    batch_data = json.loads(clean_json)
                    
                    # Append and SAVE IMMEDIATELY (Checkpoint)
                    full_exam.extend(batch_data)
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(full_exam, f, indent=4)
                    
                    total_input += response.usage.input_tokens
                    total_output += response.usage.output_tokens
                    print(f"[Success] Mined {len(batch_data)} questions. Checkpoint saved.")
                    batch_success = True
                    break
                else:
                    raise ValueError("JSON anchors missing.")
                
            except Exception as e:
                print(f"[Error] {batch['name']} Attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print("Cooling down 65s before retry...")
                    time.sleep(65)

        if idx < len(BATCH_CONFIGS) - 1 and batch_success:
            print("Mitigation: Sleeping 65s...")
            time.sleep(65)

    print(f"\nEXAM COMPLETE: {len(full_exam)} total questions in {DATA_FILE}")

if __name__ == "__main__":
    generate_exam()
