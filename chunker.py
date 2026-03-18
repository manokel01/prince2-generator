import os
import re
from pathlib import Path

def split_manual():
    manual_path = Path("data/source_manual/PRINCE2_v7_manual.md")
    if not manual_path.exists():
        print(f"Error: {manual_path} not found.")
        return

    content = manual_path.read_text(encoding="utf-8")

    # Regex patterns for the exact chapter headings, matching start of line
    sections = {
        "principles": [r"^(#+\s*)?2\.?\s+.*Principles", r"^(#+\s*)?PRINCE2\s+Principles"],
        "people": [r"^(#+\s*)?3\.?\s+People", r"^(#+\s*)?People"],
        "practices": [r"^(#+\s*)?4\.?\s+Introduction to PRINCE2 Practices", r"^(#+\s*)?Introduction to PRINCE2 Practices"],
        "processes": [r"^(#+\s*)?12\.?\s+Introduction to PRINCE2 Processes", r"^(#+\s*)?Introduction to PRINCE2 Processes"]
    }

    output_dir = Path("data/syllabus")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, patterns in sections.items():
        start_idx = -1
        for pattern in patterns:
            # MULTILINE allows ^ to match the start of any line, IGNORECASE handles capitalization quirks
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                if line_end == -1: line_end = len(content)
                
                line_text = content[line_start:line_end].strip()
                
                # Filter: Must not be a TOC table row (|) and must be a short header line (< 60 chars)
                if "|" not in line_text and len(line_text) < 60:
                    start_idx = match.start()
                    break
            if start_idx != -1: break
        
        if start_idx != -1:
            # Define the cutoff point by finding the next sequential chapter
            next_chap = ""
            if name == "principles": next_chap = r"^(#+\s*)?3\.?\s+People"
            elif name == "people": next_chap = r"^(#+\s*)?4\.?\s+Introduction"
            elif name == "practices": next_chap = r"^(#+\s*)?5\.?\s+Organizing"
            elif name == "processes": next_chap = r"^(#+\s*)?13\.?\s+Starting"

            next_match = re.search(next_chap, content[start_idx+50:], re.MULTILINE | re.IGNORECASE)
            end_idx = start_idx + 50 + next_match.start() if next_match else len(content)
            
            chunk = content[start_idx:end_idx]
            output_file = output_dir / f"{name}.md"
            output_file.write_text(chunk, encoding="utf-8")
            print(f"Extracted: {output_file}")
        else:
            print(f"Warning: Could not find content header for {name}.")

if __name__ == "__main__":
    split_manual()
