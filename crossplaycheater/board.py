"""Scrabble board data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

BOARD_SIZE = 15


@dataclass
class Cell:
    """
    Represents a single cell on the Scrabble board.

    :param letter: The letter in this cell, or None if empty.
    :param is_blank: Whether this is a blank tile (wildcard).
    """

    letter: str | None = None
    is_blank: bool = False

    def __str__(self) -> str:
        if self.letter is None:
            return "."
        return self.letter.lower() if self.is_blank else self.letter.upper()


@dataclass
class ScrabbleBoard:
    """
    Represents a 15x15 Scrabble board.

    :param grid: 2D list of Cell objects representing the board state.
    """

    grid: list[list[Cell]] = field(default_factory=lambda: [
        [Cell() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
    ])

    @classmethod
    def from_strings(cls, rows: list[str]) -> ScrabbleBoard:
        """
        Create a board from a list of 15 strings.

        :param rows: List of 15 strings, each 15 characters. Use '.' for empty,
                     uppercase for normal tiles, lowercase for blank tiles.
        :returns: A new ScrabbleBoard instance.
        :raises ValueError: If input dimensions are incorrect.
        """
        if len(rows) != BOARD_SIZE:
            raise ValueError(f"Expected {BOARD_SIZE} rows, got {len(rows)}")

        board = cls()
        for row_idx, row in enumerate(rows):
            if len(row) != BOARD_SIZE:
                raise ValueError(
                    f"Row {row_idx} has {len(row)} chars, expected {BOARD_SIZE}"
                )
            for col_idx, char in enumerate(row):
                if char == ".":
                    continue
                board.grid[row_idx][col_idx] = Cell(
                    letter=char.upper(),
                    is_blank=char.islower(),
                )
        return board

    def get(self, row: int, col: int) -> Cell:
        """
        Get the cell at the specified position.

        :param row: Row index (0-14).
        :param col: Column index (0-14).
        :returns: The Cell at that position.
        """
        return self.grid[row][col]

    def set(self, row: int, col: int, letter: str | None, is_blank: bool = False) -> None:
        """
        Set a letter at the specified position.

        :param row: Row index (0-14).
        :param col: Column index (0-14).
        :param letter: The letter to place, or None to clear.
        :param is_blank: Whether this is a blank tile.
        """
        self.grid[row][col] = Cell(
            letter=letter.upper() if letter else None,
            is_blank=is_blank,
        )

    def is_empty(self, row: int, col: int) -> bool:
        """
        Check if a cell is empty.

        :param row: Row index (0-14).
        :param col: Column index (0-14).
        :returns: True if the cell has no letter.
        """
        return self.grid[row][col].letter is None

    def iter_cells(self) -> Iterator[tuple[int, int, Cell]]:
        """
        Iterate over all cells with their coordinates.

        :returns: Iterator yielding (row, col, cell) tuples.
        """
        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                yield row_idx, col_idx, cell

    def to_strings(self) -> list[str]:
        """
        Convert board to list of strings for display or serialization.

        :returns: List of 15 strings representing the board.
        """
        return ["".join(str(cell) for cell in row) for row in self.grid]

    def __str__(self) -> str:
        header = "   " + " ".join(f"{i:2d}" for i in range(BOARD_SIZE))
        lines = [header]
        for idx, row in enumerate(self.to_strings()):
            lines.append(f"{idx:2d} " + "  ".join(row))
        return "\n".join(lines)
