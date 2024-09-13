from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, 
    QLineEdit, QLabel, QDialogButtonBox, QMessageBox, QApplication  # Added QApplication here
)
from PyQt5.QtCore import Qt
import os
import sys
import sqlite3  # Assuming you're using SQLite for the database connection

def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class ContactSelectionWindow(QWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Select Contacts')
        self.layout = QVBoxLayout()

        # List of contacts
        self.contact_list = QListWidget()
        self.populate_contacts()
        self.layout.addWidget(self.contact_list)

        # Button to create new group
        self.create_group_button = QPushButton('Create New Group')
        self.create_group_button.clicked.connect(self.open_create_group_dialog)
        self.layout.addWidget(self.create_group_button)

        self.setLayout(self.layout)
        self.setGeometry(300, 300, 400, 300)

    def populate_contacts(self):
        """ Populate contact list from the database """
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, name, phone FROM contacts")
        contacts = cursor.fetchall()
        for contact in contacts:
            item = QListWidgetItem(f"{contact[1]} ({contact[2]})")
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, contact[0])  # Store contact ID in item
            self.contact_list.addItem(item)

    def open_create_group_dialog(self):
        """ Open the dialog for creating a new group with selected contacts """
        selected_contacts = self.get_selected_contacts()
        if not selected_contacts:
            self.show_error_message("Please select at least one contact to create a group.")
            return
        dialog = CreateGroupDialog(self.db_connection, selected_contacts)
        dialog.exec_()

    def get_selected_contacts(self):
        """ Get the list of selected contacts' IDs """
        selected_contacts = []
        for index in range(self.contact_list.count()):
            item = self.contact_list.item(index)
            if item.checkState() == Qt.Checked:
                contact_id = item.data(Qt.UserRole)
                selected_contacts.append(contact_id)
        return selected_contacts

    def show_error_message(self, message):
        """ Show an error message dialog """
        QMessageBox.critical(self, 'Error', message)

class CreateGroupDialog(QDialog):
    def __init__(self, db_connection, selected_contacts):
        super().__init__()
        self.db_connection = db_connection
        self.selected_contacts = selected_contacts
        self.initUI()

    def initUI(self):
        """ Initialize the group creation dialog UI """
        self.setWindowTitle('Create Group')
        self.layout = QVBoxLayout()

        # Input for group name
        self.group_name_edit = QLineEdit()
        self.group_name_edit.setPlaceholderText('Group Name')
        self.layout.addWidget(self.group_name_edit)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.create_group)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def create_group(self):
        """ Create a group with the selected contacts """
        group_name = self.group_name_edit.text().strip()
        if not group_name:
            self.show_error_message("Group name cannot be empty.")
            return

        # Insert group into the database
        cursor = self.db_connection.cursor()
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        group_id = cursor.lastrowid

        # Add selected contacts to the group
        for contact_id in self.selected_contacts:
            cursor.execute(
                "INSERT INTO group_contacts (group_id, contact_id) VALUES (?, ?)",
                (group_id, contact_id)
            )
        self.db_connection.commit()

        self.show_info_message("Group created successfully!")
        self.accept()

    def show_error_message(self, message):
        """ Show an error message dialog """
        QMessageBox.critical(self, 'Error', message)

    def show_info_message(self, message):
        """ Show an informational message dialog """
        QMessageBox.information(self, 'Success', message)

if __name__ == '__main__':
    # Establishing database connection (modify the path accordingly)
    db_connection = sqlite3.connect(resource_path('contacts.db'))

    app = QApplication(sys.argv)  # Make sure QApplication is defined
    window = ContactSelectionWindow(db_connection)
    window.show()
    sys.exit(app.exec_())
