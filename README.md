# Multi-Utility Tool with Plugin Support

The Multi-Utility Tool is a modular, cross‑platform application for processing various types of media and documents. Built with plugin support, it allows you to add new features, tabs, and enhancements without modifying the core code. The built‑in tabs (Audio, Image, Text, Video) are implemented as plugins, and an example HTML‑to‑PDF converter plugin is provided.

## Features

- **Plugin Architecture:**  
  Easily extend or modify the app by adding plugins in the `plugins/` folder.  
- **Media Processing:**  
  Process audio, image, text, and video files with dedicated plugins.
- **HTML-to-PDF Converter Plugin:**  
  Convert documentation websites to a single PDF using asynchronous crawling and rendering.
- **GPU Acceleration:**  
  Video processing tasks automatically attempt to use GPU acceleration (with a CPU fallback).
- **Progress & Logging:**  
  Real‑time progress feedback and logging for all operations.
- **Cancellation Support:**  
  Cancel long‑running operations gracefully.

## Prerequisites

- Python 3.7 or later  
- Git (optional, for cloning the repository)  
- Google Chrome (for the HTML‑to‑PDF Converter plugin; ensure its path is correctly set)

## Installation

1. **Clone the Repository:**

   git clone https://github.com/yourusername/multi_utility_app.git
   cd multi_utility_app
   
Create a Virtual Environment:
python -m venv venv

Activate the Virtual Environment:
On Windows:
venv\Scripts\activate

On macOS and Linux:
source venv/bin/activate

Install Dependencies:
pip install -r requirements.txt

Running the App
With the virtual environment activated, launch the app:
python app.py

The main window will open with tabs for Audio, Image, Text, Video, and HTML to PDF Converter.

Plugin System Overview
Plugins are Python modules placed in the plugins/ folder. Each plugin must define a function called register_plugin(plugin_api). The PluginAPI object passed to this function allows you to:

Add a New Tab:
Use plugin_api.add_tab(title, widget) to add a new tab to the main notebook.

Register Hooks:
Extend or modify core functionality by registering callbacks via plugin_api.register_hook(hook_name, callback).

Access Core Components:
Retrieve the main window using plugin_api.get_main_window() or interact with other UI elements through plugin_api.app.

Example Plugin: HTML-to-PDF Converter
An example plugin named html_to_pdf_plugin.py is provided in the plugins/ folder. It creates its own tab and offers an asynchronous, GUI‑driven solution to convert documentation websites to a PDF.

How It Works:
Asynchronous Crawling:
Uses aiohttp and asyncio to crawl documentation pages.

Headless Chrome Rendering:
Invokes Google Chrome in headless mode to print each page to PDF.

PDF Merging:
Merges individual PDFs into one final document using PyPDF2.

Progress Feedback & Cancellation:
Provides a progress bar, logging output, and a cancel option in the UI.

Plugin Developer Documentation
To write a plugin for this app, please refer to the following guidelines:

1. Plugin File & Naming
Place your plugin in the plugins/ folder.
Name your plugin file descriptively (e.g., my_plugin.py).
The file must define a function:
python

def register_plugin(plugin_api):
    # Your plugin code here.

2. PluginAPI Methods
Your plugin_api object provides these methods:

add_tab(title: str, widget: tk.Widget)
Adds a new tab to the main notebook.
register_hook(hook_name: str, callback: callable)
Registers a callback for a hook event (e.g., after processing a file).
trigger_hook(hook_name: str, *args, **kwargs)
(Advanced) Manually trigger a hook.
get_main_window()
Returns the main tkinter window.

3. Creating a New Tab
Example – creating a new tab:
python

def register_plugin(plugin_api):
    from tkinter import ttk
    new_tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("My New Tab", new_tab)
    
    label = ttk.Label(new_tab, text="Hello from My New Tab!")
    label.pack(padx=10, pady=10)

4. Extending Existing Functionality
You can register hooks to modify behavior:
python

def on_text_processed(file_path, result):
    print(f"File processed: {file_path}")

def register_plugin(plugin_api):
    plugin_api.register_hook("text_processed", on_text_processed)

5. Modifying Layout or Design
Access the main window and change UI properties:
python

def register_plugin(plugin_api):
    root = plugin_api.get_main_window()
    root.configure(background="#f0f0f0")
Updated Requirements
The requirements.txt file includes all dependencies required by the core app and plugins:


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

Contributing & Support

Contributions:
Pull requests and issues are welcome. Please follow the code style of the project.
Support:
Open an issue on GitHub if you encounter problems or have suggestions for new features.

License
© 2023 Your Name. Licensed under the MIT License.