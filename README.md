# Multi-Utility Tool with Plugin Support

This application is a multi-utility tool with a modular, plugin-based architecture. It allows you to process audio, image, text, and video files. The built-in tabs are implemented as the first set of plugins, and additional plugins can be added by dropping new modules into the `plugins/` directory.

## Prerequisites

- Python 3.7 or later
- Git (optional, for cloning the repository)

## Installation

1. **Clone the Repository** (or download the source code)
   git clone https://github.com/yourusername/multi_utility_app.git
   cd multi_utility_app

2. **Create a Virtual Environment**
   python -m venv venv

3. **Activate the Virtual Environment**  
   - On Windows:
     venv\Scripts\activate

   - On macOS and Linux:
     source venv/bin/activate

4. **Install Dependencies**
   pip install -r requirements.txt

## Running the App

With the virtual environment activated, run the app using:

python app.py

The application window will launch with the built-in plugin tabs (Audio, Image, Text, and Video). You can extend the app by adding additional plugin modules in the `plugins/` directory. Each plugin should implement a `register_plugin(plugin_api)` function to integrate with the core application.

## Adding New Plugins

1. Create a new Python module (e.g., `my_plugin.py`) in the `plugins/` directory.
2. Define a `register_plugin(plugin_api)` function in your module. Use the methods provided by the plugin API to add tabs, register hooks, or modify existing functionality.

### Example:

def register_plugin(plugin_api):
    from tkinter import ttk
    tab = ttk.Frame(plugin_api.app.notebook)
    plugin_api.add_tab("My Plugin", tab)
    label = ttk.Label(tab, text="Hello from My Plugin!")
    label.pack(padx=10, pady=10)
    # Additional functionality can be added here.

## Logging

The application logs messages to both the console and a log file located at `logs/app.log`.

## Deactivating the Virtual Environment

When you're done, deactivate the virtual environment with:

deactivate

## License

© 2025 Mortl. Licensed under the MIT License.
