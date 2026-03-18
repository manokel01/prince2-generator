import re
from pathlib import Path

def split_manual():
    content = Path("data/source_manual/PRINCE2_v7_manual.md").read_text(encoding="utf-8")
    out_dir = Path("data/syllabus")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Use only the 4 proven macro-boundaries
    markers = {
        "people": [r"^(#+\s*)?3\.?\s+.*People", r"^(#+\s*)?People"],
        "practices": [r"^(#+\s*)?4\.?\s+.*Introduction to PRINCE2 Practices", r"^(#+\s*)?Introduction to PRINCE2 Practices"],
        "processes": [r"^(#+\s*)?12\.?\s+.*Introduction to PRINCE2 Processes", r"^(#+\s*)?Introduction to PRINCE2 Processes"],
        "glossary": [r"^(#+\s*)?Glossary"]
    }
    
    pos = {}
    for key, patterns in markers.items():
        found = False
        for pattern in patterns:
            if found: break
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                line = content[line_start:line_end]
                
                if "|" not in line and len(line.strip()) < 80:
                    pos[key] = match.start()
                    found = True
                    break
                    
    # Fallback to absolute indices if Docling weirdness hides a header
    idx_people = pos.get("people", 74741)
    idx_practices = pos.get("practices", 152429)
    idx_processes = pos.get("processes", 599243)
    idx_glossary = pos.get("glossary", 855754)

    def write_chunk(name, start, end):
        # Snap to nearest double newline to keep paragraphs intact
        actual_end = content.find('\n\n', end) if end < len(content) else end
        if actual_end == -1 or actual_end > end + 5000:
            actual_end = end 
            
        chunk_data = content[start:actual_end]
        (out_dir / f"{name}.md").write_text(chunk_data)
        print(f"Extracted: {name}.md ({(actual_end - start) // 1024} KB)")
        return actual_end

    # 1. Intro & Principles (~74KB)
    write_chunk("01_intro_principles", 0, idx_people)
    
    # 2. People (~77KB)
    write_chunk("02_people", idx_people, idx_practices)
    
    # 3. Practices split into 4 safe parts (~111KB each)
    step = (idx_processes - idx_practices) // 4
    cur = write_chunk("03_practices_p1", idx_practices, idx_practices + step)
    cur = write_chunk("04_practices_p2", cur, cur + step)
    cur = write_chunk("05_practices_p3", cur, cur + step)
    write_chunk("06_practices_p4", cur, idx_processes)
    
    # 4. Processes split into 3 safe parts (~85KB each)
    step = (idx_glossary - idx_processes) // 3
    cur = write_chunk("07_processes_p1", idx_processes, idx_processes + step)
    cur = write_chunk("08_processes_p2", cur, cur + step)
    write_chunk("09_processes_p3", cur, idx_glossary)

if __name__ == "__main__":
    split_manual()
