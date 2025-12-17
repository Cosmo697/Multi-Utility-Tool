# Multi-Utility Tool with Plugin Support

The **Multi-Utility Tool** is a modular, cross-platform application for processing and organizing media and documents. With built-in **plugin support**, new features, tabs, and enhancements can be added without modifying the core code. The default tabs (**Audio, Audio Separator, Image, Text, Video, Archive, PDF Tools, File Organizer, HTML-to-PDF Converter**) are implemented as plugins.

## Features

### Plugin Architecture
- Easily extend or modify the app by adding plugins to the `plugins/` folder. Each plugin can add tabs, UI, and custom actions.

### Agent-Based Design
Core functionality is organized into small **agents** in the `agents/` package. Each agent handles one primary task (logging, plugin loading, hotkeys, tray integration, and the UI) and communicates via the `AppCore` coordinator. This structure keeps components loosely coupled and easy to test.

### Major Plugins
- **Audio Plugin**: Batch convert, normalize, and process audio files with presets for podcast and voiceover.
- **Audio Separator Plugin**: Separate stems (vocals, drums, etc.) using Demucs, or denoise voice with DeepFilterNet3.
- **Image Plugin**: Batch resize, reformat, and rename images with aspect ratio and margin options.
- **Text Plugin**: Merge, deduplicate, search/replace, convert, and analyze text files (with Markdown, wordcloud, etc.).
- **Video Plugin**: Extract frames/audio, join clips, convert formats, and more, with GPU acceleration.
- **Archive Plugin**: Compress files/folders to ZIP or extract ZIP archives.
- **PDF Tools Plugin**: Merge or split PDF files.
- **File Organizer Plugin**: Organize, move, copy, rename, delete files, and find/delete duplicates with flexible options.
- **HTML-to-PDF Converter Plugin**: Crawl documentation sites and render all pages to a single PDF using headless Chrome.

### Media Processing
- Process **audio, image, text, and video files** using dedicated plugins.

### File Organization & Deduplication
- Organize, move, copy, rename, and delete files in bulk.
- Scan for and manage duplicate files with flexible options.

### Progress & Logging
- Real-time progress feedback and logging for all operations.

### Global Hotkeys & Tray
- Assign custom shortcuts to start presets even when the app is in the background.
- Minimize to system tray with quick actions and notifications.

### Context Menus
- Right-click drop areas for actions like **Apply Preset**, **Open File Location**, and **Copy Path**.
- Optional script `scripts/install_context_menu.py` adds a Windows Explorer entry for quick sending to the app.

## Prerequisites
- **Python 3.7** or later
- **Git** (optional, for cloning the repository)
- **Google Chrome** (required for the HTML-to-PDF Converter plugin)

## Installation

1. Clone the Repository:
   ```sh
   git clone https://github.com/Cosmo697/Multi-Utility-Tool.git
   cd Multi-Utility-Tool
   ```
2. Create a Virtual Environment:
   ```sh
   python -m venv venv
   ```
3. Activate the Virtual Environment:
   - Windows:
     ```sh
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```sh
     source venv/bin/activate
     ```
4. Install Dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Running the App

With the virtual environment activated, launch the app:
   ```sh
   python app.py
   ```
The main window will open with **tabs for Audio, Audio Separator, Image, Text, Video, Archive, PDF Tools, File Organizer, and HTML-to-PDF Converter**.

## Plugin System Overview

Plugins are **Python modules** placed in the `plugins/` folder. Each plugin must define a function:
   ```python
   def register_plugin(plugin_api):
       # Your plugin code here.
   ```
The **PluginAPI** object allows you to:

- Add a New Tab:
  ```python
  plugin_api.add_tab(title, widget)
  ```
  *(Creates a new tab in the main notebook.)*

- Register Hooks:
  ```python
  plugin_api.register_hook(hook_name, callback)
  ```
  *(Modify core functionality by registering event callbacks.)*

- Access Core Components:
  ```python
  plugin_api.get_main_window()
  ```
  *(Retrieve the main application window.)*

## Example Plugin: HTML-to-PDF Converter

The example `html_to_pdf_plugin.py` in `plugins/` creates its own tab and provides an **asynchronous, GUI-driven solution** to convert documentation websites into a PDF.

### How It Works
- Asynchronous Crawling: Uses `aiohttp` and `asyncio` to crawl pages.
- Headless Chrome Rendering: Prints each page to PDF using **Google Chrome in headless mode**.
- PDF Merging: Combines PDFs into one document using `PyPDF2`.
- Progress Feedback & Cancellation: Displays a progress bar, logs, and a cancel option in the UI.

## Plugin Developer Documentation

### Creating a New Tab
Example of adding a new tab in a plugin:
   ```python
   def register_plugin(plugin_api):
       from tkinter import ttk
       new_tab = ttk.Frame(plugin_api.app.notebook)
       plugin_api.add_tab("My New Tab", new_tab)
       
       label = ttk.Label(new_tab, text="Hello from My New Tab!")
       label.pack(padx=10, pady=10)
   ```

### Extending Existing Functionality
Registering hooks to modify behavior:
   ```python
   def on_text_processed(file_path, result):
       print(f"File processed: {file_path}")
       
   def register_plugin(plugin_api):
       plugin_api.register_hook("text_processed", on_text_processed)
   ```

### Modifying Layout or Design
Access the main window and change UI properties:
   ```python
   def register_plugin(plugin_api):
       root = plugin_api.get_main_window()
       root.configure(background="#f0f0f0")
   ```

## Updated Requirements

The `requirements.txt` includes all necessary dependencies:
```
ffmpeg-python
tkinterdnd2
tk
ttkthemes
pillow
markdown
pdfkit
wordcloud
weasyprint
python-docx
pyyaml
nvidia-ml-py3
aiohttp
beautifulsoup4
PyPDF2
keyboard
pystray
pywin32
soundfile
# and any other plugin-specific dependencies
```

## Changelog

- Added **Audio Separator** plugin for stem separation and denoising.
- Improved **File Organizer** with file management and deduplication.
- Added **Archive** plugin for compressing and extracting `.zip` files.
- Added **PDF Tools** plugin for merging and splitting PDFs.
- Added global hotkey support and system tray integration.
- Fixed text merging bug and optimized word de-duplication logic.

## Contributing & Support

### Contributions
Pull requests and issue reports are welcome. Please follow the project's coding style and contribution guidelines.

### Support
If you encounter issues or have feature suggestions, open an issue on GitHub.

## License

© 2023-2025 Cosmo697. Licensed under the MIT License.

## Performance & Scalability Notes

- **Plugin discovery** runs in **O(n)** relative to the number of plugin files and avoids loading
  items outside the configured directory for security. Each plugin load is timed and logged so
  slow modules can be identified quickly.
- **Task execution** is thread-pooled with exponential backoff retries and cooperative
  cancellation; CPU-bound work scales vertically with available cores and horizontally by running
  additional worker processes or application instances.
- Expect lightweight memory overhead because plugins are streamed one by one instead of being
  preloaded. Logging and metrics use iterative writes to avoid large in-memory buffers.

