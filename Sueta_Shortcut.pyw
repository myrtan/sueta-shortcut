import os
import sys
import ctypes
import subprocess
import tkinter as tk
import webbrowser
import winreg
from datetime import datetime
from tkinter import messagebox
from typing import Callable, Iterable, Optional

APP_TITLE = "Sueta Shortcut"
WINDOW_W = 980
WINDOW_H = 640
ICON_FILE = "sueta.ico"
APP_ID = "sueta.shortcut.app"
RADIUS = 18

BG = "#140b10"
CARD = "#5a2432"
PANEL = "#25141b"
PANEL_BORDER = "#3c1c26"
BUTTON = "#8b4254"
FG = "#fff5f7"
SUB = "#efccd4"
STATUS = "#d9a8b6"

ALT_ACCOUNTS_PATH = r"C:\Program Files (x86)\Steam\config\loginusers.vdf"
WINDOWS_INSTALL_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
WINDOWS_INSTALL_VALUE = "InstallDate"

REG_PATHS = [
    ("1", "Store", r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store"),
    ("2", "AppSwitched", r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\AppSwitched"),
    ("3", "ShowJumpView", r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\ShowJumpView"),
    ("4", "RunMRU", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
]

CHECK_LINKS = [
    ("LastActivityView", "https://www.nirsoft.net/utils/lastactivityview.zip"),
    ("USBDeview", "https://www.nirsoft.net/utils/usbdeview-x64.zip"),
    ("System Informer", "https://disk.yandex.ru/d/TO1Epwdy9Padqw"),
    ("Recuva", "https://download.ccleaner.com/rcsetup154.exe"),
    ("Everything", "https://www.voidtools.com/Everything-1.4.1.1032.x64.zip"),
]

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010

root: Optional[tk.Tk] = None
status_var: Optional[tk.StringVar] = None


def set_status(text: str) -> None:
    if status_var is not None:
        status_var.set(text)


def resource_path(filename: str) -> str:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, filename)


def show_error(text: str) -> None:
    messagebox.showerror(APP_TITLE, text)


def show_info(text: str) -> None:
    messagebox.showinfo(APP_TITLE, text)


def set_app_id() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def _send_native_icons(window: tk.Tk, icon_path: str) -> None:
    try:
        hwnd = window.winfo_id()
        big_icon = ctypes.windll.user32.LoadImageW(0, icon_path, IMAGE_ICON, 256, 256, LR_LOADFROMFILE)
        small_icon = ctypes.windll.user32.LoadImageW(0, icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        if big_icon:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, big_icon)
        if small_icon:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small_icon)
    except Exception:
        pass


def apply_icon(window: tk.Tk) -> None:
    icon_path = resource_path(ICON_FILE)
    if not os.path.exists(icon_path):
        return

    def _apply_once() -> None:
        try:
            window.iconbitmap(default=icon_path)
        except Exception:
            try:
                window.wm_iconbitmap(icon_path)
            except Exception:
                pass
        _send_native_icons(window, icon_path)

    try:
        window.update_idletasks()
    except Exception:
        pass

    _apply_once()
    for delay in (50, 250, 800, 1500):
        window.after(delay, _apply_once)


def rounded_points(x1: int, y1: int, x2: int, y2: int, r: int):
    return [
        x1 + r, y1,
        x1 + r, y1,
        x2 - r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1 + r,
        x1, y1,
    ]


def silent_popen(args: list[str]) -> None:
    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
        shell=False,
    )


def run_hidden(args: list[str]) -> None:
    subprocess.run(
        args,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
        shell=False,
    )


def start_target(target: str) -> bool:
    try:
        os.startfile(target)
        return True
    except Exception:
        return False


def open_program(args: list[str], error_text: str) -> None:
    try:
        silent_popen(args)
    except Exception as error:
        show_error(f"{error_text}\n\n{error}")


def open_folder(path: str) -> None:
    if not path:
        show_error("Путь не найден.")
        return
    if not os.path.exists(path):
        show_error(f"Путь не найден:\n{path}")
        return
    try:
        os.startfile(path)
        set_status(f"Открыто: {os.path.basename(path) or path}")
    except Exception as error:
        show_error(f"Не удалось открыть:\n{path}\n\n{error}")


def open_uri(uri: str) -> None:
    if start_target(uri):
        return
    try:
        webbrowser.open(uri, new=2)
    except Exception as error:
        show_error(f"Не удалось открыть:\n{uri}\n\n{error}")


def open_first_available(*targets: str) -> None:
    for target in targets:
        if start_target(target):
            return
    open_uri(targets[-1])


def open_link(url: str) -> None:
    try:
        webbrowser.open(url, new=2)
        set_status(f"Открыта ссылка: {url}")
    except Exception as error:
        show_error(f"Не удалось открыть ссылку.\n\n{error}")


def open_alt_accounts() -> None:
    if not os.path.exists(ALT_ACCOUNTS_PATH):
        show_error(f"Файл не найден:\n{ALT_ACCOUNTS_PATH}")
        return
    try:
        silent_popen(["notepad.exe", ALT_ACCOUNTS_PATH])
        set_status("Открыт loginusers.vdf")
    except Exception as error:
        show_error(f"Не удалось открыть файл.\n\n{error}")


def open_regedit_path(reg_path: str, label: str) -> None:
    try:
        run_hidden(
            [
                "reg", "add",
                r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Applets\Regedit",
                "/v", "LastKey",
                "/t", "REG_SZ",
                "/d", reg_path,
                "/f",
            ]
        )
        silent_popen(["regedit.exe"])
        set_status(f"Открыт regedit: {label}")
    except Exception as error:
        show_error(f"Не удалось открыть путь в regedit.\n\n{error}")


def show_windows_install_date() -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WINDOWS_INSTALL_KEY) as key:
            install_date, _ = winreg.QueryValueEx(key, WINDOWS_INSTALL_VALUE)
        readable = datetime.fromtimestamp(int(install_date)).strftime("%d.%m.%Y %H:%M:%S")
        show_info(f"Дата установки Windows:\n{readable}")
        set_status(f"Дата Windows: {readable}")
    except Exception as error:
        show_error(f"Не удалось получить дату установки Windows.\n\n{error}")


