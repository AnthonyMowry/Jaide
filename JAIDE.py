from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk


APP_VERSION = "TIMECODE CALC"
FRAME_RATES = ("24", "30", "59", "60")

# Deep emerald palette: charcoal-green surfaces with emerald accents.
BG = "#222222"
SURFACE = "#101B17"
CARD = "#14251F"
ENTRY = "#0A1511"
BORDER = "#176B50"
ACCENT = "#059669"
ACCENT_HOVER = "#10B981"
ACCENT_DARK = "#065F46"
TEXT = "#F1F7F4"
MUTED = "#9AAFA6"
WHITE = "#FFFFFF"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class TimecodeInput(ctk.CTkFrame):
    """Compact reusable HH:MM:SS:FF input."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, fg_color="transparent")

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

        validation = (self.register(self._validate_integer), "%P")

        for index, (variable, caption) in enumerate(
            zip(self.variables, ("HH", "MM", "SS", "FF"))
        ):
            column = index * 2

            field = ctk.CTkEntry(
                self,
                textvariable=variable,
                width=49,
                height=37,
                justify="center",
                corner_radius=10,
                border_width=1,
                border_color=BORDER,
                fg_color=ENTRY,
                text_color=TEXT,
                font=ctk.CTkFont(family="Courier New", size=14, weight="bold"),
                validate="key",
                validatecommand=validation,
            )
            field.grid(row=0, column=column, padx=2)
            field.bind(
                "<FocusIn>",
                lambda _event, widget=field: widget.select_range(0, "end"),
            )
            field.bind(
                "<FocusOut>",
                lambda _event, value=variable: self._pad_value(value),
            )

            ctk.CTkLabel(
                self,
                text=caption,
                width=49,
                text_color=MUTED,
                font=ctk.CTkFont(size=9, weight="bold"),
            ).grid(row=1, column=column, pady=(2, 0))

            if index < 3:
                ctk.CTkLabel(
                    self,
                    text=":",
                    width=7,
                    text_color=ACCENT_HOVER,
                    font=ctk.CTkFont(size=15, weight="bold"),
                ).grid(row=0, column=column + 1)

    @staticmethod
    def _validate_integer(proposed_value: str) -> bool:
        return proposed_value == "" or (
            proposed_value.isdigit() and len(proposed_value) <= 2
        )

    @staticmethod
    def _pad_value(variable: tk.StringVar) -> None:
        value = variable.get().strip()
        variable.set("00" if not value else value.zfill(2))

    def get_values(self) -> tuple[int, int, int, int]:
        return tuple(
            int(variable.get().strip()) if variable.get().strip() else 0
            for variable in self.variables
        )  # type: ignore[return-value]

    def to_frames(
        self,
        fps: int,
        hour_format: int,
        field_name: str,
        use_hour_format: bool = True,
    ) -> int:
        hours, minutes, seconds, frames = self.get_values()

        if use_hour_format:
            if hour_format == 12 and not 0 <= hours <= 12:
                raise ValueError(
                    f"{field_name}: hours must be between 00 and 12 "
                    "in 12-hour mode."
                )
            if hour_format == 24 and not 0 <= hours <= 23:
                raise ValueError(
                    f"{field_name}: hours must be between 00 and 23 "
                    "in 24-hour mode."
                )

        if not 0 <= minutes <= 59:
            raise ValueError(f"{field_name}: minutes must be between 00 and 59.")
        if not 0 <= seconds <= 59:
            raise ValueError(f"{field_name}: seconds must be between 00 and 59.")
        if not 0 <= frames < fps:
            raise ValueError(
                f"{field_name}: at {fps} FPS, frames must be between "
                f"00 and {fps - 1:02d}."
            )

        return ((((hours * 60) + minutes) * 60 + seconds) * fps) + frames

    def clear(self) -> None:
        for variable in self.variables:
            variable.set("00")


def frames_to_timecode(total_frames: int, fps: int) -> str:
    sign = "-" if total_frames < 0 else ""
    total_frames = abs(total_frames)

    hours, remainder = divmod(total_frames, 60 * 60 * fps)
    minutes, remainder = divmod(remainder, 60 * fps)
    seconds, frames = divmod(remainder, fps)

    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


class InputRow(ctk.CTkFrame):
    """Compact rounded row containing a label and timecode input."""

    def __init__(self, parent: tk.Misc, title: str) -> None:
        super().__init__(
            parent,
            fg_color=CARD,
            corner_radius=15,
            border_width=1,
            border_color=BORDER,
        )
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            width=95,
            anchor="w",
            text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(14, 6), pady=11, sticky="w")

        self.input = TimecodeInput(self)
        self.input.grid(row=0, column=1, padx=(4, 14), pady=9, sticky="e")


class TimecodeCalculator(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title(f"JAIDE — {APP_VERSION}")
        self.configure(fg_color=BG)
        self.resizable(True, True)
        self.minsize(460, 420)

        self.frame_rate = tk.StringVar(value="30")
        self.operation = tk.StringVar(value="Add")
        self.hour_format = tk.IntVar(value=24)
        self.result = tk.StringVar(value="00:00:00:00")
        self.settings_window: ctk.CTkToplevel | None = None

        self._build_interface()
        self._update_operation_display()

        self.bind("<Return>", lambda _event: self.calculate())
        self.bind("<Escape>", lambda _event: self.clear())
        self.after_idle(self._set_startup_geometry)

        # This makes it immediately obvious which file Python launched.
        print(f"Running {APP_VERSION} from: {Path(__file__).resolve()}")

    def _set_startup_geometry(self) -> None:
        """Set one compact initial size; never auto-resize afterward."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        width = min(570, max(460, screen_width - 80))
        height = min(620, max(440, screen_height - 120))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_interface(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.page = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=ACCENT_DARK,
            scrollbar_button_hover_color=BORDER,
        )
        self.page.grid(row=0, column=0, sticky="nsew")
        self.page.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.page, fg_color="transparent")
        header.grid(row=0, column=0, padx=16, pady=(14, 9), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkFrame(header, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            heading,
            text="JAIDE",
            text_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=27, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            heading,
            text=APP_VERSION.upper(),
            text_color=MUTED,
            font=ctk.CTkFont(size=9, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="Options",
            width=88,
            height=34,
            corner_radius=11,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=BG,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_settings,
        ).grid(row=0, column=1, sticky="e")

        main = ctk.CTkFrame(
            self.page,
            fg_color=SURFACE,
            corner_radius=20,
            border_width=1,
            border_color=ACCENT_DARK,
        )
        main.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")
        main.grid_columnconfigure(0, weight=1)

        controls = ctk.CTkFrame(main, fg_color="transparent")
        controls.grid(row=0, column=0, padx=14, pady=(14, 10), sticky="ew")
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            controls,
            text="FPS",
            text_color=MUTED,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.frame_rate_menu = ctk.CTkOptionMenu(
            controls,
            variable=self.frame_rate,
            values=list(FRAME_RATES),
            width=105,
            height=34,
            corner_radius=10,
            fg_color=ENTRY,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=CARD,
            dropdown_hover_color=ACCENT_DARK,
            dropdown_text_color=TEXT,
            text_color=TEXT,
            dynamic_resizing=False,
        )
        self.frame_rate_menu.grid(row=0, column=1, padx=(0, 12), sticky="w")

        self.operation_selector = ctk.CTkSegmentedButton(
            controls,
            variable=self.operation,
            values=["Add", "Subtract"],
            width=205,
            height=34,
            corner_radius=10,
            border_width=1,
            fg_color=ENTRY,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=ENTRY,
            unselected_hover_color=ACCENT_DARK,
            text_color=WHITE,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._update_operation_display,
        )
        self.operation_selector.grid(row=0, column=2, sticky="e")

        input_area = ctk.CTkFrame(main, fg_color="transparent")
        input_area.grid(row=1, column=0, padx=14, sticky="ew")
        input_area.grid_columnconfigure(0, weight=1)

        self.first_row = InputRow(input_area, "Timecode 1")
        self.first_row.grid(row=0, column=0, pady=(0, 7), sticky="ew")
        self.first_input = self.first_row.input

        self.second_row = InputRow(input_area, "Timecode 2")
        self.second_row.grid(row=1, column=0, pady=7, sticky="ew")
        self.second_input = self.second_row.input

        self.paid_som_row = InputRow(input_area, "Paid SOM")
        self.paid_som_row.grid(row=2, column=0, pady=7, sticky="ew")
        self.paid_som_input = self.paid_som_row.input

        ctk.CTkButton(
            main,
            text="Calculate",
            height=43,
            corner_radius=13,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=BG,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.calculate,
        ).grid(row=2, column=0, padx=14, pady=(12, 9), sticky="ew")

        result_panel = ctk.CTkFrame(
            main,
            fg_color=ENTRY,
            corner_radius=15,
            border_width=2,
            border_color=ACCENT,
        )
        result_panel.grid(row=3, column=0, padx=14, pady=(0, 9), sticky="ew")
        result_panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            result_panel,
            text="RESULT",
            text_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=0, column=0, padx=(14, 8), pady=14, sticky="w")

        ctk.CTkLabel(
            result_panel,
            textvariable=self.result,
            text_color=WHITE,
            font=ctk.CTkFont(family="Courier New", size=20, weight="bold"),
        ).grid(row=0, column=1, padx=(8, 14), pady=14, sticky="e")

        ctk.CTkButton(
            main,
            text="Clear",
            height=35,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#1A2C25",
            border_width=1,
            border_color=ACCENT_DARK,
            text_color=MUTED,
            command=self.clear,
        ).grid(row=4, column=0, padx=14, pady=(0, 14), sticky="ew")

    def _update_operation_display(self, _choice: str | None = None) -> None:
        """Show or hide Paid SOM without touching main-window geometry."""
        if self.operation.get() == "Subtract":
            self.paid_som_row.grid()
        else:
            self.paid_som_row.grid_remove()

    def calculate(self) -> None:
        try:
            fps = int(self.frame_rate.get())
            hour_format = self.hour_format.get()
            first_hours, _, _, _ = self.first_input.get_values()

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
                if (
                    hour_format == 24
                    and first_hours == 0
                    and first_frames < second_frames
                ):
                    first_frames += 24 * 60 * 60 * fps

                if first_frames <= second_frames:
                    raise ValueError(
                        "For subtraction, Timecode 1 must be later "
                        "than Timecode 2."
                    )

                paid_som_frames = self.paid_som_input.to_frames(
                    fps,
                    hour_format,
                    "Paid SOM",
                    use_hour_format=False,
                )
                total_frames = first_frames - second_frames + paid_som_frames

            self.result.set(frames_to_timecode(total_frames, fps))

        except ValueError as error:
            messagebox.showerror("Invalid Timecode", str(error), parent=self)

    def clear(self) -> None:
        self.first_input.clear()
        self.second_input.clear()
        self.paid_som_input.clear()
        self.result.set("00:00:00:00")

    def open_settings(self) -> None:
        """Open options beside the app; never appear centered first."""
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = ctk.CTkToplevel(self)
        self.settings_window = window
        window.withdraw()
        window.title("JAIDE Options")
        window.resizable(False, False)
        window.configure(fg_color=BG)
        window.transient(self)
        window.protocol("WM_DELETE_WINDOW", self._close_settings)

        card = ctk.CTkFrame(
            window,
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=ACCENT,
        )
        card.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(
            card,
            text="Time Format",
            text_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 4))

        temporary_format = tk.StringVar(value=f"{self.hour_format.get()}-hour")

        selector = ctk.CTkSegmentedButton(
            card,
            variable=temporary_format,
            values=["12-hour", "24-hour"],
            height=39,
            corner_radius=11,
            fg_color=ENTRY,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=ENTRY,
            unselected_hover_color=ACCENT_DARK,
            text_color=WHITE,
        )
        selector.pack(fill="x", padx=18, pady=(10, 12))

        ctk.CTkLabel(
            card,
            text=(
                "12-hour: Timecode 1 uses 01–12.\n"
                "24-hour: hours use 00–23.\n"
                "Paid SOM is always a duration."
            ),
            justify="left",
            anchor="w",
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
        ).pack(fill="x", padx=18, pady=(0, 14))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(0, 18))
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            buttons,
            text="Cancel",
            height=37,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#1A2C25",
            border_width=1,
            border_color=ACCENT_DARK,
            text_color=MUTED,
            command=self._close_settings,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Save",
            height=37,
            corner_radius=11,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=BG,
            command=lambda: self.save_settings(temporary_format.get()),
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        window.update_idletasks()
        width = max(350, window.winfo_reqwidth())
        height = window.winfo_reqheight()
        gap = 12

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        right_x = self.winfo_x() + self.winfo_width() + gap
        left_x = self.winfo_x() - width - gap

        if right_x + width <= screen_width - 10:
            x = right_x
        elif left_x >= 10:
            x = left_x
        else:
            x = max(10, min(self.winfo_x(), screen_width - width - 10))

        y = max(10, min(self.winfo_y() + 30, screen_height - height - 50))

        window.geometry(f"{width}x{height}+{x}+{y}")
        window.deiconify()
        window.lift()
        window.grab_set()
        window.focus_force()

    def _close_settings(self) -> None:
        if self.settings_window is not None and self.settings_window.winfo_exists():
            try:
                self.settings_window.grab_release()
            except tk.TclError:
                pass
            self.settings_window.destroy()
        self.settings_window = None

    def save_settings(self, selected_format: str) -> None:
        self.hour_format.set(12 if selected_format == "12-hour" else 24)
        self._close_settings()


if __name__ == "__main__":
    app = TimecodeCalculator()
    app.mainloop()
