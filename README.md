# PRINCE2-Generator

A zero-bloat, terminal-native PRINCE2 7th Edition Practitioner exam generator.

## Architecture: Native Void
- **OS**: Fedora (Wayland) + Hyprland
- **UI**: Kitty + Textual (TUI)
- **Logic**: Python 3.14 + Anthropic Claude 3.5 Sonnet
- **Ingestion**: Docling (IBM) for high-fidelity PDF/DOCX parsing
- **Data**: Decoupled ~/dotfiles synced via Rclone Bisync

## Features
- **Hidden State Matrix**: Maps organizational titles (e.g., "Head of Finance") to PRINCE2 roles (e.g., "Executive") internally.
- **Deductive Testing**: Strictly forbids PRINCE2 terminology in scenario prose to force role identification.
- **Syllabus Accuracy**: Enforces 7th Edition marks allocation (Practices 51%, Processes 30%, Principles 10%, People 9%).
- **Batch Generation**: 7 batches of 10 questions to maintain reasoning integrity and prevent API timeouts.

## Workspace
- `data/source_manual/`: Official v7 Manual (Ground Truth)
- `data/golden_datasets/`: Mock exams with rationales (Style/Traps source)
- `data/target_scenario/`: Target project (e.g., Louistown)
- `data/syllabus/`: Segmented Markdown chunks for RAG context

## Commands
- `python parser.py`: Recursive Docling conversion of PDF/DOCX to Markdown.
- `python chunker.py`: Segments the manual into Syllabus-specific chunks.
- `python generator.py`: (In Development) Batch API orchestration.
- `python app.py`: (In Development) Textual TUI for interactive testing.
