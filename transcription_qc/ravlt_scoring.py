import tkinter as tk
try:
    from .initials import InitialsEntryApp
    from .audio_player_app import AudioPlayerApp
except ImportError:
    import os, sys
    sys.path.append(os.path.dirname(__file__))
    from initials import InitialsEntryApp
    from audio_player_app import AudioPlayerApp


if __name__ == "__main__":
    initials_root = tk.Tk()
    initials_app = InitialsEntryApp(initials_root, initials_callback=lambda initials: initials_root.destroy())
    initials_root.mainloop()
    entered_initials = initials_app.entered_initials
    audio_player_root = tk.Tk()
    app = AudioPlayerApp(audio_player_root, entered_initials)
    audio_player_root.mainloop()


