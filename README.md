# Multi-Utility Tool with Plugin Support

The **Multi-Utility Tool** is a modular, cross-platform application for processing various types of media and documents. With built-in **plugin support**, new features, tabs, and enhancements can be added without modifying the core code. The default tabs (**Audio, Image, Text, Video**) are implemented as plugins, and an **HTML-to-PDF converter plugin** is included as an example.

## Features

### Plugin Architecture
- Easily extend or modify the app by adding plugins to the `plugins/` folder.

### Media Processing
- Process **audio, image, text, and video files** using dedicated plugins.

### HTML-to-PDF Converter Plugin
- Convert documentation websites into a **single PDF** using asynchronous crawling and rendering.

### Archive Plugin
- Quickly compress or extract `.zip` archives directly from the UI.

### GPU Acceleration
- Video processing tasks **automatically use GPU acceleration**, with a CPU fallback when necessary.

### Progress & Logging
- Real-time progress feedback and logging for all operations.

### Cancellation Support
- Gracefully cancel long-running operations.

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
The main window will open with **tabs for Audio, Image, Text, Video, and HTML-to-PDF Converter**.

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
```

## Changelog

- Added **Archive** plugin for compressing and extracting `.zip` files.
- Fixed text merging bug and optimized word de-duplication logic.

## Contributing & Support

### Contributions
Pull requests and issue reports are welcome. Please follow the project's coding style and contribution guidelines.

### Support
If you encounter issues or have feature suggestions, open an issue on GitHub.

## License

© 2023 Your Name. Licensed under the MIT License.

