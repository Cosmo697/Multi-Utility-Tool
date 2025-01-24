# utils/helpers.py

import os
import logging
import threading
from queue import Queue

logger = logging.getLogger(__name__)

def thread_safe_queue_put(queue, item):
    """
    Safely add an item to the queue in a thread-safe manner.
    """
    try:
        logger.debug(f"Attempting to add item to queue: {item}")
        with threading.Lock():
            queue.put(item)
        logger.info(f"Successfully added item to queue: {item}")
    except Exception as e:
        logger.error(f"Error adding item to queue: {e}")
        raise

def ensure_output_dir(output_dir):
    """
    Ensure the output directory exists, creating it if necessary.
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        else:
            logger.debug(f"Output directory already exists: {output_dir}")
    except Exception as e:
        logger.error(f"Error creating output directory: {e}")
        raise

def find_files_in_folder(folder, valid_extensions=None):
    """
    Recursively find files in the specified folder with valid extensions.
    """
    try:
        logger.info(f"Searching for files in folder: {folder}")
        valid_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if valid_extensions is None or file.lower().endswith(tuple(valid_extensions)):
                    valid_files.append(os.path.join(root, file))
        logger.info(f"Found {len(valid_files)} valid files in folder: {folder}")
        return valid_files
    except Exception as e:
        logger.error(f"Error finding files in folder {folder}: {e}")
        raise

def update_status_label(status_label, message):
    """
    Update a Tkinter status label with a given message.
    """
    try:
        status_label.config(text=message)
        logger.debug(f"Updated status label with message: {message}")
    except Exception as e:
        logger.error(f"Error updating status label: {e}")
        raise

def thread_safe_queue_get(queue):
    """
    Safely retrieve an item from the queue in a thread-safe manner.
    """
    try:
        logger.debug("Attempting to get item from queue.")
        with threading.Lock():
            item = queue.get()
        logger.info(f"Successfully retrieved item from queue: {item}")
        return item
    except Exception as e:
        logger.error(f"Error retrieving item from queue: {e}")
        raise

def generate_unique_file_path(output_folder, base_name, suffix, ext):
    """
    Generate a unique file path by appending a counter if the file already exists.
    """
    try:
        potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}.{ext}")
        counter = 1
        while os.path.exists(potential_file_path):
            padded_counter = f"{counter:03}"
            potential_file_path = os.path.join(output_folder, f"{base_name}{suffix}_{padded_counter}.{ext}")
            counter += 1
        logger.debug(f"Generated unique file path: {potential_file_path}")
        return potential_file_path
    except Exception as e:
        logger.error(f"Error generating unique file path: {e}")
        raise
