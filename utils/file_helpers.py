import os
import logging
from constants import OUTPUT_DIR

logger = logging.getLogger(__name__)

def ensure_file_output_dir(file_path):
    directory = os.path.dirname(file_path)
    output_dir = os.path.join(directory, OUTPUT_DIR)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    return output_dir

def generate_unique_file_path(output_folder, base_name, suffix, ext):
    potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}.{ext}")
    counter = 1
    while os.path.exists(potential_file_path):
        padded_counter = f"{counter:03d}"
        potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}_{padded_counter}.{ext}")
        counter += 1
    logger.debug(f"Generated unique file path: {potential_file_path}")
    return potential_file_path

def find_files_in_folder(folder, valid_extensions=None):
    logger.info(f"Searching for files in folder: {folder}")
    valid_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if valid_extensions is None or file.lower().endswith(valid_extensions):
                valid_files.append(os.path.join(root, file))
    logger.info(f"Found {len(valid_files)} valid files in folder: {folder}")
    return valid_files

def create_drop_area(parent, width=40, height=10, text_str="Drop files here"):
    import tkinter as tk
    from tkinterdnd2 import DND_FILES
    drop_area = tk.Text(parent, width=width, height=height, bg="#3e3e3e", fg="#d3d3d3")
    drop_area.insert(tk.END, text_str)
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=10, fill=tk.BOTH, expand=True)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def read_file_content(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == ".md":
        import markdown
        with open(file_path, 'r', encoding='utf-8') as f:
            return markdown.markdown(f.read())
    elif ext in [".rtf", ".html", ".htm", ".xml", ".py"]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == ".json":
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f), indent=4)
    elif ext == ".csv":
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            return "\n".join([", ".join(row) for row in reader])
    elif ext in [".yaml", ".yml"]:
        import yaml
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.dump(yaml.safe_load(f))
    elif ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    elif ext == ".pdf":
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)
            return "\n".join([reader.getPage(i).extract_text() for i in range(reader.numPages)])
    else:
        return "Unsupported file format."
