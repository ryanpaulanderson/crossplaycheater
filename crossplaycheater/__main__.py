"""CLI entry point for board analysis."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from crossplaycheater.board_analyzer import AnalyzerConfig, BoardAnalyzer


def main() -> int:
    """
    Run the board analyzer CLI.

    :returns: Exit code (0 for success, 1 for failure).
    :rtype: int
    """
    parser = argparse.ArgumentParser(
        description="Analyze a Scrabble board screenshot"
    )
    parser.add_argument("image", help="Path to the board screenshot")
    parser.add_argument(
        "-o", "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="OCR confidence threshold (0-1, default: 0.5)",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = AnalyzerConfig(ocr_confidence_threshold=args.confidence)
    analyzer = BoardAnalyzer(config)

    try:
        board = analyzer.analyze(args.image)
    except FileNotFoundError as e:
        logging.error("file_not_found", extra={"error": str(e)})
        return 1
    except ValueError as e:
        logging.error("analysis_failed", extra={"error": str(e)})
        return 1

    if args.output == "json":
        output = {
            "rows": board.to_strings(),
            "cells": [
                {"row": r, "col": c, "letter": cell.letter, "is_blank": cell.is_blank}
                for r, c, cell in board.iter_cells()
                if cell.letter is not None
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(board)

    return 0


if __name__ == "__main__":
    sys.exit(main())
