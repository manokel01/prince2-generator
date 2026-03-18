# PRINCE2 Practitioner Exam Generator

A terminal-native engine designed to generate high-fidelity mock exams for the PRINCE2 7th Edition Practitioner qualification.

## Project Overview

This tool transforms a raw business scenario into a 70-mark mock exam. It uses Retrieval-Augmented Generation (RAG) to ensure every question is grounded in the official v7 manual while mimicking the "trap-heavy" style of official PeopleCert papers.

## Smart Features & Syllabus Alignment

-   **Strict Syllabus Weighting:** Mathematically enforces the official Practitioner distribution: Principles (10%), People (9%), Practices (51%), and Processes (30%).
    
-   **Cognitive Targeting:** Forces the LLM to generate questions strictly at Bloom's Taxonomy Levels 3 (Application) and 4 (Analysis), explicitly banning Level 1/2 recall questions.
    
-   **Anti-Clumping & Hallucination Defenses:** Instructs the LLM to distribute questions evenly across chunked content and explicitly bans PeopleCert's "Matching" format to ensure compatibility with single-character A-D options.
    
-   **Intelligent Auditor:** Beyond basic JSON validation, `auditor.py` performs a full Sequence Integrity Audit, auto-sorts questions into their correct chronological chapter order, and maps generated topics to official syllabus boundaries.
    
-   **Official Pass Threshold:** The TUI evaluates the final score against the strict 42/70 (60%) pass mark required for Practitioner certification.
    

## Architecture & Workflow

-   **Ingestion:** Raw PDFs and Word docs are converted to clean Markdown using the Docling engine to preserve complex tables and role matrices.
    
-   **Mathematical Chunking:** The official manual is sliced into 9 strictly-sized chunks (<115KB) to respect Tier 1 LLM token limits and maintain high-precision context windows.
    
-   **Hidden State Logic:** The engine internally maps organizational titles (e.g., "Head of Finance") to PRINCE2 roles (e.g., "Executive"). It generates a scenario narrative that strictly avoids PRINCE2 terminology, forcing the user to deduce roles during the exam.
    
-   **Stateful Generation:** Powered by Claude 4.6 Sonnet. Uses a 16-batch architecture with 65s rate-limit mitigation and automatic XML-categorized state checkpointing to `exam_data.json`.
    
-   **Data Integrity & Validation:** An independent `auditor.py` script enforces a strict A-D schema, detects generation collisions, auto-sorts chronological flow, and automatically repairs hallucinated JSON options.
    
-   **Native Void TUI:** A terminal interface built with Textual featuring sidebar navigation, progress tracking (\[✓\] marks), and dedicated scrollable modals for scenarios and rationales.
    

## Workspace Structure

| Path | Description |
| --- | --- |
| `data/source_manual/` | Contains the official PRINCE2 v7 Manual (The Ground Truth). |
| `data/golden_datasets/` | Past mock exams and rationales used for style transfer and "trap" logic. |
| `data/target_scenario/` | The specific scenario text and role outlines currently being processed (e.g., Louistown or Findef). |
| `data/syllabus/` | Processed Markdown chunks used by the AI during question generation. |
| `exam_data.json` | The compiled, stateful exam output. |

## Setup & Installation

1.  **Install Python Dependencies:** Ensure you are using Python 3.10+ and install the required packages:
    
        pip install anthropic python-dotenv textual docling
        
    
2.  **Configure API Credentials:** Create a `.env` file in the root directory and add your Anthropic API key:
    
        ANTHROPIC_API_KEY=your_api_key_here
        
    

## Complete Workflow

Follow this exact sequence to generate and take an exam:

1.  **Ingest & Chunk the Manual (One-time setup):**
    
        python parser.py
        python chunker.py
        
    
2.  **Generate the Exam:**
    
        python generator.py
        
    
    _Note: This takes ~25-30 minutes. The script enforces a mandatory 65-second sleep between batches to mitigate Anthropic Tier 1 rate limits (429 errors). Leave it running._
    
3.  **Audit & Repair:**
    
        python auditor.py --repair
        
    
    _Crucial step. This physically sorts the JSON to match the official Practitioner chronological sequence, enforces the official 36/21 weightings, and strips hallucinated options._
    
4.  **Launch the Exam:**
    
        python app.py
        
    

## Managing Data & Troubleshooting

The generation engine is stateful, meaning it writes to `exam_data.json` continuously.

-   **How to start a new exam (or wipe corrupted data):** If you want to generate a completely new exam from a new scenario, or if your JSON is irreparably corrupted, you **must** delete the state file before generating:
    
        rm exam_data.json
        python generator.py
        
    
-   **API Credit Exhaustion (400 Errors):** If your Anthropic prepaid balance hits $0.00 mid-generation, the script will crash. **Do not delete `exam_data.json`.** Simply top up your account balance on the Anthropic console and re-run `python generator.py`. The script will instantly skip all finished batches and resume exactly where it crashed.
    
-   **Rate Limits (429 Errors):** These are expected. The script will automatically catch them, sleep for 65 seconds, and retry.
    

## TUI Keybinds

-   **Tab**: Switch focus between Sidebar and Options
    
-   **j / k** or **↑ / ↓**: Navigate focused list / Scroll modals
    
-   **Enter**: Submit answer / Select question / Dismiss rationale
    
-   **s**: Toggle scenario modal overlay
    
-   **q**: Quit exam
