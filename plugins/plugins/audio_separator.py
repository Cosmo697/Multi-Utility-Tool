import os
import subprocess
import threading
import tempfile
import shutil
import soundfile as sf
import warnings
import glob
import time
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# === Suppress torchaudio AudioMetaData warning ===
warnings.filterwarnings("ignore", message="`torchaudio\\.backend\\.common\\.AudioMetaData`")

# === Patch DeepFilterNet3 for cuDNN crash on non-contiguous tensors ===
try:
    import df.deepfilternet3 as dfn
    def patched_forward(self, spec, erb_feat, spec_feat):
        spec_feat = spec_feat.contiguous()
        return self._original_forward(spec, erb_feat, spec_feat)
    if hasattr(dfn.DfNet, 'forward') and not hasattr(dfn.DfNet, '_original_forward'):
        dfn.DfNet._original_forward = dfn.DfNet.forward
        dfn.DfNet.forward = patched_forward
except Exception:
    pass


def run_command(cmd, console, done_event):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        console.insert(tk.END, line)
        console.see(tk.END)
    proc.wait()
    console.insert(tk.END, f"\n--- Done (exit {proc.returncode}) ---\n")
    done_event.set()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Separator")
        self.geometry("900x600")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)

        self.demucs_tab = ttk.Frame(tabs)
        self.dpf_tab = ttk.Frame(tabs)

        tabs.add(self.demucs_tab, text="Demucs (Stem Separation)")
        tabs.add(self.dpf_tab, text="DeepFilterNet3 (Voice Denoise)")

        self.build_demucs_tab()
        self.build_dpf_tab()

    def build_demucs_tab(self):
        f = self.demucs_tab
        self.dmx_in = tk.StringVar()
        self.dmx_out = tk.StringVar()
        self.model = tk.StringVar(value="htdemucs")
        self.two_stem = tk.BooleanVar()
        self.target = tk.StringVar(value="vocals")

        ttk.Label(f, text="Input file:").grid(row=0, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.dmx_in, width=60).grid(row=0, column=1)
        ttk.Button(f, text="Browse", command=lambda: self.browse(self.dmx_in, "file")).grid(row=0, column=2)

        ttk.Label(f, text="Output folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.dmx_out, width=60).grid(row=1, column=1)
        ttk.Button(f, text="Browse", command=lambda: self.browse(self.dmx_out, "folder")).grid(row=1, column=2)

        ttk.Label(f, text="Model:").grid(row=2, column=0, sticky="w")
        ttk.Combobox(f, textvariable=self.model, values=[
            "htdemucs", "htdemucs_ft", "mdx_extra_q", "htdemucs_6s"
        ], width=20).grid(row=2, column=1, sticky="w")

        ttk.Checkbutton(f, text="2-stem mode", variable=self.two_stem, command=self.toggle_target).grid(row=3, column=0, sticky="w")
        self.target_menu = ttk.Combobox(f, textvariable=self.target, values=["vocals", "drums", "bass", "other"], state="disabled", width=10)
        self.target_menu.grid(row=3, column=1, sticky="w")

        ttk.Button(f, text="Run Demucs", command=self.run_demucs).grid(row=4, column=1)
        self.console_dmx = scrolledtext.ScrolledText(f, width=100, height=20)
        self.console_dmx.grid(row=5, column=0, columnspan=3)

    def build_dpf_tab(self):
        f = self.dpf_tab
        self.dpf_in = tk.StringVar()
        self.dpf_out = tk.StringVar()
        self.dpf_gpu = tk.BooleanVar()

        ttk.Label(f, text="Input WAV:").grid(row=0, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.dpf_in, width=60).grid(row=0, column=1)
        ttk.Button(f, text="Browse", command=lambda: self.browse(self.dpf_in, "file", [("WAV files", "*.wav")])).grid(row=0, column=2)

        ttk.Label(f, text="Output folder:").grid(row=1, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.dpf_out, width=60).grid(row=1, column=1)
        ttk.Button(f, text="Browse", command=lambda: self.browse(self.dpf_out, "folder")).grid(row=1, column=2)

        ttk.Checkbutton(f, text="Use GPU", variable=self.dpf_gpu).grid(row=2, column=0, sticky="w")

        ttk.Button(f, text="Run DeepFilter", command=self.run_dpf).grid(row=3, column=1)
        self.console_dpf = scrolledtext.ScrolledText(f, width=100, height=20)
        self.console_dpf.grid(row=4, column=0, columnspan=3)

    def browse(self, var, mode, types=None):
        val = filedialog.askopenfilename(filetypes=types) if mode == "file" else filedialog.askdirectory()
        if val: var.set(val)

    def toggle_target(self):
        self.target_menu.config(state="readonly" if self.two_stem.get() else "disabled")

    def run_demucs(self):
        inp = self.dmx_in.get()
        out = self.dmx_out.get() or os.path.dirname(inp)
        model = self.model.get()
        if not inp: return

        cmd = ["demucs", "-n", model, inp, "-o", out]
        if self.two_stem.get():
            cmd.insert(1, f"--two-stems={self.target.get()}")

        self.console_dmx.delete("1.0", tk.END)
        threading.Thread(target=run_command, args=(cmd, self.console_dmx, threading.Event()), daemon=True).start()

    def run_dpf(self):
        inp = self.dpf_in.get()
        out_dir = self.dpf_out.get() or os.path.dirname(inp)
        base = os.path.splitext(os.path.basename(inp))[0]
        out_file = os.path.join(out_dir, f"{base}_denoised.wav")

        def chunk_process():
            tmpdir = tempfile.mkdtemp()
            duration = 60.0
            try:
                y, sr = sf.read(inp)
            except Exception as e:
                self.console_dpf.insert(tk.END, f"Failed to read input file:\n{e}\n")
                return

            nchunks = int(len(y) / (sr * duration)) + 1
            outputs = []

            self.console_dpf.insert(tk.END, f"📂 Processing {nchunks} chunks from {inp}\n\n")

            for i in range(nchunks):
                start = int(i * sr * duration)
                end = int(min(len(y), (i + 1) * sr * duration))
                chunk = y[start:end]
                chunk_path = os.path.join(tmpdir, f"chunk_{i}.wav")

                sf.write(chunk_path, chunk, sr)
                cmd = ["deepFilter", chunk_path, "-o", tmpdir]
                if not self.dpf_gpu.get():
                    cmd.insert(1, "--no-gpu")

                self.console_dpf.insert(tk.END, f"▶️ Chunk {i + 1}/{nchunks}: running DeepFilter...\n")
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                self.console_dpf.insert(tk.END, result.stdout)

                # Find most recent WAV in tmpdir
                time.sleep(0.2)
                wavs = glob.glob(os.path.join(tmpdir, "*.wav"))
                if not wavs:
                    self.console_dpf.insert(tk.END, f"❌ Chunk {i + 1} produced no output file.\n\n")
                    continue
                out_chunk = max(wavs, key=os.path.getmtime)

                if os.path.isfile(out_chunk):
                    self.console_dpf.insert(tk.END, f"✅ Chunk {i + 1} processed.\n\n")
                    outputs.append(out_chunk)
                else:
                    self.console_dpf.insert(tk.END, f"❌ Chunk {i + 1} failed to produce output.\n\n")

            if not outputs:
                self.console_dpf.insert(tk.END, "❌ No chunks processed successfully. Aborting.\n")
                return

            self.console_dpf.insert(tk.END, f"\n🔄 Reassembling {len(outputs)} chunks...\n")
            try:
                with sf.SoundFile(out_file, 'w', samplerate=sr, channels=y.shape[1] if len(y.shape) > 1 else 1) as outf:
                    for f in outputs:
                        data, _ = sf.read(f)
                        outf.write(data)
                self.console_dpf.insert(tk.END, f"\n💾 Saved output: {out_file}\n")
                messagebox.showinfo("Done", f"Denoised file saved:\n{out_file}")
            except Exception as e:
                self.console_dpf.insert(tk.END, f"\n❌ Error during reassembly: {e}\n")

            shutil.rmtree(tmpdir)

        self.console_dpf.delete("1.0", tk.END)
        threading.Thread(target=chunk_process, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
