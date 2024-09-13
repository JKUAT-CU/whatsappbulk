from asyncqt import QEventLoop
from PyQt5.QtCore import Qt, QCoreApplication, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import os
import sys
import asyncio
import logging
import platform
from asyncio.subprocess import PIPE

# Import the MainApp class from mainwindow.py
from mainwindow import MainApp

# Path to the QR code image file and log file
qr_code_path = 'qrcode.png'
log_file_path = 'logs/qr_log.log'

def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_executable_name():
    """ Return the name of the executable based on the operating system """
    os_name = platform.system().lower()
    if os_name == 'linux':
        return 'qrcode-linux'
    elif os_name == 'windows':
        return 'qrcode-win.exe'
    elif os_name == 'darwin':
        return 'qrcode-macos'
    else:
        raise RuntimeError(f"Unsupported OS: {os_name}")

class QRCodeScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        # Set up logging
        self.log_file_path = 'qrapp.log'
        logging.basicConfig(
            filename=self.log_file_path,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.debug('Logging setup complete.')
        
        # Initialize the UI and start the processes
        self.initUI()
        asyncio.create_task(self.run_qrcode_executable())
        
        # Set up a timer to periodically check for the QR code image and log file
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_updates_periodically)
        self.timer.start(1000)  # Check every 1000 ms (1 second)

    def initUI(self):
        """ Initialize the UI elements """
        self.setWindowTitle('QR Code Scanner')
        self.layout = QVBoxLayout()
        self.qr_label = QLabel('Waiting for QR Code...', self)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.qr_label)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 300, 300)

    async def run_qrcode_executable(self):
        """ Run the QR code executable based on the operating system """
        executable_name = get_executable_name()
        executable_path = resource_path(executable_name)
        
        logging.debug(f"Executable path: {executable_path}")

        try:
            # Run the executable as a subprocess
            process = await asyncio.create_subprocess_exec(
                executable_path,
                stdout=PIPE,
                stderr=PIPE
            )
            await self.handle_executable_output(process)
        except FileNotFoundError as e:
            logging.error(f"Executable not found: {e}")

    async def handle_executable_output(self, process):
        """ Handle the output from the executable process """
        while True:
            output = await process.stdout.readline()
            if output == b'':  # End of process
                break

            output_decoded = output.decode().strip()
            logging.debug(f"Executable Output: {output_decoded}")

            if output_decoded == 'Client is ready!':
                await self.on_success()

    async def check_for_qr_code(self):
        """ Check if the QR code image exists and update the label """
        if os.path.exists(qr_code_path):
            pixmap = QPixmap(qr_code_path)
            self.qr_label.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio))
            self.qr_label.setText('')  # Clear the text
        else:
            self.qr_label.setText('Waiting for QR Code...')

    def check_for_updates_periodically(self):
        """ Periodically check for QR code image and log file updates """
        asyncio.create_task(self.check_for_qr_code())
        asyncio.create_task(self.check_log_file())

    async def check_log_file(self):
        """ Check the log file for updates and handle accordingly """
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as log_file:
                lines = log_file.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    logging.debug(f"Log File Last Line: {last_line}")

                    if 'Client is ready!' in last_line:
                        await self.on_success()

    async def on_success(self):
        """ Handle successful QR code scanning """
        logging.info("QR code scanned successfully!")

        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)
            logging.info(f"Deleted {qr_code_path}")

        # Quit the current application
        QCoreApplication.instance().quit()

        # Start the MainApp from mainwindow.py
        self.start_main_app()

    def start_main_app(self):
        """ Start the main application """
        app = QApplication(sys.argv)
        main_window = MainApp()  # Assuming MainApp is the main window class
        main_window.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    scanner = QRCodeScannerApp()
    scanner.show()
    with loop:
        loop.run_forever()
