import tkinter as tk
from tkinter import ttk, messagebox


def validate_frame_rate(frame_rate_text: str) -> int:
    """Validate and return the selected frame rate."""
    try:
        frame_rate = int(frame_rate_text)
    except ValueError as exc:
        raise ValueError("Frame rate must be a whole number.") from exc

    if frame_rate <= 0:
        raise ValueError("Frame rate must be greater than zero.")

    return frame_rate


def timecode_to_frames(timecode: str, fps: int) -> int:
    """Convert HH:MM:SS:FF timecode to total frames."""
    parts = timecode.strip().split(":")

    if len(parts) != 4:
        raise ValueError("Use the format HH:MM:SS:FF.")

    try:
        hours, minutes, seconds, frames = (
            int(part) for part in parts
        )
    except ValueError as exc:
        raise ValueError(
            "Timecode values must be whole numbers."
        ) from exc

    if min(hours, minutes, seconds, frames) < 0:
        raise ValueError(
            "Enter positive values only. "
            "Subtraction may produce a negative result."
        )

    if minutes >= 60:
        raise ValueError("Minutes must be between 0 and 59.")

    if seconds >= 60:
        raise ValueError("Seconds must be between 0 and 59.")

    if frames >= fps:
        raise ValueError(
            f"At {fps} FPS, frames must be between 0 and {fps - 1}."
        )

    return (((hours * 60) + minutes) * 60 + seconds) * fps + frames


def frames_to_timecode(total_frames: int, fps: int) -> str:
    """Convert total frames to normalized HH:MM:SS:FF timecode."""
    sign = "-" if total_frames < 0 else ""
    total_frames = abs(total_frames)

    hours, remainder = divmod(total_frames, 60 * 60 * fps)
    minutes, remainder = divmod(remainder, 60 * fps)
    seconds, frames = divmod(remainder, fps)

    return (
        f"{sign}{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}:"
        f"{frames:02d}"
    )


class TimecodeCalculator(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("JAIDE")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        self.frame_rate = tk.StringVar(value="30")
        self.first_timecode = tk.StringVar(value="00:00:00:00")
        self.second_timecode = tk.StringVar(value="00:00:00:00")
        self.third_timecode = tk.StringVar(value="00:00:00:00")
        self.result = tk.StringVar(value="00:00:00:00")

        self._build_interface()

    def _build_interface(self) -> None:
        title = ttk.Label(
            self,
            text="JAIDE",
            font=("TkDefaultFont", 24, "bold"),
        )
        title.grid(
            row=0,
            column=0,
            columnspan=3,
            pady=(0, 4),
        )

        subtitle = ttk.Label(
            self,
            text="HH:MM:SS:FF",
        )
        subtitle.grid(
            row=1,
            column=0,
            columnspan=3,
            pady=(0, 14),
        )

        ttk.Label(self, text="Frame Rate").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        frame_rate_dropdown = ttk.Combobox(
            self,
            textvariable=self.frame_rate,
            values=("24", "30", "59", "60"),
            state="readonly",
            width=8,
            justify="center",
            font=("TkFixedFont", 13),
        )

        frame_rate_dropdown.grid(
            row=2,
            column=1,
            columnspan=2,
            pady=6,
        )

        ttk.Label(self, text="Timecode 1").grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        first_entry = ttk.Entry(
            self,
            textvariable=self.first_timecode,
            width=18,
            justify="center",
            font=("TkFixedFont", 13),
        )
        first_entry.grid(
            row=3,
            column=1,
            columnspan=2,
            pady=6,
        )

        ttk.Label(self, text="Timecode 2").grid(
            row=4,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        second_entry = ttk.Entry(
            self,
            textvariable=self.second_timecode,
            width=18,
            justify="center",
            font=("TkFixedFont", 13),
        )
        second_entry.grid(
            row=4,
            column=1,
            columnspan=2,
            pady=6,
        )

        ttk.Label(self, text="Paid SOM").grid(
            row=5,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=6,
        )

        third_entry = ttk.Entry(
            self,
            textvariable=self.third_timecode,
            width=18,
            justify="center",
            font=("TkFixedFont", 13),
        )
        third_entry.grid(
            row=5,
            column=1,
            columnspan=2,
            pady=6,
        )

        add_button = ttk.Button(
            self,
            text="Add",
            command=lambda: self.calculate("add"),
            width=12,
        )
        add_button.grid(
            row=6,
            column=1,
            padx=(0, 5),
            pady=(14, 10),
        )

        subtract_button = ttk.Button(
            self,
            text="Subtract",
            command=lambda: self.calculate("subtract"),
            width=12,
        )
        subtract_button.grid(
            row=6,
            column=2,
            padx=(5, 0),
            pady=(14, 10),
        )

        ttk.Separator(
            self,
            orient="horizontal",
        ).grid(
            row=7,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=8,
        )

        ttk.Label(self, text="Result").grid(
            row=8,
            column=0,
            sticky="w",
            padx=(0, 10),
            pady=8,
        )

        result_label = ttk.Label(
            self,
            textvariable=self.result,
            anchor="center",
            width=17,
            font=("TkFixedFont", 15, "bold"),
        )
        result_label.grid(
            row=8,
            column=1,
            columnspan=2,
            pady=8,
        )

        clear_button = ttk.Button(
            self,
            text="Clear",
            command=self.clear,
        )
        clear_button.grid(
            row=9,
            column=1,
            columnspan=2,
            padx=5,
            pady=(12, 0),
        )

        first_entry.focus_set()

        self.bind(
            "<Return>",
            lambda _event: self.calculate("add"),
        )

    def calculate(self, operation: str) -> None:
        try:
            fps = validate_frame_rate(self.frame_rate.get())

            first_frames = timecode_to_frames(
                self.first_timecode.get(),
                fps,
            )
            second_frames = timecode_to_frames(
                self.second_timecode.get(),
                fps,
            )
            third_frames = timecode_to_frames(
                self.third_timecode.get(),
                fps,
            )

            if operation == "add":
                total_frames = first_frames + second_frames
            else:
                total_frames = (
                    first_frames
                    - second_frames
                    + third_frames
                )

            self.result.set(
                frames_to_timecode(total_frames, fps)
            )

        except ValueError as error:
            messagebox.showerror(
                "Invalid Timecode",
                str(error),
            )

    def clear(self) -> None:
        self.first_timecode.set("00:00:00:00")
        self.second_timecode.set("00:00:00:00")
        self.third_timecode.set("00:00:00:00")
        self.result.set("00:00:00:00")


if __name__ == "__main__":
    app = TimecodeCalculator()
    app.mainloop()