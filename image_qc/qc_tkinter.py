import tkinter as tk
try:
    from .file_dialogs_tk import select_files
    from .data_editor_tk import DataEditorGUI
except ImportError:
    import os, sys
    sys.path.append(os.path.dirname(__file__))
    from file_dialogs_tk import select_files
    from data_editor_tk import DataEditorGUI


if __name__ == '__main__':
    test_fpath, image_dirs = select_files()
    root = tk.Tk()
    editor = DataEditorGUI(root, test_fpath, image_dirs)
    root.mainloop()