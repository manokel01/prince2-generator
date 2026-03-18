# PRINCE2 Practitioner Exam Generator

A terminal-native engine designed to generate high-fidelity mock exams for the PRINCE2 7th Edition Practitioner qualification. 

## Project Overview
This tool transforms a raw business scenario into a 70-mark mock exam. It uses Retrieval-Augmented Generation (RAG) to ensure every question is grounded in the official v7 manual while mimicking the "trap-heavy" style of official PeopleCert papers.

## Architecture & Workflow
1. **Ingestion**: Raw PDFs and Word docs are converted to clean Markdown using the `Docling` engine to preserve complex tables and role matrices.
2. **Mathematical Chunking**: The official manual is sliced into 9 strictly-sized chunks (<115KB) to respect Tier 1 LLM token limits and maintain high-precision context windows.
3. **Hidden State Logic**: The engine internally maps organizational titles (e.g., "Head of Finance") to PRINCE2 roles (e.g., "Executive"). It generates a scenario narrative that strictly avoids PRINCE2 terminology, forcing the user to deduce roles during the exam.
4. **Stateful Generation**: Powered by Claude 3.5 Sonnet (v4.6). Uses a 16-batch architecture with 65s rate-limit mitigation and automatic state checkpointing to `exam_data.json`. Resumes automatically if interrupted.
5. **Data Integrity & Validation**: An independent `auditor.py` script enforces a strict A-D schema, detects generation collisions, and automatically repairs hallucinated JSON options.
6. **Interactive TUI**: A terminal interface built with `Textual` for a focused, distraction-free testing environment.

## Workspace Structure
- `data/source_manual/`: Contains the official PRINCE2 v7 Manual (The Ground Truth).
- `data/golden_datasets/`: Past mock exams and rationales used for style transfer and "trap" logic.
- `data/target_scenario/`: The specific scenario text and role outlines currently being processed (e.g., Louistown or Findef).
- `data/syllabus/`: Processed Markdown chunks used by the AI during question generation.
- `exam_data.json`: The compiled, stateful exam output.

## Commands
- `python parser.py`: Recursively converts all files in `data/` to Markdown.
- `python chunker.py`: Slices the converted manual into syllabus-specific chunks.
- `python generator.py`: Orchestrates the LLM to build the 70-question exam JSON.
- `python auditor.py`: Validates the generated JSON schema, content uniqueness, and rationale length.
- `python auditor.py --repair`: Automatically strips hallucinated options (e.g., Option E) from the dataset.
- `python app.py`: Launches the interactive TUI mock exam.

## TUI Keybinds
- `j` / `k` or `↑` / `↓`: Navigate options
- `ENTER`: Submit
- `s`: Toggle scenario overlay
- `q`: Quit exam