class RoundedPanel(tk.Canvas):
    def __init__(self, parent, bg_color: str, border_color: Optional[str] = None, radius: int = RADIUS, **kwargs):
        super().__init__(parent, bg=BG, highlightthickness=0, bd=0, **kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _event=None) -> None:
        self.delete("panel")
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())

        if self.border_color:
            self.create_polygon(
                rounded_points(1, 1, width - 1, height - 1, self.radius),
                smooth=True,
                fill=self.border_color,
                outline="",
                tags="panel",
            )
            inset = 2
        else:
            inset = 0

        self.create_polygon(
            rounded_points(inset, inset, width - inset, height - inset, max(4, self.radius - 1)),
            smooth=True,
            fill=self.bg_color,
            outline="",
            tags="panel",
        )


class ActionCard(tk.Canvas):
    def __init__(self, parent, icon_text: str, title: str, subtitle: str, command: Callable[[], None]):
        super().__init__(parent, bg=BG, height=96, highlightthickness=0, bd=0, cursor="hand2")
        self.icon_text = icon_text
        self.title = title
        self.subtitle = subtitle
        self.command = command
        self.bind("<Configure>", self._redraw)
        self.bind("<Button-1>", lambda _e: self.command())

    def _redraw(self, _event=None) -> None:
        self.delete("all")
        width = max(110, self.winfo_width())
        height = max(70, self.winfo_height())
        inset = 1

        self.create_polygon(
            rounded_points(inset, inset, width - inset, height - inset, RADIUS),
            smooth=True,
            fill=CARD,
            outline="",
        )
        self.create_text(34, height / 2, text=self.icon_text, font=("Segoe UI Emoji", 20), fill=FG, anchor="center")
        self.create_text(68, 34, text=self.title, font=("Bahnschrift SemiBold", 10), fill=FG, anchor="w")
        self.create_text(68, 62, text=self.subtitle, font=("Bahnschrift", 8), fill=SUB, anchor="w", width=width - 98)


class MiniButton(tk.Canvas):
    def __init__(self, parent, text: str, command: Callable[[], None]):
        super().__init__(parent, bg=PANEL, height=38, highlightthickness=0, bd=0, cursor="hand2")
        self.text_value = text
        self.command = command
        self.bind("<Configure>", self._redraw)
        self.bind("<Button-1>", lambda _e: self.command())

    def _redraw(self, _event=None) -> None:
        self.delete("all")
        width = max(70, self.winfo_width())
        height = max(30, self.winfo_height())
        inset = 1

        self.create_polygon(
            rounded_points(inset, inset, width - inset, height - inset, 12),
            smooth=True,
            fill=BUTTON,
            outline="",
        )
        self.create_text(
            width / 2,
            height / 2,
            text=self.text_value,
            font=("Bahnschrift SemiBold", 9),
            fill=FG,
            anchor="center",
            width=width - 20,
        )


