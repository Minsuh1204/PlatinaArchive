from __future__ import annotations

import os
import re
import sys
import time
from typing import Dict, List, Optional

import imagehash
import pytesseract
import requests
from PIL import Image, ImageGrab, ImageOps

# Assuming these are correctly defined in models.py with the 'self' fix
# and AnalysisReport is a simple data class for results.
from models import AnalysisReport, Pattern, Song

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["TESSDATA_PREFIX"] = os.path.join(base_dir, "tesseract", "tessdata")

# --- CONFIGURATION CONSTANTS ---
# Use one dictionary for all ROI ratios for better maintainability.
# The keys correspond to the variable names used in the original code.
# Format: (x_start, y_start, x_end, y_end) or (x, y) for single point.
REF_W, REF_H = 1920, 1080

ROI_CONFIG = {
    # Bounding Boxes (x_start, y_start, x_end, y_end)
    "jacket": (122, 193, 522, 593),
    "judge": (959, 301, 1283, 367),
    "line": (37, 32, 75, 81),
    "level": (395, 700, 502, 762),
    "patch": (979, 186, 1320, 251),
    "score": (953, 418, 1316, 483),
    "notes_area": (874, 0, 950, 0),  # Placeholder for common X
    # Notes Y-Coordinates (start_y, end_y) for fixed X (notes_area)
    "total_notes": (589, 614),
    "perfect_high_y": (650, 675),
    "perfect_y": (686, 713),
    "great_y": (725, 751),
    "good_y": (764, 788),
    "miss_y": (800, 828),
    # Single Points (x, y)
    "difficulty_color": (300, 730),
}

# Use a dictionary for color templates for maintainability
DIFFICULTY_COLORS = {
    "EASY": (254, 179, 26),
    "HARD": (252, 109, 111),
    "OVER": (187, 99, 219),
    "PLUS": (69, 81, 141),
}
COLOR_TOLERANCE = 5  # Use a small tolerance for minor compression changes


# --- CORE ANALYZER CLASS ---


