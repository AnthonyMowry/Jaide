import tkinter as tk
from tkinter import ttk, messagebox


FRAME_RATES = ("24", "30", "59", "60")


class TimecodeInput(ttk.Frame):
    """A reusable HH:MM:SS:FF timecode input."""

    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.hours = tk.StringVar(value="00")
        self.minutes = tk.StringVar(value="00")
        self.seconds = tk.StringVar(value="00")
        self.frames = tk.StringVar(value="00")

        self.variables = (
            self.hours,
            self.minutes,
            self.seconds,
            self.frames,
        )

        labels = ("HH", "MM", "SS", "FF")

        validation = (
            self.register(self._validate_integer),
            "%P",
        )

        for index, (variable, label_text) in enumerate(
            zip(self.variables, labels)
        ):
            entry_column = index * 2

            entry = ttk.Entry(
                self,
                textvariable=variable,
                width=4,
                justify="center",
                font=("TkFixedFont", 13),
                validate="key",
                validatecommand=validation,
            )
            entry.grid(
                row=0,
                column=entry_column,
                padx=2,
            )

            entry.bind(
                "<FocusIn>",
                lambda _event, widget=entry: widget.select_range(0, "end"),
            )

            entry.bind(
                "<FocusOut>",
                lambda _event, value=variable: self._pad_value(value),
            )

            ttk.Label(
                self,
                text=label_text,
                anchor="center",
            ).grid(
                row=1,
                column=entry_column,
                pady=(3, 0),
            )

            if index < 3:
                ttk.Label(
                    self,
                    text=":",
                    font=("TkFixedFont", 13, "bold"),
                ).grid(
                    row=0,
                    column=entry_column + 1,
                )

    @staticmethod
    def _validate_integer(proposed_value: str) -> bool:
        """
        Allow blank input while editing or an integer containing
        no more than two digits.
        """
        return (
            proposed_value == ""
            or (
                proposed_value.isdigit()
                and len(proposed_value) <= 2
            )
        )

    @staticmethod
    def _pad_value(variable: tk.StringVar) -> None:
        """Convert blank values to 00 and pad single digits."""
        value = variable.get().strip()

        if value == "":
            variable.set("00")
        else:
            variable.set(value.zfill(2))

    def get_values(self) -> tuple[int, int, int, int]:
        """Return the four entered timecode values as integers."""
        values = []

        for variable in self.variables:
            text = variable.get().strip()
            values.append(int(text) if text else 0)

        return tuple(values)

    def to_frames(
            self,
            fps: int,
            hour_format: int,
            field_name: str,
            use_hour_format: bool = True,
        ) -> int:
            """Validate the entered timecode and convert it to frames."""
            hours, minutes, seconds, frames = self.get_values()

            # Only apply the 12/24-hour restriction when requested.
            if use_hour_format:
                if hour_format == 12:
                    if not 0 <= hours <= 12:
                        raise ValueError(
                            f"{field_name}: hours must be between 00 and 12 "
                            "in 12-hour mode."
                        )
                else:
                    if not 0 <= hours <= 23:
                        raise ValueError(
                            f"{field_name}: hours must be between 00 and 23 "
                            "in 24-hour mode."
                        )

            if not 0 <= minutes <= 59:
                raise ValueError(
                    f"{field_name}: minutes must be between 00 and 59."
                )

            if not 0 <= seconds <= 59:
                raise ValueError(
                    f"{field_name}: seconds must be between 00 and 59."
                )

            if not 0 <= frames < fps:
                raise ValueError(
                    f"{field_name}: at {fps} FPS, frames must be between "
                    f"00 and {fps - 1:02d}."
                )

            return (
                (((hours * 60) + minutes) * 60 + seconds)
                * fps
                + frames
            )

    def clear(self) -> None:
        """Reset all four boxes to zero."""
        for variable in self.variables:
            variable.set("00")


