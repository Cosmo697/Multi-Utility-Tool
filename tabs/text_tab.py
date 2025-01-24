# tabs/text_tab.py

import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from queue import Empty
from datetime import datetime
from tkinterdnd2 import DND_FILES
import markdown
import pdfkit
from wordcloud import WordCloud
import logging

from utils.helpers import ensure_output_dir, find_files_in_folder, generate_unique_file_path

logger = logging.getLogger(__name__)

def setup_text_tab(tab, app):
    try:
        logger.info("Setting up Text tab.")
        ttk.Label(tab, text="Drag and drop text files or folders here for processing.").pack(pady=10)
        
        # Original
        merge_var = tk.BooleanVar(value=False)
        deduplicate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Merge Files", variable=merge_var).pack(pady=5)
        ttk.Checkbutton(tab, text="Deduplicate Words", variable=deduplicate_var).pack(pady=5)
        
        # NEW: Find & Replace
        find_label = ttk.Label(tab, text="Find:")
        find_label.pack()
        find_var = tk.StringVar(value="")
        ttk.Entry(tab, textvariable=find_var, width=20).pack()

        replace_label = ttk.Label(tab, text="Replace With:")
        replace_label.pack()
        replace_var = tk.StringVar(value="")
        ttk.Entry(tab, textvariable=replace_var, width=20).pack()

        # NEW: Convert Markdown
        convert_md_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Convert Markdown to HTML/PDF", variable=convert_md_var).pack(pady=5)

        # NEW: Word frequency/stats
        freq_stats_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Word Frequency / Stats (Generate Word Cloud)", variable=freq_stats_var).pack(pady=5)

        drop_area = create_drop_area(tab)
        drop_area.dnd_bind('<<Drop>>', lambda e: handle_text_drop(
            e, app, merge_var, deduplicate_var, find_var, replace_var, convert_md_var, freq_stats_var
        ))
        logger.info("Text tab setup complete.")
    except Exception as e:
        logger.error(f"Error setting up Text tab: {e}")
        raise

def create_drop_area(parent):
    drop_area = tk.Text(parent, width=40, height=10, bg="lightgray")
    drop_area.insert(tk.END, "Drop your text files here")
    drop_area.config(state=tk.DISABLED)
    drop_area.pack(pady=20)
    drop_area.drop_target_register(DND_FILES)
    return drop_area

def handle_text_drop(event, app, merge_var, deduplicate_var, find_var, replace_var, convert_md_var, freq_stats_var):
    try:
        logger.info("Handling dropped text files.")
        paths = app.root.tk.splitlist(event.data)
        text_files = []
        for path in paths:
            if os.path.isdir(path):
                text_files.extend(find_files_in_folder(path, valid_extensions=[".txt",".md"]))
            elif os.path.isfile(path) and path.lower().endswith((".txt",".md")):
                text_files.append(path)
                
        if not text_files:
            messagebox.showerror("Error", "No valid text files were found.")
            logger.warning("No valid text files found during drop event.")
            return

        app.start_progress()
        app.update_status("Processing text files...")
        logger.info(f"Starting processing for dropped files: {text_files}")
        t = threading.Thread(
            target=process_dropped_files,
            args=(
                text_files, merge_var.get(), deduplicate_var.get(),
                find_var.get(), replace_var.get(),
                convert_md_var.get(), freq_stats_var.get(),
                app
            ),
            daemon=True
        )
        t.start()
    except Exception as e:
        logger.error(f"Error handling text drop: {e}")
        raise

def process_dropped_files(files, merge, deduplicate, find_str, replace_str,
                          convert_md, freq_stats, app):
    try:
        logger.info("Processing dropped text files.")
        # We'll do original logic first: merge or deduplicate or copy
        # Then also do find/replace, markdown convert, and freq stats if chosen
        # Because merges or dedup might produce new files. But let's keep it simpler:
        # We'll apply original logic to each file, *plus* new logic in a single pass.

        # However, if merge is selected, we handle that in one shot:
        if merge:
            merge_text_files(files, app)
        else:
            for f in files:
                if deduplicate:
                    deduplicate_text_files(f, app)
                else:
                    copy_text_file(f, app)

        # Now do advanced find/replace, convert MD, freq stats
        handle_advanced_features(files, find_str, replace_str, convert_md, freq_stats, app)

    except Exception as e:
        logger.error(f"Error processing dropped files: {e}")
        app.queue.put((files[0], str(e)))
    finally:
        app.queue.put((files[0], "Done processing text files."))

def copy_text_file(file_path, app):
    """Original: just copy the file to 'output' folder."""
    try:
        logger.info(f"Copying text file: {file_path}")
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "text_processed")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, "_copy", ext[1:])
        with open(file_path, 'r', encoding='utf-8', errors='replace') as infile, \
             open(output_file, 'w', encoding='utf-8', errors='replace') as outfile:
            for line in infile:
                outfile.write(line)
        app.queue.put((file_path, f"Copied text to: {output_file}"))
    except Exception as e:
        logger.error(f"Error processing text file {file_path}: {e}")
        app.queue.put((file_path, str(e)))
    finally:
        app.increment_progress()

