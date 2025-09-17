import sys
import tkinter as tk
from tkinter import filedialog


def select_files():
    root = tk.Tk()
    root.withdraw()

    csv_path = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

    if not csv_path:
        sys.exit("No CSV file selected")

    image_dir = filedialog.askdirectory(title="Select image directory")

    if not image_dir:
        sys.exit("No image directory selected")

    return csv_path, image_dir


