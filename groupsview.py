import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class GroupViewWindow(QWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.initUI()

    def initUI(self):
        self.setWindowTitle('View Groups')
        self.layout = QVBoxLayout()

        # Tree view for groups
        self.group_tree = QTreeWidget()
        self.group_tree.setHeaderLabels(['Group Name'])
        self.group_tree.itemClicked.connect(self.on_item_clicked)
        self.layout.addWidget(self.group_tree)

        # Load groups from the database
        self.load_groups()

        self.setLayout(self.layout)
        self.setGeometry(300, 300, 400, 300)

    def load_groups(self):
        """Load group names from the database into the tree view."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, name FROM groups")
        groups = cursor.fetchall()
        for group_id, group_name in groups:
            group_item = QTreeWidgetItem([group_name])
            group_item.setData(0, Qt.UserRole, group_id)  # Store the group ID in the item
            group_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)  # Indicate that this item has children
            self.group_tree.addTopLevelItem(group_item)

    def on_item_clicked(self, item, column):
        """Load contacts when a group item is clicked."""
        if item.childCount() == 0:  # Only load if not already loaded
            group_id = item.data(0, Qt.UserRole)
            self.load_contacts(item, group_id)

    def load_contacts(self, group_item, group_id):
        """Load contacts associated with a group and display them under the group item."""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT c.name
            FROM contacts c
            JOIN group_contacts gc ON c.id = gc.contact_id
            WHERE gc.group_id = ?
        """, (group_id,))
        contacts = cursor.fetchall()
        for contact_name, in contacts:
            contact_item = QTreeWidgetItem([contact_name])
            group_item.addChild(contact_item)
        group_item.setExpanded(True)  # Automatically expand the item to show contacts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Use resource_path to locate the SQLite database
        db_path = resource_path('contacts.db')
        self.db_connection = sqlite3.connect(db_path)  # Ensure db_path is used here

        self.initUI()

    def initUI(self):
        """Set up the main window UI."""
        self.setWindowTitle('Main Window')
        self.setGeometry(300, 300, 400, 300)
        self.central_widget = GroupViewWindow(self.db_connection)
        self.setCentralWidget(self.central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
