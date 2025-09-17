import tkinter as tk
from tkinter import filedialog, simpledialog, ttk, messagebox
import os
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import matplotlib
matplotlib.use('Agg')
AUDIO_ENABLED = True

try:
    import pygame
except ImportError:
    print('pygame import error')
    AUDIO_ENABLED = False
try:
    from scipy.io import wavfile
except ImportError:
    print('scipy import error')
    AUDIO_ENABLED = False
try:
    import sounddevice as sd
except ImportError:
    print('sounddevice import error')
    AUDIO_ENABLED = False


class AudioPlayerApp:
    def __init__(self, root, initials):
        self.root = root
        self.root.title("Audio Player App")

        self.df = None
        self.current_index = 0
        self.cursor_position = 0
        self.start_time = 0
        self.end_time = 0
        self.start_section = 0
        self.end_section = 0
        self.insert_start_section = 0
        self.insert_end_section = 0
        self.audio_segment = None
        self.file_path = None
        self.validation_pressed = False
        self.start_showing_text = False
        self.finished_file = False
        self.rate = 44100
        self.mouse_position = None
        self.onset_position = None
        self.offset_position = None
        self.edit = False
        self.insert = False

        self.zoom_factor = 0.8
        self.max_zoom_count = int(1 / (1 - self.zoom_factor)) + 2
        self.zoom_count = 0

        self.initials = initials
        self.entered_text = None

        self.edited_folder = 'edited'
        os.makedirs(self.edited_folder, exist_ok=True)

        pygame.mixer.init()

        self.create_widgets()

    def create_widgets(self):
        self.csv_frame = ttk.Frame(self.root)
        self.csv_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.csv_text = tk.Text(self.csv_frame, wrap="none")
        self.csv_text.pack(side="left", fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(self.csv_frame, command=self.csv_text.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.csv_text["yscrollcommand"] = scrollbar_y.set

        self.canvas_placeholder = tk.Canvas(self.root, width=400, height=300, bg="white")
        self.canvas_placeholder.grid(row=0, column=2)

        self.controls_label = tk.StringVar()
        self.controls_label.set('Controls')
        self.label_display_3 = tk.Label(self.root, textvariable=self.controls_label)
        self.label_display_3.grid(row=1, column=0, padx=0, pady=0)

        self.task_text = tk.StringVar()
        self.label_display_2 = tk.Label(self.root, textvariable=self.task_text)
        self.label_display_2.grid(row=1, column=0, padx=10, pady=10)

        self.start_button = tk.Button(self.root, text="Start", state=tk.DISABLED, command=self.start_playback)
        self.start_button.grid(row=2, column=0, padx=10, pady=0)

        self.restart_button = tk.Button(self.root, text="Restart", state=tk.DISABLED, command=self.restart)
        self.restart_button.grid(row=3, column=0, padx=10, pady=0)

        self.next_row_button = tk.Button(self.root, text="Next Row", state=tk.DISABLED, command=self.next_playback)
        self.next_row_button.grid(row=4, column=0, padx=10, pady=0)

        self.next_file_button = tk.Button(self.root, text="Next File", state=tk.DISABLED, command=self.next_file)
        self.next_file_button.grid(row=5, column=0, padx=10, pady=0)

        self.refresh_button = tk.Button(self.root, text="Refresh", state=tk.DISABLED, command=self.refresh)
        self.refresh_button.grid(row=6, column=0, padx=10, pady=0)

        self.import_button = tk.Button(self.root, text="Import", command=lambda: self.import_data(False))
        self.import_button.grid(row=7, column=0, padx=10, pady=0)

        self.whole_audio_button = tk.Button(self.root, text="Play Full Audio", state=tk.DISABLED, command=self.play_full_audio)
        self.whole_audio_button.grid(row=8, column=0, padx=10, pady=0)

        self.label_text = tk.StringVar()
        self.label_display_1 = tk.Label(self.root, textvariable=self.label_text)
        self.label_display_1.grid(row=0, column=1, padx=0, pady=0)

        self.zoom_in_button = tk.Button(self.root, text="Zoom In", command=self.zoom_in, state=tk.DISABLED)
        self.zoom_in_button.grid(row=1, column=1, padx=0, pady=0)

        self.zoom_out_button = tk.Button(self.root, text="Zoom Out", command=self.zoom_out, state=tk.DISABLED)
        self.zoom_out_button.grid(row=2, column=1, padx=0, pady=0)

        self.edit_label = tk.StringVar()
        self.edit_label.set('Edits')
        self.label_display_3 = tk.Label(self.root, textvariable=self.edit_label)
        self.label_display_3.grid(row=3, column=1, padx=0, pady=0)

        self.start_edit_button = tk.Button(self.root, text="Start Edit", state=tk.DISABLED, command=lambda: self.open_popup('edit'), bg='red')
        self.start_edit_button.grid(row=4, column=1, padx=0, pady=0)

        self.save_edit_button = tk.Button(self.root, text="Save Edit", state=tk.DISABLED, command=lambda: self.mark_edit_label('edit', 'edit'), bg='red')
        self.save_edit_button.grid(row=5, column=1, padx=0, pady=0)

        self.drop_button = tk.Button(self.root, text="Drop", state=tk.DISABLED, command=lambda: self.mark_edit_label('drop', 'drop'), bg='yellow')
        self.drop_button.grid(row=6, column=1, padx=0, pady=0)

        self.start_insert_button = tk.Button(self.root, text="Start Insert", state=tk.DISABLED, command=lambda: self.open_popup('insert'), bg='blue')
        self.start_insert_button.grid(row=7, column=1, padx=0)

        self.save_insert_button = tk.Button(self.root, text="Save Insert", state=tk.DISABLED, command=lambda: self.mark_edit_label('insert', 'insert'), bg='blue')
        self.save_insert_button.grid(row=8, column=1, padx=0)

        self.space = tk.StringVar()
        self.space.set('Quality Check')
        self.label_display_2 = tk.Label(self.root, textvariable=self.space)
        self.label_display_2.grid(row=1, column=2, padx=0, pady=0)

        self.accept_button = tk.Button(self.root, text="Accept", state=tk.DISABLED, command=lambda: self.mark_qc_label('accept', 'accept'), bg='green')
        self.accept_button.grid(row=2, column=2, padx=0, pady=0)

        self.review_button = tk.Button(self.root, text="For Review", state=tk.DISABLED, command=lambda: self.mark_qc_label('for_review', 'for_review'), bg='yellow')
        self.review_button.grid(row=3, column=2, padx=10, pady=0)

        self.off_task_button = tk.Button(self.root, text="Off Task", state=tk.DISABLED, command=lambda: self.mark_qc_label('off_task', 'off_task'), bg='orange')
        self.off_task_button.grid(row=4, column=2, padx=10)

        self.add_note_button = tk.Button(self.root, text="Add Note", state=tk.DISABLED, command=lambda: self.mark_qc_label('add_note', 'add_note'))
        self.add_note_button.grid(row=5, column=2, padx=10)

        self.search_button = tk.Button(self.root, text="Search", command=lambda: self.open_popup('search'), state=tk.DISABLED)
        self.search_button.grid(row=6, column=2, padx=10)

        self.search_result_label = tk.Label(self.root, text="")
        self.search_result_label.grid(row=7, column=2, padx=10)

        self.play_current_audio = tk.Button(self.root, text="Play Current Audio", command=self.play_audio_segment)
        self.play_current_audio.grid(row=8, column=2, padx=10, pady=0)

    def open_popup(self, button_val):
        def get_text_and_continue():
            entered_text = entry_var.get()
            print("Entered text:", entered_text)
            if button_val == 'search':
                self.search_data(entered_text)
            elif button_val == 'insert':
                self.next_row_button.config(state=tk.DISABLED)
                self.mark_edit_label(button_val, entered_text)
            else:
                self.next_row_button.config(state=tk.DISABLED)
                self.mark_edit_label(button_val, entered_text)
            popup.destroy()
            self.root.update()

        popup = tk.Toplevel(self.root)
        popup.title("Popup Window")

        entry_label = tk.Label(popup, text="Enter text:")
        entry_label.pack(padx=10, pady=5)

        entry_var = tk.StringVar()
        entry = tk.Entry(popup, textvariable=entry_var)
        entry.pack(padx=10, pady=10)

        continue_button = tk.Button(popup, text="Continue", command=get_text_and_continue)
        continue_button.pack(pady=10)

    def display_csv(self):
        self.csv_text.delete(1.0, "end")
        csv_string = self.df.iloc[:, :].to_string(index=True)
        lines = csv_string.split('\n')
        for i, line in enumerate(lines, start=1):
            if i == self.current_index + 2:
                self.csv_text.insert("end", line + "\n", "highlight")
            else:
                self.csv_text.insert("end", line + "\n")
        self.csv_text.tag_configure("highlight", background="yellow")

    def refresh(self):
        self.df = self.df.sort_values('onset')
        self.df = self.df.reset_index(drop=True)
        self.display_csv()
        self.root.update()

    def get_time_axis(self):
        return np.linspace(0, self.audio_duration, len(self.audio_data))

    def load_audio(self):
        sample_rate, audio_data = wavfile.read(self.audio_file_path)
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
        return audio_data

    def zoom_in(self):
        if self.zoom_count >= self.max_zoom_count:
            return
        x_range_length = self.x_range[1] - self.x_range[0]
        new_x_range_length = x_range_length * self.zoom_factor
        cursor_position = self.red_cursor_line.get_xdata()[0]
        if cursor_position - new_x_range_length / 2 < 0 or cursor_position + new_x_range_length / 2 > self.initial_x_range[1]:
            if cursor_position - new_x_range_length / 2 < 0:
                new_min = 0
                new_max = new_min + new_x_range_length
            else:
                new_max = self.initial_x_range[1]
                new_min = new_max - new_x_range_length
        else:
            new_min = cursor_position - new_x_range_length / 2
            new_max = cursor_position + new_x_range_length / 2
        self.x_range = (new_min, new_max)
        self.zoom_count += 1
        self.ax.set_xlim(self.x_range)
        self.canvas.draw()

    def zoom_out(self):
        if self.x_range[1] - self.x_range[0] >= self.initial_x_range[1] - self.initial_x_range[0]:
            return
        x_range_length = self.x_range[1] - self.x_range[0]
        new_x_range_length = x_range_length / self.zoom_factor
        cursor_position = self.red_cursor_line.get_xdata()[0]
        if cursor_position - new_x_range_length / 2 < 0 or cursor_position + new_x_range_length / 2 > self.initial_x_range[1]:
            if cursor_position - new_x_range_length / 2 < 0:
                new_min = 0
                new_max = new_min + new_x_range_length
            else:
                new_max = self.initial_x_range[1]
                new_min = new_max - new_x_range_length
        else:
            new_min = cursor_position - new_x_range_length / 2
            new_max = cursor_position + new_x_range_length / 2
        self.x_range = (new_min, new_max)
        self.zoom_count -= 1
        self.ax.set_xlim(self.x_range)
        self.canvas.draw()

    def init_plot(self):
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot(self.get_time_axis(), self.audio_data)
        self.red_cursor_line = self.ax.axvline(x=self.cursor_position, color='red', linestyle='-', linewidth=2)
        self.green_cursor_line, = self.ax.plot([0, 0], [-1, 1], color='green', linestyle='-', linewidth=2, visible=False)
        self.yellow_start_line = self.ax.axvline(x=self.start_section, color='yellow', linestyle='-', linewidth=1, visible=False)
        self.red_highlight_space = plt.axvspan(self.start_section, self.end_section, color='red', alpha=0, label='Highlighted Area')
        self.yellow_end_line = self.ax.axvline(x=self.end_section, color='yellow', linestyle='-', linewidth=1, visible=False)
        self.blue_start_line = self.ax.axvline(x=self.start_section, color='blue', linestyle='-', linewidth=1, visible=False)
        self.blue_highlight_space = plt.axvspan(self.start_section, self.end_section, color='blue', alpha=0, label='Insert Area', visible=False)
        self.blue_end_line = self.ax.axvline(x=self.end_section, color='blue', linestyle='-', linewidth=1, visible=False)
        self.ax.set_xlim(self.x_range)
        self.ax.set_ylim(-1, 1)
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Amplitude')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=2, padx=10, pady=10)
        return self.red_cursor_line, self.green_cursor_line

    def update_plot(self):
        self.root.update()
        cursor_line_x = self.cursor_position
        self.red_cursor_line.set_xdata([cursor_line_x, cursor_line_x])
        self.yellow_start_line.set_visible(True)
        self.yellow_start_line.set_xdata([self.start_section, self.start_section])
        self.red_highlight_space.remove()
        self.red_highlight_space = plt.axvspan(self.start_section, self.end_section, color='red', alpha=0.3, label='Highlighted Area')
        self.yellow_end_line.set_visible(True)
        self.yellow_end_line.set_xdata([self.end_section, self.end_section])
        self.blue_start_line.set_xdata([self.insert_start_section, self.insert_start_section])
        self.blue_highlight_space.remove()
        self.blue_highlight_space = plt.axvspan(self.insert_start_section, self.insert_end_section, color='blue', alpha=0.3, label='Insert Area', visible=False)
        self.blue_end_line.set_xdata([self.insert_end_section, self.insert_end_section])
        self.green_cursor_line.set_xdata([self.mouse_position, self.mouse_position])
        self.canvas.draw()
        return self.red_cursor_line, self.green_cursor_line

    def on_motion(self, event):
        if event.xdata is not None:
            cursor_line_x = event.xdata
            self.mouse_position = cursor_line_x
            self.green_cursor_line.set_xdata([self.mouse_position, self.mouse_position])
            self.green_cursor_line.set_visible(True)
        else:
            self.green_cursor_line.set_visible(False)
        self.canvas.draw()

    def on_click(self, event):
        if event.xdata is not None:
            if self.onset_position != None:
                self.offset_position = event.xdata
                if self.edit:
                    self.end_section = self.offset_position
                if self.insert:
                    self.blue_end_line.set_visible(True)
                    self.blue_highlight_space.set_visible(True)
                    self.insert_end_section = self.offset_position
                self.update_plot()
                self.root.update()
                print(f"Clicked at time: {self.offset_position} seconds")
            else:
                self.onset_position = event.xdata
                if self.edit:
                    self.start_section = self.onset_position
                if self.insert:
                    self.blue_start_line.set_visible(True)
                    self.insert_start_section = self.onset_position
                self.update_plot()
                self.root.update()
                print(f"Clicked at time: {self.onset_position} seconds")

    def restart(self):
        self.current_index = 0
        self.start_button.config(state=tk.NORMAL)
        self.refresh_button.config(state=tk.DISABLED)
        self.start_insert_button.config(state=tk.DISABLED)
        self.save_insert_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.NORMAL)
        self.next_row_button.config(state=tk.DISABLED)
        self.next_file_button.config(state=tk.NORMAL)
        self.accept_button.config(state=tk.DISABLED)
        self.start_edit_button.config(state=tk.DISABLED)
        self.save_edit_button.config(state=tk.DISABLED)
        self.drop_button.config(state=tk.DISABLED)
        self.review_button.config(state=tk.DISABLED)
        self.off_task_button.config(state=tk.DISABLED)
        self.add_note_button.config(state=tk.NORMAL)
        self.off_task_button.config(state=tk.NORMAL)
        self.word = ''
        self.display_csv()
        self.label_text.set(self.word)

    def search_data(self, search_query):
        if search_query.isdigit():
            t = self.find_closest_time(int(search_query))
            self.display_info_and_play_audio(t)
        else:
            self.display_info_and_play_audio(self.find_matching_word(search_query.lower()))

    def display_info_and_play_audio(self, index):
        if 0 <= index < len(self.df):
            self.start_button.config(state=tk.DISABLED)
            self.start_showing_text = True
            self.restart_button.config(state=tk.NORMAL)
            self.next_row_button.config(state=tk.NORMAL)
            self.next_file_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)
            self.accept_button.config(state=tk.NORMAL)
            self.start_edit_button.config(state=tk.NORMAL)
            self.save_edit_button.config(state=tk.DISABLED)
            self.review_button.config(state=tk.NORMAL)
            self.off_task_button.config(state=tk.NORMAL)
            self.add_note_button.config(state=tk.NORMAL)
            self.off_task_button.config(state=tk.NORMAL)
            self.start_insert_button.config(state=tk.NORMAL)
            self.save_insert_button.config(state=tk.DISABLED)
            self.drop_button.config(state=tk.NORMAL)
            self.root.update()
            self.search_result_label.config(text="")
            self.current_index = index
            self.get_audio_segment()
            self.current_index -= 1
            self.next_playback()
        else:
            self.search_result_label.config(text="Please check spelling/submitted Start Time.")

    def find_matching_word(self, search_word):
        matching_rows = self.df[self.df['word'].str.lower().eq(search_word)]
        if not matching_rows.empty:
            return matching_rows.index[0]
        else:
            return -1

    def find_closest_time(self, search_time):
        closest_index = np.argmin(np.abs(self.df['onset'] - search_time).values)
        return closest_index

    def get_audio_duration(self, file_path):
        sample_rate, audio_data = wavfile.read(file_path)
        duration = len(audio_data) / sample_rate
        return duration * 1000

    def update_cursor_position(self, sample_rate, total_samples):
        start_time_sec = self.start_time / 1000
        end_time_sec = self.end_time / 1000
        duration_sec = end_time_sec - start_time_sec

        start_ticks = time.time()
        while time.time() - start_ticks < duration_sec:
            elapsed_sec = time.time() - start_ticks
            self.cursor_position = start_time_sec + elapsed_sec
            self.red_cursor_line.set_xdata([self.cursor_position, self.cursor_position])
            self.canvas.draw()
            self.root.update()
            time.sleep(0.01)  # small delay to animate smoothly

    def play_full_audio(self):
        try:
            sample_rate, audio_data = wavfile.read(self.audio_file_path)
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

            self.start_time = 0
            self.end_time = len(audio_data) / sample_rate * 1000
            self.cursor_position = 0

            # Play asynchronously
            sd.play(audio_data, sample_rate)
            
            # Start cursor animation
            self.animate_cursor(self.start_time / 1000, self.end_time / 1000)
            
        except Exception as e:
            print(f"Error playing full audio: {e}")

    def animate_cursor(self, start_sec, end_sec):
        step = 0.01  # seconds
        if self.cursor_position < end_sec:
            self.red_cursor_line.set_xdata([self.cursor_position, self.cursor_position])
            self.canvas.draw()
            self.cursor_position += step
            self.root.after(int(step*1000), lambda: self.animate_cursor(start_sec, end_sec))

    def play_audio_segment(self):
        try:
            sample_rate, audio_data = wavfile.read(self.audio_file_path)
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

            start_sample = int(self.start_time * sample_rate / 1000)
            end_sample = int(self.end_time * sample_rate / 1000)
            segment = audio_data[start_sample:end_sample]

            self.cursor_position = self.start_time / 1000

            sd.play(segment, sample_rate)
            self.animate_cursor(self.start_time / 1000, self.end_time / 1000)
            
        except Exception as e:
            print(f"Error playing audio segment: {e}")

    def start_playback(self):
        self.label_text.set('')
        self.start_button.config(state=tk.DISABLED)
        self.start_showing_text = True
        self.restart_button.config(state=tk.NORMAL)
        self.next_row_button.config(state=tk.NORMAL)
        self.next_file_button.config(state=tk.NORMAL)
        self.refresh_button.config(state=tk.NORMAL)
        self.accept_button.config(state=tk.NORMAL)
        self.start_edit_button.config(state=tk.NORMAL)
        self.save_edit_button.config(state=tk.DISABLED)
        self.review_button.config(state=tk.NORMAL)
        self.start_insert_button.config(state=tk.NORMAL)
        self.save_insert_button.config(state=tk.DISABLED)
        self.drop_button.config(state=tk.NORMAL)
        self.add_note_button.config(state=tk.NORMAL)
        self.off_task_button.config(state=tk.NORMAL)
        self.zoom_in_button.config(state=tk.NORMAL)
        self.zoom_out_button.config(state=tk.NORMAL)
        self.search_button.config(state=tk.NORMAL)
        self.display_word()
        self.update_plot()
        self.root.update()
        self.rename_old_files()

    def get_audio_segment(self):
        if AUDIO_ENABLED:
            self.start_time = (self.df.iloc[self.current_index, 1] * 1000) - 500
            self.cursor_position = self.start_time
            if self.current_index == len(self.df) - 1:
                if self.get_audio_duration(self.audio_file_path) < (self.df.iloc[self.current_index, 2] * 1000) + 2000:
                    self.end_time = self.get_audio_duration(self.audio_file_path)
                else:
                    self.end_time = (self.df.iloc[self.current_index, 2] * 1000) + 2000
            else:
                self.end_time = (self.df.iloc[self.current_index, 2] * 1000) + 2000
            self.start_section = (self.df.iloc[self.current_index, 1])
            self.end_section = (self.df.iloc[self.current_index, 2])
            return True
        else:
            return None

    def display_word(self):
        if self.df is not None and self.current_index < len(self.df):
            if self.start_showing_text:
                self.word = self.df.iloc[self.current_index, 0]
                self.label_text.set(f'Current word: {self.word}')
                self.audio_segment = self.get_audio_segment()

    def next_playback(self):
        self.root.update()
        self.df = self.df.sort_values('onset')
        self.df = self.df.reset_index(drop=True)
        self.onset_position = None
        self.offset_position = None
        self.edit = False
        self.insert = False
        if self.current_index < len(self.df) - 1:
            self.current_index += 1
            self.display_word()
            self.display_csv()
            self.update_plot()
            self.root.update()
            if self.current_index == len(self.df) - 1 and self.validation_pressed:
                self.next_row_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.NORMAL)
            self.next_row_button.config(state=tk.NORMAL)
            self.next_file_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)
            self.accept_button.config(state=tk.NORMAL)
            self.start_edit_button.config(state=tk.NORMAL)
            self.save_edit_button.config(state=tk.DISABLED)
            self.review_button.config(state=tk.NORMAL)
            self.off_task_button.config(state=tk.NORMAL)
            self.add_note_button.config(state=tk.NORMAL)
            self.start_insert_button.config(state=tk.NORMAL)
            self.save_insert_button.config(state=tk.DISABLED)
            self.drop_button.config(state=tk.NORMAL)
            self.zoom_in_button.config(state=tk.NORMAL)
            self.zoom_out_button.config(state=tk.NORMAL)
            self.search_button.config(state=tk.NORMAL)
        else:
            if self.current_file != len(self.files):
                self.finished_file = True
                self.next_file_button.config(state=tk.NORMAL)
                self.label_text.set('Finished validating this file. Press "Next File" to continue.')
            else:
                self.next_file_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)
            self.next_row_button.config(state=tk.DISABLED)
            self.accept_button.config(state=tk.DISABLED)
            self.start_edit_button.config(state=tk.DISABLED)
            self.save_edit_button.config(state=tk.DISABLED)
            self.review_button.config(state=tk.DISABLED)
            self.off_task_button.config(state=tk.DISABLED)
            self.add_note_button.config(state=tk.DISABLED)
            self.start_insert_button.config(state=tk.DISABLED)
            self.save_insert_button.config(state=tk.DISABLED)
            self.drop_button.config(state=tk.DISABLED)
            self.zoom_in_button.config(state=tk.DISABLED)
            self.zoom_out_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.DISABLED)
        self.save_data()

    def rename_old_files(self):
        directory = self.folder_path.replace('audio_transcripts', 'edited')
        os.makedirs(directory, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(self.file_path))[0]
        self.edited_file_path = os.path.join(directory, f'{base_filename}_edited_file.csv')
        index = 0
        existing_file = self.edited_file_path
        while os.path.exists(existing_file):
            new_name = f'{base_filename}_edited_file_OLD{"_" + str(index) if index > 0 else ""}.csv'
            new_file_path = os.path.join(directory, new_name)
            existing_file = new_file_path
            index += 1
        for i in range(index-1, 0, -1):
            old_file_path = os.path.join(directory, f'{base_filename}_edited_file_OLD{"_" + str(i-1) if i > 1 else ""}.csv')
            new_file_path = os.path.join(directory, f'{base_filename}_edited_file_OLD_{i}.csv')
            os.rename(old_file_path, new_file_path)
        if index > 0:
            os.rename(self.edited_file_path, os.path.join(directory, f'{base_filename}_edited_file_OLD.csv'))

    def save_data(self):
        self.df.to_csv(self.edited_file_path, index=False)
        print(f"Changes saved to: {self.edited_file_path}")

    def import_data(self, file):
        if not file:
            try:
                self.folder_path = filedialog.askdirectory(title="Select Folder")
                self.files = []
                for filename in os.listdir(self.folder_path):
                    if filename.endswith(".csv") and "Recall" in filename:
                        self.file_path = self.folder_path + '/' + filename
                        self.files.append(self.file_path)
                self.current_file = 0
                self.files.sort()
            except Exception as e:
                print(e)
        self.file_path = self.files[self.current_file]
        dir = self.file_path.split('/')
        print(self.file_path)
        self.name = dir[-1].split('_')[0]
        self.task_text.set(f'Now displaying: {self.name}')
        self.audio_file_path = (f"{'/'.join(dir[:-1])}/{self.name}.wav")
        audio_list = self.audio_file_path.split('/')
        audio_list[-3] = 'audio_transcripts'
        self.audio_file_path = '/'.join(audio_list)
        if self.file_path:
            self.df = pd.read_csv(self.file_path)
            self.df = self.df.copy()
            self.display_csv()
            self.audio_duration = self.get_audio_duration(self.audio_file_path)/1000
            self.audio_data = self.load_audio()
            self.initial_x_range = (0, self.audio_duration)
            self.x_range = self.initial_x_range
            self.init_plot()
            self.canvas.draw()
            if 'quality_check_label' not in self.df.columns:
                self.df['quality_check_label'] = pd.Series([float('nan')]*len(self.df), dtype='float')
            if 'note' not in self.df.columns:
                self.df['note'] = pd.Series([float('nan')]*len(self.df), dtype='float')
            self.start_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.NORMAL)
            self.next_row_button.config(state=tk.DISABLED)
            self.next_file_button.config(state=tk.NORMAL)
            self.accept_button.config(state=tk.DISABLED)
            self.start_edit_button.config(state=tk.DISABLED)
            self.save_edit_button.config(state=tk.DISABLED)
            self.review_button.config(state=tk.DISABLED)
            self.off_task_button.config(state=tk.DISABLED)
            self.add_note_button.config(state=tk.DISABLED)
            self.drop_button.config(state=tk.DISABLED)
            self.start_insert_button.config(state=tk.DISABLED)
            self.save_insert_button.config(state=tk.DISABLED)
            self.whole_audio_button.config(state=tk.NORMAL)
            self.search_button.config(state=tk.DISABLED)
            self.validation_pressed = False
            self.current_index = 0

    def next_file(self):
        self.edit = False
        self.insert = False
        if self.current_file == len(self.files) - 1:
            self.label_text.set("Finished validating all files.")
            self.start_button.config(state=tk.DISABLED)
            self.refresh_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)
            self.next_row_button.config(state=tk.DISABLED)
            self.accept_button.config(state=tk.DISABLED)
            self.start_edit_button.config(state=tk.DISABLED)
            self.save_edit_button.config(state=tk.DISABLED)
            self.review_button.config(state=tk.DISABLED)
            self.off_task_button.config(state=tk.DISABLED)
            self.start_insert_button.config(state=tk.DISABLED)
            self.save_insert_button.config(state=tk.DISABLED)
            self.drop_button.config(state=tk.DISABLED)
            self.add_note_button.config(state=tk.DISABLED)
            self.off_task_button.config(state=tk.DISABLED)
        else:
            self.current_file += 1
            self.current_index = 0
            self.import_data(True)
            self.label_text.set("Press the 'Start' button to begin the next file")

    def mark_qc_label(self, label, qc_label_value):
        if pd.notna(self.df.at[self.current_index, 'word']):
            self.df.at[self.current_index, 'editor'] = self.initials
            if self.df.loc[self.current_index, 'quality_check_label'] != 'insert':
                self.df.at[self.current_index, 'quality_check_label'] = qc_label_value
            self.validation_pressed = True
            if label == 'add_note':
                user_input = simpledialog.askstring("Input", "Add note in space below:")
                if user_input is not None:
                    self.df.at[self.current_index, 'note'] = user_input
            self.root.update()
            self.save_data()

    def mark_edit_label(self, label, data):
        if pd.notna(self.df.at[self.current_index, 'word']):
            self.df.at[self.current_index, 'editor'] = self.initials
            if label == 'drop':
                self.df = self.df.drop(self.current_index).reset_index(drop=True)
                self.current_index -= 1
            else:
                if label == 'edit':
                    if self.edit:
                        self.edit_data(self.new_word)
                        self.save_edit_button.config(state=tk.DISABLED)
                        self.next_row_button.config(state=tk.NORMAL)
                        self.edit = False
                        self.onset_position = None
                    else:
                        self.edit = True
                        self.new_word = data
                        self.start_edit_button.config(state=tk.DISABLED)
                        self.save_edit_button.config(state=tk.NORMAL)
                        self.start_insert_button.config(state=tk.DISABLED)
                        self.save_insert_button.config(state=tk.DISABLED)
                elif label == 'insert':
                    if self.insert:
                        if data != '':
                            self.insert_data(self.new_word)
                        else:
                            messagebox.showinfo("Insert Popup", "Make you've input a word into the space below")
                        self.save_insert_button.config(state=tk.DISABLED)
                        self.next_row_button.config(state=tk.NORMAL)
                        self.blue_end_line.set_visible(False)
                        self.blue_start_line.set_visible(False)
                        self.blue_highlight_space.set_visible(False)
                        self.insert = False
                        self.onset_position = None
                    else:
                        self.insert = True
                        self.new_word = data
                        self.start_insert_button.config(state=tk.DISABLED)
                        self.save_insert_button.config(state=tk.NORMAL)
                        self.start_edit_button.config(state=tk.DISABLED)
                        self.save_edit_button.config(state=tk.DISABLED)
            self.root.update()
            self.save_data()

    def edit_data(self, data):
        if data == '':
            data = self.word
            confidence = self.df.loc[self.current_index, 'confidence']
        else:
            confidence = np.nan
        if self.onset_position == None:
            self.onset_position = self.df.loc[self.current_index, 'onset']
        if self.offset_position == None:
            self.offset_position = self.df.loc[self.current_index, 'offset']
        edit_label = 'edit'
        if self.df.loc[self.current_index, 'quality_check_label'] == 'insert':
            edit_label = 'insert'
        self.df.loc[self.current_index] = [data, self.start_section, self.end_section, confidence] + [edit_label] + [np.nan] + [self.initials] + [np.nan] * (self.df.shape[1] - 7)

    def insert_data(self, data):
        index_to_insert = self.current_index + 1
        new_row = [data, self.insert_start_section, self.insert_end_section] + [np.nan] + ['insert'] + [np.nan] + [self.initials] + [np.nan] * (self.df.shape[1] - 7)
        new_df = pd.DataFrame([new_row], columns=self.df.columns)
        self.df = pd.concat([self.df.iloc[:index_to_insert], new_df, self.df.iloc[index_to_insert:]], ignore_index=True)


