"""Scrabble board analyzer and utilities."""

from __future__ import annotations

from crossplaycheater.board import BOARD_SIZE, Cell, ScrabbleBoard
from crossplaycheater.board_analyzer import AnalyzerConfig, BoardAnalyzer, analyze_board

__all__ = [
    "BOARD_SIZE",
    "Cell",
    "ScrabbleBoard",
    "AnalyzerConfig",
    "BoardAnalyzer",
    "analyze_board",
]
