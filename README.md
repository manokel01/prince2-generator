# PRINCE2 Practitioner Exam Generator

# 

A terminal-based application designed to generate high-fidelity mock exams for the PRINCE2 7th Edition Practitioner qualification.

## Project Overview

# 

This tool transforms a raw business scenario into a 70-mark mock exam. It uses Retrieval-Augmented Generation (RAG) to ensure every question is grounded in the official v7 manual while mimicking the "trap-heavy" style of official PeopleCert papers.

## Smart Features & Syllabus Alignment

# 

-   **Strict Syllabus Weighting:** Mathematically enforces the official Practitioner distribution: Principles (10%), People (9%), Practices (51%), and Processes (30%).
    
-   **Cognitive Targeting:** Forces the LLM to generate questions strictly at Bloom's Taxonomy Levels 3 (Application) and 4 (Analysis), explicitly banning Level 1/2 recall questions.
    
-   **Anti-Clumping & Hallucination Defenses:** Instructs the LLM to distribute questions evenly across chunked content and explicitly bans PeopleCert's "Matching" format to ensure compatibility with single-character A-D options.
    
-   **Intelligent Auditor:** Performs a full Sequence Integrity Audit, auto-sorts questions into their correct chronological chapter order, and maps generated topics to official syllabus boundaries.
    
-   **Official Pass Threshold:** The interface evaluates the final score against the strict 42/70 (60%) pass mark required for Practitioner certification.
    

## Interactive Exam Environment Features

# 

-   **High-Contrast Interface:** A fast, command-line environment optimized for focus, featuring a high-contrast dark theme and minimal visual overhead.
    
-   **Dual-Panel Navigation:** Focus-switchable layout featuring a persistent sidebar for progress tracking and a primary area for question interaction.
    
-   **Instant Feedback & Rationales:** Automatically grades responses and triggers an overlay modal containing detailed, color-coded explanations for every answer.
    
-   **Scenario Reference System:** Dedicated modal overlay allows users to consult the project scenario and role mapping at any time without losing their current position in the exam.
    
-   **Progress Persistence:** Visual tracking of answered items (`[✓]`) in the navigation sidebar, with automatic gray-out and lock logic to prevent re-submission.
    
-   **Keyboard-First Workflow:** Comprehensive support for Vim-style navigation (`j`/`k`) and arrow keys for scrolling through scenario text and selecting options.
    

## Architecture & Workflow

# 

-   **Ingestion:** Raw PDFs and Word docs are converted to clean Markdown using the Docling engine to preserve complex tables and role matrices.
    
-   **Mathematical Chunking:** The official manual is sliced into 9 strictly-sized chunks (<115KB) to respect Tier 1 LLM token limits and maintain high-precision context windows.
    
-   **Hidden State Logic:** The engine internally maps organizational titles to PRINCE2 roles, generating scenario narratives that avoid PRINCE2 terminology to test the candidate's ability to deduce roles.
    
-   **Stateful Generation:** Powered by Claude 3.5 Sonnet. Uses a 16-batch architecture with 65s rate-limit mitigation and automatic XML-categorized state checkpointing.
    
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
        
    
3.  **Audit & Repair:**
    
        python auditor.py --repair
        
    
4.  **Launch the Exam:**
    
        python app.py
        
    

## TUI Keybinds

# 

-   **Tab**: Switch focus between Sidebar and Options
    
-   **j / k** or **↑ / ↓**: Navigate lists / Scroll modals
    
-   **Enter**: Submit answer / Select question / Dismiss rationale
    
-   **s**: Toggle scenario reference overlay
    
-   **q**: Quit exam
