import os
import tempfile
import shutil
import pytest
import tkinter as tk
from tkinter import ttk
from plugins.plugins import file_organizer_plugin

class DummyAPI:
    def trigger_hook(self, *args, **kwargs):
        pass

@pytest.fixture
def temp_dir_with_files():
    d = tempfile.mkdtemp()
    files = []
    for i in range(3):
        f = os.path.join(d, f"file{i}.txt")
        with open(f, "w") as fp:
            fp.write(f"content {i}")
        files.append(f)
    yield d, files
    shutil.rmtree(d)

def test_list_files(temp_dir_with_files):
    d, files = temp_dir_with_files
    root = tk.Tk()
    tab = ttk.Frame(root)
    ui = file_organizer_plugin.OrganizerUI(tab, DummyAPI())
    ui.folder_var.set(d)
    ui._refresh_file_list()
    listed = [ui.file_tree.item(child)["values"][0] for child in ui.file_tree.get_children()]
    for f in files:
        assert os.path.basename(f) in listed
    root.destroy()

def test_move_files(temp_dir_with_files):
    d, files = temp_dir_with_files
    dest = tempfile.mkdtemp()
    root = tk.Tk()
    tab = ttk.Frame(root)
    ui = file_organizer_plugin.OrganizerUI(tab, DummyAPI())
    ui.folder_var.set(d)
    ui._refresh_file_list()
    # Select all files
    for child in ui.file_tree.get_children():
        ui.file_tree.selection_add(child)
    # Patch filedialog.askdirectory to return dest
    file_organizer_plugin.filedialog.askdirectory = lambda **kwargs: dest
    ui._move_files()
    # All files should now be in dest
    for f in files:
        assert os.path.exists(os.path.join(dest, os.path.basename(f)))
    root.destroy()
    shutil.rmtree(dest)

def test_delete_files(temp_dir_with_files):
    d, files = temp_dir_with_files
    root = tk.Tk()
    tab = ttk.Frame(root)
    ui = file_organizer_plugin.OrganizerUI(tab, DummyAPI())
    ui.folder_var.set(d)
    ui._refresh_file_list()
    for child in ui.file_tree.get_children():
        ui.file_tree.selection_add(child)
    # Patch messagebox.askyesno to always return True
    file_organizer_plugin.messagebox.askyesno = lambda *a, **k: True
    ui._delete_files()
    for f in files:
        assert not os.path.exists(f)
    root.destroy()

def test_rename_files(temp_dir_with_files):
    d, files = temp_dir_with_files
    root = tk.Tk()
    tab = ttk.Frame(root)
    ui = file_organizer_plugin.OrganizerUI(tab, DummyAPI())
    ui.folder_var.set(d)
    ui._refresh_file_list()
    for child in ui.file_tree.get_children():
        ui.file_tree.selection_add(child)
    # Patch simpledialog.askstring to return a new name
    file_organizer_plugin.simpledialog.askstring = lambda *a, **k: "renamed.txt"
    ui._rename_files()
    assert os.path.exists(os.path.join(d, "renamed.txt"))
    root.destroy()