def merge_text_files(file_paths, app):
    """Original: merge multiple text files into one."""
    try:
        logger.info("Merging text files.")
        base_name = "merged"
        ext = "txt"
        output_folder = os.path.join(os.path.dirname(file_paths[0]), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, "", ext)
        with open(output_file, 'w', encoding='utf-8', errors='replace') as outfile:
            for i, file_path in enumerate(file_paths):
                with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                    outfile.write(infile.read())
                    if i < len(file_paths) - 1:
                        outfile.write("\n---\n")
        app.queue.put((file_paths[0], f"Text files merged and saved to: {output_file}"))
    except Exception as e:
        logger.error(f"Error merging text files: {e}")
        app.queue.put((file_paths[0], str(e)))
    finally:
        app.increment_progress()

def deduplicate_text_files(file_path, app):
    """Original: remove duplicate words from the file."""
    try:
        logger.info(f"Deduplicating text file: {file_path}")
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output")
        ensure_output_dir(output_folder)
        output_file = generate_unique_file_path(output_folder, base_name, "_deduplicated", ext[1:])
        unique_words = set()
        with open(file_path, 'r', encoding='utf-8', errors='replace') as infile, \
             open(output_file, 'w', encoding='utf-8', errors='replace') as outfile:
            for word in infile.read().split():
                if word not in unique_words:
                    outfile.write(word + " ")
                    unique_words.add(word)
        app.queue.put((file_path, f"Duplicate words removed, file saved to: {output_file}"))
    except Exception as e:
        logger.error(f"Error deduplicating text file {file_path}: {e}")
        app.queue.put((file_path, str(e)))
    finally:
        app.increment_progress()

# -------------- NEW FEATURES MERGED --------------

def handle_advanced_features(files, find_str, replace_str, convert_md, freq_stats, app):
    """
    For each file, do:
      1) Advanced find/replace
      2) If .md and convert_md => produce HTML + PDF
      3) If freq_stats => gather all words => then generate stats+wordcloud
    We'll do find/replace file by file, and accumulate all words in memory for freq stats.
    """
    try:
        output_folders = set()
        all_words = []
        for f in files:
            folder = advanced_process_single_file(f, find_str, replace_str, convert_md, all_words, app)
            if folder: output_folders.add(folder)

        # If freq_stats => gather stats, generate wordcloud
        if freq_stats and all_words:
            folder = generate_word_stats_and_cloud(files[0], all_words, app)
            if folder: output_folders.add(folder)
        
        # auto-open
        for of in output_folders:
            os.startfile(of)
    except Exception as e:
        logger.error(f"Error in advanced features: {e}")
        app.queue.put((files[0], str(e)))

def advanced_process_single_file(file_path, find_str, replace_str, convert_md, all_words, app):
    """
    1) Find/replace
    2) If .md => convert to HTML/PDF
    3) Accumulate words in all_words
    """
    try:
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        output_folder = os.path.join(os.path.dirname(file_path), "output", "advanced_text")
        ensure_output_dir(output_folder)

        # read the file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
            content = infile.read()

        # find/replace
        if find_str:
            # basic direct replace or re.sub
            # content = re.sub(find_str, replace_str, content)
            content = content.replace(find_str, replace_str)

        # save the updated text
        processed_txt = generate_unique_file_path(output_folder, base_name, "_adv", "txt")
        with open(processed_txt, 'w', encoding='utf-8', errors='replace') as outfile:
            outfile.write(content)

        # if .md and convert_md => produce HTML + PDF
        if ext.lower() == ".md" and convert_md:
            import markdown
            html = markdown.markdown(content)
            html_file = generate_unique_file_path(output_folder, base_name, "_converted", "html")
            with open(html_file, 'w', encoding='utf-8', errors='replace') as oh:
                oh.write(html)
            pdf_file = generate_unique_file_path(output_folder, base_name, "_converted", "pdf")
            pdfkit.from_file(html_file, pdf_file)

        # gather words
        words_in_file = re.findall(r"\w+", content.lower())
        all_words.extend(words_in_file)

        app.queue.put((file_path, f"Advanced text processing done: {processed_txt}"))
        return output_folder
    except Exception as e:
        logger.error(f"Error in advanced process for file {file_path}: {e}")
        app.queue.put((file_path, str(e)))
    finally:
        app.increment_progress()

def generate_word_stats_and_cloud(first_file, all_words, app):
    """
    Analyze word frequency, produce stats file, generate wordcloud
    """
    try:
        output_folder = os.path.join(os.path.dirname(first_file), "output", "text_stats")
        ensure_output_dir(output_folder)

        freq_dict = {}
        for w in all_words:
            freq_dict[w] = freq_dict.get(w, 0) + 1

        total_words = len(all_words)
        unique_words = len(freq_dict)
        sorted_words = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)

        stats_file = generate_unique_file_path(output_folder, "word_stats", "", "txt")
        with open(stats_file, 'w', encoding='utf-8') as sf:
            sf.write(f"Total Words: {total_words}\n")
            sf.write(f"Unique Words: {unique_words}\n\n")
            sf.write("Top 50 words:\n")
            for i, (wd, cnt) in enumerate(sorted_words[:50], start=1):
                sf.write(f"{i}. {wd} = {cnt}\n")

        # Word cloud
        from wordcloud import WordCloud
        wc = WordCloud(width=800, height=400, background_color='white')
        wc.generate_from_frequencies(freq_dict)
        wc_file = generate_unique_file_path(output_folder, "wordcloud", "", "png")
        wc.to_file(wc_file)

        app.queue.put((None, f"Word stats saved to: {stats_file}, Word cloud: {wc_file}"))
        return output_folder
    except Exception as e:
        logger.error(f"Error generating word stats/cloud: {e}")
        app.queue.put((None, f"Word stats error: {str(e)}"))
    return None
