import tkinter as tk
from tkinter import filedialog as fd
import concurrent.futures
import time
import datetime
import os
import re
import functools
import subprocess


class ui:
    def __init__(self):
        self.root = tk.Tk()

        self.input_frame = tk.Frame(self.root)
        self.input_frame.grid(row=0, column=0)

        self.cur_cuts = tk.Label(self.root, text="")
        self.cur_cuts.grid(row=0, column=1)

        # Construct input label, entry and button
        tk.Label(self.input_frame, text="Input:").grid(row=0, column=0)
        self.input = tk.StringVar()
        tk.Entry(self.input_frame, textvariable=self.input).grid(row=0, column=1)
        tk.Button(self.input_frame, text="Choose input", command=lambda *args: self.choose_file()).grid(row=0, column=2)
        self.extract_video = tk.BooleanVar()
        tk.Checkbutton(self.input_frame, text="Extract with youtube-dl", variable=self.extract_video).grid(row=0, column=3)

        # Construct output label, entry and button
        tk.Label(self.input_frame, text="Output:").grid(row=1, column=0)
        self.output = tk.StringVar()
        tk.Entry(self.input_frame, textvariable=self.output).grid(row=1, column=1)
        tk.Button(self.input_frame, text="Choose output", command=lambda *args: self.save_file()).grid(row=1, column=2)

        # Tuple containing 2 tuples with 4 tkinter StringVar variables for START and END timestamps
        self.timestamp = tuple(tuple(tk.StringVar() for _ in range(4)) for _ in range(2))

        # Trace every change in timestamp variables
        for row in range(2):
            self.timestamp[row][0].trace("w", functools.partial(self.only_numeric, self.timestamp[row][0]))
        for row in range(2):
            for column in range(1, 3):
                self.timestamp[row][column].trace("w", functools.partial(self.int_limit, self.timestamp[row][column], 59))
        for row in range(2):
            self.timestamp[row][3].trace("w", functools.partial(self.int_limit, self.timestamp[row][3], 999))

        # Construct START and END timestamp ui
        tk.Label(self.input_frame, text="Start - End (H:M:S.MS)").grid(row=3, column=0)

        for row in range(2):
            for column in range(4):
                tk.Entry(self.input_frame, textvariable=self.timestamp[row][column]).grid(row=4+row, column=column)

        # Construct button to begin video trimming
        self.trim_button = tk.Button(self.input_frame, text="Trim")
        self.trim_button.grid(row=6, column=0)

        # Construct STATUS label
        self.status = tk.StringVar()
        tk.Label(self.input_frame, textvariable=self.status).grid(row=6, column=1)

    def choose_file(self):  # Input file dialog
        self.dir = fd.askopenfilename(filetypes=[("Video File", ["*.mov", "*.mp4", "*.m4a", "*.3gp", "*.3g2", "*.mj2"]),
                                                 ("All Files", "*.*")])
        self.input.set(self.dir)

    def save_file(self):  # Output file dialog
        self.dir = fd.asksaveasfilename(initialfile="output.mp4",
                                        filetypes=[("Video File", ["*.mov", "*.mp4", "*.m4a", "*.3gp", "*.3g2", "*.mj2"]),
                                                   ("All Files", "*.*")])

        # If the file doesn't end with an extension, give it ".mp4"
        if self.dir and "." not in self.dir:
            self.dir += ".mp4"

        self.output.set(self.dir)

    def int_limit(self, var, limit, *args):  # Ensure, that value is below or equal to given limit
        self.only_numeric(var)

        if var.get() == "":
            return

        elif int(var.get()) > limit:
            var.set(limit)

    def only_numeric(self, var, *args):  # Ensure, that value stays numeric
        var.set(re.sub('[^0-9]', '', var.get()).lstrip("0"))


class app:
    def __init__(self, ui):
        self.ui = ui
        self.ui.trim_button.config(command=self.trim)
        self.ui.status.set("Running operations: 0")

        executor.submit(self.command_executor)

    def trim(self):
        self.ui.status.set("processing")

        # Get timestamps and join them to the H:M:S.MS format
        self.str_time = []
        for i in range(2):
            self.str_time.append(int(self.ui.timestamp[i][0].get() if self.ui.timestamp[i][0].get() != "" else "0")*3600 +
                                 int(self.ui.timestamp[i][1].get() if self.ui.timestamp[i][1].get() != "" else "0")*60 +
                                 int(self.ui.timestamp[i][2].get() if self.ui.timestamp[i][2].get() != "" else "0") +
                                 float("0."+self.ui.timestamp[i][-1].get()))

        # Abort if input file or output filename is missing
        if self.ui.input.get() == "" or self.ui.output.get() == "":
            self.ui.status.set("missing input/output")
            return

        if self.str_time[1] == 0:  # Set END timestamp to "" if it's 0
            self.to = ""
        elif self.str_time[0] >= self.str_time[1]:  # Abort if START >= END
            self.ui.status.set("invalid timestamp")
            return
        else:
            self.to = " -to "+str(self.str_time[1])

        if self.str_time[0] > seek_treshold:
            self.start = [" -ss "+str(self.str_time[0]-seek_treshold), " -ss "+str(seek_treshold)]
        else:
            self.start = ["", " -ss "+str(self.str_time[0])]

        if self.ui.extract_video.get():
            self.input_video = subprocess.check_output(str("youtube-dl -g "+self.ui.input.get())).strip().decode("utf-8")
        else:
            self.input_video = self.ui.input.get()

        self.quote = '"'  # remove quotes if copying file path from file explorer
        # Compile the ffmpeg command
        self.ffmpeg_command = (f'ffmpeg {self.start[0]}{self.to} -i "{self.input_video.strip(self.quote)}"{self.start[1]} -c:v copy -c:a copy "{self.ui.output.get().strip(self.quote)}"')
        self.commands.append(self.ffmpeg_command)

    def run_ffmpeg(self, command):  # Runs a given windows shell command
        self.t1 = time.perf_counter()
        self.running_operations.add(self.t1)

        self.ui.status.set(f"Running operations: {len(self.running_operations)}")

        os.system(command)
        self.t2 = time.perf_counter()
        print(f"\nCommand: '{command}'")
        print(f"Completed in: {datetime.timedelta(seconds=self.t2-self.t1)}\n")
        self.running_operations.discard(self.t1)

        self.ui.status.set(f"Running operations: {len(self.running_operations)}")

    def command_executor(self):
        self.commands = []
        self.running_operations = set()
        while True:
            while self.commands:
                for _ in range(len(self.commands)):
                    self.cmd = self.commands.pop()
                    executor.submit(self.run_ffmpeg, self.cmd)


if __name__ == "__main__":
    seek_treshold = 30
    executor = concurrent.futures.ThreadPoolExecutor()
    app = app(ui())
    app.ui.root.mainloop()
