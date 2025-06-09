import os
import re
import logging
from collections import Counter
import markdown
import pdfkit
from wordcloud import WordCloud

from utils.file_helpers import (
    ensure_file_output_dir,
    generate_unique_file_path,
)
from utils.diagnostics import increment_usage, time_block

logger = logging.getLogger(__name__)

def process_text_files(
    files, merge_files, deduplicate, find_str, replace_str, convert_md, freq_stats, app
):
    """Process multiple text files with optional transformations."""
    increment_usage("text")
    app.queue.put((None, "status", "Processing text files..."))
    app.start_progress()

    master_content = []
    all_words = []
    total = len(files)

    for i, file_path in enumerate(files, start=1):
        try:
            with time_block(f"text:{os.path.basename(file_path)}"):
                with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                    content = infile.read().replace('\x00', '')
            if find_str:
                content = content.replace(find_str, replace_str)
            if deduplicate:
                words = content.split()
                deduped = list(dict.fromkeys(words))
                content = " ".join(deduped)
            if merge_files:
                master_content.append(content)
            else:
                out_dir = ensure_file_output_dir(file_path)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                out_file = generate_unique_file_path(out_dir, base_name, "_processed", "txt")
                with open(out_file, 'w', encoding='utf-8', errors='replace') as outf:
                    outf.write(content)
                app.queue.put((file_path, "status", f"Processed text saved: {out_file}"))
            all_words.extend(re.findall(r"\w+", content.lower()))
            if convert_md and file_path.lower().endswith(".md"):
                convert_markdown(file_path, content, app)
        except Exception as e:
            logger.error("Error processing %s: %s", file_path, e)
            app.queue.put((file_path, "status", f"Error: {str(e)}"))
        app.increment_progress(i, total)

    if merge_files and master_content:
        try:
            merged = "\n---\n".join(master_content)
            out_dir = ensure_file_output_dir(files[0])
            merged_file = generate_unique_file_path(out_dir, "merged", "", "txt")
            with open(merged_file, 'w', encoding='utf-8', errors='replace') as mf:
                mf.write(merged)
            app.queue.put((None, "status", f"Merged text saved: {merged_file}"))
        except Exception as e:
            logger.error(f"Error merging text files: {e}")
            app.queue.put((None, "status", f"Merge Error: {str(e)}"))

    if freq_stats and all_words:
        try:
            out_dir = ensure_file_output_dir(files[0])
            freq_counter = Counter(all_words)
            generate_word_stats_and_cloud(freq_counter, out_dir, app)
        except Exception as e:
            logger.error(f"Error generating word stats: {e}")
            app.queue.put((None, "status", f"Word stats error: {str(e)}"))

    app.queue.put((None, "done", "Text processing complete."))

def convert_markdown(file_path, content, app):
    try:
        html = markdown.markdown(content)
        out_dir = ensure_file_output_dir(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        html_file = generate_unique_file_path(out_dir, base_name, "_converted", "html")
        with open(html_file, 'w', encoding='utf-8') as oh:
            oh.write(html)
        pdf_file = generate_unique_file_path(out_dir, base_name, "_converted", "pdf")
        pdfkit.from_file(html_file, pdf_file)
        app.queue.put((file_path, "status", f"Markdown converted: {html_file}, {pdf_file}"))
    except Exception as e:
        logger.error(f"Error converting MD: {e}")
        app.queue.put((file_path, "status", f"MD convert error: {str(e)}"))

def generate_word_stats_and_cloud(freq_counter, out_dir, app):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    total_words = sum(freq_counter.values())
    unique_words = len(freq_counter)
    sorted_words = freq_counter.most_common()

    stats_file = generate_unique_file_path(out_dir, "word_stats", "", "txt")
    with open(stats_file, 'w', encoding='utf-8') as sf:
        sf.write(f"Total Words: {total_words}\n")
        sf.write(f"Unique Words: {unique_words}\n\n")
        sf.write("Top 50 words:\n")
        for i, (wd, cnt) in enumerate(sorted_words[:50], start=1):
            sf.write(f"{i}. {wd} = {cnt}\n")

    wc = WordCloud(width=800, height=400, background_color='white')
    wc.generate_from_frequencies(freq_counter)
    wc_file = generate_unique_file_path(out_dir, "wordcloud", "", "png")
    wc.to_file(wc_file)

    app.queue.put((None, "status", f"Word stats saved: {stats_file}, Word cloud: {wc_file}"))
