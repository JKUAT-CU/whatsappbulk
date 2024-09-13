import os
import sys
import subprocess

# Import Python files
import qr
import mainwindow
import creategroups
import groupsview
# Function to find the correct path for bundled resources
def resource_path(relative_path):
    """ Get the absolute path to bundled files. Handles both development and PyInstaller modes. """
    if getattr(sys, 'frozen', False):  # If the program is frozen (bundled)
        base_path = sys._MEIPASS        # Extracted temporary folder path in bundled mode
    else:
        base_path = os.path.abspath(".")  # Regular path when running from source
    return os.path.join(base_path, relative_path)

# Function to run JavaScript files using Node.js
def run_js(file_name):
    js_path = resource_path(file_name)   # Locate JS file in the bundle
    try:
        subprocess.run(["node", js_path], check=True)  # Execute JS file via Node.js
    except Exception as e:
        print(f"Error executing {file_name}: {e}")

if __name__ == "__main__":
    # Start the QR module (qr.py)
    print("Starting QR module...")
    qr.main()  # Assuming qr.py has a main() function  
    print("Application finished.")
