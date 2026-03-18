# PRINCE2 Practitioner Exam Generator

# 

A terminal-based application designed to generate high-fidelity mock exams for the PRINCE2 7th Edition Practitioner qualification.

## Project Overview

# 

This tool transforms a raw business scenario into a 70-mark mock exam. It uses Retrieval-Augmented Generation (RAG) to ensure every question is grounded in the official v7 manual while mimicking the "trap-heavy" style of official PeopleCert papers.

## The Challenge of Practitioner-Level Realism

# 

Creating a high-fidelity PRINCE2 7th Edition Practitioner exam is significantly more complex than a standard Foundation quiz. Traditional AI generation often fails because it lacks the "trap-heavy" nuance of official PeopleCert papers. Several key engineering challenges were identified and solved:

-   **1\. The Cognitive Gap (Bloom's Taxonomy):** Most AI models default to "recall" questions. Practitioner exams require Bloom's Level 3 (Application) and Level 4 (Analysis).
    
    -   _Solution:_ The generation engine explicitly bans definitions. It forces a reasoning-based structure ("Yes, because..." / "No, because...") where every option is a plausible management action, but only one is correct based on specific PRINCE2 rules.
        
-   **2\. Knowledge Bleed & Sequence Integrity:** Large Language Models (LLMs) suffer from "knowledge bleed." If you ask for a question on _Principles_, the LLM often pulls in terminology from _Processes_ or _Practices_ prematurely, ruining the syllabus distribution.
    
    -   _Solution:_ **Programmatic Guardrails (The Kill Switch)** are implemented. The script physically intercepts the LLM output and forcefully maps it to the correct syllabus category before saving, ensuring a perfect 10/9/51/30 weighting across the 70 questions.
        
-   **3\. Role-Mapping Anonymity:** Official exams test your ability to identify who is who. If the exam says "The Executive did X," it's too easy.
    
    -   _Solution:_ The engine uses a "Hidden State" logic. It maps internal job titles (e.g., "Head of Logistics") to PRINCE2 roles (e.g., "Senior Supplier"). Questions only use the internal job titles, forcing you to deduce the correct project role before you can answer.
        
-   **4\. Mathematical Weighting & Chunking:** Feeding the entire 300-page manual to an LLM at once results in "lost-in-the-middle" hallucinations and generic questions.
    
    -   _Solution:_ **Mathematical Chunking** is utilized. The manual is sliced into 9 specific Markdown chunks under 115KB. The generator processes these one by one, ensuring every question is grounded in a specific, high-resolution context window from the official syllabus.
        
-   **5\. The 'Matching' Format Constraint:** Official exams use complex A–E matching questions (mapping 3 actions to 5 roles). These often break standard JSON schemas and simple terminal UI layouts.
    
    -   _Solution:_ A **Combination Multiple-Choice** approach is utilized. The matching items are listed in the question body, and the four options (A–D) provide different mapping combinations. This tests the same rigorous logic while maintaining a clean, terminal-compatible interface.
        

## Smart Features & Syllabus Alignment

# 

-   **Official Syllabus Weighting:** Mathematically enforces the Practitioner distribution: Principles (10%), People (9%), Practices (51%), and Processes (30%).
    
-   **Cognitive Depth:** Generates questions at Bloom's Taxonomy Levels 3 (Application) and 4 (Analysis), focusing on situational reasoning rather than simple recall.
    
-   **Standardized Rationale Template:** Every question includes a 3-part rationale (Why Correct / Why Wrong / Manual Citations) formatted in clean Markdown, stripped of conversational filler and question-ID noise.
    
-   **Programmatic Guardrails (Kill Switch):** Python-level post-processing physically intercepts the LLM's JSON output to forcefuly map sequence categories, completely eliminating cross-batch knowledge bleed.
    
-   **Auto-Recovery & Resilience:** Built-in "Wait and Retry" logic specifically designed for Tier 1 API limits. The script automatically catches rate-limit errors, pauses for 65 seconds, and retries the batch without losing progress.
    
-   **Syllabus-Targeted Auditing:** The `auditor.py` script performs a sequence integrity check, ensuring questions appear in the correct chronological order as they do in the official manual.
    
-   **Official Pass Threshold:** The interface evaluates final performance against the 42/70 (60%) pass threshold required for certification.
    

## Interactive Exam Environment Features

# 

-   **High-Contrast Interface:** A fast, command-line environment optimized for focus, featuring a high-contrast dark theme.
    
-   **Dual-Panel Navigation:** Tab-switchable layout featuring a persistent sidebar for progress tracking and a primary area for question interaction.
    
-   **Instant Feedback:** Automatically grades responses and triggers an overlay modal containing detailed explanations (rationales) for every answer.
    
-   **Scenario Reference System:** Dedicated modal overlay allows users to consult the project scenario and role mapping at any time (`s`) without losing their place in the exam.
    
-   **Progress Persistence:** Visual tracking of answered items (`[✓]`) in the navigation sidebar, with automatic lock logic to prevent re-submission.
    

## Architecture & Workflow

# 

-   **Ingestion:** Raw PDFs and Word docs are converted to clean Markdown using the Docling engine to preserve complex tables and role matrices.
    
-   **Mathematical Chunking:** The official manual is sliced into 9 strictly-sized chunks (<115KB) to respect Tier 1 LLM token limits and maintain high-precision context windows.
    
-   **Stateful Generation:** Powered by Claude 4.6 Sonnet. Uses a 16-batch architecture with 65s rate-limit mitigation and automatic XML-categorized state checkpointing to `exam_data.json`.
    
-   **Validation Engine:** An independent auditor script enforces a strict A-D schema and automatically repairs hallucinated JSON structures.
    

## Workspace Structure

# 

| Path | Description |
| --- | --- |
| `data/source_manual/` | Official PRINCE2 v7 Manual (The Ground Truth). |
| `data/golden_datasets/` | Past mock exams and rationales used for style transfer and "trap" logic. |
| `data/target_scenario/` | Specific scenario text and role outlines currently being processed. |
| `data/syllabus/` | Processed Markdown chunks used by the AI during question generation. |
| `exam_data.json` | The compiled, stateful exam output. |

## Setup & Installation

# 

1.  **Install Python Dependencies:**
    
        pip install anthropic python-dotenv textual docling
        
    
2.  **Configure API Credentials:** Create a `.env` file in the root directory and add your Anthropic API key:
    
        ANTHROPIC_API_KEY=your_api_key_here
        
    

## Complete Workflow

# 

1.  **Ingest & Chunk the Manual:**
    
        python parser.py
        python chunker.py
        
    
2.  **Generate the Exam:**
    
        python generator.py
        
    
    _Note: This takes ~30 minutes. The script will hit "Rate Limit" errors; it is programmed to wait 65s and retry automatically. Do not close the terminal._
    
3.  **Audit & Repair:**
    
        python auditor.py --repair
        
    
4.  **Launch the Exam:**
    
        python app.py
        
    

## Troubleshooting

# 

-   **Rate Limits (429 Errors):** These are normal for Tier 1 accounts. The script will log the error, wait for the reset period, and retry.
    
-   **API Credit Exhaustion (400 Errors):** If you run out of credits, the script stops. Top up your Anthropic balance and run `python generator.py` again—it will resume from the last saved question.
    
-   **Resetting the Exam:** To generate a fresh exam, delete the `exam_data.json` file.
    

## TUI Keybinds

# 

-   **Tab**: Switch focus between Sidebar and Options
    
-   **j / k** or **↑ / ↓**: Navigate lists / Scroll modals
    
-   **Enter**: Submit answer / Select question / Dismiss rationale
    
-   **s**: Toggle scenario reference overlay
    
-   **q**: Quit exam
