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

# RE-BALANCED BATCHES (Total: 70 Questions - Official PRINCE2 v7 Weights)
BATCH_CONFIGS = [
    {"name": "B1: Intro", "files": ["01_intro_principles.md"], "count": 7},
    {"name": "B2: People", "files": ["02_people.md"], "count": 6},
    
    # 51% Practices = 36 Questions
    {"name": "B3: Prac P1-A", "files": ["03_practices_p1.md"], "count": 5},
    {"name": "B4: Prac P1-B", "files": ["03_practices_p1.md"], "count": 4},
    {"name": "B5: Prac P2-A", "files": ["04_practices_p2.md"], "count": 5},
    {"name": "B6: Prac P2-B", "files": ["04_practices_p2.md"], "count": 4},
    {"name": "B7: Prac P3-A", "files": ["05_practices_p3.md"], "count": 5},
    {"name": "B8: Prac P3-B", "files": ["05_practices_p3.md"], "count": 4},
    {"name": "B9: Prac P4-A", "files": ["06_practices_p4.md"], "count": 5},
    {"name": "B10: Prac P4-B", "files": ["06_practices_p4.md"], "count": 4},
    
    # 30% Processes = 21 Questions
    {"name": "B11: Proc P1-A", "files": ["07_processes_p1.md"], "count": 4},
    {"name": "B12: Proc P1-B", "files": ["07_processes_p1.md"], "count": 3},
    {"name": "B13: Proc P2-A", "files": ["08_processes_p2.md"], "count": 4},
    {"name": "B14: Proc P2-B", "files": ["08_processes_p2.md"], "count": 3},
    {"name": "B15: Proc P3-A", "files": ["09_processes_p3.md"], "count": 4},
    {"name": "B16: Proc P3-B", "files": ["09_processes_p3.md"], "count": 3}
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
    
    # Categorized XML-structured Golden Datasets
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

    total_input = 0
    total_output = 0

    # THE MASTER PROMPT (System Instruction)
    system_instruction = """
    Act as a PRINCE2 7th Edition Lead Examiner. Your task is to generate high-fidelity, Practitioner-level exam questions.
    
    CORE RULES:
    1. PERSONA: You are rigorous, detail-oriented, and mimic the "trap-heavy" style of PeopleCert.
    2. COGNITIVE LEVEL: Questions MUST be Bloom's Level 3 (Application) or Level 4 (Analysis). NEVER ask for simple definitions or recall (Level 1/2). 
    3. QUESTION FORMAT: Strongly prefer the official Practitioner reasoning structure for options: 'Yes, because...', 'Yes, because...', 'No, because...', 'No, because...'.
    4. BANNED FORMATS: Do NOT generate 'Matching' questions (where 3 actions are mapped to 5 roles). Generate ONLY 'Classic' multiple-choice questions with exactly 4 options (A, B, C, D) and a single correct letter answer.
    5. ROLE ANONYMITY: Never use PRINCE2 role titles (Executive, Senior User, etc.) in questions or options. Use the internal job titles provided in the Role Mapping.
    6. TRAP LOGIC: Analyze the provided <golden_answers>. Emulate their distractor construction: plausible management products applied in wrong contexts, correct principles applied to wrong roles.
    7. NOISE ROLES: Identify stakeholders in the Golden Scenarios who have no formal project role. You MUST invent 2-3 similar 'Red Herring' roles for the current target scenario to use as distractor options.
    8. ASSESSMENT CRITERIA: When testing Practices or Processes, focus specifically on how to apply Key Management Products (e.g., PIDs, Registers, Logs), Role Focus Areas (RACI accountabilities), and Tailoring Techniques.
    9. OUTPUT FORMAT: Respond ONLY with a valid JSON array. No preamble, no conversational filler, no markdown formatting.
    """

    for idx, batch in enumerate(BATCH_CONFIGS):
        target_q_range_end = sum(b['count'] for b in BATCH_CONFIGS[:idx+1])
        if finished_count >= target_q_range_end:
            print(f"--- Skipping {batch['name']} (Already mined) ---")
            continue

        print(f"\n--- Running {batch['name']} ---")
        syllabus_context = "\n".join([load_data(f"data/syllabus/{f}") for f in batch['files']])

        # THE DATA PROMPT (User Message)
        user_message = f"""
        Generate {batch['count']} questions based on the following data:

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
        
        CRITICAL INSTRUCTION: Distribute the {batch['count']} questions evenly across the different chapters/sub-topics found within the <syllabus_data>. Do not focus all questions on just the first topic you read. Ensure the 'topic' field explicitly names the chapter being tested (e.g. "Practices - Business Case").

        Target JSON Schema:
        [{{'id':int, 'topic':str, 'question':str, 'options':{{'A':str,'B':str,'C':str,'D':str}}, 'answer':str, 'rationale':str}}]
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
                
                # Strip conversational noise and find the actual JSON array
                start_idx = raw_text.find('[')
                end_idx = raw_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    clean_json = raw_text[start_idx:end_idx]
                    batch_data = json.loads(clean_json)
                    
                    full_exam.extend(batch_data)
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(full_exam, f, indent=4)
                    
                    in_tok = response.usage.input_tokens
                    out_tok = response.usage.output_tokens
                    total_input += in_tok
                    total_output += out_tok
                    
                    print(f"[Success] Mined {len(batch_data)} questions. Checkpoint saved.")
                    print(f"[Audit] Cost for batch: Input: {in_tok} | Output: {out_tok}")
                    batch_success = True
                    break
                else:
                    raise ValueError("No JSON array brackets found in Claude's response.")
            except Exception as e:
                print(f"[Error] {batch['name']} Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Cooling down for 65s before retry...")
                    time.sleep(65)

        if idx < len(BATCH_CONFIGS) - 1 and batch_success:
            print("Mitigation: Sleeping 65s between batches...")
            time.sleep(65)

    print(f"\nEXAM COMPLETE: {len(full_exam)} total questions in {DATA_FILE}")

if __name__ == "__main__":
    generate_exam()