def frames_to_timecode(total_frames: int, fps: int) -> str:
    """Convert a total number of frames to HH:MM:SS:FF."""
    sign = "-" if total_frames < 0 else ""
    total_frames = abs(total_frames)

    hours, remainder = divmod(
        total_frames,
        60 * 60 * fps,
    )
    minutes, remainder = divmod(
        remainder,
        60 * fps,
    )
    seconds, frames = divmod(
        remainder,
        fps,
    )

    return (
        f"{sign}{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}:"
        f"{frames:02d}"
    )


class TimecodeCalculator(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Jaide Timecode Calculator")
        self.resizable(False, False)
        self.configure(
            padx=20,
            pady=20,
        )

        self.frame_rate = tk.StringVar(value="30")
        self.operation = tk.StringVar(value="Add")
        self.hour_format = tk.IntVar(value=24)
        self.result = tk.StringVar(value="00:00:00:00")

        self.settings_window = None

        self._build_menu()
        self._build_interface()
        self._update_operation_display()

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)

        options_menu = tk.Menu(
            menu_bar,
            tearoff=False,
        )
        options_menu.add_command(
            label="Settings...",
            command=self.open_settings,
        )

        menu_bar.add_cascade(
            label="Options",
            menu=options_menu,
        )

        self.config(menu=menu_bar)

    def _build_interface(self) -> None:
        title = ttk.Label(
            self,
            text="JAIDE",
            font=("TkDefaultFont", 24, "bold"),
        )
        title.grid(
            row=0,
            column=0,
            columnspan=2,
            pady=(0, 4),
        )

        subtitle = ttk.Label(
            self,
            text="HH:MM:SS:FF",
        )
        subtitle.grid(
            row=1,
            column=0,
            columnspan=2,
            pady=(0, 18),
        )

        ttk.Label(
            self,
            text="Frame Rate",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=6,
        )

        frame_rate_dropdown = ttk.Combobox(
            self,
            textvariable=self.frame_rate,
            values=FRAME_RATES,
            state="readonly",
            width=8,
            justify="center",
        )
        frame_rate_dropdown.grid(
            row=2,
            column=1,
            sticky="w",
            pady=6,
        )

        ttk.Label(
            self,
            text="Operation",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=6,
        )

        operation_dropdown = ttk.Combobox(
            self,
            textvariable=self.operation,
            values=("Add", "Subtract"),
            state="readonly",
            width=12,
            justify="center",
        )
        operation_dropdown.grid(
            row=3,
            column=1,
            sticky="w",
            pady=6,
        )
        operation_dropdown.bind(
            "<<ComboboxSelected>>",
            self._update_operation_display,
        )

        self.first_label = ttk.Label(
            self,
            text="Timecode 1",
        )
        self.first_label.grid(
            row=4,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=8,
        )

        self.first_input = TimecodeInput(self)
        self.first_input.grid(
            row=4,
            column=1,
            sticky="w",
            pady=8,
        )

        self.second_label = ttk.Label(
            self,
            text="Timecode 2",
        )
        self.second_label.grid(
            row=5,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=8,
        )

        self.second_input = TimecodeInput(self)
        self.second_input.grid(
            row=5,
            column=1,
            sticky="w",
            pady=8,
        )

        self.paid_som_label = ttk.Label(
            self,
            text="Paid SOM",
        )
        self.paid_som_label.grid(
            row=6,
            column=0,
            sticky="w",
            padx=(0, 15),
            pady=8,
        )

        self.paid_som_input = TimecodeInput(self)
        self.paid_som_input.grid(
            row=6,
            column=1,
            sticky="w",
            pady=8,
        )

        calculate_button = ttk.Button(
            self,
            text="Calculate",
            command=self.calculate,
            width=16,
        )
        calculate_button.grid(
            row=7,
            column=0,
            columnspan=2,
            pady=(16, 10),
        )

        ttk.Separator(
            self,
            orient="horizontal",
        ).grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=8,
        )

        ttk.Label(
            self,
            text="Result",
        ).grid(
            row=9,
            column=0,
            sticky="w",
            padx=(0, 15),
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
            row=9,
            column=1,
            sticky="w",
            pady=8,
        )

        clear_button = ttk.Button(
            self,
            text="Clear",
            command=self.clear,
            width=12,
        )
        clear_button.grid(
            row=10,
            column=0,
            columnspan=2,
            pady=(12, 0),
        )

        self.bind(
            "<Return>",
            lambda _event: self.calculate(),
        )

    def _update_operation_display(self, _event=None) -> None:
        """Show Paid SOM only when subtraction is selected."""
        if self.operation.get() == "Subtract":
            self.paid_som_label.grid()
            self.paid_som_input.grid()
        else:
            self.paid_som_label.grid_remove()
            self.paid_som_input.grid_remove()

    def calculate(self) -> None:
        try:
            fps = int(self.frame_rate.get())
            hour_format = self.hour_format.get()

            first_hours, _, _, _ = self.first_input.get_values()

            # In 12-hour mode, Timecode 1 must use hours 01 through 12.
            if hour_format == 12 and first_hours == 0:
                raise ValueError(
                    "Timecode 1: hours must be between 01 and 12 "
                    "in 12-hour mode."
                )

            first_frames = self.first_input.to_frames(
                fps,
                hour_format,
                "Timecode 1",
            )

            second_frames = self.second_input.to_frames(
                fps,
                hour_format,
                "Timecode 2",
            )

            if self.operation.get() == "Add":
                total_frames = first_frames + second_frames

            else:
                # In 24-hour mode, 00 in Timecode 1 may mean
                # midnight at the beginning of the next day.
                if (
                    hour_format == 24
                    and first_hours == 0
                    and first_frames < second_frames
                ):
                    frames_per_day = 24 * 60 * 60 * fps
                    first_frames += frames_per_day

                # Check after applying the possible midnight rollover.
                if first_frames <= second_frames:
                    raise ValueError(
                        "For subtraction, Timecode 1 must be later "
                        "than Timecode 2."
                    )

                # Paid SOM is a duration, so the 12/24-hour setting
                # does not restrict its hour value.
                paid_som_frames = self.paid_som_input.to_frames(
                    fps,
                    hour_format,
                    "Paid SOM",
                    use_hour_format=False,
                )

                total_frames = (
                    first_frames
                    - second_frames
                    + paid_som_frames
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
        self.first_input.clear()
        self.second_input.clear()
        self.paid_som_input.clear()
        self.result.set("00:00:00:00")

    def open_settings(self) -> None:
        """Open the separate settings window."""
        if (
            self.settings_window is not None
            and self.settings_window.winfo_exists()
        ):
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self)
        self.settings_window.title("Settings")
        self.settings_window.resizable(False, False)
        self.settings_window.transient(self)
        self.settings_window.grab_set()
        self.settings_window.configure(
            padx=22,
            pady=22,
        )

        temporary_hour_format = tk.IntVar(
            value=self.hour_format.get()
        )

        ttk.Label(
            self.settings_window,
            text="Time Format",
            font=("TkDefaultFont", 13, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 12),
        )

        ttk.Radiobutton(
            self.settings_window,
            text="12-hour",
            variable=temporary_hour_format,
            value=12,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4,
        )

        ttk.Radiobutton(
            self.settings_window,
            text="24-hour",
            variable=temporary_hour_format,
            value=24,
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4,
        )

        description = ttk.Label(
            self.settings_window,
            text=(
                "12-hour mode allows hours from 00–12.\n"
                "24-hour mode allows hours from 00–23."
            ),
            justify="left",
        )
        description.grid(
            row=3,
            column=0,
            sticky="w",
            pady=(10, 18),
        )

        button_frame = ttk.Frame(self.settings_window)
        button_frame.grid(
            row=4,
            column=0,
            sticky="e",
        )

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.settings_window.destroy,
        ).grid(
            row=0,
            column=0,
            padx=(0, 6),
        )

        ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_settings(
                temporary_hour_format.get()
            ),
        ).grid(
            row=0,
            column=1,
        )

    def save_settings(self, selected_format: int) -> None:
        self.hour_format.set(selected_format)

        if (
            self.settings_window is not None
            and self.settings_window.winfo_exists()
        ):
            self.settings_window.destroy()


if __name__ == "__main__":
    app = TimecodeCalculator()
    app.mainloop()