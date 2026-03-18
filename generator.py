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

# RE-BALANCED BATCHES WITH STRICT PROGRAMMATIC GUARDRAILS
BATCH_CONFIGS = [
    {"name": "B1: Intro", "files": ["01_intro_principles.md"], "count": 7, "category": "Intro/Principles", "focus": "Introduction and the 7 Principles. DO NOT generate questions about Practices, Processes, or People."},
    {"name": "B2: People", "files": ["02_people.md"], "count": 6, "category": "People", "focus": "People, Team Management, Communication, and Stakeholders. DO NOT generate questions about Practices or Processes."},
    
    # Practices
    {"name": "B3: Prac P1-A", "files": ["03_practices_p1.md"], "count": 5, "category": "Practices", "focus": "Practices (e.g., Business Case, Organizing). DO NOT generate questions about Processes."},
    {"name": "B4: Prac P1-B", "files": ["03_practices_p1.md"], "count": 4, "category": "Practices", "focus": "Practices (e.g., Business Case, Organizing). DO NOT generate questions about Processes."},
    {"name": "B5: Prac P2-A", "files": ["04_practices_p2.md"], "count": 5, "category": "Practices", "focus": "Practices (e.g., Quality, Plans). DO NOT generate questions about Processes."},
    {"name": "B6: Prac P2-B", "files": ["04_practices_p2.md"], "count": 4, "category": "Practices", "focus": "Practices (e.g., Quality, Plans). DO NOT generate questions about Processes."},
    {"name": "B7: Prac P3-A", "files": ["05_practices_p3.md"], "count": 5, "category": "Practices", "focus": "Practices (e.g., Risk). DO NOT generate questions about Processes."},
    {"name": "B8: Prac P3-B", "files": ["05_practices_p3.md"], "count": 4, "category": "Practices", "focus": "Practices (e.g., Risk). DO NOT generate questions about Processes."},
    {"name": "B9: Prac P4-A", "files": ["06_practices_p4.md"], "count": 5, "category": "Practices", "focus": "Practices (e.g., Issues, Progress). DO NOT generate questions about Processes."},
    {"name": "B10: Prac P4-B", "files": ["06_practices_p4.md"], "count": 4, "category": "Practices", "focus": "Practices (e.g., Issues, Progress). DO NOT generate questions about Processes."},
    
    # Processes
    {"name": "B11: Proc P1-A", "files": ["07_processes_p1.md"], "count": 4, "category": "Processes", "focus": "Processes (Starting up, Directing)."},
    {"name": "B12: Proc P1-B", "files": ["07_processes_p1.md"], "count": 3, "category": "Processes", "focus": "Processes (Starting up, Directing)."},
    {"name": "B13: Proc P2-A", "files": ["08_processes_p2.md"], "count": 4, "category": "Processes", "focus": "Processes (Initiating, Controlling a Stage)."},
    {"name": "B14: Proc P2-B", "files": ["08_processes_p2.md"], "count": 3, "category": "Processes", "focus": "Processes (Initiating, Controlling a Stage)."},
    {"name": "B15: Proc P3-A", "files": ["09_processes_p3.md"], "count": 4, "category": "Processes", "focus": "Processes (Managing Product Delivery, Stage Boundary, Closing)."},
    {"name": "B16: Proc P3-B", "files": ["09_processes_p3.md"], "count": 3, "category": "Processes", "focus": "Processes (Managing Product Delivery, Stage Boundary, Closing)."}
]

DATA_FILE = Path("exam_data.json")

