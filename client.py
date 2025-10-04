import time
import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from analyzer import ScreenshotAnalyzer, fetch_songs
from models import AnalysisReport


class PlatinaArchiveClient:
    def __init__(self, app):
        self.app = app
        app.title("PLATiNA::ARCHIVE Client v0.0.1")
        app.geometry("800x600")
        app.resizable(False, False)

        app.configure(bg="#E0E0E0")

        self.analyzer = None

        self.top_frame = ttk.Frame(app, style="Top.TFrame")
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.title_label = ttk.Label(self.top_frame, text="Test")

        self.main_content_frame = ttk.Frame(app, style="Main.TFrame")
        self.main_content_frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5
        )

        self.jacket_canvas = tk.Canvas(
            self.main_content_frame,
            width=200,
            height=200,
            bg="white",
            relief=tk.SOLID,
            bd=1,
        )
        self.jacket_canvas.grid(
            row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nw"
        )
        self.jacket_photo = None  # For PhotoImage object

        # Info Labels Frame
        self.info_frame = ttk.Frame(self.main_content_frame, style="Info.TFrame")
        self.info_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nwe")
        self.info_frame.grid_columnconfigure(0, weight=1)  # Allow info frame to expand

        # Song Name
        self.song_name_label = ttk.Label(
            self.info_frame, text="Song Name: N/A", font=("Segoe UI", 12, "bold")
        )
        self.song_name_label.pack(anchor="w", pady=2)

        # Judge Rate
        self.judge_rate_label = ttk.Label(self.info_frame, text="Judge: N/A")
        self.judge_rate_label.pack(anchor="w", pady=2)

        # Lines and Difficulty (can be on one line or separate)
        self.lines_diff_label = ttk.Label(self.info_frame, text="Lines: N/A, Diff: N/A")
        self.lines_diff_label.pack(anchor="w", pady=2)

        # --- Log Output Frame (mimics the lower section) ---
        self.log_frame = ttk.Frame(app, style="Log.TFrame")
        self.log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_text = tk.Text(
            self.log_frame,
            wrap=tk.WORD,
            height=10,
            font=("Consolas", 9),
            bg="#F0F0F0",
            fg="black",
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)

        # --- Button for Triggering Analysis ---
        self.analyze_button = ttk.Button(
            app, text="Analyze Screenshot (Alt+Insert)", command=self.run_analysis
        )
        self.analyze_button.pack(side=tk.BOTTOM, pady=5)

        app.bind("<Alt-Insert>", self.run_analysis)

        self.log_message(
            "App started. Press Alt+PrtSc and then Alt-Inert to run analysis or press button"
        )

        # --- Button for reloading song DB ---
        self.reload_db_button = ttk.Button(
            app, text="Reload song DB", command=self.load_db
        )
        self.reload_db_button.pack(side=tk.BOTTOM, pady=5)
        self.load_db()

    def load_db(self):
        # Fetch song data
        song_data = None
        while not song_data:
            try:
                song_data = fetch_songs()
            except:
                time.sleep(0.5)  # Try again after 0.5s
        self.log_message(f"{len(song_data)} songs loaded")
        self.analyzer = ScreenshotAnalyzer(song_data)

    def log_message(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def update_display(self, report: AnalysisReport):
        # Size: 400x400
        resized_jacket_image = report.jacket_image.resize((200, 200))
        self.jacket_photo = ImageTk.PhotoImage(resized_jacket_image)
        self.jacket_canvas.delete("all")
        self.jacket_canvas.create_image(
            100, 100, image=self.jacket_photo, anchor=tk.CENTER
        )

        # Update labels
        self.song_name_label.config(text=report.song.title)
        self.judge_rate_label.config(text=f"{report.judge}%")
        self.lines_diff_label.config(
            text=f"{report.line}L {report.difficulty} Lv.{report.level}"
        )

        # Log results
        self.log_message("--- Analysis Complete ---")
        self.log_message(str(report))
        self.log_message(f"Read hash: {report.jacket_hash}")
        if report.match_distance > 5:
            self.log_message(
                f"Warning: Jacket match distance {report.match_distance} is high. Result might be uncertain."
            )
        # Do sanity check for ocr-read level
        if not report.level in report.song.get_available_levels(report.line, report.difficulty):
            self.log_message(
                f"Warning: Level {report.level} is NOT registered on DB. Result might be uncertain."
            )

    def run_analysis(self, event=None):
        self.log_message("Reading clipboard for image...")
        report = self.analyzer.extract_info()
        self.update_display(report)


if __name__ == "__main__":
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Top.TFrame", background="#E0E0E0")
    style.configure("Main.TFrame", background="#F8F8F8")
    style.configure("Info.TFrame", background="#F8F8F8")
    style.configure("Log.TFrame", background="#E0E0E0")
    style.configure("TCheckbutton", background="#E0E0E0")

    client = PlatinaArchiveClient(root)
    root.mainloop()