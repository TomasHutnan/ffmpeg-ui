import tkinter as tk
from tkinter import filedialog as fd
import concurrent.futures
import time
import datetime
import os
import re


class ui:
    def __init__(self):
        self.root = tk.Tk()

        # Construct input label, entry and button
        tk.Label(text="Input:").grid(row=0, column=0)
        self.input = tk.StringVar()
        tk.Entry(textvariable=self.input).grid(row=0, column=1)
        tk.Button(text="Choose input", command=lambda *args: self.choose_file()).grid(row=0, column=2)

        # Construct output label, entry and button
        tk.Label(text="Output:").grid(row=1, column=0)
        self.output = tk.StringVar()
        tk.Entry(textvariable=self.output).grid(row=1, column=1)
        tk.Button(text="Choose output", command=lambda *args: self.save_file()).grid(row=1, column=2)

        # Tuple containing 2 tuples with 4 tkinter StringVar variables for START and END timestamps
        self.timestamp = tuple(tuple(tk.StringVar() for _ in range(4)) for _ in range(2))

        # Cloudn't do this section with for loops for an unknown reason
        # Trace every change in timestamp variables
        self.timestamp[0][0].trace("w", lambda *args: self.only_numeric(var=self.timestamp[0][0]))
        self.timestamp[0][1].trace("w", lambda *args: self.int_limit(var=self.timestamp[0][1], limit=59))
        self.timestamp[0][2].trace("w", lambda *args: self.int_limit(var=self.timestamp[0][2], limit=59))
        self.timestamp[0][3].trace("w", lambda *args: self.int_limit(var=self.timestamp[0][3], limit=999))

        self.timestamp[1][0].trace("w", lambda *args: self.only_numeric(var=self.timestamp[1][0]))
        self.timestamp[1][1].trace("w", lambda *args: self.int_limit(var=self.timestamp[1][1], limit=59))
        self.timestamp[1][2].trace("w", lambda *args: self.int_limit(var=self.timestamp[1][2], limit=59))
        self.timestamp[1][3].trace("w", lambda *args: self.int_limit(var=self.timestamp[1][3], limit=999))

        # Construct START and END timestamp ui
        tk.Label(text="Start - End (H:M:S.MS)").grid(row=3, column=0)

        for row in range(2):
            for column in range(4):
                tk.Entry(textvariable=self.timestamp[row][column]).grid(row=4+row, column=column)

        # Construct button to begin video trimming
        self.trim_button = tk.Button(text="Trim")
        self.trim_button.grid(row=6, column=0)

        # Construct STATUS label
        self.status = tk.StringVar()
        tk.Label(textvariable=self.status).grid(row=6, column=1)

    def choose_file(self):  # Input file dialog
        self.dir = fd.askopenfilename(filetypes=[("All Files", "*.*"),
                                                 ("MP4", "*.mp4")])
        self.input.set(self.dir)

    def save_file(self):  # Output file dialog
        self.dir = fd.asksaveasfilename(initialfile="output.mp4",
                                        filetypes=[("MP4", "*.mp4"),
                                                   ("All Files", "*.*")])

        # If the file doesn't end with an extension, give it ".mp4"
        if "." not in self.dir:
            self.dir += ".mp4"

        self.output.set(self.dir)

    def int_limit(self, var, limit):  # Ensure, that value is below or equal to given limit
        self.only_numeric(var)

        if var.get() == "":
            return

        elif int(var.get()) > limit:
            var.set(limit)

    def only_numeric(self, var):  # Ensure, that value stays numeric
        var.set(re.sub('[^0-9]', '', var.get()).lstrip("0"))


class app:
    def __init__(self, ui):
        self.ui = ui
        self.ui.trim_button.config(command=self.trim)
        self.ui.status.set("idle")

    def trim(self):
        self.ui.status.set("processing")

        # Get timestamps and join them to the H:M:S.MS format
        self.str_time = []
        for i in range(2):
            self.str_time.append(int(self.ui.timestamp[i][0].get() if self.ui.timestamp[i][0].get() != "" else "0")*3600 +
                                 int(self.ui.timestamp[i][1].get() if self.ui.timestamp[i][1].get() != "" else "0")*60 +
                                 int(self.ui.timestamp[i][2].get() if self.ui.timestamp[i][2].get() != "" else "0") +
                                 float("0."+self.ui.timestamp[i][-1].get()))

        # Abort if START > END
        if self.str_time[0] >= self.str_time[1]:
            self.ui.status.set("invalid timestamp")
            return

        # Abort if input file or output filename is missing
        elif self.ui.input.get() == "" or self.ui.output.get() == "":
            self.ui.status.set("missing input/output")
            return

        if self.str_time[1] == 0:  # Set END timestamp to "" if it's 0
            self.to = ""
        else:
            self.to = " -to "+str(self.str_time[1])

        # Compile the ffmpeg command
        self.ffmpeg_command = ('ffmpeg -ss {start}{end} -i "{inpt}" -c:v copy -c:a copy "{outp}"'.format(start=self.str_time[0],
                                                                                                         end=self.to,
                                                                                                         inpt=self.ui.input.get(),
                                                                                                         outp=self.ui.output.get()))
        print(self.ffmpeg_command)
        commands.append(self.ffmpeg_command)


def run_ffmpeg(command):  # Runs a given windows shell command
    t1 = time.perf_counter()
    os.system(command)
    t2 = time.perf_counter()
    print("/n")
    print(f"Command: {command}")
    print(f"Completed in: {datetime.timedelta(seconds=t2-t1)}")


def infinite_run():
    while True:
        while not commands:
            time.sleep(1)
        for _ in range(len(commands)):
            executor.submit(run_ffmpeg, commands.pop())


if __name__ == "__main__":
    commands = []
    executor = concurrent.futures.ThreadPoolExecutor()
    executor.submit(infinite_run)
    app = app(ui())
    app.ui.root.mainloop()
