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

# MICRO-BATCHING TO PREVENT LLM ATTENTION DECAY ("DRIFT")
BATCH_CONFIGS = [
    {"name": "B1: Intro A", "files": ["01_intro_principles.md"], "count": 4, "category": "Intro/Principles", "focus": "Ensure Continued Business Justification, Learn from Experience, Define Roles."},
    {"name": "B2: Intro B", "files": ["01_intro_principles.md"], "count": 3, "category": "Intro/Principles", "focus": "Manage by Exception, Manage by Stages, Focus on Products, Tailor to Suit."},
    
    {"name": "B3: People A", "files": ["02_people.md"], "count": 3, "category": "People", "focus": "Leading Successful Teams, Communication."},
    {"name": "B4: People B", "files": ["02_people.md"], "count": 3, "category": "People", "focus": "Leading Successful Change, Stakeholders."},
    
    # Practices (Split into chunks of 3 or 4 max)
    {"name": "B5: Prac P1-A", "files": ["03_practices_p1.md"], "count": 3, "category": "Practices", "focus": "Business Case practice."},
    {"name": "B6: Prac P1-B", "files": ["03_practices_p1.md"], "count": 3, "category": "Practices", "focus": "Business Case practice."},
    {"name": "B7: Prac P1-C", "files": ["03_practices_p1.md"], "count": 3, "category": "Practices", "focus": "Organizing practice."},
    {"name": "B8: Prac P2-A", "files": ["04_practices_p2.md"], "count": 3, "category": "Practices", "focus": "Plans practice."},
    {"name": "B9: Prac P2-B", "files": ["04_practices_p2.md"], "count": 3, "category": "Practices", "focus": "Plans practice."},
    {"name": "B10: Prac P2-C", "files": ["04_practices_p2.md"], "count": 3, "category": "Practices", "focus": "Quality practice."},
    {"name": "B11: Prac P3-A", "files": ["05_practices_p3.md"], "count": 3, "category": "Practices", "focus": "Risk practice."},
    {"name": "B12: Prac P3-B", "files": ["05_practices_p3.md"], "count": 3, "category": "Practices", "focus": "Risk practice."},
    {"name": "B13: Prac P3-C", "files": ["05_practices_p3.md"], "count": 3, "category": "Practices", "focus": "Risk practice (focus on Risk Budget and Metrics)."},
    {"name": "B14: Prac P4-A", "files": ["06_practices_p4.md"], "count": 3, "category": "Practices", "focus": "Issues practice."},
    {"name": "B15: Prac P4-B", "files": ["06_practices_p4.md"], "count": 3, "category": "Practices", "focus": "Issues practice."},
    {"name": "B16: Prac P4-C", "files": ["06_practices_p4.md"], "count": 3, "category": "Practices", "focus": "Progress practice."},
    
    # Processes (Split into chunks of 3 or 4 max)
    {"name": "B17: Proc P1-A", "files": ["07_processes_p1.md"], "count": 4, "category": "Processes", "focus": "Starting up a Project process."},
    {"name": "B18: Proc P1-B", "files": ["07_processes_p1.md"], "count": 3, "category": "Processes", "focus": "Directing a Project process."},
    {"name": "B19: Proc P2-A", "files": ["08_processes_p2.md"], "count": 4, "category": "Processes", "focus": "Initiating a Project process."},
    {"name": "B20: Proc P2-B", "files": ["08_processes_p2.md"], "count": 3, "category": "Processes", "focus": "Controlling a Stage process."},
    {"name": "B21: Proc P3-A", "files": ["09_processes_p3.md"], "count": 3, "category": "Processes", "focus": "Managing Product Delivery process."},
    {"name": "B22: Proc P3-B", "files": ["09_processes_p3.md"], "count": 2, "category": "Processes", "focus": "Managing a Stage Boundary process."},
    {"name": "B23: Proc P3-C", "files": ["09_processes_p3.md"], "count": 2, "category": "Processes", "focus": "Closing a Project process."}
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
    # Unified Context & Spec loading
    scenario = load_data("data/target_scenario/active_scenario.md")
    exam_spec = load_data("data/golden_datasets/prince2_exam_generation_spec.md")
    
    golden_dir = Path("data/golden_datasets")
    scenarios_xml = []
    questions_xml = []
    answers_xml = []
    
    if golden_dir.exists():
        for md_file in golden_dir.glob("*.md"):
            name = md_file.name.lower()
            # Explicitly exclude the spec document from being parsed as a generic golden file
            if "spec" in name:
                continue
                
            content = md_file.read_text(encoding='utf-8')
            if "scenario" in name:
                scenarios_xml.append(f"<golden_scenario source='{md_file.name}'>\n{content}\n</golden_scenario>")
            elif "question" in name:
                questions_xml.append(f"<golden_questions source='{md_file.name}'>\n{content}\n</golden_questions>")
            elif "answer" in name:
                answers_xml.append(f"<golden_answers source='{md_file.name}'>\n{content}\n</golden_answers>")

    full_exam = get_existing_progress()
    finished_count = len(full_exam)
    print(f"Found {finished_count} existing questions. Resuming...")

    # The System Instruction is now entirely driven by your Master Spec
    system_instruction = f"""
    Act as a PRINCE2 7th Edition Lead Examiner. Your task is to generate high-fidelity, Practitioner-level exam questions.
    
    You MUST strictly adhere to the following Generation Specification for structure, tone, trap logic, and Bloom's taxonomy:
    
    <generation_specification>
    {exam_spec}
    </generation_specification>
    """

    for idx, batch in enumerate(BATCH_CONFIGS):
        target_q_range_end = sum(b['count'] for b in BATCH_CONFIGS[:idx+1])
        if finished_count >= target_q_range_end:
            print(f"--- Skipping {batch['name']} (Already mined) ---")
            continue

        print(f"\n--- Running {batch['name']} ---")
        syllabus_context = "\n".join([load_data(f"data/syllabus/{f}") for f in batch['files']])

        # --- DYNAMIC CATEGORY GUARDRAILS ---
        category_warnings = ""
        if batch['category'] == "Processes":
            category_warnings = """
            CRITICAL CATEGORY RULES FOR 'PROCESSES':
            1. TRAP 11 AVOIDANCE: If creating a matching question about roles, DO NOT make the answer the same role 3 times (e.g., Executive, Executive, Executive). Mix 'Responsible' and 'Accountable' tasks so the answers vary.
            2. PERSPECTIVE ALIGNMENT: Ensure the character taking the action actually owns that action in the PRINCE2 RACI tables (e.g., PMs do not 'accept' work packages, Team Managers do).
            """
        elif batch['category'] == "Practices":
            category_warnings = """
            CRITICAL CATEGORY RULES FOR 'PRACTICES':
            1. TRAP 9 AVOIDANCE: Do not conflate tolerances. Stage tolerances are escalated to the Board. Project tolerances are escalated to Corporate/Programme management.
            """

        user_message = f"""
                Generate {batch['count']} questions.
                
                CRITICAL SCOPE RESTRICTION:
                For this batch, your ONLY focus is: {batch['focus']}
                You MUST completely ignore your pre-trained knowledge of other PRINCE2 chapters. Base the questions strictly on this project context:
        
                <project_context>
                {scenario}
                </project_context>
        
                <syllabus_data>
                {syllabus_context}
                </syllabus_data>
        
                <style_reference_golden_data>
                {"\n".join(scenarios_xml)}
                {"\n".join(questions_xml)}
                {"\n".join(answers_xml)}
                </style_reference_golden_data>
                
                ⚠️ ANTI-BLEED FIREWALL RULE (CRITICAL) ⚠️
                The <style_reference_golden_data> contains examples from OTHER projects. 
                YOU ARE STRICTLY FORBIDDEN from using any character names, company names, or events from the golden data. 
                The golden data is ONLY to teach you the 'Yes/Because' format and Practitioner trap logic.
                EVERY SINGLE QUESTION you generate MUST be set exclusively within the specific world and characters defined in the <project_context>.

                JSON GENERATION REQUIREMENTS:
                1. Use exactly the JSON schema provided below.
                2. CATEGORY-SPECIFIC RULES: {category_warnings}
                3. TOPIC PREFIX: The 'topic' field MUST explicitly start with "{batch['category']} - ". Do not use long dashes (—), use only the standard hyphen (-).
                4. OPTION VERBOSITY BAN: Options must be extremely concise (1 sentence). They MUST state the underlying PRINCE2 methodology rule. You are FORBIDDEN from repeating scenario narrative, job titles, or operational actions inside the options themselves.

                Target JSON Schema:
                [{{
                  "id": "Q[nn]",
                  "category": "{batch['category']}",
                  "topic": "{batch['category']} - [Specific Sub-topic]",
                  "type": "classic|matching",
                  "scenario_reference": "[character or event from scenario used in stem]",
                  "question": "[question text]",
                  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
                  "answer": "[A|B|C|D]",
                  "rationale": {{
                    "correct": "[why correct option is right]",
                    "wrong": {{
                      "A": "[why wrong, if not correct]",
                      "B": "[why wrong, if not correct]",
                      "C": "[why wrong, if not correct]",
                      "D": "[why wrong, if not correct]"
                    }},
                    "manual_reference": "[section and page range]"
                  }},
                  "bloom_level": "3|4",
                  "difficulty": "medium|hard"
                }}]
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
                
                # Hardened extraction logic
                start_idx = raw_text.find('[')
                end_idx = raw_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx != 0:
                    clean_json = raw_text[start_idx:end_idx]
                    batch_data = json.loads(clean_json)
                    
                    # Programmatic Kill Switch
                    for q in batch_data:
                        # 1. Force Category & Topic Integrity
                        q['category'] = batch['category']
                        raw_topic = q.get('topic', '').replace('—', '-')
                        if ' - ' in raw_topic:
                            clean_topic = raw_topic.split(' - ', 1)[-1].strip()
                        else:
                            clean_topic = raw_topic.strip()
                        q['topic'] = f"{batch['category']} - {clean_topic}"
                        
                        # 2. Force A/B (Positive) and C/D (Negative) Option Grouping
                        options_dict = q.get('options', {})
                        if len(options_dict) == 4 and all(k in options_dict for k in ['A', 'B', 'C', 'D']):
                            old_items = list(options_dict.items())
                            is_rationale = any(str(v).lower().strip().startswith(('yes', 'no', 'it applies')) for v in options_dict.values())
                            
                            if is_rationale:
                                pos_items = [i for i in old_items if str(i[1]).lower().strip().startswith(('yes', 'it applies it well'))]
                                neg_items = [i for i in old_items if str(i[1]).lower().strip().startswith(('no', 'it applies it poorly'))]
                                
                                if len(pos_items) == 2 and len(neg_items) == 2:
                                    # Create the strictly grouped order
                                    new_order = [pos_items[0], pos_items[1], neg_items[0], neg_items[1]]
                                    new_keys = ['A', 'B', 'C', 'D']
                                    
                                    # Create a map of where the old letters ended up
                                    old_to_new = {old_key: new_key for new_key, (old_key, text) in zip(new_keys, new_order)}
                                    
                                    # Remap the Options dictionary
                                    q['options'] = {new_key: text for new_key, (old_key, text) in zip(new_keys, new_order)}
                                    
                                    # Safely remap the Answer key to point to the new letter location
                                    old_ans = str(q.get('answer', '')).strip()
                                    if old_ans in old_to_new:
                                        q['answer'] = old_to_new[old_ans]
                                        
                                    # Safely remap the Rationale 'wrong' dictionary
                                    rationale = q.get('rationale', {})
                                    if 'wrong' in rationale and isinstance(rationale['wrong'], dict):
                                        new_wrong = {old_to_new.get(k, k): v for k, v in rationale['wrong'].items()}
                                        rationale['wrong'] = new_wrong
                    
                    full_exam.extend(batch_data)
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(full_exam, f, indent=4)
                    
                    print(f"[Success] Mined {len(batch_data)} questions. Checkpoint saved.")
                    batch_success = True
                    break
                else:
                    raise ValueError("No JSON array found in response.")
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
