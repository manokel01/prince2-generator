import os
from pathlib import Path
from docling.document_converter import DocumentConverter

def convert_documents():
    base_dir = Path("data")
    converter = DocumentConverter()
    
    if not base_dir.exists():
        print(f"Error: Directory '{base_dir}' not found. Please ensure it exists.")
        return

    # Recursively find all PDFs and Word documents in all subfolders
    extensions = ["*.pdf", "*.docx", "*.doc"]
    files_to_convert = []
    for ext in extensions:
        files_to_convert.extend(base_dir.rglob(ext))
    
    if not files_to_convert:
        print("No documents found in the 'data' directory or its subfolders.")
        return

    print(f"Found {len(files_to_convert)} files. Starting conversion...")

    for file_path in files_to_convert:
        # relative_to keeps the terminal output clean (e.g., "golden_datasets/NowByou_scenario.pdf")
        print(f"Converting: {file_path.relative_to(base_dir)}")
        try:
            result = converter.convert(file_path)
            
            # Output the Markdown file next to the original file
            output_filename = file_path.with_suffix('.md')
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(result.document.export_to_markdown())
                
            print(f"Saved: {output_filename.relative_to(base_dir)}")
        except Exception as e:
            print(f"Failed to convert {file_path.name}: {e}")

if __name__ == "__main__":
    convert_documents()
