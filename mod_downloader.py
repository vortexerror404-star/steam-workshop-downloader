#!/usr/bin/env python3

import json
import os
import platform
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
import tkinter as tk

from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, ttk


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODS_DIR = BASE_DIR / "mods_telecharges"
STAGING_DIR = BASE_DIR / ".steamcmd_staging"
CONFIG_FILE = BASE_DIR / "config.json"
GITHUB_URL = "https://github.com/vortexerror404-star/steam-workshop-downloader"

API_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
COLLECTION_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails?appids="

HTTP_TIMEOUT = 15
USER_AGENT = "SteamWorkshopDownloader/1.0"

try:
    MODS_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


# ============================================================
# TRADUCTIONS (FR / EN)
# ============================================================

TRANSLATIONS = {
    "fr": {
        "subtitle": "Télécharge et organise tes mods Steam Workshop",
        "workshop_links": "Liens ou IDs du Workshop :",
        "verify": "Vérifier les liens",
        "clear": "Vider",
        "per_game": "Un dossier par jeu",
        "steamcmd_path": "Chemin de SteamCMD :",
        "browse": "Parcourir...",
        "steam_account": "Compte Steam (optionnel) :",
        "steam_account_hint": "Le mot de passe n'est ni demandé ni stocké.",
        "download": "🚀 Télécharger",
        "cancel": "Annuler",
        "open_folder": "Ouvrir le dossier",
        "choose_dest": "Choisir destination",
        "status_ready": "En attente",
        "log_title": "JOURNAL",
        "theme_dark": "🌙 Sombre",
        "theme_light": "☀ Clair",
        "theme_hacker": "💻 Hacker",
        "lang_btn": "EN",
        "help_btn": "?",
        "dev_mode": "⚙ Mode développeur",
        "staging_dir": "Dossier temporaire (staging) :",
        "ready_msg": "Prêt. Dossier cible : {path}",
        "steamcmd_missing": "⚠ SteamCMD introuvable : indique son chemin ci-dessous.",
        "no_id": "Aucun ID",
        "no_id_msg": "Colle au moins un lien Workshop ou un ID numérique.",
        "steamcmd_not_found": "SteamCMD introuvable",
        "steamcmd_not_found_msg": "Indique un chemin valide vers SteamCMD.",
        "verifying": "Vérification de {n} lien(s)...",
        "verify_ok": "✓ {fid} — {title}",
        "verify_fail": "✗ {fid} — {err}",
        "preparing": "Préparation de {n} mod(s)...",
        "downloading_btn": "⏳ Téléchargement...",
        "progress_mod": "Téléchargement mod {i}/{total} ({fid})...",
        "done": "Terminé : {s} réussi(s), {f} échec(s).",
        "cancelled": "Annulé : {s} réussi(s), {f} échec(s).",
        "no_mods": "Aucun mod à télécharger.",
        "cancel_requested": "Annulation demandée...",
        "processing": "Traitement : {title} (ID: {fid})",
        "installed": "Installé dans : {path}",
        "fail_mod": "Échec mod {fid} : {err}",
        "collection": "Collection détectée ({n} mods) : {title}",
        "app_id_missing": "App ID introuvable.",
        "src_missing": "Dossier source introuvable.",
        "destination": "Dossier de destination : {path}",
        "select_steamcmd": "Sélectionner SteamCMD",
        "select_dest": "Choisir le dossier de destination",
        "open_folder_err": "Impossible d'ouvrir le dossier :\n{err}",
        "staging_browse": "Choisir le dossier de staging",
        "help_title": "À propos / Aide",
        "help_text": (
            "Steam Workshop Downloader v1.0\n\n"
            "1. Collez vos liens ou IDs Steam Workshop.\n"
            "2. Vérifiez que le chemin vers SteamCMD est correct.\n"
            "3. Cliquez sur Télécharger !\n\n"
            "Fonctionnalités :\n"
            "- Classement automatique par jeu (optionnel)\n"
            "- Prise en charge des collections\n"
            "- Thèmes personnalisés & Multilingue\n\n"
            "Visitez le dépôt GitHub pour les mises à jour :"
        ),
        "github_btn": "🌐 Ouvrir le GitHub",
    },
    "en": {
        "subtitle": "Download and organize your Steam Workshop mods",
        "workshop_links": "Workshop links or IDs:",
        "verify": "Verify links",
        "clear": "Clear",
        "per_game": "One folder per game",
        "steamcmd_path": "SteamCMD path:",
        "browse": "Browse...",
        "steam_account": "Steam account (optional):",
        "steam_account_hint": "Password is neither requested nor stored.",
        "download": "🚀 Download",
        "cancel": "Cancel",
        "open_folder": "Open folder",
        "choose_dest": "Choose destination",
        "status_ready": "Waiting",
        "log_title": "LOG",
        "theme_dark": "🌙 Dark",
        "theme_light": "☀ Light",
        "theme_hacker": "💻 Hacker",
        "lang_btn": "FR",
        "help_btn": "?",
        "dev_mode": "⚙ Developer mode",
        "staging_dir": "Temporary folder (staging):",
        "ready_msg": "Ready. Target folder: {path}",
        "steamcmd_missing": "⚠ SteamCMD not found: set its path below.",
        "no_id": "No ID",
        "no_id_msg": "Paste at least one Workshop link or numeric ID.",
        "steamcmd_not_found": "SteamCMD not found",
        "steamcmd_not_found_msg": "Set a valid path to SteamCMD.",
        "verifying": "Verifying {n} link(s)...",
        "verify_ok": "✓ {fid} — {title}",
        "verify_fail": "✗ {fid} — {err}",
        "preparing": "Preparing {n} mod(s)...",
        "downloading_btn": "⏳ Downloading...",
        "progress_mod": "Downloading mod {i}/{total} ({fid})...",
        "done": "Done: {s} succeeded, {f} failed.",
        "cancelled": "Cancelled: {s} succeeded, {f} failed.",
        "no_mods": "No mods to download.",
        "cancel_requested": "Cancellation requested...",
        "processing": "Processing: {title} (ID: {fid})",
        "installed": "Installed to: {path}",
        "fail_mod": "Failed mod {fid}: {err}",
        "collection": "Collection detected ({n} mods): {title}",
        "app_id_missing": "App ID not found.",
        "src_missing": "Source folder not found.",
        "destination": "Destination folder: {path}",
        "select_steamcmd": "Select SteamCMD",
        "select_dest": "Choose destination folder",
        "open_folder_err": "Cannot open folder:\n{err}",
        "staging_browse": "Choose staging folder",
        "help_title": "About / Help",
        "help_text": (
            "Steam Workshop Downloader v1.0\n\n"
            "1. Paste your Steam Workshop links or IDs.\n"
            "2. Make sure the SteamCMD path is correct.\n"
            "3. Click Download!\n\n"
            "Features:\n"
            "- Automatic per-game sorting (optional)\n"
            "- Collection support\n"
            "- Custom themes & Multilingual\n\n"
            "Check out the GitHub repository for updates:"
        ),
        "github_btn": "🌐 Open GitHub",
    },
}


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def load_json(path, default):
    try:
        if Path(path).is_file():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def find_steamcmd():
    for name in ("steamcmd", "steamcmd.sh", "steamcmd.exe"):
        found = shutil.which(name)
        if found:
            return found

    home = Path.home()
    candidates = [
        home / "steamcmd" / "steamcmd.sh",
        home / ".steam" / "steamcmd" / "steamcmd.sh",
        home / ".local" / "share" / "Steam" / "steamcmd" / "steamcmd.sh",
        Path("C:/steamcmd/steamcmd.exe"),
        Path("C:/Program Files (x86)/steamcmd/steamcmd.exe"),
        Path("/usr/games/steamcmd"),
        Path("/opt/steamcmd/steamcmd.sh"),
    ]
    for path in candidates:
        try:
            if path.is_file():
                return str(path)
        except Exception:
            continue
    return ""


