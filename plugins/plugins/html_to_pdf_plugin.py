import os
import sys
import subprocess
import tempfile
import shutil
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from PyPDF2 import PdfMerger
from bs4 import BeautifulSoup
import urllib.parse
import asyncio
import aiohttp
import time


# Exception for cancellations
class OperationCancelled(Exception):
    pass


def canonicalize(url):
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
    )


def render_page_to_pdf(chrome_path, url, output_path, cancel_event):
    process = subprocess.Popen(
        [
            chrome_path,
            "--headless",
            "--disable-gpu",
            f"--print-to-pdf={output_path}",
            url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    while True:
        if cancel_event.is_set():
            process.kill()
            process.communicate()
            raise OperationCancelled(f"Rendering cancelled for {url}")
        ret = process.poll()
        if ret is not None:
            if ret != 0:
                stdout, stderr = process.communicate()
                raise RuntimeError(f"Error rendering {url} to PDF: {stderr.decode()}")
            break
        time.sleep(0.1)


def merge_pdfs(pdf_files, output_path):
    merger = PdfMerger()
    for pdf in pdf_files:
        merger.append(pdf)
    merger.write(output_path)
    merger.close()


async def async_crawl_docs(start_url, cancel_event, log_callback):
    visited = set()
    queue = asyncio.Queue()
    await queue.put(start_url)
    parsed = urllib.parse.urlparse(start_url)
    base_path = os.path.dirname(parsed.path)
    if not base_path.endswith("/"):
        base_path += "/"
    base_url = f"{parsed.scheme}://{parsed.netloc}{base_path}"

    async with aiohttp.ClientSession() as session:

        async def worker():
            while True:
                try:
                    url = await asyncio.wait_for(queue.get(), timeout=0.2)
                except asyncio.TimeoutError:
                    if cancel_event.is_set() or queue.empty():
                        break
                    continue
                if cancel_event.is_set():
                    queue.task_done()
                    break
                if url in visited:
                    queue.task_done()
                    continue
                visited.add(url)
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status != 200:
                            log_callback(
                                f"Warning: {url} returned status code {response.status}."
                            )
                            queue.task_done()
                            continue
                        text = await response.text()
                        soup = BeautifulSoup(text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            absolute_url = urllib.parse.urljoin(url, href)
                            absolute_url = canonicalize(absolute_url)
                            if (
                                absolute_url.startswith(base_url)
                                and absolute_url not in visited
                            ):
                                await queue.put(absolute_url)
                except Exception as e:
                    log_callback(f"Warning: error fetching {url}: {e}")
                queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(10)]
        await asyncio.gather(*workers)
    if cancel_event.is_set():
        raise OperationCancelled("Operation cancelled during crawling.")
    return list(visited)


async def async_render_pages(
    urls, chrome_path, temp_dir, cancel_event, log_callback, progress_update_callback
):
    semaphore = asyncio.Semaphore(4)
    loop = asyncio.get_event_loop()

    async def render_page(idx, page_url):
        if cancel_event.is_set():
            raise OperationCancelled("Operation cancelled before rendering page.")
        output_file = os.path.join(temp_dir, f"page_{idx:03d}.pdf")
        async with semaphore:
            await loop.run_in_executor(
                None,
                render_page_to_pdf,
                chrome_path,
                page_url,
                output_file,
                cancel_event,
            )
        progress_update_callback(1)
        log_callback(f"Rendered {page_url} to PDF.")
        return idx, output_file

    tasks = [asyncio.create_task(render_page(idx, url)) for idx, url in enumerate(urls)]
    pdf_files = [None] * len(urls)
    try:
        for task in asyncio.as_completed(tasks):
            if cancel_event.is_set():
                for t in tasks:
                    t.cancel()
                raise OperationCancelled("Operation cancelled during rendering.")
            idx, pdf_file = await task
            pdf_files[idx] = pdf_file
    except asyncio.CancelledError:
        raise OperationCancelled("Operation cancelled during rendering.")
    return pdf_files


async def generate_pdf_async(
    url,
    output_path,
    chrome_path,
    log_callback,
    progress_init_callback,
    progress_update_callback,
    cancel_event,
):
    log_callback("Crawling documentation asynchronously...")
    urls = await async_crawl_docs(url, cancel_event, log_callback)
    if cancel_event.is_set():
        raise OperationCancelled("Operation cancelled during crawling.")
    if not urls:
        log_callback("Error: No documentation pages found.")
        return False
    log_callback(f"Found {len(urls)} pages. Starting asynchronous rendering...")
    progress_init_callback(len(urls))
    temp_dir = tempfile.mkdtemp(prefix="doc_pdf_")
    try:
        pdf_files = await async_render_pages(
            urls,
            chrome_path,
            temp_dir,
            cancel_event,
            log_callback,
            progress_update_callback,
        )
        if cancel_event.is_set():
            raise OperationCancelled("Operation cancelled before merging PDFs.")
        log_callback("Merging individual PDFs into final document...")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, merge_pdfs, pdf_files, output_path)
        log_callback(f"PDF generated successfully: {output_path}")
    finally:
        shutil.rmtree(temp_dir)
    return True


class HtmlToPdfPlugin(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.last_output_path = None
        self.cancel_event = None
        self.build_ui()

    def build_ui(self):
        # Layout configuration
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Documentation URL:").grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        self.url_entry = ttk.Entry(self, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Output PDF Filename:").grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        self.out_entry = ttk.Entry(self, width=60)
        self.out_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self, text="Chrome Path:").grid(
            row=2, column=0, sticky="e", padx=5, pady=5
        )
        self.chrome_entry = ttk.Entry(self, width=60)
        self.chrome_entry.insert(
            0, r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        )
        self.chrome_entry.grid(row=2, column=1, padx=5, pady=5)

        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.generate_button = ttk.Button(
            self.button_frame, text="Generate PDF", command=self.on_generate
        )
        self.generate_button.grid(row=0, column=0, padx=5)

        self.cancel_button = ttk.Button(
            self.button_frame, text="Cancel", command=self.on_cancel, state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, padx=5)

        self.open_dir_button = ttk.Button(
            self.button_frame,
            text="Open Output Directory",
            command=self.open_output_directory,
            state="disabled",
        )
        self.open_dir_button.grid(row=0, column=2, padx=5)

        self.progress_bar = ttk.Progressbar(
            self, orient="horizontal", length=400, mode="determinate"
        )
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.log_text = tk.Text(self, height=12, width=80, state="normal")
        self.log_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        self.scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=5, column=2, sticky="ns")

    def log_message(self, message):
        self.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def progress_init(self, total):
        self.after(0, lambda: self._init_progress(total))

    def _init_progress(self, total):
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = total

    def progress_update(self, increment):
        self.after(0, lambda: self._update_progress(increment))

    def _update_progress(self, increment):
        self.progress_bar["value"] += increment

    def on_generate(self):
        url = self.url_entry.get().strip()
        out_filename = self.out_entry.get().strip()
        chrome_path = self.chrome_entry.get().strip()
        if not url or not out_filename or not chrome_path:
            messagebox.showerror("Error", "Please fill all fields.")
            return
        if not os.path.isfile(chrome_path):
            messagebox.showerror(
                "Error", f"Chrome executable not found at {chrome_path}"
            )
            return
        if not out_filename.lower().endswith(".pdf"):
            out_filename += ".pdf"
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, out_filename)
        self.generate_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.open_dir_button.config(state="disabled")
        self.log_text.delete(1.0, tk.END)
        self.progress_bar["value"] = 0
        self.cancel_event = threading.Event()
        self.api.start_thread(
            target=self.run_generate,
            args=(url, out_filename, chrome_path),
        )

    def on_cancel(self):
        if self.cancel_event:
            self.cancel_event.set()
            self.log_message("Cancellation requested.")
            self.cancel_button.config(state="disabled")

    def open_output_directory(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            directory = os.path.dirname(os.path.abspath(self.last_output_path))
            try:
                if sys.platform.startswith("win"):
                    os.startfile(directory)
                elif sys.platform.startswith("darwin"):
                    subprocess.run(["open", directory])
                else:
                    subprocess.run(["xdg-open", directory])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open directory: {e}")
        else:
            messagebox.showerror("Error", "Output file not found.")

    def run_generate(self, url, out_filename, chrome_path):
        try:
            asyncio.run(
                generate_pdf_async(
                    url,
                    out_filename,
                    chrome_path,
                    self.log_message,
                    self.progress_init,
                    self.progress_update,
                    self.cancel_event,
                )
            )
            self.log_message("Process completed successfully.")
            self.last_output_path = os.path.abspath(out_filename)
            self.after(0, lambda: self.open_dir_button.config(state="normal"))
        except OperationCancelled as oc:
            self.log_message(f"Cancelled: {oc}")
        except Exception as e:
            self.log_message(f"Process encountered errors: {e}")
        finally:
            self.after(0, lambda: self.generate_button.config(state="normal"))
            self.after(0, lambda: self.cancel_button.config(state="disabled"))


def register_plugin(plugin_api):
    # Create a new tab and instantiate the HTML-to-PDF converter UI.
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("HTML to PDF Converter", tab)
    converter = HtmlToPdfPlugin(tab)
    converter.pack(fill=tk.BOTH, expand=True)
