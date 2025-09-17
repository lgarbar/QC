### QC Toolkit

Unified tools for manual quality control of audio transcriptions and image/OCR data.

### Structure

- `qc_launcher.py`: Detects dataset type (audio vs image) and launches the correct GUI.
- `transcription_qc/`: Audio QC package
  - `initials.py`: Initials entry dialog
  - `audio_player_app.py`: Tkinter app for audio and transcript review
  - `ravlt_scoring.py`: Thin launcher
- `image_qc/`: Image QC package
  - `file_dialogs_tk.py`: File selection dialogs
  - `data_editor_tk.py`: Tkinter editor for image/OCR rows
  - `qc_tkinter.py`: Thin launcher (PyQt counterpart optional if present)
- `requirements.txt`: Python dependencies

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Use

```bash
python qc_launcher.py /path/to/source_dir
```

Options:
- `--prefer-tk` to prefer Tk over PyQt for image QC.

### Data detection

- Audio QC: presence of both `.wav` and `.csv` → launches `transcription_qc` tool.
- Image QC: presence of images and `.csv`/`.txt` → launches `image_qc` tool.

### Notes

- GUIs will still prompt via file dialogs to confirm exact files/dirs.
- Future: extend launcher for ECG/EDA/eye-tracking.


