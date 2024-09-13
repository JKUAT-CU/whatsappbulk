import os
import sys
import sqlite3
import json
import traceback
import bs4
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, QComboBox, QLabel, QProgressBar, QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, QTimer
import subprocess
import platform

def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_executable_name():
    """ Return the name of the executable based on the operating system """
    os_name = platform.system().lower()
    if os_name == 'linux':
        return 'sendmessage-linux'
    elif os_name == 'windows':
        return 'sendmessage-win.exe'
    elif os_name == 'darwin':
        return 'sendmessage-macos'
    else:
        raise RuntimeError(f"Unsupported OS: {os_name}")

class SendMessageWindow(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.initUI()
        
        # Set up a timer to periodically check for new log messages
        self.log_file_path = 'messages.log'
        self.log_check_timer = QTimer()
        self.log_check_timer.timeout.connect(self.read_log_file)
        self.log_check_timer.start(1000)  # Check every 1000 ms (1 second)
        self.last_log_position = 0  # To keep track of where we are in the log file

    def initUI(self):
        self.setWindowTitle('Send Message')
        self.setGeometry(400, 200, 600, 400)

        layout = QVBoxLayout()

        # Group selection dropdown
        self.group_dropdown = QComboBox()
        self.populate_groups()
        layout.addWidget(QLabel("Select Group:"))
        layout.addWidget(self.group_dropdown)

        # CKEditor text editor
        self.web_view = QWebEngineView()
        self.load_ckeditor_editor()
        layout.addWidget(self.web_view)

        # Send button
        send_button = QPushButton('Send Message')
        send_button.clicked.connect(self.send_message)
        layout.addWidget(send_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def load_ckeditor_editor(self):
        # Ensure CKEditor is loaded correctly from the HTML file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_file_path = os.path.join(base_dir, 'static/ckeditor/index.html')
        self.web_view.setUrl(QUrl.fromLocalFile(html_file_path))

    def populate_groups(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT id, name FROM groups")
            groups = cursor.fetchall()
            for group in groups:
                self.group_dropdown.addItem(group[1], group[0])
        except sqlite3.Error as e:
            self.show_error_message(f"Database error: {e}")

    def get_contacts_for_group(self, group_id):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT contacts.phone FROM contacts
                INNER JOIN group_contacts ON contacts.id = group_contacts.contact_id
                WHERE group_contacts.group_id = ?
            """, (group_id,))
            contacts = [row[0] for row in cursor.fetchall()]
            return contacts
        except sqlite3.Error as e:
            self.show_error_message(f"Database error: {e}")
            return []

    def send_message(self):
        group_id = self.group_dropdown.currentData()
        contacts = self.get_contacts_for_group(group_id)

        if not contacts:
            self.show_error_message("No contacts found for the selected group.")
            return

        # Get CKEditor content through JavaScript call
        self.web_view.page().runJavaScript("getCKEditorContent();", self.process_message)

    def process_message(self, content):
        message = bs4.BeautifulSoup(content, 'html.parser').get_text().strip()

        if not message:
            self.show_error_message("Message content is empty.")
            return

        contacts = self.get_contacts_for_group(self.group_dropdown.currentData())
        contacts = [f"{contact}@c.us" if not contact.endswith('@c.us') else contact for contact in contacts]

        data = {'contacts': contacts, 'message': message}

        # Write data to JSON file
        json_file_path = 'message_data.json'
        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(data, json_file)
        except IOError as e:
            self.show_error_message(f"Error writing to JSON file: {e}")
            return

        # Start the executable script
        self.message_sender_thread = MessageSenderThread(json_file_path)
        self.message_sender_thread.progress.connect(self.progress_bar.setValue)
        self.message_sender_thread.completed.connect(self.on_send_complete)
        self.message_sender_thread.error.connect(self.show_error_message)  # Connect the error signal
        self.message_sender_thread.start()

    def on_send_complete(self):
        self.progress_bar.setValue(100)
        self.show_info_message("Messages sent successfully!")
        self.close()

    def show_error_message(self, message):
        QMessageBox.critical(self, 'Error', message)

    def show_info_message(self, message):
        QMessageBox.information(self, 'Info', message)

    def read_log_file(self):
        """ Read from the log file and handle new messages """
        if not os.path.exists(self.log_file_path):
            return

        try:
            with open(self.log_file_path, 'r') as log_file:
                log_file.seek(self.last_log_position)
                new_logs = log_file.read()
                self.last_log_position = log_file.tell()  # Update position

                if new_logs:
                    self.process_log_messages(new_logs)
        except Exception as e:
            self.show_error_message(f"Error reading log file: {e}")

    def process_log_messages(self, logs):
        """ Process the new logs from the log file """
        for line in logs.splitlines():
            if 'Error' in line:
                self.show_error_message(f"Log Error: {line}")
            elif 'Info' in line:
                self.show_info_message(f"Log Info: {line}")

class MessageSenderThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal()
    error = pyqtSignal(str)  # New signal for error reporting

    def __init__(self, json_file_path):
        super().__init__()
        self.json_file_path = json_file_path

    def run(self):
        try:
            # Determine the executable based on the OS
            executable_name = get_executable_name()
            executable_path = resource_path(executable_name)  # Adjust path to the executable
            process = subprocess.Popen(
                [executable_path, self.json_file_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output and 'Progress:' in output:
                    progress = int(output.split(':')[1].strip())
                    self.progress.emit(progress)

            return_code = process.wait()
            if return_code == 0:
                self.completed.emit()
            else:
                self.error.emit(f"Failed with return code {return_code}")

        except Exception as e:
            self.error.emit(f"Error in thread: {e}")

if __name__ == "__main__":
    # Setup DB connection
    db_connection = None
    try:
        db_path = "contacts.db"  
        db_connection = sqlite3.connect(db_path)

        app = QApplication(sys.argv)
        window = SendMessageWindow(db_connection)
        window.show()
        sys.exit(app.exec_())

    except sqlite3.Error as e:
        print(f"Failed to connect to the database: {e}")
    finally:
        if db_connection:
            db_connection.close()