class SideSection(tk.Frame):
    def __init__(self, parent, title: str):
        super().__init__(parent, bg=BG)
        self.panel = RoundedPanel(self, bg_color=PANEL, border_color=PANEL_BORDER, radius=RADIUS)
        self.panel.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=PANEL)
        self.body.pack(fill="both", expand=True, padx=12, pady=10)
        self.body.columnconfigure(0, weight=1)
        self.title_label = tk.Label(
            self.body,
            text=title,
            bg=PANEL,
            fg=FG,
            font=("Bahnschrift SemiBold", 10),
            anchor="w",
        )
        self.title_label.pack(anchor="w", pady=(0, 8))


def build_quick_actions() -> list[tuple[str, str, str, Callable[[], None]]]:
    return [
        ("🕘", "Recent", "Недавние файлы и ярлыки", lambda: open_folder(os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent"))),
        ("🧪", "Temp", "Временные файлы", lambda: open_folder(os.environ.get("TEMP", ""))),
        ("⚡", "Prefetch", "Системный кэш запуска", lambda: open_folder(r"C:\Windows\Prefetch")),
        ("🧩", "Regedit", "Редактор реестра Windows", lambda: open_program(["regedit.exe"], "Не удалось открыть regedit.")),
        ("🛡", "Защита от вирусов", "Журнал защиты и системный антивирус", lambda: open_first_available("windowsdefender://threat", "windowsdefender:", "ms-settings:windowsdefender")),
        ("🔒", "Изоляция ядра", "Параметры безопасности устройства", lambda: open_first_available("windowsdefender://coreisolation", "ms-settings:windowsdefender", "windowsdefender:")),
        ("📶", "Использование данных", "Сеть и интернет", lambda: open_first_available("ms-settings:datausage", "ms-settings:network")),
        ("🗑", "Корзина", "Недавно удаленные файлы", lambda: open_program(["explorer.exe", "shell:RecycleBinFolder"], "Не удалось открыть корзину.")),
        ("🖥", "Дата Windows", "Дата установки системы", show_windows_install_date),
    ]


QUICK_ACTIONS = build_quick_actions()


def create_app() -> tk.Tk:
    global root, status_var

    set_app_id()

    root = tk.Tk()
    status_var = tk.StringVar(value="Готово")

    root.title(APP_TITLE)
    root.configure(bg=BG)
    root.resizable(False, False)

    x = (root.winfo_screenwidth() - WINDOW_W) // 2
    y = (root.winfo_screenheight() - WINDOW_H) // 2
    root.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")
    root.minsize(WINDOW_W, WINDOW_H)
    apply_icon(root)

    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="both", expand=True, padx=16, pady=16)

    content = tk.Frame(outer, bg=BG)
    content.pack(fill="both", expand=True)
    content.columnconfigure(0, weight=5, uniform="layout")
    content.columnconfigure(1, weight=3, uniform="layout")

    left = tk.Frame(content, bg=BG)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    left.columnconfigure(0, weight=1)
    left.columnconfigure(1, weight=1)

    rows_needed = (len(QUICK_ACTIONS) + 1) // 2
    for row_index in range(rows_needed):
        left.rowconfigure(row_index, weight=1)

    for index, (icon_text, title, subtitle, command) in enumerate(QUICK_ACTIONS):
        row = index // 2
        column = index % 2
        card = ActionCard(left, icon_text, title, subtitle, command)
        card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)

    right = tk.Frame(content, bg=BG)
    right.grid(row=0, column=1, sticky="nsew")
    right.columnconfigure(0, weight=1)
    right.rowconfigure(0, weight=0)
    right.rowconfigure(1, weight=0)

    registry_section = SideSection(right, "Быстрые пути реестра")
    registry_section.grid(row=0, column=0, sticky="ew", pady=(6, 10))

    for row_index, (button_number, short_name, reg_path) in enumerate(REG_PATHS):
        button = MiniButton(
            registry_section.body,
            f"Путь {button_number}",
            lambda path=reg_path, name=short_name: open_regedit_path(path, name),
        )
        button.pack(fill="x", pady=(0, 8 if row_index < len(REG_PATHS) - 1 else 0))

    links_section = SideSection(right, "Дальнейшая проверка")
    links_section.grid(row=1, column=0, sticky="ew")

    alt_button = MiniButton(links_section.body, "Альтернативные аккаунты", open_alt_accounts)
    alt_button.pack(fill="x", pady=(0, 8))

    for row_index, (title, url) in enumerate(CHECK_LINKS):
        button = MiniButton(links_section.body, title, lambda link=url: open_link(link))
        button.pack(fill="x", pady=(0, 8 if row_index < len(CHECK_LINKS) - 1 else 0))

    status_bar = tk.Label(
        outer,
        textvariable=status_var,
        bg=BG,
        fg=STATUS,
        font=("Bahnschrift", 8),
        anchor="w",
    )
    status_bar.pack(fill="x", pady=(8, 0))

    return root


if __name__ == "__main__":
    app = create_app()
    app.mainloop()