def load_data(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""

def get_existing_progress():
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
    
    golden_dir = Path("data/golden_datasets")
    scenarios_xml = []
    questions_xml = []
    answers_xml = []
    
    if golden_dir.exists():
        for md_file in golden_dir.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')
            name = md_file.name.lower()
            if "scenario" in name:
                scenarios_xml.append(f"<golden_scenario source='{md_file.name}'>\n{content}\n</golden_scenario>")
            elif "question" in name:
                questions_xml.append(f"<golden_questions source='{md_file.name}'>\n{content}\n</golden_questions>")
            elif "answer" in name:
                answers_xml.append(f"<golden_answers source='{md_file.name}'>\n{content}\n</golden_answers>")

    full_exam = get_existing_progress()
    finished_count = len(full_exam)
    print(f"Found {finished_count} existing questions. Resuming...")

    system_instruction = """
    Act as a PRINCE2 7th Edition Lead Examiner. Your task is to generate high-fidelity, Practitioner-level exam questions.
    
    CORE RULES:
    1. PERSONA: You are rigorous, detail-oriented, and mimic the "trap-heavy" style of PeopleCert.
    2. COGNITIVE LEVEL: Questions MUST be Bloom's Level 3 (Application) or Level 4 (Analysis). NEVER ask for simple definitions or recall. 
    3. QUESTION FORMAT: Strongly prefer the Practitioner reasoning structure for options: 'Yes, because...', 'Yes, because...', 'No, because...', 'No, because...'.
    4. BANNED FORMATS: Do NOT generate 'Matching' questions. Generate ONLY multiple-choice questions with exactly 4 options (A, B, C, D).
    5. ROLE ANONYMITY: Never use PRINCE2 role titles (Executive, Senior User, etc.) in questions/options. Use the internal job titles from the Role Mapping.
    6. TRAP LOGIC: Emulate distractor construction: plausible management products in wrong contexts, correct principles applied to wrong roles.
    7. NOISE ROLES: Invent 2-3 'Red Herring' roles for the target scenario to use as distractor options.
    8. OUTPUT FORMAT: Respond ONLY with a valid JSON array. No preamble.
    """

    for idx, batch in enumerate(BATCH_CONFIGS):
        target_q_range_end = sum(b['count'] for b in BATCH_CONFIGS[:idx+1])
        if finished_count >= target_q_range_end:
            print(f"--- Skipping {batch['name']} (Already mined) ---")
            continue

        print(f"\n--- Running {batch['name']} ---")
        syllabus_context = "\n".join([load_data(f"data/syllabus/{f}") for f in batch['files']])

        user_message = f"""
        Generate {batch['count']} questions.
        
        CRITICAL SCOPE RESTRICTION:
        For this batch, your ONLY focus is: {batch['focus']}
        You MUST completely ignore your pre-trained knowledge of other PRINCE2 chapters. Base the questions strictly on this data:

        <syllabus_data>
        {syllabus_context}
        </syllabus_data>

        <target_scenario>
        {scenario}
        </target_scenario>

        <role_mapping>
        {roles_outline}
        </role_mapping>

        <style_reference_golden_data>
        {"\n".join(scenarios_xml)}
        {"\n".join(questions_xml)}
        {"\n".join(answers_xml)}
        </style_reference_golden_data>
        
        CRITICAL DATA INSTRUCTION: 
        The 'topic' field MUST explicitly start with "{batch['category']} - ". Do not deviate from this prefix.

        Target JSON Schema:
        [{{'id':int, 'topic':'{batch['category']} - [Specific Sub-topic]', 'question':str, 'options':{{'A':str,'B':str,'C':str,'D':str}}, 'answer':str, 'rationale':str}}]
        """

        max_retries = 3
        batch_success = False
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system=system_instruction,
                    messages=[{"role": "user", "content": user_message}]
                )
                
                raw_text = response.content[0].text
                start_idx = raw_text.find('[')
                end_idx = raw_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    clean_json = raw_text[start_idx:end_idx]
                    batch_data = json.loads(clean_json)
                    
                    # PROGRAMMATIC KILL SWITCH: Force-inject correct category mapping
                    for q in batch_data:
                        if not q['topic'].startswith(batch['category']):
                            q['topic'] = f"{batch['category']} - {q['topic']}"
                    
                    full_exam.extend(batch_data)
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(full_exam, f, indent=4)
                    
                    in_tok = response.usage.input_tokens
                    out_tok = response.usage.output_tokens
                    
                    print(f"[Success] Mined {len(batch_data)} questions. Checkpoint saved.")
                    print(f"[Audit] Cost for batch: Input: {in_tok} | Output: {out_tok}")
                    batch_success = True
                    break
                else:
                    raise ValueError("No JSON array brackets found.")
            except Exception as e:
                print(f"[Error] {batch['name']} Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Cooling down for 65s before retry...")
                    time.sleep(65)

        if idx < len(BATCH_CONFIGS) - 1 and batch_success:
            print("Mitigation: Sleeping 65s between batches...")
            time.sleep(65)

if __name__ == "__main__":
    generate_exam()
