import tkinter as tk
from tkinter import ttk, messagebox

FPS = 30


def timecode_to_frames(timecode: str) -> int:
    """Convert HH:MM:SS:FF timecode to total frames."""
    parts = timecode.strip().split(":")

    if len(parts) != 4:
        raise ValueError("Use the format HH:MM:SS:FF.")

    try:
        hours, minutes, seconds, frames = (int(part) for part in parts)
    except ValueError as exc:
        raise ValueError("Timecode values must be whole numbers.") from exc

    if min(hours, minutes, seconds, frames) < 0:
        raise ValueError("Enter positive values only. Subtraction may produce a negative result.")
    if minutes >= 60:
        raise ValueError("Minutes must be between 0 and 59.")
    if seconds >= 60:
        raise ValueError("Seconds must be between 0 and 59.")
    if frames >= FPS:
        raise ValueError(f"Frames must be between 0 and {FPS - 1}.")

    return (((hours * 60) + minutes) * 60 + seconds) * FPS + frames


def frames_to_timecode(total_frames: int) -> str:
    """Convert total frames to normalized HH:MM:SS:FF timecode."""
    sign = "-" if total_frames < 0 else ""
    total_frames = abs(total_frames)

    hours, remainder = divmod(total_frames, 60 * 60 * FPS)
    minutes, remainder = divmod(remainder, 60 * FPS)
    seconds, frames = divmod(remainder, FPS)

    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


class TimecodeCalculator(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("30 FPS Timecode Calculator")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        self.first_timecode = tk.StringVar(value="00:00:00:00")
        self.second_timecode = tk.StringVar(value="00:00:00:00")
        self.third_timecode = tk.StringVar(value="00:00:00:00")
        self.result = tk.StringVar(value="00:00:00:00")

        self._build_interface()

    def _build_interface(self) -> None:
        title = ttk.Label(
            self,
            text="Timecode Calculator",
            font=("TkDefaultFont", 16, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 4))

        subtitle = ttk.Label(self, text="30 frames per second • HH:MM:SS:FF")
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 18))

        ttk.Label(self, text="Timecode 1").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=6
        )
        first_entry = ttk.Entry(
            self,
            textvariable=self.first_timecode,
            width=18,
            justify="center",
            font=("TkFixedFont", 13),
        )
        first_entry.grid(row=2, column=1, columnspan=2, pady=6)

        ttk.Label(self, text="Timecode 2").grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=6
        )
        second_entry = ttk.Entry(
            self,
            textvariable=self.second_timecode,
            width=18,
            justify="center",
            font=("TkFixedFont", 13),
        )
        second_entry.grid(row=3, column=1, columnspan=2, pady=6)

        ttk.Label(self, text="Paid SOM").grid(
            row=4, column=0, sticky="w", padx=(0, 10), pady=6
        )
        third_entry = ttk.Entry(
            self,
            textvariable=self.third_timecode,
            width=18,
            justify="center",
            font=("TkFixedFont", 13),
        )
        third_entry.grid(row=4, column=1, columnspan=2, pady=6)

        add_button = ttk.Button(
            self,
            text="Add",
            command=lambda: self.calculate("add"),
            width=12,
        )
        add_button.grid(row=5, column=1, padx=(0, 5), pady=(14, 10))

        subtract_button = ttk.Button(
            self,
            text="Subtract",
            command=lambda: self.calculate("subtract"),
            width=12,
        )
        subtract_button.grid(row=5, column=2, padx=(5, 0), pady=(14, 10))

        ttk.Separator(self, orient="horizontal").grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=8
        )

        ttk.Label(self, text="Result").grid(
            row=7, column=0, sticky="w", padx=(0, 10), pady=8
        )
        result_label = ttk.Label(
            self,
            textvariable=self.result,
            anchor="center",
            width=17,
            font=("TkFixedFont", 15, "bold"),
        )
        result_label.grid(row=7, column=1, columnspan=2, pady=8)

        clear_button = ttk.Button(self, text="Clear", command=self.clear)
        clear_button.grid(
            row=8,
            column=1,
            columnspan=2,
            padx=5,
            pady=(12, 0)
        )

        first_entry.focus_set()
        self.bind("<Return>", lambda _event: self.calculate("add"))

    def calculate(self, operation: str) -> None:
        try:
            first_frames = timecode_to_frames(self.first_timecode.get())
            second_frames = timecode_to_frames(self.second_timecode.get())
            third_frames = timecode_to_frames(self.third_timecode.get())


            if operation == "add":
                total_frames = first_frames + second_frames
            else:
                total_frames = first_frames - second_frames + third_frames

            self.result.set(frames_to_timecode(total_frames))
        except ValueError as error:
            messagebox.showerror("Invalid Timecode", str(error))

    def clear(self) -> None:
        self.first_timecode.set("00:00:00:00")
        self.second_timecode.set("00:00:00:00")
        self.result.set("00:00:00:00")


if __name__ == "__main__":
    app = TimecodeCalculator()
    app.mainloop()
