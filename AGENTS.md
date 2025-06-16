# Agent Overview

This application uses small self-contained agents to handle major features. Each agent lives in the `agents/` package and exposes a focused API.

## LoggerAgent
- **File**: `agents/logger_agent.py`
- **Responsibility**: configure root logging and provide access to loggers.
- **Key Methods**:
  - `__init__(level)` – setup rotating file and console logging.
  - `get_logger(name)` – retrieve a logger by name.

## PluginAgent
- **File**: `agents/plugin_agent.py`
- **Responsibility**: manage hooks and load plugins.
- **Key Methods**:
  - `__init__(app)` – create hooks, expose them on `app`, load plugins.
  - `trigger(hook, *args, **kwargs)` – trigger a hook.
  - `collect(hook, *args, **kwargs)` – collect results from a hook.

## HotkeyAgent
- **File**: `agents/hotkey_agent.py`
- **Responsibility**: register and manage global hotkeys.
- **Key Methods**:
  - `add_hotkey(hotkey, preset)` – register a new hotkey.
  - `remove_hotkey(hotkey)` – remove a hotkey.
  - `open_manager()` – display the hotkey management window.

## TrayAgent
- **File**: `agents/tray_agent.py`
- **Responsibility**: system tray integration for quick preset access and notifications.
- **Key Methods**:
  - `show()` – display the tray icon.
  - `notify(message)` – show a tray notification.

## UIAgent
- **File**: `agents/ui_agent.py`
- **Responsibility**: build the Tkinter user interface and handle status/progress updates.
- **Key Methods**:
  - `attach()` – bind events and start queue processing once other agents exist.
  - `add_plugin_tab(title, frame)` – add a tab supplied by a plugin.
  - `open_logs_window()` – open the live log viewer.
  - `increment_progress(current, total)` – update the progress bar via a queue.

## Application Core
- **File**: `core/app_core.py`
- **Responsibility**: initialize and connect all agents.
- **Key Methods**:
  - `__init__()` – create each agent and finalize setup.
  - `add_plugin_tab(title, frame)` – delegate to `UIAgent.add_plugin_tab`.

These agents are loosely coupled and interact through the main `AppCore` object which exposes shared resources like the Tk root window. Plugins interact with the system via `PluginAgent` and `PluginAPI`.

## Plugins Overview

Plugins extend the app with new tabs and features. Each plugin is a Python module in `plugins/plugins/` and is loaded by the `PluginAgent`. Major plugins include:

- **Audio Plugin**: Batch convert, normalize, and process audio files with presets for podcast and voiceover.
- **Audio Separator Plugin**: Separate stems (vocals, drums, etc.) using Demucs, or denoise voice with DeepFilterNet3.
- **Image Plugin**: Batch resize, reformat, and rename images with aspect ratio and margin options.
- **Text Plugin**: Merge, deduplicate, search/replace, convert, and analyze text files (with Markdown, wordcloud, etc.).
- **Video Plugin**: Extract frames/audio, join clips, convert formats, and more, with GPU acceleration.
- **Archive Plugin**: Compress files/folders to ZIP or extract ZIP archives.
- **PDF Tools Plugin**: Merge or split PDF files.
- **File Organizer Plugin**: Organize, move, copy, rename, delete files, and find/delete duplicates with flexible options.
- **HTML-to-PDF Converter Plugin**: Crawl documentation sites and render all pages to a single PDF using headless Chrome.

Each plugin registers itself with the app and can add tabs, UI, and hooks for custom actions.
