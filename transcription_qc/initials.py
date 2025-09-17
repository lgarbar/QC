import tkinter as tk


class InitialsEntryApp:
    def __init__(self, root, initials_callback):
        self.root = root
        self.root.title("Initials Entry")
        self.initials_callback = initials_callback

        self.label = tk.Label(root, text="Enter Your Initials:")
        self.label.pack()

        self.entry = tk.Entry(root)
        self.entry.pack()

        self.submit_button = tk.Button(root, text="Submit", command=self.submit_initials)
        self.submit_button.pack()

        self.entered_initials = None

    def submit_initials(self):
        initials = self.entry.get()
        if initials:
            self.entered_initials = initials
            self.initials_callback(initials)
            self.root.quit()


