from pathlib import Path
import zipfile, textwrap

base = Path("/mnt/data/LUA-HUB-Connect")
(base / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

main_py = r'''"""
LUA-HUB Connect - Windows desktop starter project
Build with GitHub Actions using .github/workflows/build.yml.

This is a connection/control-panel starter, not a finished audio transport or
phone-screen receiver. The route switches and volume sliders save preferences;
they do not yet capture/stream Chrome audio, create a virtual microphone, or
mirror an Android display. Those features need a real audio/video backend and
a compatible receiver on the phone.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

APP_TITLE = "LUA-HUB Connect"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LUA-HUB" / "Connect"
CONFIG_PATH = APP_DIR / "settings.json"
PBKDF2_ITERATIONS = 310_000

BG = "#10141d"
CARD = "#1a2230"
CARD2 = "#222d3e"
FG = "#eef3fb"
MUTED = "#9ba9bd"
BLUE = "#69b5ff"
GREEN = "#48d597"
RED = "#ff777f"


def load_config():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    defaults = {"salt": "", "password_hash": "", "devices": [], "routes": {}}
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update(data)
    except (OSError, json.JSONDecodeError):
        pass
    return defaults


def save_config(config):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, indent=2), encoding="utf-8")
    tmp.replace(CONFIG_PATH)


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
    ).hex()


class LuaHub:
    ROUTES = [
        ("youtube_to_phone", "YouTube Chrome PC → HP"),
        ("pc_audio_to_phone", "Audio PC/game → HP"),
        ("youtube_to_virtual_mic", "YouTube Chrome PC → mic virtual game"),
        ("phone_audio_to_pc", "Audio HP → speaker/headphone PC"),
    ]

    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.route_enabled = {}
        self.route_volume = {}
        self.route_volume_labels = {}
        root.title(APP_TITLE)
        root.geometry("920x760")
        root.minsize(800, 650)
        root.configure(bg=BG)
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("TFrame", background=BG)
        self.style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=7)
        self.style.configure("TEntry", fieldbackground=CARD2, foreground=FG)
        self.style.configure("TCheckbutton", background=CARD2, foreground=FG)
        self.style.configure("Horizontal.TScale", background=CARD2)
        self.show_lock()

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_lock(self):
        self.clear()
        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(fill="both", expand=True)
        panel = tk.Frame(wrap, bg=CARD, padx=34, pady=30, highlightbackground="#344259", highlightthickness=1)
        panel.place(relx=.5, rely=.5, anchor="center", width=440)
        tk.Label(panel, text="LUA-HUB", bg=CARD, fg=BLUE, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(panel, text="Connect", bg=CARD, fg=FG, font=("Segoe UI", 27, "bold")).pack(anchor="w")
        tk.Label(panel, text="Koneksi perangkat • Kontrol audio • Bluetooth", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 22))

        if not self.config["password_hash"]:
            tk.Label(panel, text="Buat password aplikasi (minimal 8 karakter)", bg=CARD, fg=FG).pack(anchor="w")
            self.password_entry = ttk.Entry(panel, show="*", width=38)
            self.password_entry.pack(fill="x", pady=(6, 8), ipady=5)
            self.confirm_entry = ttk.Entry(panel, show="*", width=38)
            self.confirm_entry.pack(fill="x", pady=(0, 14), ipady=5)
            self.confirm_entry.bind("<Return>", lambda _e: self.create_password())
            ttk.Button(panel, text="Simpan password & buka aplikasi", command=self.create_password).pack(fill="x")
        else:
            tk.Label(panel, text="Masukkan password", bg=CARD, fg=FG).pack(anchor="w")
            self.password_entry = ttk.Entry(panel, show="*", width=38)
            self.password_entry.pack(fill="x", pady=(6, 14), ipady=5)
            self.password_entry.bind("<Return>", lambda _e: self.unlock())
            ttk.Button(panel, text="Buka aplikasi", command=self.unlock).pack(fill="x")
        tk.Label(panel, text="Password disimpan sebagai hash bersalt, bukan teks biasa.",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(18, 0))

    def create_password(self):
        password = self.password_entry.get()
        if len(password) < 8:
            messagebox.showwarning(APP_TITLE, "Password harus minimal 8 karakter.")
            return
        if password != self.confirm_entry.get():
            messagebox.showwarning(APP_TITLE, "Konfirmasi password tidak cocok.")
            return
        salt = secrets.token_bytes(16).hex()
        self.config["salt"] = salt
        self.config["password_hash"] = hash_password(password, salt)
        save_config(self.config)
        self.show_main()

    def unlock(self):
        password = self.password_entry.get()
        try:
            ok = hash_password(password, self.config["salt"]) == self.config["password_hash"]
        except (ValueError, KeyError):
            ok = False
        if not ok:
            messagebox.showerror(APP_TITLE, "Password salah.")
            return
        self.show_main()

    def panel(self, parent, title):
        frame = tk.Frame(parent, bg=CARD, padx=13, pady=11, highlightbackground="#344259", highlightthickness=1)
        frame.pack(fill="x", pady=(0, 10))
        tk.Label(frame, text=title, bg=CARD, fg=FG, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 9))
        return frame

    def show_main(self):
        self.clear()
        page = tk.Frame(self.root, bg=BG)
        page.pack(fill="both", expand=True, padx=18, pady=15)
        header = tk.Frame(page, bg=BG)
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="LUA-HUB Connect", bg=BG, fg=FG, font=("Segoe UI", 23, "bold")).pack(side="left")
        ttk.Button(header, text="Kunci aplikasi", command=self.show_lock).pack(side="right")

        notice = tk.Frame(page, bg="#392f1c", padx=11, pady=9, highlightbackground="#735c2c", highlightthickness=1)
        notice.pack(fill="x", pady=(0, 10))
        tk.Label(notice, text="CATATAN PROTOTIPE", bg="#392f1c", fg="#ffdc8c",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(notice, text="Tombol ON/OFF dan volume menyimpan setelan saja. Streaming audio, mic virtual, dan mirroring belum diimplementasikan; perlu backend serta receiver yang kompatibel.",
                 bg="#392f1c", fg="#f4e9cf", font=("Segoe UI", 9), wraplength=840, justify="left").pack(anchor="w", pady=(3, 0))

        self.build_connection(page)
        self.build_routes(page)
        self.build_devices(page)
        tk.Label(page, text=f"Pengaturan lokal: {CONFIG_PATH}", bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")

    def build_connection(self, parent):
        p = self.panel(parent, "1. Koneksi melalui IP")
        row = tk.Frame(p, bg=CARD)
        row.pack(fill="x")
        tk.Label(row, text="IP / hostname", bg=CARD, fg=MUTED).grid(row=0, column=0, sticky="w")
        tk.Label(row, text="Port", bg=CARD, fg=MUTED).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.host_entry = ttk.Entry(row)
        self.host_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.port_entry = ttk.Entry(row, width=9)
        self.port_entry.insert(0, "8765")
        self.port_entry.grid(row=1, column=1, padx=(10, 0), pady=(4, 0))
        ttk.Button(row, text="Tes koneksi", command=self.test_connection).grid(row=1, column=2, padx=(10, 0), pady=(4, 0))
        ttk.Button(row, text="Pengaturan Bluetooth", command=self.open_bluetooth).grid(row=1, column=3, padx=(8, 0), pady=(4, 0))
        row.columnconfigure(0, weight=1)
        self.connection_label = tk.Label(p, text="Status: belum dites", bg=CARD, fg=MUTED, font=("Segoe UI", 9))
        self.connection_label.pack(anchor="w", pady=(8, 0))

    def test_connection(self):
        host = self.host_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
            if not host or not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showwarning(APP_TITLE, "Masukkan host dan port valid (1–65535).")
            return
        self.connection_label.configure(text=f"Menguji {host}:{port} ...", fg=BLUE)

        def work():
            try:
                with socket.create_connection((host, port), timeout=3):
                    msg, color = f"Port TCP {host}:{port} dapat dihubungi; protokol audio/video belum diverifikasi.", GREEN
            except OSError as exc:
                msg, color = f"Koneksi gagal: {exc}", RED
            self.root.after(0, lambda: self.connection_label.configure(text=msg, fg=color))
        threading.Thread(target=work, daemon=True).start()

    def open_bluetooth(self):
        try:
            os.startfile("ms-settings:bluetooth")
        except (AttributeError, OSError):
            try:
                subprocess.Popen(["cmd", "/c", "start", "", "ms-settings:bluetooth"], shell=False)
            except OSError as exc:
                messagebox.showerror(APP_TITLE, f"Tidak bisa membuka Bluetooth Settings: {exc}")

    def build_routes(self, parent):
        p = self.panel(parent, "2. Audio routing — ON/OFF dan volume")
        tk.Label(p, text="Kontrol per jalur. Sampai backend audio ditambahkan, ini hanya menyimpan preferensi.",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 7))
        for key, title in self.ROUTES:
            saved = self.config.get("routes", {}).get(key, {})
            row = tk.Frame(p, bg=CARD2, padx=9, pady=6)
            row.pack(fill="x", pady=3)
            left = tk.Frame(row, bg=CARD2)
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=title, bg=CARD2, fg=FG, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            enabled = tk.BooleanVar(value=bool(saved.get("enabled", False)))
            self.route_enabled[key] = enabled
            ttk.Checkbutton(left, text="ON", variable=enabled, command=lambda k=key: self.save_route(k)).pack(anchor="w")
            volume = tk.IntVar(value=int(saved.get("volume", 70)))
            self.route_volume[key] = volume
            controls = tk.Frame(row, bg=CARD2)
            controls.pack(side="right")
            tk.Label(controls, text="Volume", bg=CARD2, fg=MUTED, font=("Segoe UI", 8)).pack(side="left", padx=(0, 6))
            ttk.Scale(controls, from_=0, to=100, variable=volume, orient="horizontal",
                      command=lambda _v, k=key: self.save_route(k)).pack(side="left")
            label = tk.Label(controls, text=f"{volume.get()}%", bg=CARD2, fg=BLUE, width=5,
                             font=("Segoe UI", 9, "bold"))
            label.pack(side="left", padx=(5, 0))
            self.route_volume_labels[key] = label
            volume.trace_add("write", lambda *_args, k=key: self.volume_changed(k))

    def volume_changed(self, key):
        self.route_volume_labels[key].configure(text=f"{self.route_volume[key].get()}%")
        self.save_route(key)

    def save_route(self, key):
        self.config.setdefault("routes", {})[key] = {
            "enabled": bool(self.route_enabled[key].get()),
            "volume": int(self.route_volume[key].get()),
        }
        save_config(self.config)

    def build_devices(self, parent):
        p = self.panel(parent, "3. Daftar perangkat tepercaya (lokal)")
        row = tk.Frame(p, bg=CARD)
        row.pack(fill="x")
        self.device_entry = ttk.Entry(row)
        self.device_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Tambah perangkat", command=self.add_device).pack(side="left", padx=(8, 0))
        ttk.Button(row, text="Cabut dari daftar", command=self.remove_device).pack(side="left", padx=(8, 0))
        self.device_list = tk.Listbox(p, height=3, bg=CARD2, fg=FG, selectbackground=BLUE, relief="flat")
        self.device_list.pack(fill="x", pady=(8, 0))
        self.refresh_devices()
        tk.Label(p, text="Daftar ini hanya tersimpan di PC, belum mengautentikasi receiver.", bg=CARD,
                 fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 0))

    def refresh_devices(self):
        self.device_list.delete(0, tk.END)
        for item in self.config.get("devices", []):
            self.device_list.insert(tk.END, item)

    def add_device(self):
        name = self.device_entry.get().strip()
        if not name:
            messagebox.showinfo(APP_TITLE, "Isi nama perangkat.")
            return
        devices = self.config.setdefault("devices", [])
        if name not in devices:
            devices.append(name)
            save_config(self.config)
            self.refresh_devices()
        self.device_entry.delete(0, tk.END)

    def remove_device(self):
        selected = self.device_list.curselection()
        if not selected:
            messagebox.showinfo(APP_TITLE, "Pilih perangkat dari daftar.")
            return
        name = self.device_list.get(selected[0])
        self.config["devices"] = [item for item in self.config.get("devices", []) if item != name]
        save_config(self.config)
        self.refresh_devices()


def main():
    root = tk.Tk()
    LuaHub(root)
    root.mainloop()


if __name__ == "__main__":
    main()
'''

workflow = r'''name: Build LUA-HUB Connect for Windows

on:
  workflow_dispatch:
  push:
    branches: [ "main" ]
    tags: [ "v*" ]

permissions:
  contents: write

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Check Python syntax
        run: python -m py_compile main.py

      - name: Install PyInstaller
        run: python -m pip install --upgrade pyinstaller

      - name: Build EXE
        run: python -m PyInstaller --noconfirm --clean --onefile --windowed --name "LUA-HUB-Connect" main.py

      - name: Upload EXE artifact
        uses: actions/upload-artifact@v4
        with:
          name: LUA-HUB-Connect-Windows
          path: dist/LUA-HUB-Connect.exe
          if-no-files-found: error

      - name: Publish EXE to GitHub Release on version tag
        if: startsWith(github.ref, 'refs/tags/v')
        uses: softprops/action-gh-release@v2
        with:
          files: dist/LUA-HUB-Connect.exe
'''

readme = r'''# LUA-HUB Connect (Windows)

Windows desktop starter project with password lock, TCP connection test, Bluetooth settings shortcut, local device list, and per-route ON/OFF/volume preferences.

## Files

- `main.py` — Python/Tkinter Windows desktop app.
- `.github/workflows/build.yml` — GitHub Actions workflow to build a Windows `.exe`.

## Build automatically on GitHub

1. Create a GitHub repository named `LUA-HUB-Connect`.
2. Upload `main.py`, `README.md`, and `.github/workflows/build.yml` while preserving the folder path.
3. Open **Actions** and enable workflows if GitHub asks.
4. Select **Build LUA-HUB Connect for Windows** → **Run workflow**.
5. When it finishes, open the successful workflow run and download the `LUA-HUB-Connect-Windows` artifact.
6. To publish a public Release download, create and push a version tag such as `v0.1.0`; the workflow will attach the EXE to that Release.

## Important feature status

This is a **starter/control-panel prototype**, not a full audio/video transport yet.

Implemented in this starter:
- First-run app password and unlock screen.
- Salted PBKDF2-HMAC-SHA256 password hash (password is not stored as plaintext).
- IP/hostname TCP connectivity test.
- Shortcut to Windows Bluetooth settings.
- Local trusted-device list.
- ON/OFF preferences and individual volume settings for the listed audio routes.

Not implemented yet:
- Capturing Chrome/YouTube audio and sending it to Android.
- Sending PC/game audio to the phone.
- Virtual microphone/audio routing into a game's microphone input.
- Receiving phone audio on the PC.
- Phone screen mirroring in portrait/landscape.

The route switches and volume sliders currently save preferences only; they do not alter or transmit real audio. Real audio routing needs a backend and often a virtual audio device. Phone audio/video needs a compatible receiver/protocol on the phone or supported native casting. An IP/port test only checks TCP reachability, not protocol support or secure authentication.

## Run locally

Install Python 3.10+ on Windows, then from this folder run:

```bat
py main.py
```

## Build locally

```bat
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "LUA-HUB-Connect" main.py
```

Output: `dist\LUA-HUB-Connect.exe`.

## GitHub Actions security

The workflow uses GitHub-hosted Windows runners. It does not require secrets. Do not upload your local settings file; the app stores it under `%LOCALAPPDATA%\LUA-HUB\Connect\settings.json`.
'''

(base / "main.py").write_text(main_py, encoding="utf-8")
(base / "README.md").write_text(readme, encoding="utf-8")
(base / ".github" / "workflows" / "build.yml").write_text(workflow, encoding="utf-8")

zip_path = Path("/mnt/data/LUA-HUB-Connect-GitHub-Source.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in base.rglob("*"):
        if p.is_file():
            zf.write(p, p.relative_to(base.parent))

print("Project package created:")
print(zip_path)
print("Files:")
for p in base.rglob("*"):
    if p.is_file():
        print(p.relative_to(base))