def extract_ids(text):
    ids = []
    for raw in re.split(r"[\s,;]+", text.strip()):
        if not raw:
            continue
        match = re.search(r"[?&]id=(\d+)", raw) or re.fullmatch(r"(\d{5,})", raw)
        if match:
            fid = match.group(1)
            if fid not in ids:
                ids.append(fid)
    return ids


def http_json(url, data=None):
    headers = {"User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = urllib.request.Request(url, data=data, headers=headers)
    last_error = None

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.7 * (attempt + 1))

    raise RuntimeError(f"Steam unreachable: {last_error}")


def fetch_details(file_id):
    data = urllib.parse.urlencode(
        {"itemcount": 1, "publishedfileids[0]": file_id}
    ).encode("utf-8")
    payload = http_json(API_URL, data)
    details_list = payload.get("response", {}).get("publishedfiledetails", [])
    if not details_list:
        raise ValueError("No details returned.")
    details = details_list[0]
    if details.get("result") != 1:
        raise ValueError("Mod not found or private.")
    return details


def fetch_collection_children(collection_id):
    data = urllib.parse.urlencode(
        {"collectioncount": 1, "publishedfileids[0]": collection_id}
    ).encode("utf-8")
    payload = http_json(COLLECTION_URL, data)
    details = payload.get("response", {}).get("collectiondetails", [])
    if not details:
        return []
    return [
        str(c.get("publishedfileid"))
        for c in details[0].get("children", [])
        if c.get("publishedfileid")
    ]


