"""Scrabble board analyzer and utilities."""

from __future__ import annotations

from crossplaycheater.board import BOARD_SIZE, Cell, ScrabbleBoard
from crossplaycheater.board_analyzer import (AnalyzerConfig, BoardAnalyzer,
                                             analyze_board)
from crossplaycheater.preprocessing import PreprocessingConfig

__all__ = [
    "BOARD_SIZE",
    "Cell",
    "ScrabbleBoard",
    "AnalyzerConfig",
    "BoardAnalyzer",
    "analyze_board",
    "PreprocessingConfig",
]