class ScreenshotAnalyzer:
    """
    Manages the data fetching, scaling, OCR, and analysis logic.
    """

    def __init__(self, song_database: List[Song]):
        tesseract_exe_path = os.path.join(base_dir, "tesseract", "tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
        self.song_db: Dict[int, Song] = {song.id: song for song in song_database}
        self.jacket_hash_map: Dict[str, Song] = self._build_jacket_hash_map()
        self.PHASH_THRESHOLD = 5

    # --- Setup Methods ---

    def _build_jacket_hash_map(self) -> Dict[str, Song]:
        """Creates a map of pHash strings to Song objects for quick lookup."""
        hash_map = {}
        for song in self.song_db.values():
            if song.phash:
                hash_map[song.phash] = song
            if song.plus_phash:
                hash_map[song.plus_phash] = song
        return hash_map

    # --- Static Helper Methods ---

    @staticmethod
    def _ratio(x: int, y: int) -> tuple[float, float]:
        """Calculates normalized coordinates relative to 1920x1080."""
        return x / REF_W, y / REF_H

    @staticmethod
    def _scale_coordinate(
        ratio_x: float, ratio_y: float, size: tuple[int, int]
    ) -> tuple[int, int]:
        """Scales normalized coordinates to the current screenshot size."""
        user_width, user_height = size
        abs_x = int(round(user_width * ratio_x))
        abs_y = int(round(user_height * ratio_y))
        return abs_x, abs_y

    def _crop_and_ocr(
        self, img: Image, config_key: str, ocr_func, is_point=False, **kwargs
    ):
        """Helper to handle scaling, cropping, and running OCR."""
        ref_coords = ROI_CONFIG[config_key]
        size = img.size

        if is_point:
            rx, ry = self._ratio(ref_coords[0], ref_coords[1])
            abs_x, abs_y = self._scale_coordinate(rx, ry, size)
            return ocr_func(img, abs_x, abs_y, **kwargs)  # Call color/point function

        # Handle notes area with common X but separate Y
        if config_key in [
            "perfect_high_y",
            "perfect_y",
            "great_y",
            "good_y",
            "miss_y",
            "total_notes",
        ]:
            notes_x = ROI_CONFIG["notes_area"]
            rx0, rxf = self._ratio(notes_x[0], 0)[0], self._ratio(notes_x[2], 0)[0]
            ry0, ryf = (
                self._ratio(0, ref_coords[0])[1],
                self._ratio(0, ref_coords[1])[1],
            )
        else:
            # Bounding box logic
            rx0, ry0 = self._ratio(ref_coords[0], ref_coords[1])
            rxf, ryf = self._ratio(ref_coords[2], ref_coords[3])

        abs_x0, abs_y0 = self._scale_coordinate(rx0, ry0, size)
        abs_xf, abs_yf = self._scale_coordinate(rxf, ryf, size)

        crop = img.crop((abs_x0, abs_y0, abs_xf, abs_yf))
        return ocr_func(crop, **kwargs)

    # --- OCR / Matching Functions (Moved from global scope) ---

    def get_best_match_song(
        self, target_hash: imagehash.ImageHash
    ) -> tuple[Optional[Song], int]:
        """Finds the Song object corresponding to the target pHash."""
        min_distance = float("inf")
        best_match_song = None

        for phash_str, song_obj in self.jacket_hash_map.items():
            # Tesseract 5 hash format is used for consistency
            ref_hash = imagehash.hex_to_hash(phash_str)
            distance = target_hash - ref_hash

            if distance < min_distance:
                min_distance = distance
                best_match_song = song_obj
        return best_match_song, min_distance

    @staticmethod
    def get_ocr_judge(img_crop: Image.Image) -> float:
        """OCR for judge percentage (e.g., 99.0000%)."""
        # Fix: Char whitelist spelling
        ocr_config = r"--psm 7 -c tessedit_char_whitelist=0123456789.%"
        text = pytesseract.image_to_string(img_crop, config=ocr_config).strip()

        # Cleanup and convert to float
        text = text.replace("%", "")
        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def get_ocr_line(img_crop: Image.Image) -> int:
        """OCR for line count (4, 6). If no text, assume 6."""
        # Whitelist 4, 6, and 8
        ocr_config = r"--psm 7 -c tessedit_char_whitelist=46"
        text = pytesseract.image_to_string(img_crop, config=ocr_config).strip()

        # Fallback logic: if OCR is empty, assume 6 (a common game logic)
        try:
            return int(text)
        except ValueError:
            return 6

    @staticmethod
    def get_ocr_integer(img_crop: Image.Image, do_invert: bool = False) -> int:
        """OCR for pure integer values (Level, Score, Notes)."""
        # Upscale and make image bw for better ocr result
        img_crop = ScreenshotAnalyzer._upscale_and_convert_image_bw(img_crop)
        if do_invert:
            img_crop = ImageOps.invert(img_crop)
        config = "--psm 7 --oem 1 -c tessedit_char_whitelist=0123456789"
        text = pytesseract.image_to_string(img_crop, config=config).strip()
        try:
            return int(text)
        except ValueError:
            print(f"Error when converting the text to str: '{text}'")
            img_crop.show()
            return 0

    @staticmethod
    def get_ocr_patch(img_crop: Image.Image) -> float:
        """OCR for patch value (e.g., 2.79)."""
        config = r"--psm 7 -c tessedit_char_whitelist=0123456789.+"
        text = (
            pytesseract.image_to_string(img_crop, config=config)
            .strip()
            .replace("+", "")
        )

        # Post-processing fix for patch if the decimal is missed
        if not "." in text and len(text) >= 3:
            text = text[: len(text) - 2] + "." + text[-2:]

        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def get_difficulty(r: int, g: int, b: int) -> str:
        """Identifies difficulty based on RGB color match."""
        target_rgb = (r, g, b)
        for difficulty, color in DIFFICULTY_COLORS.items():
            # Simple tolerance check for each channel
            if all(abs(target_rgb[i] - color[i]) <= COLOR_TOLERANCE for i in range(3)):
                return difficulty
        return "UNKNOWN"

    @staticmethod
    def calculate_judge_rate(ph: int, p: int, g: int, d: int, m: int) -> float:
        """Calculates Judge Rate (Accuracy) percentage."""
        # Total Judge Points = (PH + P) * 100 + Great * 70 + Good * 30 + Miss * 0
        total_judge = (ph + p) * 100 + g * 70 + d * 30
        total_notes = ph + p + g + d + m
        return round(
            total_judge / total_notes, 4
        )  # Returns a percentage (0.0 to 100.0)

    @staticmethod
    def calculate_score(perfect_high: int, perfect: int, great: int):
        return 200 * perfect_high + 150 * perfect + 100 * great

    @staticmethod
    def calculate_rank(judge_rate: float) -> str:
        """Calculates rank based on judge rate."""
        if judge_rate >= 99.8:
            return "SS+"
        elif judge_rate >= 99.5:
            return "SS"
        elif judge_rate >= 99:
            return "S+"
        elif judge_rate >= 98:
            return "S"
        elif judge_rate >= 97:
            return "AA+"
        elif judge_rate >= 95:
            return "AA"
        elif judge_rate >= 90:
            return "A+"
        elif judge_rate >= 80:
            return "A"
        elif judge_rate >= 70:
            return "B"
        else:
            return "C"

    @staticmethod
    def calculate_patch(level: int, rank: str, is_plus: bool, judge: float) -> float:
        """Calculates the P.A.T.C.H. value."""
        rank_ratio = {
            "C": 0.2,
            "B": 0.3,
            "A": 0.4,
            "A+": 0.5,
            "AA": 0.6,
            "AA+": 0.7,
            "S": 0.8,
            "S+": 0.9,
            "SS": 0.95,
            "SS+": 1,
        }

        if rank == "F":
            return 0.0  # Handle case not in rank_ratio

        patch_base = level * 42 * (judge / 100) * rank_ratio[rank]
        if is_plus:
            patch_base *= 1.02

        # The game often rounds this value to two decimal places
        return round(patch_base, 2)

    @staticmethod
    def verify_notes_count(
        total: int, perfect_high: int, perfect: int, great: int, good: int, miss: int
    ):
        if total == perfect_high + perfect + great + good + miss:
            return perfect_high, perfect, great, good, miss
        elif perfect_high > total:
            perfect_high = total - (perfect + great + good + miss)
        elif perfect > total:
            perfect = total - (perfect_high + great + good + miss)
        elif great > total:
            great = total - (perfect_high + perfect + good + miss)
        elif good > total:
            good = total - (perfect_high + perfect + great + miss)
        else:
            miss = total - (perfect_high + perfect + great + good)
        return perfect_high, perfect, great, good, miss

    @staticmethod
    def _upscale_and_convert_image_bw(img: Image):
        resized_img = img.resize(
            (img.width * 4, img.height * 4), Image.Resampling.LANCZOS
        )
        grayscale_img = resized_img.convert("L")
        bw_img = grayscale_img.point(lambda x: 255 if x > 200 else 0, "1")
        return bw_img

    # --- Main Execution Method ---
    def extract_info(self, image_path: str | None = None) -> AnalysisReport:
        """Main method to analyze a screenshot and return a structured report."""
        try:
            if image_path:
                img = Image.open(image_path)
            else:
                # Try to read image from clipboard
                img = ImageGrab.grabclipboard()
        except FileNotFoundError:
            print(f"Error: File not found at {image_path}")
            return AnalysisReport(song_name="FILE NOT FOUND")

        if img is None:
            print("Error: Clipboard is empty or does not contain an image.")
            # Return an empty report to prevent the crash
            return AnalysisReport(song_name="NO IMAGE")

        # --- 1. jacket and Song Match ---
        jacket_crop = self._crop_and_ocr(
            img, "jacket", lambda x: x
        )  # Pass crop back as PIL Image
        jacket_hash = imagehash.phash(jacket_crop)
        matched_song, match_distance = self.get_best_match_song(jacket_hash)

        # --- 2. OCR Extraction ---
        # Note: 'good' corresponds to the 'good' count in the stats.
        judge_rate_ocr = self._crop_and_ocr(img, "judge", self.get_ocr_judge)
        lines = self._crop_and_ocr(img, "line", self.get_ocr_line)
        level_ocr = self._crop_and_ocr(img, "level", self.get_ocr_integer, do_invert=True)
        patch_ocr = self._crop_and_ocr(img, "patch", self.get_ocr_patch)
        score_ocr = self._crop_and_ocr(img, "score", self.get_ocr_integer)
        total_notes = self._crop_and_ocr(img, "total_notes", self.get_ocr_integer)
        perfect_high = self._crop_and_ocr(img, "perfect_high_y", self.get_ocr_integer)
        perfect = self._crop_and_ocr(img, "perfect_y", self.get_ocr_integer)
        great = self._crop_and_ocr(img, "great_y", self.get_ocr_integer)
        good = self._crop_and_ocr(img, "good_y", self.get_ocr_integer)
        miss = self._crop_and_ocr(img, "miss_y", self.get_ocr_integer)
        perfect_high, perfect, great, good, miss = self.verify_notes_count(
            total_notes, perfect_high, perfect, great, good, miss
        )

        # --- 3. Difficulty Color Check ---
        r, g, b = img.getpixel(
            self._scale_coordinate(
                *self._ratio(*ROI_CONFIG["difficulty_color"]), img.size
            )
        )
        difficulty_str = self.get_difficulty(r, g, b)
        is_plus_difficulty = difficulty_str == "PLUS"

        # --- 4. Calculation ---
        calculated_judge_rate = self.calculate_judge_rate(
            perfect_high, perfect, great, good, miss
        )
        calculated_score = self.calculate_score(perfect_high, perfect, great)
        calculated_rank = self.calculate_rank(calculated_judge_rate)

        level_int = level_ocr
        calculated_patch = self.calculate_patch(
            level_int, calculated_rank, is_plus_difficulty, calculated_judge_rate
        )
        available_levels = matched_song.get_available_levels(lines, difficulty_str)
        if len(available_levels) == 1:
            level_int = available_levels[0]

        is_full_combo = miss == 0
        is_perfect_decode = calculated_judge_rate == 100

        # --- 5. Return Structured Report ---
        return AnalysisReport(
            matched_song,
            calculated_score,
            calculated_judge_rate,
            calculated_patch,
            lines,
            difficulty_str,
            level_int,
            jacket_crop,
            jacket_hash,
            match_distance,
            calculated_rank,
            is_full_combo,
            is_perfect_decode,
        )


# --- INITIALIZATION AND EXECUTION ---


def fetch_songs():
    """Fetches song and pattern data from the API."""
    songs_endpoint = "https://www.endeavy.dev/api/public/platina_songs"
    patterns_endpoint = "https://www.endeavy.dev/api/public/platina_patterns"

    # Use POST method and check status
    res_songs = requests.post(songs_endpoint)
    res_patterns = requests.post(patterns_endpoint)
    res_songs.raise_for_status()
    res_patterns.raise_for_status()

    songs_json = res_songs.json()
    patterns_json = res_patterns.json()

    # Build the Song objects
    songs = {}
    for song_data in songs_json:
        # Assuming Song.__init__ is fixed to accept 'self' and correct keys
        song = Song(
            song_id=song_data.get("songID"),
            title=song_data.get("title"),
            artist=song_data.get("artist", "").strip(),
            bpm=song_data.get("BPM"),
            dlc=song_data.get("DLC"),
            phash=song_data.get("pHash"),
            plus_phash=song_data.get("plusPHash"),
        )
        songs[song.id] = song

    # Link Patterns to Songs
    for pattern_data in patterns_json:
        song_id = pattern_data.get("songID")
        if song_id in songs:
            pattern = Pattern(
                line=pattern_data.get("line"),
                difficulty=pattern_data.get("difficulty"),
                level=pattern_data.get("level"),
                designer=pattern_data.get("designer"),
            )
            songs[song_id].add_pattern(pattern)
        # Warning print statement removed for cleaner refactor

    return list(songs.values())


if __name__ == "__main__":
    # 1. Fetch data once at startup
    song_data = None
    while not song_data:
        try:
            song_data = fetch_songs()
        except requests.exceptions.RequestException as e:
            time.sleep(0.5)  # Try again after 0.5s

    # 2. Initialize the analyzer
    analyzer = ScreenshotAnalyzer(song_data)

    # 3. Process screenshots
    ref = os.listdir("example")
    for r in ref:
        print(f"Processing: {r}")
        report = analyzer.extract_info(f"example/{r}")
        print(
            f"{report.song.title} - {report.song.artist} | {report.line}L {report.difficulty} Lv.{report.level}"
        )
        print(f"Judge: {report.judge}")
        print(f"Score: {report.score}")
        print(f"P.A.T.C.H: {report.patch}")
        print("\n\n\n")
