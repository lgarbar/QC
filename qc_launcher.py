import argparse
import os
import sys
import subprocess
from typing import Tuple, Optional
import tkinter as tk
from tkinter import filedialog


def detect_qc_mode(source_dir: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Detect QC mode from contents of source_dir.

    Returns a tuple: (mode, csv_path_or_dir, aux_path)
    - mode: 'audio', 'image', or 'unknown'
    - For audio: (csv_dir, None) — expects CSVs with transcripts and corresponding WAVs
    - For image: (csv_path, image_dir)
    """
    # Collect files
    all_files = []
    for root, _, files in os.walk(source_dir):
        for f in files:
            all_files.append(os.path.join(root, f))

    lower = [f.lower() for f in all_files]

    wavs = [f for f in all_files if f.lower().endswith('.wav')]
    csvs = [f for f in all_files if f.lower().endswith('.csv')]
    txts = [f for f in all_files if f.lower().endswith('.txt')]
    images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'))]

    # Heuristic: audio if we see wav + csvs that look like transcripts
    if wavs and csvs:
        # Prefer a directory that contains the transcript CSVs
        # The existing audio app prompts for a folder and looks for CSVs with "Recall" in name
        # so we pass the source_dir to let user pick via GUI, or a detected transcripts dir
        return 'audio', source_dir, None

    # Heuristic: image QC if images + a CSV (metadata/ocr) exist
    if images and (csvs or txts):
        # Existing image PyQt5 app expects: csv_path and image_dir
        # Choose the first CSV we find within the source_dir
        csv_path = next((c for c in csvs), None)
        # Choose an image directory: use the parent directory of first image if under source_dir
        if images:
            image_dir = os.path.dirname(images[0])
        else:
            image_dir = source_dir
        return 'image', csv_path, image_dir

    return 'unknown', None, None


def launch_audio_gui(csv_dir: str) -> int:
    """
    Launch the existing Tkinter audio QC tool.
    The script `ravlt_scoring.py` opens a folder dialog by default.
    We simply run it; user will pick the appropriate folder if needed.
    """
    # New package name: transcription_qc
    script_path = os.path.join(os.path.dirname(__file__), 'transcription_qc', 'ravlt_scoring.py')
    if not os.path.exists(script_path):
        print(f"Audio GUI not found at {script_path}")
        return 1
    # Run in a separate process using the current Python interpreter
    return subprocess.call([sys.executable, script_path])


def launch_image_gui(csv_path: str, image_dir: str, prefer_pyqt5: bool = True) -> int:
    """
    Launch the existing image QC GUI. Prefer PyQt5 version if available.
    The PyQt5 script normally prompts for paths via UI; we will provide them by
    temporarily setting argv and letting the script open its selection dialog,
    or we can directly exec the class. For simplicity, call the script and let the UI prompt.
    """
    base_dir_candidates = [
        os.path.join(os.path.dirname(__file__), 'image_qc'),
    ]

    pyqt5_script = None
    tk_script = None
    for base_dir in base_dir_candidates:
        candidate_pyqt = os.path.join(base_dir, 'qc_pyqt5.py')
        candidate_tk = os.path.join(base_dir, 'qc_tkinter.py')
        if pyqt5_script is None and os.path.exists(candidate_pyqt):
            pyqt5_script = candidate_pyqt
        if tk_script is None and os.path.exists(candidate_tk):
            tk_script = candidate_tk

    target = pyqt5_script if prefer_pyqt5 and pyqt5_script else tk_script
    if not target:
        print("Image GUI not found under 'image_qc'.")
        return 1

    # Both scripts open file dialogs themselves; just run and let user pick
    return subprocess.call([sys.executable, target])

def main():
    parser = argparse.ArgumentParser(description='Unified QC launcher')
    parser.add_argument('--source', help='Path to source directory containing data to QC')
    parser.add_argument('--prefer-tk', action='store_true', default=True,
                        help='Prefer Tkinter image GUI instead of PyQt5')
    args = parser.parse_args()

    # If no source is given, prompt the user with a directory selection dialog
    if args.source:
        source_dir = os.path.abspath(args.source)
    else:
        root = tk.Tk()
        root.withdraw()  # Hide the main Tk window
        source_dir = filedialog.askdirectory(title="Select source directory for QC")
        if not source_dir:
            print("No source directory selected. Exiting.")
            sys.exit(1)
        source_dir = os.path.abspath(source_dir)

    if not os.path.isdir(source_dir):
        print(f"Source is not a directory: {source_dir}")
        sys.exit(2)

    mode, primary, secondary = detect_qc_mode(source_dir)
    print(f"Detected mode: {mode}")

    if mode == 'audio':
        rc = launch_audio_gui(primary or source_dir)
        sys.exit(rc)
    elif mode == 'image':
        prefer_pyqt5 = not args.prefer_tk
        rc = launch_image_gui(primary or source_dir,
                              secondary or source_dir,
                              prefer_pyqt5=prefer_pyqt5)
        sys.exit(rc)
    else:
        print('Unable to infer QC mode from directory contents. Expected either:')
        print('- Audio: .wav files and transcript .csv files')
        print('- Image: image files (.png/.jpg/...) and OCR/metadata .csv or .txt')
        sys.exit(3)


if __name__ == '__main__':
    main()