def fetch_game_name(app_id):
    try:
        payload = http_json(f"{APP_DETAILS_URL}{app_id}")
        app = payload.get(str(app_id), {})
        if app.get("success"):
            return app.get("data", {}).get("name", f"App_{app_id}")
    except Exception:
        pass
    return f"App_{app_id}"


def safe_name(name, fallback="mod"):
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name))
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:80].rstrip(" .") or fallback


def open_folder(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))
    elif system == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


# ============================================================
# APPLICATION PRINCIPALE
# ============================================================

class ModApp:

    PALETTES = {
        "dark": {
            "bg": "#12151b", "panel": "#1b2029", "entry": "#0d1015",
            "fg": "#f3f5f7", "muted": "#aeb8c6",
            "btn": "#303846", "btn_active": "#414c5d",
            "primary": "#0878e8", "primary_active": "#0966c3",
            "danger": "#793b40", "danger_active": "#93494f",
            "log_bg": "#080a0d", "log_fg": "#b6f5c8",
            "font": ("Segoe UI", 10),
            "font_bold": ("Segoe UI", 10, "bold"),
            "font_title": ("Segoe UI", 18, "bold"),
            "font_small": ("Segoe UI", 9),
            "font_log": ("Consolas", 9),
        },
        "light": {
            "bg": "#f4f6f9", "panel": "#ffffff", "entry": "#ffffff",
            "fg": "#1a1f2a", "muted": "#5a6677",
            "btn": "#e2e7ee", "btn_active": "#cfd6e0",
            "primary": "#0878e8", "primary_active": "#0966c3",
            "danger": "#c94a52", "danger_active": "#b13a42",
            "log_bg": "#fbfcfe", "log_fg": "#1f6f3f",
            "font": ("Segoe UI", 10),
            "font_bold": ("Segoe UI", 10, "bold"),
            "font_title": ("Segoe UI", 18, "bold"),
            "font_small": ("Segoe UI", 9),
            "font_log": ("Consolas", 9),
        },
        "hacker": {
            "bg": "#000000", "panel": "#0a0a0a", "entry": "#050505",
            "fg": "#00ff66", "muted": "#00aa44",
            "btn": "#001a0a", "btn_active": "#00330f",
            "primary": "#00ff66", "primary_active": "#00cc52",
            "danger": "#330000", "danger_active": "#4d0000",
            "log_bg": "#000000", "log_fg": "#00ff66",
            "font": ("Consolas", 10),
            "font_bold": ("Consolas", 10, "bold"),
            "font_title": ("Consolas", 18, "bold"),
            "font_small": ("Consolas", 9),
            "font_log": ("Consolas", 9),
        },
    }

    def __init__(self, root):
        self.root = root

        config = load_json(CONFIG_FILE, {})
        self.theme = config.get("theme", "dark")
        if self.theme not in self.PALETTES:
            self.theme = "dark"
        self.lang = config.get("lang", "fr")
        if self.lang not in TRANSLATIONS:
            self.lang = "fr"

        self.dev_mode = tk.BooleanVar(master=self.root, value=config.get("dev_mode", False))
        self.per_game_folder = tk.BooleanVar(master=self.root, value=config.get("per_game_folder", True))
        self.steamcmd_var = tk.StringVar(master=self.root, value=config.get("steamcmd_path", "") or find_steamcmd())
        self.user_var = tk.StringVar(master=self.root, value=config.get("user_account", ""))
        self.staging_var = tk.StringVar(master=self.root, value=config.get("staging_dir", str(STAGING_DIR)))
        self.status_var = tk.StringVar(master=self.root, value="")

        self.log_queue = queue.Queue()
        self.busy = False
        self.cancel_event = threading.Event()
        self.current_process = None
        self.mods_dir = Path(config.get("mods_dir", str(MODS_DIR)))
        self.staging_dir = Path(self.staging_var.get())

        self.root.title("Steam Workshop Downloader v1.0")
        self.root.geometry("920x820")
        self.root.minsize(760, 640)

        self.build_ui()
        self.apply_theme()
        self.apply_dev_mode()
        self.retranslate()

        self.log(self.t("ready_msg", path=self.mods_dir))
        if self.steamcmd_var.get() and Path(self.steamcmd_var.get()).is_file():
            self.log(f"✓ SteamCMD détecté : {self.steamcmd_var.get()}", "ok")
        else:
            self.log(self.t("steamcmd_missing"), "warn")

        self.root.after(100, self.flush_events)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def t(self, key, **kw):
        txt = TRANSLATIONS[self.lang].get(key, key)
        if kw:
            try:
                return txt.format(**kw)
            except Exception:
                return txt
        return txt

    def toggle_lang(self):
        self.lang = "en" if self.lang == "fr" else "fr"
        self.save_config()
        self.retranslate()

    def save_config(self):
        save_json(CONFIG_FILE, {
            "theme": self.theme,
            "lang": self.lang,
            "dev_mode": self.dev_mode.get(),
            "per_game_folder": self.per_game_folder.get(),
            "mods_dir": str(self.mods_dir),
            "staging_dir": str(self.staging_dir),
            "steamcmd_path": self.steamcmd_var.get(),
            "user_account": self.user_var.get(),
        })

    def retranslate(self):
        self.subtitle_lbl.configure(text=self.t("subtitle"))
        self.lang_btn.configure(text=self.t("lang_btn"))
        self.help_btn.configure(text=self.t("help_btn"))

        self.links_lbl.configure(text=self.t("workshop_links"))
        self.verify_btn.configure(text=self.t("verify"))
        self.clear_btn.configure(text=self.t("clear"))
        self.per_game_chk.configure(text=self.t("per_game"))
        self.steamcmd_lbl.configure(text=self.t("steamcmd_path"))
        self.browse_btn.configure(text=self.t("browse"))
        self.dev_mode_chk.configure(text=self.t("dev_mode"))
        self.user_lbl.configure(text=self.t("steam_account"))
        self.user_hint_lbl.configure(text=self.t("steam_account_hint"))
        self.staging_lbl.configure(text=self.t("staging_dir"))
        self.staging_browse_btn.configure(text=self.t("browse"))

        self.download_btn.configure(
            text=self.t("downloading_btn") if self.busy else self.t("download")
        )
        self.cancel_btn.configure(text=self.t("cancel"))
        self.open_btn.configure(text=self.t("open_folder"))
        self.dest_btn.configure(text=self.t("choose_dest"))
        self.log_title_lbl.configure(text=self.t("log_title"))

        if not self.busy:
            self.status_var.set(self.t("status_ready"))

        self.update_theme_button()

    def update_theme_button(self):
        key = {"dark": "theme_dark", "light": "theme_light", "hacker": "theme_hacker"}[self.theme]
        self.theme_btn.configure(text=self.t(key))

    def colors(self):
        return self.PALETTES[self.theme]

    def cycle_theme(self):
        order = ["dark", "hacker", "light"]
        idx = order.index(self.theme) if self.theme in order else 0
        self.theme = order[(idx + 1) % len(order)]
        self.save_config()
        self.apply_theme()

    def apply_theme(self):
        c = self.colors()
        self.root.configure(bg=c["bg"])

        self._color_widget(self.title_lbl, bg=c["bg"], fg=c["fg"], font=c["font_title"])
        self._color_widget(self.subtitle_lbl, bg=c["bg"], fg=c["muted"], font=c["font"])
        self._color_widget(self.theme_btn, bg=c["btn"], fg=c["fg"], activebackground=c["btn_active"], font=c["font"])
        self._color_widget(self.lang_btn, bg=c["btn"], fg=c["fg"], activebackground=c["btn_active"], font=c["font_bold"])
        self._color_widget(self.help_btn, bg=c["btn"], fg=c["fg"], activebackground=c["btn_active"], font=c["font_bold"])
        self._color_widget(self.main_frame, bg=c["panel"])

        for lbl in (self.links_lbl, self.steamcmd_lbl, self.user_lbl, self.staging_lbl):
            self._color_widget(lbl, bg=c["panel"], fg=c["fg"], font=c["font_bold"])

        self._color_widget(self.user_hint_lbl, bg=c["panel"], fg=c["muted"], font=c["font_small"])

        self._color_widget(self.url_text, bg=c["entry"], fg=c["fg"], insertbackground=c["fg"], font=c["font_log"])
        self._color_widget(self.steamcmd_entry, bg=c["entry"], fg=c["fg"], insertbackground=c["fg"], font=c["font"])
        self._color_widget(self.user_entry, bg=c["entry"], fg=c["fg"], insertbackground=c["fg"], font=c["font"])
        self._color_widget(self.staging_entry, bg=c["entry"], fg=c["fg"], insertbackground=c["fg"], font=c["font"])

        for chk in (self.per_game_chk, self.dev_mode_chk):
            self._color_widget(chk, bg=c["panel"], fg=c["fg"], activebackground=c["panel"], selectcolor=c["entry"], font=c["font_small"])

        for btn in (self.verify_btn, self.clear_btn, self.browse_btn, self.open_btn, self.dest_btn, self.staging_browse_btn):
            self._color_widget(btn, bg=c["btn"], fg=c["fg"], activebackground=c["btn_active"], font=c["font"])

        self._color_widget(
            self.download_btn,
            bg=c["primary"],
            fg=("#000000" if self.theme == "hacker" else "white"),
            activebackground=c["primary_active"],
            font=c["font_bold"],
        )

        self._color_widget(
            self.cancel_btn,
            bg=c["danger"],
            fg=("#00ff66" if self.theme == "hacker" else "white"),
            activebackground=c["danger_active"],
            font=c["font"],
        )

        self._color_widget(self.log_title_lbl, bg=c["bg"], fg=c["muted"], font=c["font_bold"])

        try:
            self.log_output.configure(
                bg=c["log_bg"], fg=c["log_fg"], insertbackground=c["fg"],
                font=c["font_log"],
            )
            self.log_output.tag_config("error", foreground=("#ff0044" if self.theme == "hacker" else "#ff6b6b"))
            self.log_output.tag_config("warn", foreground=("#ffff00" if self.theme == "hacker" else "#ffcc66"))
            self.log_output.tag_config("ok", foreground=("#00ff66" if self.theme == "hacker" else "#5ddb8c"))
            self.log_output.tag_config("info", foreground=c["fg"])
        except tk.TclError:
            pass

        for frame in (self.header_frame, self.buttons_frame, self.status_frame, self.log_title_frame):
            try:
                frame.configure(bg=c["bg"])
            except tk.TclError:
                pass

        for frame in (self.row_actions, self.steam_row, self.dev_toggle_frame, self.dev_frame, self.staging_row):
            try:
                frame.configure(bg=c["panel"])
            except tk.TclError:
                pass

        self.update_theme_button()

    @staticmethod
    def _color_widget(widget, **opts):
        try:
            widget.configure(**opts)
        except tk.TclError:
            pass

    # --------------------------------------------------------
    # CONSTRUCTION DE L'INTERFACE
    # --------------------------------------------------------

    def build_ui(self):
        c = self.colors()
        bg, panel, fg, muted = c["bg"], c["panel"], c["fg"], c["muted"]

        self.header_frame = tk.Frame(self.root, bg=bg)
        self.header_frame.pack(fill=tk.X, padx=24, pady=(14, 0))

        self.title_lbl = tk.Label(self.header_frame, text="Steam Workshop Downloader", font=c["font_title"], fg=fg, bg=bg)
        self.title_lbl.pack(side=tk.LEFT)

        head_btns = tk.Frame(self.header_frame, bg=bg)
        head_btns.pack(side=tk.RIGHT)

        self.lang_btn = tk.Button(head_btns, text="EN", command=self.toggle_lang, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=10, pady=4, font=c["font_bold"])
        self.lang_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.theme_btn = tk.Button(head_btns, text="🌙", command=self.cycle_theme, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=10, pady=4, font=c["font"])
        self.theme_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.help_btn = tk.Button(head_btns, text="?", command=self.show_help, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=10, pady=4, font=c["font_bold"])
        self.help_btn.pack(side=tk.RIGHT)

        self.subtitle_lbl = tk.Label(self.root, text="...", font=c["font"], fg=muted, bg=bg)
        self.subtitle_lbl.pack(anchor="w", padx=24, pady=(0, 10))

        self.main_frame = tk.Frame(self.root, bg=panel, padx=16, pady=14)
        self.main_frame.pack(fill=tk.X, padx=24, pady=5)

        self.links_lbl = tk.Label(self.main_frame, text="...", font=c["font_bold"], fg=fg, bg=panel)
        self.links_lbl.pack(anchor="w")

        self.url_text = tk.Text(self.main_frame, height=4, wrap=tk.WORD, undo=True, bg=c["entry"], fg=fg, insertbackground=fg, relief=tk.FLAT, padx=9, pady=8, font=c["font_log"])
        self.url_text.pack(fill=tk.X, pady=(4, 0))

        self.row_actions = tk.Frame(self.main_frame, bg=panel)
        self.row_actions.pack(fill=tk.X, pady=(8, 0))

        self.verify_btn = tk.Button(self.row_actions, text="...", command=self.verify_links, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=12, pady=5, font=c["font"])
        self.verify_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(self.row_actions, text="...", command=lambda: self.url_text.delete("1.0", tk.END), bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=12, pady=5, font=c["font"])
        self.clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.per_game_chk = tk.Checkbutton(self.row_actions, text="...", variable=self.per_game_folder, command=self.save_config, bg=panel, fg=fg, activebackground=panel, selectcolor=c["entry"], font=c["font_small"])
        self.per_game_chk.pack(side=tk.LEFT, padx=(16, 0))

        self.steamcmd_lbl = tk.Label(self.main_frame, text="...", font=c["font_bold"], fg=fg, bg=panel)
        self.steamcmd_lbl.pack(anchor="w", pady=(12, 5))

        self.steam_row = tk.Frame(self.main_frame, bg=panel)
        self.steam_row.pack(fill=tk.X)

        self.steamcmd_entry = tk.Entry(self.steam_row, textvariable=self.steamcmd_var, bg=c["entry"], fg=fg, insertbackground=fg, relief=tk.FLAT, font=c["font"])
        self.steamcmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.steamcmd_var.trace_add("write", lambda *args: self.save_config())

        self.browse_btn = tk.Button(self.steam_row, text="...", command=self.browse_steamcmd, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=12, pady=5, font=c["font"])
        self.browse_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.dev_toggle_frame = tk.Frame(self.main_frame, bg=panel)
        self.dev_toggle_frame.pack(fill=tk.X, pady=(12, 0))

        self.dev_mode_chk = tk.Checkbutton(self.dev_toggle_frame, text="...", variable=self.dev_mode, command=self.toggle_dev_mode, bg=panel, fg=muted, activebackground=panel, selectcolor=c["entry"], font=c["font_small"])
        self.dev_mode_chk.pack(side=tk.LEFT)

        self.dev_frame = tk.Frame(self.main_frame, bg=panel)

        self.user_lbl = tk.Label(self.dev_frame, text="...", font=c["font_bold"], fg=fg, bg=panel)
        self.user_lbl.pack(anchor="w", pady=(8, 3))

        self.user_entry = tk.Entry(self.dev_frame, textvariable=self.user_var, bg=c["entry"], fg=fg, insertbackground=fg, relief=tk.FLAT, font=c["font"])
        self.user_entry.pack(fill=tk.X, ipady=6)
        self.user_var.trace_add("write", lambda *args: self.save_config())

        self.user_hint_lbl = tk.Label(self.dev_frame, text="...", font=c["font_small"], fg=muted, bg=panel)
        self.user_hint_lbl.pack(anchor="w", pady=(3, 0))

        self.staging_lbl = tk.Label(self.dev_frame, text="...", font=c["font_bold"], fg=fg, bg=panel)
        self.staging_lbl.pack(anchor="w", pady=(10, 3))

        self.staging_row = tk.Frame(self.dev_frame, bg=panel)
        self.staging_row.pack(fill=tk.X)

        self.staging_entry = tk.Entry(self.staging_row, textvariable=self.staging_var, bg=c["entry"], fg=fg, insertbackground=fg, relief=tk.FLAT, font=c["font"])
        self.staging_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self.staging_var.trace_add("write", lambda *args: self.save_config())

        self.staging_browse_btn = tk.Button(self.staging_row, text="...", command=self.browse_staging, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=12, pady=5, font=c["font"])
        self.staging_browse_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.buttons_frame = tk.Frame(self.root, bg=bg)
        self.buttons_frame.pack(pady=12)

        self.download_btn = tk.Button(self.buttons_frame, text="...", command=self.start_download, bg=c["primary"], fg="white", activebackground=c["primary_active"], relief=tk.FLAT, cursor="hand2", font=c["font_bold"], padx=18, pady=9)
        self.download_btn.pack(side=tk.LEFT, padx=4)

        self.cancel_btn = tk.Button(self.buttons_frame, text="...", command=self.cancel_download, state=tk.DISABLED, bg=c["danger"], fg="white", activebackground=c["danger_active"], relief=tk.FLAT, cursor="hand2", padx=15, pady=9, font=c["font"])
        self.cancel_btn.pack(side=tk.LEFT, padx=4)

        self.open_btn = tk.Button(self.buttons_frame, text="...", command=self.open_mods_folder, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=14, pady=9, font=c["font"])
        self.open_btn.pack(side=tk.LEFT, padx=4)

        self.dest_btn = tk.Button(self.buttons_frame, text="...", command=self.choose_destination, bg=c["btn"], fg=fg, activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", padx=14, pady=9, font=c["font"])
        self.dest_btn.pack(side=tk.LEFT, padx=4)

        self.status_frame = tk.Frame(self.root, bg=bg)
        self.status_frame.pack(fill=tk.X, padx=24, pady=(2, 4))

        tk.Label(self.status_frame, textvariable=self.status_var, font=c["font_small"], fg=muted, bg=bg).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, padx=24, pady=(0, 10))

        self.log_title_frame = tk.Frame(self.root, bg=bg)
        self.log_title_frame.pack(fill=tk.X, padx=24, pady=(0, 5))

        self.log_title_lbl = tk.Label(self.log_title_frame, text="...", font=c["font_bold"], fg=muted, bg=bg)
        self.log_title_lbl.pack(anchor="w")

        self.log_output = scrolledtext.ScrolledText(self.root, bg=c["log_bg"], fg=c["log_fg"], insertbackground=fg, font=c["font_log"], relief=tk.FLAT, wrap=tk.WORD, state=tk.DISABLED)
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))

    def toggle_dev_mode(self):
        self.save_config()
        self.apply_dev_mode()

    def apply_dev_mode(self):
        if self.dev_mode.get():
            self.dev_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.dev_frame.pack_forget()

    def show_help(self):
        c = self.colors()
        top = tk.Toplevel(self.root)
        top.title(self.t("help_title"))
        top.geometry("440x360")
        top.configure(bg=c["panel"])
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()

        lbl = tk.Label(top, text=self.t("help_text"), font=c["font"], fg=c["fg"], bg=c["panel"], justify=tk.LEFT)
        lbl.pack(padx=20, pady=(20, 10), anchor="w")

        link_btn = tk.Button(top, text=GITHUB_URL, font=c["font_small"], fg=c["primary"], bg=c["entry"], relief=tk.FLAT, cursor="hand2", command=lambda: webbrowser.open(GITHUB_URL))
        link_btn.pack(padx=20, pady=5, fill=tk.X)

        close_btn = tk.Button(top, text="OK", font=c["font_bold"], fg=c["fg"], bg=c["btn"], activebackground=c["btn_active"], relief=tk.FLAT, cursor="hand2", command=top.destroy, width=10)
        close_btn.pack(pady=15)

    # --------------------------------------------------------
    # ACTIONS & LOGS
    # --------------------------------------------------------

    def log(self, message, kind="info"):
        self.log_queue.put(("__LOG__", str(message), kind))

    def flush_events(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple):
                    if item[0] == "__LOG__":
                        _, msg, kind = item
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.log_output.configure(state=tk.NORMAL)
                        self.log_output.insert(tk.END, f"[{timestamp}] {msg}\n", kind)
                        self.log_output.see(tk.END)
                        self.log_output.configure(state=tk.DISABLED)
                    elif item[0] == "__PROGRESS__":
                        _, val, status = item
                        self.progress.configure(value=val)
                        self.status_var.set(status)
                    elif item[0] == "__DONE__":
                        _, summary = item
                        self.busy = False
                        self.current_process = None
                        c = self.colors()
                        self.download_btn.configure(
                            state=tk.NORMAL,
                            text=self.t("download"),
                            bg=c["primary"]
                        )
                        self.cancel_btn.configure(state=tk.DISABLED)
                        self.status_var.set(summary)
        except queue.Empty:
            pass

        try:
            if self.root.winfo_exists():
                self.root.after(100, self.flush_events)
        except tk.TclError:
            pass

    def browse_steamcmd(self):
        path = filedialog.askopenfilename(title=self.t("select_steamcmd"))
        if path:
            self.steamcmd_var.set(path)
            self.save_config()

    def browse_staging(self):
        path = filedialog.askdirectory(title=self.t("staging_browse"))
        if path:
            self.staging_var.set(path)
            self.staging_dir = Path(path)
            self.save_config()

    def choose_destination(self):
        path = filedialog.askdirectory(title=self.t("select_dest"), initialdir=str(self.mods_dir))
        if path:
            self.mods_dir = Path(path)
            self.log(self.t("destination", path=self.mods_dir))
            self.save_config()

    def open_mods_folder(self):
        try:
            open_folder(self.mods_dir)
        except Exception as exc:
            messagebox.showerror("Erreur", self.t("open_folder_err", err=exc))

    def verify_links(self):
        if self.busy:
            return
        raw_ids = extract_ids(self.url_text.get("1.0", tk.END))
        if not raw_ids:
            messagebox.showerror(self.t("no_id"), self.t("no_id_msg"))
            return
        self.log(self.t("verifying", n=len(raw_ids)))
        threading.Thread(target=self._verify_worker, args=(raw_ids,), daemon=True).start()

    def _verify_worker(self, ids):
        for fid in ids:
            try:
                d = fetch_details(fid)
                if d.get("file_type") == 2:
                    self.log(self.t("collection", n=len(d.get("children", [])), title=d.get("title", "?")), "warn")
                else:
                    self.log(self.t("verify_ok", fid=fid, title=d.get("title", "Mod")), "ok")
            except Exception as exc:
                self.log(self.t("verify_fail", fid=fid, err=exc), "error")

    def start_download(self):
        if self.busy:
            return
        raw_ids = extract_ids(self.url_text.get("1.0", tk.END))
        if not raw_ids:
            messagebox.showerror(self.t("no_id"), self.t("no_id_msg"))
            return

        steamcmd = self.steamcmd_var.get().strip()
        if not steamcmd or not Path(steamcmd).is_file():
            messagebox.showerror(self.t("steamcmd_not_found"), self.t("steamcmd_not_found_msg"))
            return

        self.busy = True
        c = self.colors()
        self.download_btn.configure(state=tk.DISABLED, text=self.t("downloading_btn"), bg=c["btn"])
        self.cancel_btn.configure(state=tk.NORMAL)
        self.cancel_event.clear()

        threading.Thread(target=self._download_worker_thread, args=(raw_ids, steamcmd), daemon=True).start()

    def cancel_download(self):
        if self.busy:
            self.cancel_event.set()
            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
            self.log(self.t("cancel_requested"), "warn")

    def _download_worker_thread(self, ids, steamcmd):
        succeeded = 0
        failed = 0
        try:
            self.mods_dir.mkdir(parents=True, exist_ok=True)
            self.staging_dir.mkdir(parents=True, exist_ok=True)

            expanded = []
            for fid in ids:
                if self.cancel_event.is_set():
                    break
                try:
                    d = fetch_details(fid)
                    if d.get("file_type") == 2:
                        for cid in fetch_collection_children(fid):
                            if cid not in expanded:
                                expanded.append(cid)
                    else:
                        if fid not in expanded:
                            expanded.append(fid)
                except Exception as exc:
                    self.log(f"✗ {fid} — {exc}", "error")
                    failed += 1

            total = len(expanded)
            if total == 0:
                self.log_queue.put(("__DONE__", self.t("no_mods")))
                return

            for idx, fid in enumerate(expanded, 1):
                if self.cancel_event.is_set():
                    break

                pct = int(((idx - 1) / total) * 100)
                status_msg = self.t("progress_mod", i=idx, total=total, fid=fid)
                self.log_queue.put(("__PROGRESS__", pct, status_msg))

                try:
                    self._download_single_mod(fid, steamcmd)
                    succeeded += 1
                except Exception as exc:
                    self.log(self.t("fail_mod", fid=fid, err=exc), "error")
                    failed += 1

            if self.cancel_event.is_set():
                summary = self.t("cancelled", s=succeeded, f=failed)
            else:
                summary = self.t("done", s=succeeded, f=failed)

            self.log_queue.put(("__PROGRESS__", 100, summary))
            self.log_queue.put(("__DONE__", summary))

        except Exception as exc:
            self.log(f"Erreur worker : {exc}", "error")
            self.log_queue.put(("__DONE__", "Erreur critique."))

    def _download_single_mod(self, file_id, steamcmd):
        details = fetch_details(file_id)
        app_id = str(details.get("consumer_app_id") or details.get("creator_app_id") or "")
        title = details.get("title", file_id)

        if not app_id or app_id == "0":
            raise ValueError(self.t("app_id_missing"))

        self.log(self.t("processing", title=title, fid=file_id), "info")
        game_name = fetch_game_name(app_id) if self.per_game_folder.get() else None

        user = self.user_var.get().strip()
        login_args = ["+login", user] if user else ["+login", "anonymous"]

        cmd = [
            steamcmd,
            "+force_install_dir", str(self.staging_dir),
            *login_args,
            "+workshop_download_item", app_id, file_id,
            "validate",
            "+quit"
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace"
        )
        self.current_process = process

        for line in process.stdout:
            if self.cancel_event.is_set():
                break
            line_str = line.strip()
            if not line_str:
                continue
            if "success" in line_str.lower():
                self.log(line_str, "ok")
            elif any(w in line_str.lower() for w in ("error", "fail", "denied")):
                self.log(line_str, "error")
            elif "downloading" in line_str.lower() or "update" in line_str.lower():
                self.log(line_str, "info")

        process.wait()
        self.current_process = None

        if self.cancel_event.is_set():
            raise RuntimeError("Annulé par l'utilisateur.")

        src_dir = self.staging_dir / "steamapps" / "workshop" / "content" / app_id / file_id
        if not src_dir.is_dir():
            raise RuntimeError(self.t("src_missing"))

        if self.per_game_folder.get():
            target_parent = self.mods_dir / safe_name(game_name, f"App_{app_id}")
        else:
            target_parent = self.mods_dir

        target_dir = target_parent / f"{safe_name(title, file_id)} [{file_id}]"

        target_parent.mkdir(parents=True, exist_ok=True)
        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(src_dir, target_dir)
        self.log(self.t("installed", path=target_dir), "ok")


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = ModApp(root)
    root.mainloop()
