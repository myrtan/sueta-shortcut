import os
import sys
import ctypes
import subprocess
import webbrowser
import winreg
from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

APP_TITLE = "Sueta Shortcut"
ICON_FILE = "sueta.ico"
APP_ID = "sueta.shortcut.app"
WINDOW_W = 1360
WINDOW_H = 860

WINDOWS_INSTALL_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
WINDOWS_INSTALL_VALUE = "InstallDate"
ALT_ACCOUNTS_PATH = r"C:\Program Files (x86)\Steam\config\loginusers.vdf"
RECENT_PATH = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
PREFETCH_PATH = r"C:\Windows\Prefetch"
AMCACHE_PATH = r"C:\Windows\AppCompat\Programs\Amcache.hve"
LOGS_PATH = r"C:\Windows\System32\winevt\Logs"

REG_PATHS = [
    ("🧭 UserAssist", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"),
    ("🗂 ShellBags", r"HKEY_CURRENT_USER\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU"),
    ("📦 Store", r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store"),
    ("🪟 AppSwitched", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\AppSwitched"),
    ("📌 ShowJumpView", r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\ShowJumpView"),
    ("⚙ BAM", r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings"),
    ("⚙ DAM", r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\dam\State\UserSettings"),
    ("📝 MUICache", r"HKEY_CURRENT_USER\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"),
    ("🔎 TypedPaths", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths"),
    ("🔍 WordWheelQuery", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery"),
    ("📂 OpenSavePidlMRU", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU"),
    ("📁 LastVisitedPidlMRU", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU"),
    ("🕘 RecentDocs", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs"),
    ("🧱 AppCompatCache", r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache"),
    ("⌨ RunMRU", r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
]

LOG_FILES = [
    ("🔐 Security", os.path.join(LOGS_PATH, "Security.evtx")),
    ("🖥 System", os.path.join(LOGS_PATH, "System.evtx")),
    ("🛡 Defender", os.path.join(LOGS_PATH, "Microsoft-Windows-Windows Defender%4Operational.evtx")),
    ("⌨ PowerShell", os.path.join(LOGS_PATH, "Microsoft-Windows-PowerShell%4Operational.evtx")),
]

CHECK_LINKS = [
    ("🕵 LastActivityView", "https://www.nirsoft.net/utils/lastactivityview.zip"),
    ("🔌 USBDeview", "https://www.nirsoft.net/utils/usbdeview-x64.zip"),
    ("📊 System Informer", "https://disk.yandex.ru/d/TO1Epwdy9Padqw"),
    ("♻ Recuva", "https://download.ccleaner.com/rcsetup154.exe"),
    ("🔎 Everything", "https://www.voidtools.com/Everything-1.4.1.1032.x64.zip"),
    ("🧰 detect.ac/tools", "https://detect.ac/tools"),
]

QUICK_ACTIONS = [
    ("🕘 Recent", "Недавние файлы и ярлыки", lambda: open_folder(RECENT_PATH)),
    ("🧪 Temp", "Временные файлы пользователя", lambda: open_folder(os.environ.get("TEMP", ""))),
    ("⚡ Prefetch", "Системный кэш запуска", lambda: open_folder(PREFETCH_PATH)),
    ("🧩 Regedit", "Редактор реестра Windows", lambda: open_program(["regedit.exe"], "Не удалось открыть regedit.", "Открыт regedit")),
    ("🛡 Защита", "Окно безопасности Windows", lambda: open_first_available("windowsdefender://threat", "windowsdefender:", "ms-settings:windowsdefender")),
    ("🔒 Изоляция ядра", "Параметры безопасности устройства", lambda: open_first_available("windowsdefender://coreisolation", "ms-settings:windowsdefender", "windowsdefender:")),
    ("🌐 Сеть", "Параметры сети и расхода данных", lambda: open_first_available("ms-settings:datausage", "ms-settings:network")),
    ("🗑 Корзина", "Недавно удаленные файлы", lambda: open_program(["explorer.exe", "shell:RecycleBinFolder"], "Не удалось открыть корзину.", "Открыта корзина")),
    ("🖥 Дата Windows", "Дата установки системы", lambda: show_windows_install_date()),
    ("📦 Amcache.hve", "Показать файл базы Amcache", lambda: reveal_file(AMCACHE_PATH, "Amcache.hve")),
]

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
main_window: Optional["MainWindow"] = None


def set_status(text: str) -> None:
    if main_window is not None:
        main_window.set_status(text)


def resource_path(filename: str) -> str:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, filename)


def set_app_id() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin() -> None:
    if is_admin():
        return

    try:
        if getattr(sys, "frozen", False):
            executable = sys.executable
            params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        else:
            executable = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{script_path}"', *[f'"{arg}"' for arg in sys.argv[1:]]])

        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        if result <= 32:
            raise OSError(f"ShellExecuteW returned {result}")
    except Exception as error:
        ctypes.windll.user32.MessageBoxW(None, f"Не удалось запросить права администратора.\n\n{error}", APP_TITLE, 0x10)
    raise SystemExit(0)


def show_error(text: str) -> None:
    QMessageBox.critical(main_window, APP_TITLE, text)


def show_info(text: str) -> None:
    QMessageBox.information(main_window, APP_TITLE, text)


def silent_popen(args: list[str]) -> None:
    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
        shell=False,
    )


def run_hidden(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
        creationflags=CREATE_NO_WINDOW,
        shell=False,
    )


def open_program(args: list[str], error_text: str, success_text: Optional[str] = None) -> None:
    try:
        silent_popen(args)
        if success_text:
            set_status(success_text)
    except Exception as error:
        show_error(f"{error_text}\n\n{error}")


def start_target(target: str) -> bool:
    try:
        os.startfile(target)
        return True
    except Exception:
        return False


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


def open_file(path: str, label: str) -> None:
    if not os.path.exists(path):
        show_error(f"Файл не найден:\n{path}")
        return
    try:
        os.startfile(path)
        set_status(f"Открыт файл: {label}")
    except Exception as error:
        show_error(f"Не удалось открыть файл:\n{path}\n\n{error}")


def reveal_file(path: str, label: str) -> None:
    if not os.path.exists(path):
        show_error(f"Файл не найден:\n{path}")
        return
    open_program(
        ["explorer.exe", f"/select,{path}"],
        f"Не удалось показать файл:\n{path}",
        f"Показан файл: {label}",
    )


def open_uri(uri: str) -> None:
    if start_target(uri):
        return
    try:
        webbrowser.open(uri, new=2)
        set_status(f"Открыто: {uri}")
    except Exception as error:
        show_error(f"Не удалось открыть:\n{uri}\n\n{error}")


def open_first_available(*targets: str) -> None:
    for target in targets:
        if start_target(target):
            set_status(f"Открыто: {target}")
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
                "reg",
                "add",
                r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Applets\Regedit",
                "/v",
                "LastKey",
                "/t",
                "REG_SZ",
                "/d",
                reg_path,
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


def open_event_log(path: str, label: str) -> None:
    open_file(path, label)


def apply_shadow(widget: QWidget, color: str = "#000000", blur: int = 36, offset_y: int = 10) -> None:
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)


class GlassCardButton(QPushButton):
    def __init__(self, title: str, subtitle: str, callback: Callable[[], None]):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(False)
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(118)
        self.clicked.connect(callback)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("CardSubtitle")
        subtitle_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)

        self.setProperty("role", "card")
        apply_shadow(self, color="#00000088", blur=44, offset_y=14)


class PillButton(QPushButton):
    def __init__(self, text: str, callback: Callable[[], None], accent: bool = False):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(callback)
        self.setMinimumHeight(54)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setProperty("accent", accent)


class SectionFrame(QFrame):
    def __init__(self, title: str, columns: int):
        super().__init__()
        self.columns = columns
        self.setObjectName("SectionFrame")
        apply_shadow(self, color="#00000066", blur=32, offset_y=8)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 20, 22, 22)
        outer.setSpacing(18)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        outer.addWidget(title_label)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        outer.addLayout(self.grid)

    def add_buttons(self, buttons: list[QPushButton]) -> None:
        for index, button in enumerate(buttons):
            row = index // self.columns
            column = index % self.columns
            self.grid.addWidget(button, row, column)
        for column in range(self.columns):
            self.grid.setColumnStretch(column, 1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(WINDOW_W, WINDOW_H)
        self.setMinimumSize(1180, 760)
        self._apply_icon()
        self._build_ui()
        self._setup_shortcuts()

    def _apply_icon(self) -> None:
        icon_path = resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _setup_shortcuts(self) -> None:
        toggle_shortcut = QShortcut(QKeySequence("F11"), self)
        toggle_shortcut.activated.connect(self.toggle_fullscreen)

        exit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        exit_shortcut.activated.connect(self.exit_fullscreen)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        shell = QVBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        scroll.setWidget(content)

        shell.addWidget(scroll)

        body = QVBoxLayout(content)
        body.setContentsMargins(24, 24, 24, 24)
        body.setSpacing(20)

        quick_section = SectionFrame("Быстрые действия", 4)
        quick_buttons = [GlassCardButton(title, subtitle, callback) for title, subtitle, callback in QUICK_ACTIONS]
        quick_section.add_buttons(quick_buttons)
        body.addWidget(quick_section)

        registry_section = SectionFrame("Артефакты реестра", 3)
        registry_buttons = [PillButton(title, lambda checked=False, p=path, n=title: open_regedit_path(p, n)) for title, path in REG_PATHS]
        registry_section.add_buttons(registry_buttons)
        body.addWidget(registry_section)

        logs_section = SectionFrame("Журналы Windows", 4)
        log_buttons = [PillButton(title, lambda checked=False, p=path, n=title: open_event_log(p, n)) for title, path in LOG_FILES]
        logs_section.add_buttons(log_buttons)
        body.addWidget(logs_section)

        tools_section = SectionFrame("Дополнительные инструменты", 3)
        tool_buttons = [PillButton("👥 Альтернативные аккаунты", open_alt_accounts)]
        tool_buttons.extend(PillButton(title, lambda checked=False, link=url: open_link(link)) for title, url in CHECK_LINKS)
        tools_section.add_buttons(tool_buttons)
        body.addWidget(tools_section)

        body.addStretch(1)

        status_wrap = QFrame()
        status_wrap.setObjectName("StatusWrap")
        status_layout = QHBoxLayout(status_wrap)
        status_layout.setContentsMargins(24, 14, 24, 14)
        status_layout.setSpacing(12)

        self.status_label = QLabel("Готово")
        self.status_label.setObjectName("StatusLabel")
        help_label = QLabel("F11: полноэкранный режим, Esc: выйти из него")
        help_label.setObjectName("HelpLabel")

        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(help_label, 0, Qt.AlignRight)
        shell.addWidget(status_wrap)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.resize(WINDOW_W, WINDOW_H)
            self.set_status("Полноэкранный режим отключен")
        else:
            self.showFullScreen()
            self.set_status("Полноэкранный режим включен")

    def exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.resize(WINDOW_W, WINDOW_H)
            self.set_status("Полноэкранный режим отключен")


def build_styles() -> str:
    return """
    QMainWindow, QWidget {
        background: #090506;
        color: #f7ecef;
        font-family: "Segoe UI";
        font-size: 10pt;
    }
    QLabel {
        background: transparent;
    }
    QScrollArea {
        border: none;
        background: transparent;
    }
    QScrollBar:vertical {
        background: #12090c;
        width: 14px;
        margin: 8px 2px 8px 2px;
        border-radius: 7px;
    }
    QScrollBar::handle:vertical {
        background: #5a2b35;
        min-height: 48px;
        border-radius: 7px;
    }
    QScrollBar::handle:vertical:hover {
        background: #7a3947;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    #SectionFrame, #StatusWrap {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #12090c, stop:0.6 #0d0608, stop:1 #080405);
        border: 1px solid #4a232c;
        border-radius: 24px;
    }
    #SectionTitle {
        font-family: "Segoe UI Semibold";
        font-size: 15pt;
        color: #fff2f4;
        padding-bottom: 2px;
    }
    QPushButton[role="card"] {
        text-align: left;
        border: 1px solid #6a2e3b;
        border-radius: 22px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #261014, stop:0.55 #180b0e, stop:1 #100608);
    }
    QPushButton[role="card"]:hover {
        border: 1px solid #b45567;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #35161c, stop:0.55 #221014, stop:1 #16090c);
    }
    QPushButton[role="card"]:pressed {
        background: #110709;
    }
    #CardTitle {
        font-family: "Segoe UI Semibold";
        font-size: 14pt;
        color: #fff5f6;
    }
    #CardSubtitle {
        color: #d8aab3;
        font-size: 10pt;
    }
    PillButton, QPushButton {
        font-family: "Segoe UI Semibold";
    }
    QPushButton[accent="false"], QPushButton[accent="0"], QPushButton[accent="true"], QPushButton[accent="1"] {
        border: 1px solid #6a2e3b;
        border-radius: 18px;
        padding: 14px 18px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #2a1116, stop:1 #190a0d);
        color: #fff3f5;
    }
    QPushButton[accent="false"]:hover, QPushButton[accent="0"]:hover, QPushButton[accent="true"]:hover, QPushButton[accent="1"]:hover {
        border-color: #c16173;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #3a171e, stop:1 #241014);
    }
    QPushButton:pressed {
        padding-top: 15px;
    }
    #StatusLabel {
        color: #fff0f2;
        font-family: "Segoe UI Semibold";
        font-size: 10.5pt;
    }
    #HelpLabel {
        color: #b88f97;
        font-size: 9.5pt;
    }
    QMessageBox {
        background: #100708;
    }
    """


def main() -> int:
    global main_window

    set_app_id()
    ensure_admin()
    app = QApplication(sys.argv)
    app.setStyleSheet(build_styles())

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    main_window = MainWindow()
    main_window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
