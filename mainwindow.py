import sys
import os
import json
import subprocess
import logging
import asyncio
from asyncqt import QEventLoop
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget, QStackedWidget, QHBoxLayout, QFrame, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Function to run JavaScript files using Node.js asynchronously
def run_js_async(file_name):
    js_path = resource_path(file_name)   # Locate JS file in the bundle
    try:
        # Run the JS file in a separate subprocess asynchronously
        subprocess.Popen(["node", js_path])
    except Exception as e:
        print(f"Error executing {file_name}: {e}")

# Function to run qr.py when client is not logged in
def run_qr_py():
    try:
        subprocess.run([sys.executable, resource_path("qr.py")])
    except Exception as e:
        logging.error(f"Failed to run qr.py: {e}")

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MyApp')
        self.setGeometry(100, 100, 800, 600)

        # Check if the client is logged in
        if not self.check_client_status():
            self.show_qr_code_scanner()  # Show QR code scanner if not logged in
        else:
            self.show_main_content()  # Show main content if already logged in

    def check_client_status(self):
        status_file = 'client_status.json'
        if not os.path.exists(status_file):
            logging.info('Status file does not exist. Client not logged in.')
            return False

        try:
            with open(status_file, 'r') as file:
                status = json.load(file)
                logged_in = status.get('loggedIn', False)
                logging.info(f'Client status checked: loggedIn={logged_in}')
                return logged_in
        except Exception as e:
            logging.error(f'Error reading status file: {e}')
            return False

    def show_qr_code_scanner(self):
        logging.info('Client not logged in. Launching QR code scanner...')
        run_qr_py()  # Call the external qr.py script

    def show_main_content(self):
        logging.info('Displaying main content.')
        self.init_main_layout()

    def init_main_layout(self):
        logging.info('Initializing main layout...')
        self.main_layout = QHBoxLayout()
        self.sidebar = QVBoxLayout()
        self.sidebar.setAlignment(Qt.AlignTop)
        self.sidebar.setContentsMargins(0, 0, 0, 0)
        self.sidebar.setSpacing(10)

        self.content = QStackedWidget()
        self.create_sidebar_button("Create Group", self.show_create_group)
        self.create_sidebar_button("Send Message", self.show_send_message)
        self.create_sidebar_button("View Groups", self.show_view_groups)

        sidebar_widget = QFrame()
        sidebar_widget.setLayout(self.sidebar)
        sidebar_widget.setStyleSheet("background-color: #2e3b4e; color: white; border-right: 2px solid #1a1f30;")

        self.main_layout.addWidget(sidebar_widget, 1)
        self.main_layout.addWidget(self.content, 4)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def create_sidebar_button(self, label, function):
        logging.debug(f'Creating sidebar button: {label}')
        button = QPushButton(label)
        button.setFont(QFont('Arial', 12))
        button.setStyleSheet("""
            QPushButton {
                background-color: #3c4f65;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #557798;
            }
        """)
        button.clicked.connect(function)
        self.sidebar.addWidget(button)

    def show_create_group(self):
        logging.info('Displaying Create Group page.')
        # Example: run the associated JavaScript file when needed
        run_js_async('create_group.js')

    def show_send_message(self):
        logging.info('Displaying Send Message page.')
        # Example: run the associated JavaScript file when needed
        run_js_async('sendmessage.js')

    def show_view_groups(self):
        logging.info('Displaying View Groups page.')
        # Example: run the associated JavaScript file when needed
        run_js_async('view_groups.js')


if __name__ == '__main__':
    # Create the PyQt5 application
    app = QApplication(sys.argv)

    # Create an asyncio event loop for the PyQt app
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and show the main window
    main_app = MainApp()
    main_app.show()

    # Start the asyncio event loop and run the PyQt app
    with loop:
        loop.run_forever()
