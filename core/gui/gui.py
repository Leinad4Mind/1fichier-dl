import sys
import queue
import logging
import pickle
import os
import time
import qdarktheme
import webbrowser
import PyQt5.sip
from ..download.workers import FilterWorker, DownloadWorker
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QIcon, QStandardItemModel, QPixmap, QFontDatabase, QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGridLayout,
                             QPushButton, QSpinBox, QWidget, QMessageBox,
                             QTableView, QHBoxLayout, QDesktopWidget,
                             QPlainTextEdit, QVBoxLayout, QAbstractItemView,
                             QAbstractScrollArea, QLabel, QLineEdit,
                             QFileDialog, QProgressBar, QStackedWidget,
                             QFormLayout, QListWidget, QComboBox, QSizePolicy)
import tkinter as tk
proxy_queue = queue.Queue()


def absp(path):
    '''
    Get absolute path.
    '''
    if getattr(sys, "frozen", False):
        # Pyinstaller Path after compilation
        resolved_path = resource_path(path)
    else:
        # Python Path when executing file
        relative_path = os.path.join(os.path.dirname(__file__), '.')
        resolved_path = os.path.join(os.path.abspath(relative_path), path)

    return resolved_path


def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(
        os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def abs_config(path):
    # Fixed to program execution path
    resolved_path = os.path.abspath(path)
    return resolved_path


def alert(text):
    '''
    Create and show QMessageBox Alert.
    '''
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle('Guide')
    msg.setText(text)
    msg.exec_()


def check_selection(table):
    '''
    Get selected rows from table.
    Returns list: [Rows]
    '''
    selection = []
    for index in table.selectionModel().selectedRows():
        selection.append(index.row())
    if not selection:
        alert('Please select a file from the download list first.')
    else:
        return selection


def create_file(f):
    '''
    Create empty file.
    [note] Used to create app/settings and app/cache.
    '''
    f = abs_config(f)
    logging.debug(f'Attempting to create file: {f}...')
    os.makedirs(os.path.dirname(f), exist_ok=True)
    f = open(f, 'x')
    f.close()


def getClipboardText():
    root = tk.Tk()
    # keep the window from showing
    root.withdraw()
    return root.clipboard_get()


class GuiBehavior:
    def __init__(self, gui):
        self.filter_thread = QThreadPool()
        self.download_thread = QThreadPool()
        # Limits concurrent downloads to 1.
        self.download_thread.setMaxThreadCount(1)
        self.download_workers = []
        self.gui = gui
        self.handle_init()

    def handle_init(self):
        '''
        Load cached downloads.
        Create file in case it does not exist.
        '''
        try:
            with open(abs_config('app/cache'), 'rb') as f:
                self.cached_downloads = pickle.load(f)
                for download in self.cached_downloads:
                    self.gui.links = download[0]
                    self.add_links(True, download)
        except EOFError:
            self.cached_downloads = []
            logging.debug('No cached downloads.')
        except FileNotFoundError:
            logging.debug('create New cache File.')
            self.cached_downloads = []
            create_file('app/cache')

        '''
        Load settings.
        Create file in case it doesn't exist.
        '''
        try:
            with open(abs_config('app/settings'), 'rb') as f:
                self.settings = pickle.load(f)
                thread_count = self.settings[4]
                self.download_thread.setMaxThreadCount(int(thread_count))
                logging.debug('Now Settings Thread Count:'+str(thread_count))
        except EOFError:
            self.settings = None
            logging.debug('No settings found.')
        except FileNotFoundError:
            self.settings = None
            logging.debug('Create New settings File.')
            create_file('app/settings')
        except IndexError:
            # settings Use default value of 3 when there is no fourth element in the list
            self.settings = None
            thread_count = 3
            self.download_thread.setMaxThreadCount(int(thread_count))

    def show_loading_overlay(self):
        '''
        Show the loading overlay.
        '''
        if self.gui:
            self.gui.show_loading_overlay()

    def hide_loading_overlay(self):
        '''
        Show the loading overlay.
        '''
        if self.gui:
            self.gui.hide_loading_overlay()

    def resume_download(self):
        '''
        Resume selected downloads.
        '''
        selected_rows = check_selection(self.gui.table)

        if selected_rows:
            for i in selected_rows:
                if i < len(self.download_workers):
                    self.download_workers[i].resume()

    def stop_download(self):
        '''
        Stop selected downloads.
        '''
        selected_rows = check_selection(self.gui.table)

        if selected_rows:
            for i in reversed(selected_rows):
                if i < len(self.download_workers):
                    self.download_workers[i].stop(i)
                    # Remove the download worker from the list
                    del self.download_workers[i]

    def pause_download(self):
        '''
        Pause selected downloads.
        '''
        selected_rows = check_selection(self.gui.table)
        if selected_rows:
            for i in selected_rows:
                if i < len(self.download_workers):
                    update_data = [None, None, 'Pause', None, '0 B/s']
                    # update_signal only if it is a list type
                    if isinstance(self.download_workers[i].data, list):
                        self.download_workers[i].signals.update_signal.emit(
                            self.download_workers[i].data, update_data)
                        self.download_workers[i].pause()

    def add_links(self, state, cached_download=''):
        '''
        Calls FilterWorker()
        '''
        logging.debug('Call add_links')
        # Show loading overlay
        self.show_loading_overlay()
        worker = FilterWorker(
            self, cached_download, (self.gui.password.text() if not cached_download else ''))

        worker.signals.download_signal.connect(self.download_receive_signal)
        worker.signals.alert_signal.connect(alert)

        self.filter_thread.start(worker)

    def download_receive_signal(self, row, link, append_row=True, dl_name='', progress=0):
        '''
        Append download to row and start download.
        '''
        if append_row:
            self.gui.table_model.appendRow(row)
            index = self.gui.table_model.index(
                self.gui.table_model.rowCount()-1, 5)
            progress_bar = QProgressBar()
            progress_bar.setValue(int(progress))
            progress_bar.setGeometry(200, 150, 200, 30)
            # setting value of n for 2 decimal values
            n = 100
            # setting maximum value for 2 decimal points
            progress_bar.setMaximum(100 * n)
            self.gui.table.setIndexWidget(index, progress_bar)
            row[5] = progress_bar

        worker = DownloadWorker(
            link, self.gui.table_model, row, self.settings, dl_name)

        worker.signals.update_signal.connect(self.update_receive_signal)
        worker.signals.unpause_signal.connect(self.download_receive_signal)

        self.download_thread.start(worker)
        self.download_workers.append(worker)
        self.hide_loading_overlay()
        # Re-enable button after adding link
        self.gui.add_links_complete()

    def update_receive_signal(self, data, items):
        '''
        Update download data.
        items = [File Name, Size, Down Speed, Progress, Pass]
        '''
        if data and isinstance(data, list) and isinstance(items, list):
            if not PyQt5.sip.isdeleted(data[2]):
                for i in range(len(items)):
                    if items[i] and isinstance(items[i], str):
                        data[i].setText(str(items[i]))
                    if items[i] and not isinstance(items[i], str):
                        # setting the value by multiplying it to 100
                        n = 100
                        # progress_bar float issue casting fix
                        data[i].setValue(int(items[i]) * n)
                        data[i].setFormat("%.02f %%" % items[i])

    def set_dl_directory(self):
        file_dialog = QFileDialog(self.gui.settings)
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.exec_()
        self.gui.dl_directory_input.setText(file_dialog.selectedFiles()[0])

    def change_theme(self, theme=None):
        '''
        Change app palette (theme).
        0 = Light
        1 = Dark
        '''
        if theme:
            self.gui.theme_select.setCurrentIndex(theme)

        if self.gui.theme_select.currentIndex() == 0:
            setup_theme = getattr(qdarktheme, "setup_theme", None)
            if callable(setup_theme):
                qdarktheme.setup_theme("light")
            # self.gui.app.setPalette(self.gui.main.style().standardPalette())
        elif self.gui.theme_select.currentIndex() == 1:
            setup_theme = getattr(qdarktheme, "setup_theme", None)
            if callable(setup_theme):
                qdarktheme.setup_theme("dark")
            # self.gui.app.setPalette(dark_theme)

    def get_language(self):
        language = os.getenv('LANGUAGE') or 'en' # Get language from environment variable
        return language

    def set_language(self, language=None):
        if language:
            self.gui.theme_select.setCurrentIndex(language)

        if(self.gui.theme_select.currentIndex()) :
            return 'kr'
        else :
            return 'en'

    def load_messages(self, language):
        messages = {}
        messages_file = f'messages_{language}.txt'

        with open(messages_file, 'r', encoding='utf-8') as f:
            for line in f:
                key, value = line.strip().split(',')
                messages[key] = value

        return messages

    def save_settings(self):
        with open(abs_config('app/settings'), 'wb') as f:
            settings = []
            # Download Directory - 0
            settings.append(self.gui.dl_directory_input.text())
            # Theme              - 1
            settings.append(self.gui.theme_select.currentIndex())
            # Timeout            - 2
            settings.append(self.gui.timeout_input.value())
            # Proxy Settings     - 3
            settings.append(self.gui.proxy_settings_input.text())
			# Number of multi-downloads
            # Thread Settings     - 4
            settings.append(1)
            # settings.append(self.gui.thread_input.value())
            # Select language
            # Lang Settings     - 5
            # settings.append(self.gui.lang_select.currentIndex())
            pickle.dump(settings, f)
            self.settings = settings
        self.gui.settings.hide()

    def select_settings(self):
        '''
        Select settings page.
        '''
        selection = self.gui.settings_list.selectedIndexes()[0].row()
        self.gui.stacked_settings.setCurrentIndex(selection)

    def handle_exit(self):
        '''
        Save cached downloads data.
        '''
        active_downloads = []
        for w in self.download_workers:
            download = w.return_data()
            if download:
                active_downloads.append(download)
        active_downloads.extend(self.cached_downloads)

        with open(abs_config('app/cache'), 'wb') as f:
            if active_downloads:
                pickle.dump(active_downloads, f)

        os._exit(1)


class Gui:
    def __init__(self):
        # Init GuiBehavior()
        self.app_name = '1Fichier Downloader v1.2.1'
        self.font = None

        # Create App
        enable_hi_dpi = getattr(qdarktheme, "enable_hi_dpi", None)
        if callable(enable_hi_dpi):
            qdarktheme.enable_hi_dpi()
        app = QApplication(sys.argv)
        setup_theme = getattr(qdarktheme, "setup_theme", None)
        if callable(setup_theme):
            qdarktheme.setup_theme("light")

        font_database = QFontDatabase()
        font_id = font_database.addApplicationFont(
            absp("res/NanumGothic.ttf"))
        if font_id == -1:
            logging.debug("Font load failed!")
        else:
            font_families = font_database.applicationFontFamilies(font_id)
            self.font = QFont(font_families[0], 10)

        app.setWindowIcon(QIcon(absp('res/ico.ico')))
        app.setStyle('Fusion')
        self.app = app

        # Initialize self.main
        self.main_init()
        self.actions = GuiBehavior(self)
        app.aboutToQuit.connect(self.actions.handle_exit)

        # Create Windows
        self.main_win()
        self.add_links_win()
        # self.add_links_clipboard()
        self.settings_win()

        # Change App Theme to saved one (Palette)
        if self.actions.settings:
            self.actions.change_theme(self.actions.settings[1])

        sys.exit(app.exec_())

    def main_init(self):
        # Define Main Window
        self.main = QMainWindow()
        self.main.setWindowTitle(self.app_name)
        widget = QWidget(self.main)
        self.main.setCentralWidget(widget)

        # Create Grid
        grid = QGridLayout()

        # download_clipboard_btn Create and set up
        download_clipboard_btn = QPushButton(
            QIcon(absp('res/clipboard.svg')), ' Add from clipboard')
        download_clipboard_btn.clicked.connect(self.add_links_clipboard)
        download_clipboard_btn.setFont(self.font)

        # Top Buttons
        download_btn = QPushButton(
            QIcon(absp('res/download.svg')), ' Add Link(s)')
        download_btn.clicked.connect(lambda: self.add_links.show(
        ) if not self.add_links.isVisible() else self.add_links.raise_())
        download_btn.setFont(self.font)

        settings_btn = QPushButton(
            QIcon(absp('res/settings.svg')), ' Settings')
        settings_btn.clicked.connect(lambda: self.settings.show(
        ) if not self.settings.isVisible() else self.settings.raise_())
        settings_btn.setFont(self.font)

        # Table
        self.table = QTableView()
        headers = ['Name', 'Size', 'Status', 'Proxy server',
                    'Down Speed', 'Progress', 'Password']
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().hide()
        if self.font:
            self.table.setFont(self.font)

        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(headers)
        self.table.setModel(self.table_model)

        # Append widgets to grid
        grid.addWidget(download_clipboard_btn, 0, 0)
        grid.addWidget(download_btn, 0, 1)
        # grid.addWidget(download_clipboard_btn, 0, 1)
        grid.addWidget(settings_btn, 0, 2)
        grid.addWidget(self.table, 1, 0, 1, 3)

        # Add buttons to Horizontal Layout
        hbox = QHBoxLayout()
        # Bottom Buttons
        self.main.resume_btn = QPushButton(
            QIcon(absp('res/resume.svg')), ' Resume')
        self.main.resume_btn.setFont(self.font)
        self.main.pause_btn = QPushButton(
            QIcon(absp('res/pause.svg')), ' Pause')
        self.main.pause_btn.setFont(self.font)
        self.main.stop_btn = QPushButton(
            QIcon(absp('res/stop.svg')), ' Remove')
        self.main.stop_btn.setFont(self.font)

        hbox.addWidget(self.main.resume_btn)
        hbox.addWidget(self.main.pause_btn)
        hbox.addWidget(self.main.stop_btn)

        self.main.setWindowFlags(self.main.windowFlags()
                                 & Qt.CustomizeWindowHint)

        grid.addLayout(hbox, 2, 0, 1, 3)
        widget.setLayout(grid)
        self.main.resize(1280, 415)
        # Set size policies for the table
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.horizontalHeader().resizeSection(0,self.table.horizontalHeader().sectionSize(0)+400)
        self.table.horizontalHeader().resizeSection(3,self.table.horizontalHeader().sectionSize(3)+120)
        self.table.horizontalHeader().resizeSection(2,self.table.horizontalHeader().sectionSize(2)+30)

        # Create a loading overlay widget
        self.main.loading_overlay = QWidget(self.main)
        self.main.loading_overlay.setGeometry(
            0, 0, self.main.width(), self.main.height())
        self.main.loading_overlay.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0);")
        self.main.loading_overlay.setVisible(False)

        # SVG Add image to loading overlay widget
        svg_widget = QSvgWidget(absp('res/loading_image.svg'))
        svg_widget.setGeometry(0, 0, 100, 100)  # It needs positioning and scaling to be centered.
        svg_layout = QVBoxLayout(self.main.loading_overlay)
        svg_layout.addWidget(svg_widget)
        svg_layout.setAlignment(Qt.AlignCenter)

        sg = QDesktopWidget().screenGeometry()
        x = sg.width() - 1280 - 20              # 1280 from self.main.resize()
        y = sg.height() - 415 - 415 + 20        #  415 from self.main.resize()
        self.main.move( x, y)

        self.main.show()

    def main_win(self):
        self.main.resume_btn.clicked.connect(self.actions.resume_download)
        self.main.pause_btn.clicked.connect(self.actions.pause_download)
        self.main.stop_btn.clicked.connect(self.actions.stop_download)

    # Method to get the address of the clipboard and pass it to add_links
    def add_links_clipboard(self):
        clipboard_text = getClipboardText()
        if clipboard_text:
            lines = clipboard_text.split('\n')
            if lines:
                self.links.setPlainText(lines[0])
            else:
                self.links.setPlainText(clipboard_text)
            self.add_to_download_list()

    # Method to enable loading overlay
    def show_loading_overlay(self):
        if self.main:
            self.main.loading_overlay.setVisible(True)

    # Method to disable loading overlay
    def hide_loading_overlay(self):
        if self.main:
            self.main.loading_overlay.setVisible(False)

    def add_links_win(self):
        # Define Add Links Win
        self.add_links = QMainWindow(self.main)
        self.add_links.setWindowTitle('Add Link(s)')
        widget = QWidget(self.add_links)
        self.add_links.setCentralWidget(widget)

        # Create Vertical Layout
        layout = QVBoxLayout()

        # Links input
        layout.addWidget(QLabel('Link list (enter single or multiple items by pressing enter)'))
        self.links = QPlainTextEdit()
        layout.addWidget(self.links)

        # Password input
        layout.addWidget(QLabel('Password (enter only if set separately)'))
        self.password = QLineEdit()
        layout.addWidget(self.password)

        # Add links
        self.add_btn = QPushButton('Add to download list')
        self.add_btn.clicked.connect(self.add_to_download_list)
        layout.addWidget(self.add_btn)

        self.add_links.setMinimumSize(300, 200)
        widget.setLayout(layout)

    def settings_win(self):
        # Define Settings Win
        self.settings = QMainWindow(self.main)
        self.settings.setWindowTitle('Settings')

        # Create StackedWidget and Selection List
        self.stacked_settings = QStackedWidget()
        self.settings_list = QListWidget()
        self.settings_list.setFixedWidth(110)
        self.settings_list.addItems(['Behavior', 'Connection', 'About'])
        self.settings_list.clicked.connect(self.actions.select_settings)

        # Central Widget
        central_widget = QWidget()
        hbox = QHBoxLayout()
        hbox.addWidget(self.settings_list)
        hbox.addWidget(self.stacked_settings)
        central_widget.setLayout(hbox)
        self.settings.setCentralWidget(central_widget)

        '''
        Child widget
        Behavior Settings
        '''

        behavior_settings = QWidget()
        self.stacked_settings.addWidget(behavior_settings)

        # Main Layouts
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignTop)
        form_layout = QFormLayout()

        # Change Lang
        # form_layout.addRow(QLabel('Language:'))

        # self.lang_select = QComboBox()
        # self.lang_select.addItems(['Korean', 'English'])
        # self.lang_select.currentIndexChanged.connect(
        #     self.actions.set_language)
        # form_layout.addRow(self.lang_select)

        # Change Directory
        form_layout.addRow(QLabel('Download directory:'))

        dl_directory_btn = QPushButton('Select...')
        dl_directory_btn.clicked.connect(self.actions.set_dl_directory)

        self.dl_directory_input = QLineEdit()
        if self.actions.settings is not None:
            self.dl_directory_input.setText(self.actions.settings[0])
        self.dl_directory_input.setDisabled(True)

        form_layout.addRow(dl_directory_btn, self.dl_directory_input)

        # Bottom Buttons
        save_settings = QPushButton('Save')
        save_settings.clicked.connect(self.actions.save_settings)

        # Change theme
        form_layout.addRow(QLabel('Theme:'))

        self.theme_select = QComboBox()
        self.theme_select.addItems(['Light', 'Dark'])
        self.theme_select.currentIndexChanged.connect(
            self.actions.change_theme)
        form_layout.addRow(self.theme_select)

        vbox.addLayout(form_layout)
        vbox.addStretch()
        vbox.addWidget(save_settings)
        behavior_settings.setLayout(vbox)

        '''
        Child widget
        Connection Settings
        '''

        connection_settings = QWidget()
        self.stacked_settings.addWidget(connection_settings)

        # Main Layouts
        vbox_c = QVBoxLayout()
        vbox_c.setAlignment(Qt.AlignTop)
        form_layout_c = QFormLayout()

        # Timeout
        form_layout_c.addRow(QLabel('Timeout (default 30s):'))
        self.timeout_input = QSpinBox()
        if self.actions.settings is not None:
            self.timeout_input.setValue(self.actions.settings[2])
        else:
            self.timeout_input.setValue(30)

        form_layout_c.addRow(self.timeout_input)

        # Proxy settings
        form_layout_c.addRow(QLabel('Enter proxy list directly:'))
        self.proxy_settings_input = QLineEdit()
        if self.actions.settings is not None:
            self.proxy_settings_input.setText(self.actions.settings[3])

        form_layout_c.addRow(self.proxy_settings_input)

        # form_layout_c.addRow(QLabel('Number of simultaneous proxy downloads (requires restart):'))
        # self.thread_input = QSpinBox()
        # if self.actions.settings is not None:
        #     self.thread_input.setValue(self.actions.settings[4])
        # else:
        #     self.thread_input.setValue(3)

        # form_layout_c.addRow(self.thread_input)

        # Bottom buttons
        save_settings_c = QPushButton('Save')
        save_settings_c.clicked.connect(self.actions.save_settings)

        vbox_c.addLayout(form_layout_c)
        vbox_c.addStretch()
        vbox_c.addWidget(save_settings_c)
        connection_settings.setLayout(vbox_c)

        '''
        Child widget
        About
        '''

        about_settings = QWidget()
        self.stacked_settings.addWidget(about_settings)

        about_layout = QGridLayout()
        about_layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        logo.setPixmap(QPixmap(absp('res/ico.svg')))
        logo.setAlignment(Qt.AlignCenter)

        text = QLabel(self.app_name)
        text.setStyleSheet('font-weight: bold; color: #4256AD')

        github_btn = QPushButton(QIcon(absp('res/github.svg')), '')
        github_btn.setFixedWidth(32)
        github_btn.clicked.connect(lambda: webbrowser.open(
            'https://github.com/leinad4mind/1fichier-dl'))

        about_layout.addWidget(logo, 0, 0, 1, 0)
        about_layout.addWidget(github_btn, 1, 0)
        about_layout.addWidget(text, 1, 1)
        about_settings.setLayout(about_layout)

    def add_links_complete(self):
        # Change the state of the button when the task is complete.
        self.add_btn.setText("Add to download list")
        self.add_btn.setEnabled(True)
        # Reset link input window
        self.links.setEnabled(True)
        self.password.setEnabled(True)
        self.links.clear()

    def add_to_download_list(self):
        # It takes the entered link and converts it into a list.
        links_text = self.links.toPlainText()

        if(links_text) :
            add_links_texts = []
            # Disable the 'Add to download list' button.
            self.add_btn.setText("Adding to download list...")
            self.add_btn.setEnabled(False)

            download_links = links_text.split('\n')
            self.links.setDisabled(True)
            self.password.setDisabled(True)

            for link in download_links:
                if link.strip():  # Append only if the line is not blank.
                    add_links_texts.append(link)

             # Use 'add_links' to add download links.
            self.actions.add_links('\n'.join(add_links_texts))
        else:
            alert('Please enter a list of download links.')
