# app.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD
from queue import Queue, Empty
from tabs import setup_audio_tab, setup_image_tab, setup_text_tab, setup_video_tab
from utils.logging_config import setup_logging

# Setup Logging
setup_logging()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Utility Application")
        self.create_main_tabs()
        self.progress_bar = self.create_progress_bar()
        self.status_label = self.create_status_label()
        self.queue = Queue()  # Shared Queue for all tabs
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_main_tabs(self):
        tab_control = ttk.Notebook(self.root)
        
        audio_tab = ttk.Frame(tab_control)
        image_tab = ttk.Frame(tab_control)
        text_tab = ttk.Frame(tab_control)
        video_tab = ttk.Frame(tab_control)
        
        tab_control.add(audio_tab, text='Audio')
        tab_control.add(image_tab, text='Images')
        tab_control.add(text_tab, text='Text')
        tab_control.add(video_tab, text='Video')
        
        tab_control.pack(expand=1, fill='both')
        
        setup_audio_tab(audio_tab, self)
        setup_image_tab(image_tab, self)
        setup_text_tab(text_tab, self)
        setup_video_tab(video_tab, self)

    def create_progress_bar(self):
        progress = ttk.Progressbar(self.root, orient='horizontal', mode='indeterminate', length=280)
        progress.pack(pady=20)
        return progress

    def create_status_label(self):
        status_label = tk.Label(self.root, text="")
        status_label.pack(pady=10)
        return status_label

    def start_progress(self):
        self.progress_bar.start()

    def stop_progress(self):
        self.progress_bar.stop()

    def update_status(self, message):
        self.status_label.config(text=message)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = App(root)
    root.mainloop()