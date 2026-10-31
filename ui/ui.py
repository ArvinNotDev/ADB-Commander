"""Modern PyQt6 desktop interface for ADB Commander."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from functions.adb_commands import ADBManager
from functions.adb_extras import ADBExtras


APP_STYLE = """
QMainWindow, QWidget { background:#0a0f1a; color:#e5eaf4; font-family:"Segoe UI","Inter",sans-serif; font-size:10pt; }
QLabel { background:transparent; }
QLabel[muted="true"] { color:#8591a8; }
QLabel[eyebrow="true"] { color:#8291ad; font-size:9pt; font-weight:700; letter-spacing:1px; }
QFrame#Card { background:#111827; border:1px solid #202b3e; border-radius:18px; }
QFrame#SoftCard { background:#0e1625; border:1px solid #202b3e; border-radius:14px; }
QFrame#TopBar { background:#0d1422; border:1px solid #202b3e; border-radius:16px; }
QLabel#AppTitle { font-size:15pt; font-weight:800; color:#f4f7ff; }
QLabel#PageTitle { font-size:22pt; font-weight:800; color:#f4f7ff; }
QLabel#SectionTitle { font-size:12pt; font-weight:750; color:#f3f6fc; }
QLabel#MetricValue { font-size:19pt; font-weight:800; color:#f3f7ff; }
QLabel#ConnectionPill { background:#202b3e; border:1px solid #33445f; border-radius:10px; padding:7px 12px; font-weight:700; }
QLabel#ConnectionPill[connected="true"] { background:#12372e; color:#78e3b3; border-color:#1d5c49; }
QLabel#ConnectionPill[warning="true"] { background:#3b2b18; color:#f9cc86; border-color:#765326; }
QPushButton { background:#1a2639; color:#dbe5f6; border:1px solid #2b3a52; border-radius:10px; padding:9px 13px; font-weight:650; }
QPushButton:hover { background:#24344c; border-color:#46648f; }
QPushButton:pressed { background:#172236; }
QPushButton:disabled { color:#5f6b80; background:#121a28; border-color:#1d2738; }
QPushButton[primary="true"] { background:#4c7dff; color:#fff; border-color:#5d8aff; }
QPushButton[primary="true"]:hover { background:#6590ff; }
QPushButton[danger="true"] { background:#321f2a; color:#ffb6c4; border-color:#5c3041; }
QPushButton[nav="true"] { background:transparent; border:1px solid transparent; color:#9aa8bf; padding:10px 15px; border-radius:10px; }
QPushButton[nav="true"]:hover { background:#152035; color:#edf3ff; }
QPushButton[nav="true"]:checked { color:#fff; background:#1d2f4c; border-color:#35517e; }
QComboBox, QLineEdit { background:#0b1321; color:#e5eaf4; border:1px solid #2a3850; border-radius:10px; padding:9px 10px; selection-background-color:#416de0; }
QComboBox::drop-down { border:none; width:24px; }
QComboBox QAbstractItemView { background:#111827; color:#e5eaf4; selection-background-color:#243c63; border:1px solid #2a3850; }
QTextEdit { background:#0b1220; color:#cbd8ed; border:1px solid #233148; border-radius:12px; padding:10px; selection-background-color:#385eaa; }
QProgressBar { background:#121c2c; border:none; border-radius:3px; min-height:5px; max-height:5px; }
QProgressBar::chunk { background:#6691ff; border-radius:3px; }
QTableWidget { background:#0d1524; alternate-background-color:#101b2c; color:#dce6f8; border:1px solid #26344a; border-radius:12px; gridline-color:#202c40; selection-background-color:#21395f; selection-color:#fff; }
QHeaderView::section { background:#141f31; color:#a9b8d0; padding:10px; border:none; border-bottom:1px solid #2a3850; font-weight:700; }
QScrollBar:vertical { background:#0d1524; width:10px; margin:3px; }
QScrollBar::handle:vertical { background:#2b3b54; border-radius:4px; min-height:25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
"""


class WorkerSignals(QObject):
    finished = pyqtSignal(object, object)
    error = pyqtSignal(object, str)


class Worker(QRunnable):
    """Execute blocking ADB calls away from the GUI thread."""

    def __init__(self, fn, label: str, quiet: bool = False, on_success=None, on_error=None):
        super().__init__()
        self.setAutoDelete(False)
        self.fn, self.label, self.quiet = fn, label, quiet
        self.on_success, self.on_error = on_success, on_error
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.finished.emit(self, self.fn())
        except Exception as exc:
            self.signals.error.emit(self, str(exc))


class PhonePreview(QWidget):
    """Paint a handset illustration with a different connected state."""

    def __init__(self):
        super().__init__()
        self.connected, self.serial = False, ""
        self.setMinimumSize(230, 310)
        self.setMaximumHeight(400)

    def set_device(self, connected: bool, serial: str = ""):
        self.connected, self.serial = connected, serial
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self.rect()
        center = area.center()
        pw = min(200, max(155, area.width() - 45))
        ph = min(345, max(260, area.height() - 24))
        x, y = center.x() - pw // 2, center.y() - ph // 2 - 3
        case = QLinearGradient(x, y, x + pw, y + ph)
        case.setColorAt(0, QColor("#1d4966" if self.connected else "#1a2638"))
        case.setColorAt(1, QColor("#29235a" if self.connected else "#111827"))
        painter.setPen(QPen(QColor("#3a6682" if self.connected else "#344055"), 2))
        painter.setBrush(case)
        painter.drawRoundedRect(x, y, pw, ph, 30, 30)
        sx, sy, sw, sh = x + 10, y + 11, pw - 20, ph - 22
        screen = QLinearGradient(sx, sy, sx + sw, sy + sh)
        if self.connected:
            screen.setColorAt(0, QColor("#0e5265"))
            screen.setColorAt(.55, QColor("#183a60"))
            screen.setColorAt(1, QColor("#292451"))
        else:
            screen.setColorAt(0, QColor("#101827"))
            screen.setColorAt(1, QColor("#0c1320"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(screen)
        painter.drawRoundedRect(sx, sy, sw, sh, 22, 22)
        painter.setBrush(QColor("#080e18"))
        painter.drawRoundedRect(center.x() - 24, y + 10, 48, 6, 3, 3)
        if self.connected:
            painter.setPen(QColor("#d6e7ff"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.drawText(sx + 10, sy + 28, "ADB COMMANDER")
            painter.setPen(QPen(QColor("#79e4bd"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center.x() - 24, center.y() - 42, 48, 48)
            painter.setPen(QPen(QColor("#79e4bd"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(center.x() - 12, center.y() - 17, center.x() - 3, center.y() - 7)
            painter.drawLine(center.x() - 3, center.y() - 7, center.x() + 14, center.y() - 28)
            painter.setPen(QColor("#dbeafe"))
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.drawText(sx + 8, center.y() + 35, "Device connected")
            painter.setPen(QColor("#91a9c8"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(sx + 8, center.y() + 55, self.serial[:20])
            painter.setPen(QColor("#86e8c2"))
            painter.drawText(sx + 8, sy + sh - 17, "●  ONLINE")
            for i, height in enumerate((20, 32, 25, 43, 35, 53, 39, 46, 29)):
                painter.setBrush(QColor(87, 165, 255, 110 + i * 12))
                painter.drawRoundedRect(sx + 13 + i * 15, sy + sh - 47 - height, 8, height, 3, 3)
        else:
            painter.setPen(QColor("#8795ab"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(sx + 6, sy + 40, "WAITING FOR DEVICE")
            painter.setPen(QPen(QColor("#56657b"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(center.x() - 31, center.y() - 28, 62, 100, 8, 8)
            painter.setPen(QPen(QColor("#74849b"), 2))
            painter.drawLine(center.x() - 14, center.y() - 8, center.x() + 14, center.y() - 8)
            painter.drawLine(center.x() - 14, center.y() + 3, center.x() + 14, center.y() + 3)
            painter.drawLine(center.x() - 14, center.y() + 14, center.x() + 7, center.y() + 14)
            painter.setPen(QColor("#718099"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(sx + 8, sy + sh - 27, "Connect USB or Wi-Fi ADB")
        painter.end()


class ADBFastbootUI(QMainWindow):
    """Multi-page desktop workspace for everyday Android debugging."""

    def __init__(self):
        super().__init__()
        self.adb = None
        self.extras = None
        self.devices = []
        self.active_workers = 0
        self.device_scan_pending = False
        self.thread_pool = QThreadPool.globalInstance()
        self._workers = set()
        self._build_ui()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(lambda: self._refresh_devices(quiet=True))
        self.refresh_timer.start()
        self._refresh_devices(quiet=False)

    def _get_adb(self):
        if self.adb is None:
            self.adb = ADBManager()
        return self.adb

    def _get_extras(self):
        if self.extras is None:
            self.extras = ADBExtras(self._get_adb())
        return self.extras

    def _build_ui(self):
        self.setWindowTitle("ADB Commander")
        self.resize(1320, 860)
        self.setMinimumSize(1040, 700)
        self.setStyleSheet(APP_STYLE)
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(22, 18, 22, 14)
        root_layout.setSpacing(14)
        self.setCentralWidget(root)

        topbar = QFrame()
        topbar.setObjectName("TopBar")
        top = QHBoxLayout(topbar)
        top.setContentsMargins(18, 12, 18, 12)
        logo = QLabel("ADB")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(48, 44)
        logo.setStyleSheet("background:#4c7dff;border-radius:13px;color:white;font-size:12pt;font-weight:900;")
        top.addWidget(logo)
        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("ADB Commander")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Android device workspace")
        subtitle.setProperty("muted", True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        top.addLayout(title_col)
        top.addStretch(1)
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(240)
        self.device_combo.currentIndexChanged.connect(self._device_changed)
        top.addWidget(self.device_combo)
        refresh = QPushButton("↻  Refresh")
        refresh.clicked.connect(lambda: self._refresh_devices(quiet=False))
        top.addWidget(refresh)
        self.connection_pill = QLabel("Checking")
        self.connection_pill.setObjectName("ConnectionPill")
        self.connection_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self.connection_pill)
        root_layout.addWidget(topbar)

        nav_frame = QFrame()
        nav_frame.setObjectName("SoftCard")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 5, 8, 5)
        nav_layout.setSpacing(3)
        self.nav_buttons = []
        self.pages = QStackedWidget()
        pages = [
            ("Overview", self._make_overview),
            ("Device", self._make_device_page),
            ("Apps", self._make_apps_page),
            ("Capture", self._make_capture_page),
            ("File transfer", self._make_transfer_page),
            ("Terminal", self._make_terminal_page),
        ]
        for index, (name, builder) in enumerate(pages):
            button = QPushButton(name)
            button.setProperty("nav", True)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self._navigate(i))
            nav_layout.addWidget(button)
            self.nav_buttons.append(button)
            self.pages.addWidget(builder())
        nav_layout.addStretch(1)
        self.nav_buttons[0].setChecked(True)
        root_layout.addWidget(nav_frame)
        root_layout.addWidget(self.pages, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("muted", True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(155)
        self.progress_bar.setVisible(False)
        footer.addWidget(self.status_label)
        footer.addStretch(1)
        footer.addWidget(self.progress_bar)
        version = QLabel("ADB COMMANDER  •  DESKTOP")
        version.setProperty("eyebrow", True)
        footer.addWidget(version)
        root_layout.addLayout(footer)

    def _page(self, title: str, subtitle: str):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 6, 2, 2)
        layout.setSpacing(16)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        sub = QLabel(subtitle)
        sub.setProperty("muted", True)
        sub.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(sub)
        return page, layout

    def _card(self, title: str | None = None, subtitle: str | None = None):
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 17, 18, 17)
        layout.setSpacing(12)
        if title:
            label = QLabel(title)
            label.setObjectName("SectionTitle")
            layout.addWidget(label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty("muted", True)
            sub.setWordWrap(True)
            layout.addWidget(sub)
        return frame, layout

    def _metric(self, title: str, value: str, note: str = ""):
        card, layout = self._card()
        name = QLabel(title.upper())
        name.setProperty("eyebrow", True)
        number = QLabel(value)
        number.setObjectName("MetricValue")
        foot = QLabel(note)
        foot.setProperty("muted", True)
        foot.setWordWrap(True)
        layout.addWidget(name)
        layout.addWidget(number)
        layout.addWidget(foot)
        card.metric_value, card.metric_note = number, foot
        return card

    def _make_overview(self):
        page, layout = self._page("Your Android workspace", "A focused view of device connectivity, diagnostics and everyday ADB tools.")
        columns = QHBoxLayout()
        columns.setSpacing(16)
        phone_card, phone_layout = self._card("DEVICE PREVIEW", "Your device at a glance")
        self.phone_preview = PhonePreview()
        phone_layout.addWidget(self.phone_preview, 1)
        self.phone_state = QLabel("No device connected")
        self.phone_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phone_state.setObjectName("SectionTitle")
        phone_layout.addWidget(self.phone_state)
        hint = QLabel("Connect by USB or use Android wireless debugging.")
        hint.setProperty("muted", True)
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        phone_layout.addWidget(hint)
        columns.addWidget(phone_card, 4)

        right = QVBoxLayout()
        right.setSpacing(14)
        summary, summary_layout = self._card("DEVICE INSIGHTS", "Run diagnostics to refresh Android, storage and battery values.")
        metrics = QGridLayout()
        metrics.setSpacing(10)
        self.metric_connection = self._metric("Connection", "Offline", "Waiting for ADB")
        self.metric_android = self._metric("Android", "—", "Android release")
        self.metric_storage = self._metric("Storage", "—", "Used on /data")
        self.metric_battery = self._metric("Battery", "—", "Battery level")
        for i, card in enumerate((self.metric_connection, self.metric_android, self.metric_storage, self.metric_battery)):
            metrics.addWidget(card, i // 2, i % 2)
        summary_layout.addLayout(metrics)
        diagnostics = QPushButton("Run device diagnostics")
        diagnostics.setProperty("primary", True)
        diagnostics.clicked.connect(self._run_diagnostics)
        summary_layout.addWidget(diagnostics)
        right.addWidget(summary)

        quick, quick_layout = self._card("QUICK ACTIONS", "Jump straight into a common task.")
        quick_grid = QGridLayout()
        for i, (caption, callback) in enumerate((
            ("Device details", lambda: self._navigate(1)),
            ("Manage apps", lambda: self._navigate(2)),
            ("Take screenshot", self._capture_screenshot),
            ("Open terminal", lambda: self._navigate(5)),
        )):
            button = QPushButton(caption)
            button.clicked.connect(callback)
            quick_grid.addWidget(button, i // 2, i % 2)
        quick_layout.addLayout(quick_grid)
        right.addWidget(quick)

        activity, activity_layout = self._card("RECENT ACTIVITY", "Operations and results.")
        self.activity_box = QTextEdit()
        self.activity_box.setReadOnly(True)
        self.activity_box.setMinimumHeight(85)
        self.activity_box.setMaximumHeight(130)
        self.activity_box.setPlaceholderText("Your recent operations will appear here.")
        activity_layout.addWidget(self.activity_box)
        right.addWidget(activity)
        columns.addLayout(right, 6)
        layout.addLayout(columns, 1)
        return page

    def _make_device_page(self):
        page, layout = self._page("Device center", "Inspect device identity, health and connectivity. Reboot operations require confirmation.")
        row = QHBoxLayout()
        info, info_layout = self._card("DEVICE INFORMATION", "Brand, model, Android release and SDK level.")
        self.device_details = QTextEdit()
        self.device_details.setReadOnly(True)
        self.device_details.setMinimumHeight(165)
        self.device_details.setPlaceholderText("Select an authorized device, then load its information.")
        info_layout.addWidget(self.device_details)
        buttons = QHBoxLayout()
        info_button = QPushButton("Load device info")
        info_button.setProperty("primary", True)
        info_button.clicked.connect(lambda: self._device_action(lambda a, s: a.get_device_info(s), "Read device information", self._show_device_info))
        wifi_button = QPushButton("Wi-Fi IP")
        wifi_button.clicked.connect(lambda: self._device_action(lambda a, s: self._get_extras().get_wifi_ip(s), "Read Wi-Fi IP"))
        buttons.addWidget(info_button)
        buttons.addWidget(wifi_button)
        info_layout.addLayout(buttons)
        row.addWidget(info, 5)

        diag, diag_layout = self._card("DIAGNOSTICS", "Run individual checks without leaving this page.")
        actions = [
            ("Storage usage", lambda: self._device_action(lambda a, s: a.storage_status(s), "Read storage status")),
            ("Battery details", lambda: self._device_action(lambda a, s: a.battery_status(s), "Read battery status")),
            ("Display resolution", lambda: self._device_action(lambda a, s: self._get_extras().get_screen_resolution(s), "Read display resolution")),
            ("External storage", lambda: self._device_action(lambda a, s: "External storage detected." if a.is_there_any_sd(s) else "No external storage detected.", "Check external storage")),
            ("Root access check", lambda: self._device_action(lambda a, s: "Root access is available." if a.is_device_rooted(s) else "Root access not detected.", "Check root access")),
            ("Recent system log", self._show_logcat),
        ]
        action_grid = QGridLayout()
        action_grid.setSpacing(8)
        for i, (caption, callback) in enumerate(actions):
            button = QPushButton(caption)
            button.clicked.connect(callback)
            action_grid.addWidget(button, i // 2, i % 2)
        diag_layout.addLayout(action_grid)
        wireless_title = QLabel("WIRELESS ADB")
        wireless_title.setProperty("eyebrow", True)
        diag_layout.addWidget(wireless_title)
        wireless_hint = QLabel(
            "Pair a new TV once, then use the separate connect action whenever you need to reconnect."
        )
        wireless_hint.setWordWrap(True)
        wireless_hint.setProperty("muted", True)
        diag_layout.addWidget(wireless_hint)
        wireless_buttons = QHBoxLayout()
        pair_button = QPushButton("Pair new device…")
        pair_button.clicked.connect(self._pair_wireless)
        connect_button = QPushButton("Connect paired device…")
        connect_button.setProperty("primary", True)
        connect_button.clicked.connect(self._connect_paired_wireless)
        wireless_buttons.addWidget(pair_button)
        wireless_buttons.addWidget(connect_button)
        diag_layout.addLayout(wireless_buttons)
        row.addWidget(diag, 5)
        layout.addLayout(row, 1)

        reboot, reboot_layout = self._card("POWER CONTROLS", "These actions interrupt the current ADB session.")
        reboot_row = QHBoxLayout()
        for caption, mode in (("Reboot device", "system"), ("Reboot to bootloader", "bootloader"), ("Reboot to recovery", "recovery")):
            button = QPushButton(caption)
            if mode != "system":
                button.setProperty("danger", True)
            button.clicked.connect(lambda checked=False, m=mode: self._confirm_reboot(m))
            reboot_row.addWidget(button)
        reboot_layout.addLayout(reboot_row)
        layout.addWidget(reboot)
        return page

    def _make_apps_page(self):
        page, layout = self._page("Application manager", "Inspect installed packages and install or remove APKs on the selected device.")
        controls = QHBoxLayout()
        for caption, callback, primary, danger in (
            ("↻  Load installed apps", self._refresh_apps, True, False),
            ("Install APK…", self._install_apk, False, False),
            ("Uninstall selected", self._uninstall_app, False, True),
        ):
            button = QPushButton(caption)
            if primary:
                button.setProperty("primary", True)
            if danger:
                button.setProperty("danger", True)
            button.clicked.connect(callback)
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        card, card_layout = self._card("INSTALLED PACKAGES", "The list defaults to third-party apps.")
        self.apps_table = QTableWidget(0, 2)
        self.apps_table.setHorizontalHeaderLabels(["#", "Package name"])
        self.apps_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.apps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.apps_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.apps_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.apps_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.apps_table.setAlternatingRowColors(True)
        card_layout.addWidget(self.apps_table)
        layout.addWidget(card, 1)
        return page

    def _make_capture_page(self):
        page, layout = self._page("Capture studio", "Save screenshots, screen recordings and diagnostic logs to your computer.")
        grid = QGridLayout()
        grid.setSpacing(14)
        screenshot, screenshot_layout = self._card("SCREENSHOT", "Capture the current Android display as a PNG image.")
        icon = QLabel("▧")
        icon.setStyleSheet("font-size:35pt;color:#80aaff;")
        screenshot_layout.addWidget(icon)
        screenshot_layout.addWidget(QLabel("Capture directly through adb exec-out."))
        button = QPushButton("Capture screenshot…")
        button.setProperty("primary", True)
        button.clicked.connect(self._capture_screenshot)
        screenshot_layout.addWidget(button)
        grid.addWidget(screenshot, 0, 0)

        record, record_layout = self._card("SCREEN RECORDING", "Record the display and copy the MP4 to your computer.")
        icon2 = QLabel("◉")
        icon2.setStyleSheet("font-size:35pt;color:#c5a5ff;")
        record_layout.addWidget(icon2)
        record_layout.addWidget(QLabel("Choose a recording duration from 1 second to 1 hour."))
        rec_button = QPushButton("Record screen…")
        rec_button.clicked.connect(self._record_screen)
        record_layout.addWidget(rec_button)
        grid.addWidget(record, 0, 1)

        logs, logs_layout = self._card("DIAGNOSTIC LOG", "Export recent Android logcat output for troubleshooting.")
        logs_layout.addWidget(QLabel("Collect up to 10,000 recent lines and save them as a text file."))
        log_button = QPushButton("Export recent logcat…")
        log_button.clicked.connect(self._export_logcat)
        logs_layout.addWidget(log_button)
        grid.addWidget(logs, 1, 0, 1, 2)
        layout.addLayout(grid)
        layout.addStretch(1)
        return page

    def _make_transfer_page(self):
        page, layout = self._page("File transfer", "Move files between your computer and Android with ADB push and pull.")
        columns = QHBoxLayout()
        push, push_layout = self._card("COMPUTER → DEVICE", "Choose a local file and its destination path on Android.")
        self.push_local = QLineEdit()
        self.push_local.setPlaceholderText("Local file path…")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_push_file)
        row = QHBoxLayout()
        row.addWidget(self.push_local, 1)
        row.addWidget(browse)
        push_layout.addLayout(row)
        push_layout.addWidget(QLabel("Remote destination"))
        self.push_remote = QLineEdit("/sdcard/Download/")
        push_layout.addWidget(self.push_remote)
        push_button = QPushButton("Push file to device")
        push_button.setProperty("primary", True)
        push_button.clicked.connect(self._push_file)
        push_layout.addWidget(push_button)
        push_layout.addStretch(1)
        columns.addWidget(push)

        pull, pull_layout = self._card("DEVICE → COMPUTER", "Enter a remote file path and choose where to save the copy.")
        pull_layout.addWidget(QLabel("Remote file path"))
        self.pull_remote = QLineEdit("/sdcard/Download/")
        pull_layout.addWidget(self.pull_remote)
        self.pull_local = QLineEdit()
        self.pull_local.setPlaceholderText("Local destination path…")
        browse_dest = QPushButton("Save as…")
        browse_dest.clicked.connect(self._browse_pull_file)
        row2 = QHBoxLayout()
        row2.addWidget(self.pull_local, 1)
        row2.addWidget(browse_dest)
        pull_layout.addLayout(row2)
        pull_button = QPushButton("Pull file from device")
        pull_button.clicked.connect(self._pull_file)
        pull_layout.addWidget(pull_button)
        pull_layout.addStretch(1)
        columns.addWidget(pull)
        layout.addLayout(columns)
        note, note_layout = self._card("PATH TIPS")
        tip = QLabel("Use Android paths such as /sdcard/Download/example.pdf. Android permissions and scoped storage may restrict access to app-private directories.")
        tip.setProperty("muted", True)
        tip.setWordWrap(True)
        note_layout.addWidget(tip)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _make_terminal_page(self):
        page, layout = self._page("ADB terminal", "Run a command on the selected Android device and inspect the output here.")
        warning, warning_layout = self._card("ADVANCED TOOL", "Shell commands can change or delete data. Only run commands you understand.")
        warning_layout.addWidget(QLabel("Examples: getprop ro.product.model  •  dumpsys battery  •  pm list packages"))
        layout.addWidget(warning)
        terminal, terminal_layout = self._card("COMMAND")
        row = QHBoxLayout()
        self.shell_input = QLineEdit()
        self.shell_input.setPlaceholderText("Enter Android shell command…")
        self.shell_input.returnPressed.connect(self._execute_shell)
        row.addWidget(self.shell_input, 1)
        run = QPushButton("Run command")
        run.setProperty("primary", True)
        run.clicked.connect(self._execute_shell)
        row.addWidget(run)
        terminal_layout.addLayout(row)
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setPlaceholderText("Command output will appear here.")
        self.terminal_output.setMinimumHeight(260)
        terminal_layout.addWidget(self.terminal_output, 1)
        clear = QPushButton("Clear output")
        clear.clicked.connect(self.terminal_output.clear)
        terminal_layout.addWidget(clear, 0, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(terminal, 1)
        return page

    def _navigate(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    def _selected_serial(self):
        value = self.device_combo.currentData()
        return str(value) if value else None

    def _selected_device_ready(self):
        serial = self._selected_serial()
        return any(item.serial == serial and item.ready for item in self.devices)

    def _refresh_devices(self, quiet: bool = False):
        if self.device_scan_pending:
            return
        self.device_scan_pending = True

        def loaded(devices):
            self.device_scan_pending = False
            self._devices_loaded(devices)

        def failed(message):
            self.device_scan_pending = False
            if not quiet:
                self._append_activity("Device refresh failed: " + message)

        self._run(lambda: self._get_adb().get_devices(), "Scanning for devices", quiet=quiet, on_success=loaded, on_error=failed)

    def _devices_loaded(self, devices):
        old_serial = self._selected_serial()
        self.devices = list(devices or [])
        ready = [device for device in self.devices if device.ready]
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        if not self.devices:
            self.device_combo.addItem("No devices detected", None)
        else:
            for device in self.devices:
                state = "Connected" if device.ready else device.state.capitalize()
                self.device_combo.addItem(device.serial + "  ·  " + state, device.serial)
        index = self.device_combo.findData(old_serial) if old_serial else -1
        if index < 0 and ready:
            index = self.device_combo.findData(ready[0].serial)
        if index < 0 and self.devices:
            index = 0
        if index >= 0:
            self.device_combo.setCurrentIndex(index)
        self.device_combo.blockSignals(False)
        self._device_changed()
        if ready:
            self.status_label.setText(str(len(ready)) + " authorized device(s) detected")
        elif any(d.state == "unauthorized" for d in self.devices):
            self.status_label.setText("Unlock the phone and accept the debugging prompt")
        else:
            self.status_label.setText("No authorized Android device")
        if not self.devices:
            self.metric_android.metric_value.setText("—")
            self.metric_storage.metric_value.setText("—")
            self.metric_battery.metric_value.setText("—")

    def _device_changed(self, *_args):
        serial = self._selected_serial()
        device = next((item for item in self.devices if item.serial == serial), None)
        connected = bool(device and device.ready)
        self.connection_pill.setText("●  Connected" if connected else ("⚠  Unauthorized" if device and device.state == "unauthorized" else "○  Disconnected"))
        self.connection_pill.setProperty("connected", connected)
        self.connection_pill.setProperty("warning", bool(device and device.state == "unauthorized"))
        self.connection_pill.style().unpolish(self.connection_pill)
        self.connection_pill.style().polish(self.connection_pill)
        if hasattr(self, "phone_preview"):
            self.phone_preview.set_device(connected, serial or "")
            self.phone_state.setText("Connected · " + serial if connected else "Device needs authorization" if device and device.state == "unauthorized" else "No device connected")
        self.metric_connection.metric_value.setText("Online" if connected else "Offline")
        self.metric_connection.metric_note.setText(serial if connected else "Waiting for an authorized device")

    def _run(self, fn, label: str, quiet: bool = False, on_success=None, on_error=None):
        worker = Worker(fn, label, quiet, on_success, on_error)
        self._workers.add(worker)
        worker.signals.finished.connect(self._worker_finished)
        worker.signals.error.connect(self._worker_error)
        self.active_workers += 1
        self.progress_bar.setVisible(True)
        self.status_label.setText(label + "…")
        self.thread_pool.start(worker)

    @pyqtSlot(object, object)
    def _worker_finished(self, worker, result):
        self._workers.discard(worker)
        self.active_workers = max(0, self.active_workers - 1)
        self.progress_bar.setVisible(self.active_workers > 0)
        self.status_label.setText(worker.label + " completed")
        if not worker.quiet and worker.label != "Scanning for devices":
            self._append_activity(worker.label + " — completed")
        if worker.on_success:
            worker.on_success(result)
        elif not worker.quiet:
            self._append_activity(str(result))
        if worker.label != "Scanning for devices":
            self._refresh_devices(quiet=True)

    @pyqtSlot(object, str)
    def _worker_error(self, worker, message: str):
        self._workers.discard(worker)
        self.active_workers = max(0, self.active_workers - 1)
        self.progress_bar.setVisible(self.active_workers > 0)
        self.status_label.setText("Operation failed")
        if not worker.quiet:
            self._append_activity(worker.label + " — ERROR: " + message)
        if worker.on_error:
            worker.on_error(message)

    def _append_activity(self, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, "activity_box"):
            self.activity_box.append("[" + stamp + "] " + message)
            bar = self.activity_box.verticalScrollBar()
            bar.setValue(bar.maximum())
        else:
            self.status_label.setText(message[:140])

    def _device_action(self, action, label: str, on_success=None):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device before: " + label)
            return
        self._run(lambda: action(self._get_adb(), serial), label, on_success=on_success)

    def _show_device_info(self, result: str):
        self.device_details.setPlainText(result)
        version = next((line.partition(":")[2].strip() for line in result.splitlines() if line.startswith("Android Version:")), "—")
        self.metric_android.metric_value.setText(version or "—")
        self._append_activity("Device information loaded")

    def _run_diagnostics(self):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Connect and authorize a device before running diagnostics.")
            return

        def task():
            adb = self._get_adb()
            return {"info": adb.get_device_info(serial), "storage": adb.storage_status(serial), "battery": adb.battery_status(serial)}

        def done(result):
            self.device_details.setPlainText(result["info"])
            version = next((line.partition(":")[2].strip() for line in result["info"].splitlines() if line.startswith("Android Version:")), "—")
            self.metric_android.metric_value.setText(version or "—")
            self.metric_storage.metric_value.setText(self._percentage(result["storage"]) or "—")
            self.metric_storage.metric_note.setText(result["storage"])
            battery_match = re.search(r"(?m)^level:\s*(\d+)", result["battery"])
            self.metric_battery.metric_value.setText(battery_match.group(1) + "%" if battery_match else "—")
            battery_state = next((line.strip() for line in result["battery"].splitlines() if line.strip().startswith(("status:", "temperature:"))), "Battery details loaded")
            self.metric_battery.metric_note.setText(battery_state)
            self._append_activity("Device diagnostics refreshed")
        self._run(task, "Running device diagnostics", on_success=done)

    @staticmethod
    def _percentage(text: str):
        match = re.search(r"(\d{1,3})%", text)
        return match.group(1) + "%" if match else ""

    def _confirm_reboot(self, mode: str):
        if not self._selected_device_ready():
            self._append_activity("Select an authorized device first.")
            return
        label = {"system": "restart Android", "bootloader": "reboot into the bootloader", "recovery": "reboot into recovery"}[mode]
        answer = QMessageBox.question(self, "Confirm reboot", "Are you sure you want to " + label + "? The ADB session will be interrupted.")
        if answer != QMessageBox.StandardButton.Yes:
            return
        if mode == "system":
            self._device_action(lambda a, s: a._run(["-s", s, "reboot"], timeout=10).stdout or "Device is rebooting.", "Reboot device")
        elif mode == "bootloader":
            self._device_action(lambda a, s: a.reboot_device_to_bootloader(s), "Reboot to bootloader")
        else:
            self._device_action(lambda a, s: a.reboot_device_to_recovery(s), "Reboot to recovery")

    def _pair_wireless(self):
        """Pair this computer with a new Android Wireless Debugging device."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Pair a new device")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        guidance = QLabel(
            "On the TV, open Developer options → Wireless debugging → "
            "Pair device with pairing code. Enter the IP address and pairing port "
            "from that pairing screen, plus its six-digit code."
        )
        guidance.setWordWrap(True)
        guidance.setProperty("muted", True)
        layout.addWidget(guidance)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        pairing_endpoint = QLineEdit()
        pairing_endpoint.setPlaceholderText("TV IP and pairing port, e.g. 192.168.1.50:37123")
        pairing_code = QLineEdit()
        pairing_code.setPlaceholderText("Six-digit pairing code")
        pairing_code.setMaxLength(6)
        pairing_code.setEchoMode(QLineEdit.EchoMode.Password)
        pairing_code.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly)
        form.addRow("Pairing address:port", pairing_endpoint)
        form.addRow("Pairing code", pairing_code)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Pair device")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        endpoint = pairing_endpoint.text().strip()
        code = pairing_code.text().strip()
        if not endpoint or not code:
            QMessageBox.warning(
                self,
                "Pairing details required",
                "Enter the pairing IP:port and six-digit code shown on the TV.",
            )
            return

        def on_paired(result):
            self._append_activity(str(result))
            QMessageBox.information(
                self,
                "Pairing successful",
                "This computer is now paired with the TV.\n\n"
                "To connect, return to the main Wireless debugging screen on the TV, "
                "note its current IP address and debugging port, then choose "
                "'Connect paired device…' in ADB Commander.",
            )

        self._run(
            lambda: self._get_extras().pair_wireless(endpoint, code),
            "Pair wireless device",
            on_success=on_paired,
        )

    def _connect_paired_wireless(self):
        """Connect to a device that this computer has already paired with."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect to a paired device")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        guidance = QLabel(
            "Use this for a TV that has already been paired with this computer. "
            "On the TV, open the main Wireless debugging screen (not the pairing-code screen) "
            "and enter the current IP address and debugging port shown there."
        )
        guidance.setWordWrap(True)
        guidance.setProperty("muted", True)
        layout.addWidget(guidance)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        endpoint_input = QLineEdit()
        endpoint_input.setPlaceholderText("TV IP and debugging port, e.g. 192.168.1.50:42117")
        form.addRow("Connection address:port", endpoint_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Connect")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        endpoint = endpoint_input.text().strip()
        if not endpoint:
            QMessageBox.warning(
                self,
                "Connection address required",
                "Enter the IP address and debugging port shown on the main Wireless debugging screen.",
            )
            return

        self._run(
            lambda: self._get_extras().connect_wireless(endpoint),
            "Connect paired device",
            on_success=lambda result: self._append_activity(str(result)),
        )

    def _show_logcat(self):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device first.")
            return
        self._run(lambda: self._get_extras().get_logcat(serial=serial, lines=200), "Read recent system log", on_success=self._show_text_dialog)

    def _show_text_dialog(self, text: str):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("ADB output")
        dialog.setText("Command completed. Full output is available below.")
        dialog.setDetailedText(str(text))
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()

    def _refresh_apps(self):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device before loading apps.")
            return
        self._run(lambda: self._get_adb().list_installed_apps(serial, third_party_only=True), "Load installed apps", on_success=self._apps_loaded)

    def _apps_loaded(self, output: str):
        packages = sorted({line.strip().removeprefix("package:") for line in str(output).splitlines() if line.strip()})
        self.apps_table.setRowCount(len(packages))
        for index, package in enumerate(packages):
            self.apps_table.setItem(index, 0, QTableWidgetItem(str(index + 1)))
            self.apps_table.setItem(index, 1, QTableWidgetItem(package))
        self._append_activity(str(len(packages)) + " third-party packages loaded")

    def _install_apk(self):
        if not self._selected_device_ready():
            self._append_activity("Select an authorized device before installing an APK.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Select APK", "", "Android packages (*.apk)")
        if path:
            serial = self._selected_serial()
            self._run(lambda: self._get_adb().install_apk(path, serial), "Install APK", on_success=lambda result: self._show_text_dialog(str(result)))

    def _uninstall_app(self):
        if not self._selected_device_ready():
            self._append_activity("Select an authorized device before uninstalling an app.")
            return
        selected = self.apps_table.selectedItems()
        package = selected[1].text() if len(selected) >= 2 else ""
        if not package:
            package, accepted = QInputDialog.getText(self, "Uninstall application", "Package name (example: com.example.app):")
            if not accepted:
                return
        package = package.strip()
        if not package:
            return
        answer = QMessageBox.question(self, "Confirm uninstall", "Uninstall " + package + " from the selected device?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        serial = self._selected_serial()
        self._run(lambda: self._get_adb().uninstall_app(package, serial), "Uninstall application", on_success=lambda result: self._show_text_dialog(str(result)))

    def _capture_screenshot(self):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Connect and authorize a device before capturing a screenshot.")
            return
        suggested = "screenshot-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".png"
        path, _ = QFileDialog.getSaveFileName(self, "Save screenshot", str(Path.home() / suggested), "PNG image (*.png)")
        if path:
            self._run(lambda: self._get_adb().capture_screenshot(path, serial), "Capture screenshot", on_success=lambda result: self._append_activity(str(result)))

    def _record_screen(self):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Connect and authorize a device before recording the screen.")
            return
        suggested = "recording-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".mp4"
        path, _ = QFileDialog.getSaveFileName(self, "Save recording", str(Path.home() / suggested), "MP4 video (*.mp4)")
        if not path:
            return
        duration, accepted = QInputDialog.getInt(self, "Screen recording", "Duration in seconds:", 30, 1, 3600)
        if accepted:
            self._run(lambda: self._get_adb().record_screen(path, duration, serial), "Record screen", on_success=lambda result: self._append_activity(str(result)))

    def _browse_push_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose local file")
        if path:
            self.push_local.setText(path)
            if self.push_remote.text().strip() in ("", "/sdcard/Download/"):
                self.push_remote.setText("/sdcard/Download/" + Path(path).name)

    def _browse_pull_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save downloaded file")
        if path:
            self.pull_local.setText(path)

    def _push_file(self):
        serial = self._selected_serial()
        local, remote = self.push_local.text().strip(), self.push_remote.text().strip()
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device before transferring files.")
            return
        if not local or not remote:
            self._append_activity("Choose a local file and remote destination.")
            return
        self._run(lambda: self._get_extras().push_file(local, remote, serial), "Push file to device", on_success=lambda result: self._append_activity(str(result)))

    def _pull_file(self):
        serial = self._selected_serial()
        remote, local = self.pull_remote.text().strip(), self.pull_local.text().strip()
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device before transferring files.")
            return
        if not remote or not local:
            self._append_activity("Enter a remote path and local destination.")
            return
        self._run(lambda: self._get_extras().pull_file(remote, local, serial), "Pull file from device", on_success=lambda result: self._append_activity(str(result)))

    def _execute_shell(self):
        serial = self._selected_serial()
        command = self.shell_input.text().strip()
        if not command:
            return
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device before running a shell command.")
            return
        self.shell_input.clear()
        self.terminal_output.append("$ " + command)
        self._run(
            lambda: self._get_extras().execute_shell(command, serial),
            "Run shell command",
            on_success=lambda result: self.terminal_output.append(str(result).rstrip() or "(no output)"),
            on_error=lambda message: self.terminal_output.append("Error: " + message),
        )

    def _export_logcat(self):
        serial = self._selected_serial()
        if not serial or not self._selected_device_ready():
            self._append_activity("Select an authorized device first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export logcat", str(Path.home() / "adb-logcat.txt"), "Text files (*.txt)")
        if not path:
            return

        def save_log():
            content = self._get_extras().get_logcat(serial=serial, lines=2000)
            Path(path).expanduser().write_text(content, encoding="utf-8")
            return "Logcat exported to: " + str(Path(path).expanduser())

        self._run(save_log, "Export logcat", on_success=lambda result: self._append_activity(str(result)))

    def closeEvent(self, event):  # noqa: N802 - Qt API
        if self.active_workers:
            QMessageBox.warning(self, "Operations still running", "Wait for active ADB operations to finish before closing ADB Commander.")
            event.ignore()
            return
        self.refresh_timer.stop()
        event.accept()
