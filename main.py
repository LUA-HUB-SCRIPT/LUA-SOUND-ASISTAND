import json
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

APP_NAME = "LUA-HUB Connect"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LUA-HUB" / "Connect"
CONFIG_FILE = APP_DIR / "settings.json"

BG = "#10141d"
PANEL = "#1a2230"
PANEL2 = "#222d3e"
FG = "#eef3fb"
MUTED = "#9ba9bd"
BLUE = "#69b5ff"
GREEN = "#48d597"
RED = "#ff777f"


def load_settings():
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, ValueError):
        pass

    return {"volumes": {}, "routes": {}}


def save_settings(data):
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
    except OSError as exc:
        messagebox.showerror(
            "Gagal menyimpan",
            f"Pengaturan tidak bisa disimpan:\n{exc}"
        )


class LuaHubApp:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.route_vars = {}
        self.volume_vars = {}
        self.status_vars = {}

        root.title(APP_NAME)
        root.geometry("940x720")
        root.minsize(760, 600)
        root.configure(bg=BG)

        self.setup_style()
        self.build_ui()

        root.protocol("WM_DELETE_WINDOW", self.close_app)

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TScale",
            background=PANEL,
            troughcolor=PANEL2
        )

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        header.pack(fill="x")

        tk.Label(
            header,
            text="LUA-HUB",
            bg=BG,
            fg=BLUE,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Connect",
            bg=BG,
            fg=FG,
            font=("Segoe UI", 28, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Wireless Media Control Panel",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(2, 0))

        self.status_label = tk.Label(
            header,
            text="● Aplikasi siap",
            bg=BG,
            fg=GREEN,
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(anchor="w", pady=(12, 0))

        body = tk.Frame(self.root, bg=BG, padx=24)
        body.pack(fill="both", expand=True)

        self.build_device_panel(body)
        self.build_routes_panel(body)
        self.build_tools_panel(body)

        footer = tk.Frame(self.root, bg=BG, padx=24, pady=12)
        footer.pack(fill="x")

        tk.Label(
            footer,
            text="LUA HUB • Desktop Assistant",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Button(
            footer,
            text="Simpan Pengaturan",
            command=self.save_all,
            bg=BLUE,
            fg="#10141d",
            activebackground="#91caff",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2"
        ).pack(side="right")

    def make_panel(self, parent, title):
        frame = tk.Frame(
            parent,
            bg=PANEL,
            padx=18,
            pady=14,
            highlightbackground="#344259",
            highlightthickness=1
        )
        frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            frame,
            text=title,
            bg=PANEL,
            fg=FG,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        return frame

    def build_device_panel(self, parent):
        panel = self.make_panel(parent, "Perangkat")

        tk.Label(
            panel,
            text=(
                "Hubungkan PC dan HP melalui jaringan Wi-Fi yang sama "
                "atau Bluetooth."
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        buttons = tk.Frame(panel, bg=PANEL)
        buttons.pack(fill="x")

        tk.Button(
            buttons,
            text="Pengaturan Wi-Fi",
            command=lambda: self.open_settings("ms-settings:network-wifi"),
            bg=PANEL2,
            fg=FG,
            relief="flat",
            padx=12,
            pady=8
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Pengaturan Bluetooth",
            command=lambda: self.open_settings(
                "ms-settings:bluetooth"
            ),
            bg=PANEL2,
            fg=FG,
            relief="flat",
            padx=12,
            pady=8
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Pengaturan Suara",
            command=lambda: self.open_settings("ms-settings:sound"),
            bg=PANEL2,
            fg=FG,
            relief="flat",
            padx=12,
            pady=8
        ).pack(side="left")

    def build_routes_panel(self, parent):
        panel = self.make_panel(parent, "Rute Media")

        routes = [
            (
                "youtube_to_phone",
                "YouTube / Browser PC → HP"
            ),
            (
                "pc_audio_to_phone",
                "Audio PC / Game → HP"
            ),
            (
                "youtube_to_virtual_mic",
                "Audio Browser → Mikrofon Virtual"
            ),
            (
                "phone_audio_to_pc",
                "Audio HP → Speaker PC"
            ),
        ]

        saved_routes = self.settings.get("routes", {})
        saved_volumes = self.settings.get("volumes", {})

        for route_id, title in routes:
            row = tk.Frame(panel, bg=PANEL)
            row.pack(fill="x", pady=7)

            enabled = tk.BooleanVar(
                value=bool(saved_routes.get(route_id, False))
            )

            self.route_vars[route_id] = enabled

            tk.Checkbutton(
                row,
                text=title,
                variable=enabled,
                command=self.update_route_status,
                bg=PANEL,
                fg=FG,
                selectcolor=PANEL2,
                activebackground=PANEL,
                activeforeground=FG,
                font=("Segoe UI", 10)
            ).pack(side="left", anchor="w")

            volume = tk.DoubleVar(
                value=float(saved_volumes.get(route_id, 70))
            )
            self.volume_vars[route_id] = volume

            slider = ttk.Scale(
                row,
                from_=0,
                to=100,
                variable=volume,
                orient="horizontal",
                length=160
            )
            slider.pack(side="right", padx=(8, 0))

            value_label = tk.Label(
                row,
                text=f"{int(volume.get())}%",
                bg=PANEL,
                fg=BLUE,
                width=5,
                font=("Segoe UI", 9)
            )
            value_label.pack(side="right")

            volume.trace_add(
                "write",
                lambda *_,
                var=volume,
                label=value_label: label.config(
                    text=f"{int(var.get())}%"
                )
            )

    def build_tools_panel(self, parent):
        panel = self.make_panel(parent, "Kontrol Aplikasi")

        tk.Label(
            panel,
            text=(
                "Tombol berikut membuka utilitas Windows. "
                "Pengaturan rute dan volume aplikasi dapat disimpan."
            ),
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=800,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        buttons = tk.Frame(panel, bg=PANEL)
        buttons.pack(fill="x")

        tk.Button(
            buttons,
            text="Buka Mixer Volume",
            command=self.open_volume_mixer,
            bg=PANEL2,
            fg=FG,
            relief="flat",
            padx=12,
            pady=8
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons,
            text="Simpan Konfigurasi",
            command=self.save_all,
            bg=PANEL2,
            fg=FG,
            relief="flat",
            padx=12,
            pady=8
        ).pack(side="left")

    def open_settings(self, uri):
        try:
            os.startfile(uri)
        except (OSError, AttributeError):
            try:
                subprocess.Popen(["cmd", "/c", "start", "", uri])
            except OSError as exc:
                messagebox.showerror(
                    "Gagal membuka pengaturan",
                    str(exc)
                )

    def open_volume_mixer(self):
        try:
            subprocess.Popen(["sndvol.exe"])
        except OSError as exc:
            messagebox.showerror(
                "Mixer Volume",
                f"Tidak bisa membuka Volume Mixer:\n{exc}"
            )

    def update_route_status(self):
        active = sum(
            1 for value in self.route_vars.values()
            if value.get()
        )

        if active:
            self.status_label.config(
                text=f"● {active} rute dipilih",
                fg=BLUE
            )
        else:
            self.status_label.config(
                text="● Aplikasi siap",
                fg=GREEN
            )

    def save_all(self):
        self.settings["routes"] = {
            key: value.get()
            for key, value in self.route_vars.items()
        }

        self.settings["volumes"] = {
            key: int(value.get())
            for key, value in self.volume_vars.items()
        }

        save_settings(self.settings)

        self.status_label.config(
            text="● Pengaturan tersimpan",
            fg=GREEN
        )

    def close_app(self):
        self.save_all()
        self.root.destroy()


def main():
    root = tk.Tk()
    LuaHubApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
