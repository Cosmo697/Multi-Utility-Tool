import os
import logging

def ensure_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def update_status_label(label, message):
    label.config(text=message)
    logging.info(message)

def find_files_in_folder(folder, valid_extensions=None):
    """Recursively find files within a folder."""
    for root, _, files in os.walk(folder):
        for file in files:
            if valid_extensions is None or file.lower().endswith(tuple(valid_extensions)):
                yield os.path.join(root, file)