from __future__ import annotations

from typing import Literal

from PIL import Image
from imagehash import ImageHash


class AnalysisReport:
    def __init__(
            self,
            song: Song,
            score: int,
            judge: float,
            patch: float,
            line: Literal[4, 6],
            difficulty: Literal["EASY", "HARD", "OVER", "PLUS"],
            level: int,
            jacket_image: Image,
            jacket_hash: ImageHash,
            match_distance,
    ):
        self._song = song
        self._score = score
        self._judge = judge
        self._patch = patch
        self._line = line
        self._difficulty = difficulty
        self._level = level
        self._jacket_image = jacket_image
        self._jacket_hash = jacket_hash
        self._match_distance = match_distance

    def __str__(self):
        return f"{self.song.title} - {self.song.artist} | {self.line}L {self.difficulty} Lv.{self.level}\nJudge: {self.judge}%\nScore: {self.score}\nP.A.T.C.H.: {self.patch}"

    @property
    def song(self):
        return self._song

    @property
    def score(self):
        return self._score

    @property
    def judge(self):
        return self._judge

    @property
    def patch(self):
        return self._patch

    @property
    def line(self):
        return self._line

    @property
    def difficulty(self):
        return self._difficulty

    @property
    def level(self):
        return self._level

    @property
    def jacket_image(self):
        return self._jacket_image

    @property
    def jacket_hash(self):
        return self._jacket_hash

    @property
    def match_distance(self):
        return self._match_distance


class Pattern:
    def __init__(
            self,
            line: Literal[4, 6],
            difficulty: Literal["EASY", "HARD", "OVER", "PLUS"],
            level: int,
            designer: str,
    ):
        self._line = line
        self._difficulty = difficulty
        self._level = level
        self._designer = designer

    @property
    def line(self):
        return self._line

    @property
    def difficulty(self):
        return self._difficulty

    @property
    def level(self):
        return self._level

    @property
    def designer(self):
        return self._designer


class Song:
    def __init__(
            self,
            song_id: int,
            title: str,
            artist: str,
            bpm: str,
            dlc: str,
            phash: str | None,
            plus_phash: str | None,
    ):
        self._id = song_id
        self._title = title
        self._artist = artist
        self._bpm = bpm
        self._dlc = dlc
        self._phash = phash
        self._plus_phash = plus_phash
        self._patterns: list[Pattern] = []

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @property
    def artist(self):
        return self._artist

    @property
    def bpm(self):
        return self._bpm

    @property
    def dlc(self):
        return self._dlc

    @property
    def phash(self):
        return self._phash

    @property
    def plus_phash(self):
        return self._plus_phash

    @property
    def patterns(self):
        return self._patterns

    def add_pattern(self, pattern: Pattern):
        self._patterns.append(pattern)

    def get_available_levels(self, line: Literal[4, 6], difficulty: Literal["EASY", "HARD", "OVER", "PLUS"]) -> list[
        int]:
        levels = []
        for pattern in self._patterns:
            if pattern.line == line and pattern.difficulty == difficulty:
                levels.append(pattern.level)
        return levels


if __name__ == "__main__":
    pass
