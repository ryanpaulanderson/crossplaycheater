"""Analyze Scrabble board screenshots using computer vision."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from crossplaycheater.board import BOARD_SIZE, ScrabbleBoard
from crossplaycheater.preprocessing import (ImagePreprocessor,
                                            PreprocessingConfig)

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerConfig:
    """
    Configuration for the board analyzer.

    :param min_cell_size: Minimum expected cell size in pixels.
    :type min_cell_size: int
    :param ocr_confidence_threshold: Minimum confidence for OCR results (0-1).
    :type ocr_confidence_threshold: float
    :param empty_cell_threshold: Max non-white pixels to consider cell empty.
    :type empty_cell_threshold: float
    :param languages: Languages for OCR engine.
    :type languages: list[str] | None
    :param preprocessing: Configuration for image preprocessing.
    :type preprocessing: PreprocessingConfig | None
    """

    min_cell_size: int = 20
    ocr_confidence_threshold: float = 0.5
    empty_cell_threshold: float = 0.15
    languages: list[str] | None = None
    preprocessing: PreprocessingConfig | None = None

    def __post_init__(self) -> None:
        if self.languages is None:
            self.languages = ["en"]
        if self.preprocessing is None:
            self.preprocessing = PreprocessingConfig()


class BoardAnalyzer:
    """
    Analyzes Scrabble board screenshots and extracts the board state.

    :param config: Analyzer configuration options.
    :type config: AnalyzerConfig
    """

    def __init__(self, config: AnalyzerConfig | None = None) -> None:
        """
        Initialize the board analyzer.

        :param config: Analyzer configuration options.
        :type config: AnalyzerConfig | None
        """
        self.config = config or AnalyzerConfig()
        self.preprocessor = ImagePreprocessor(self.config.preprocessing)
        self._ocr_reader: "easyocr.Reader | None" = None

    @property
    def ocr_reader(self) -> "easyocr.Reader":
        """
        Lazy-load the OCR reader to avoid slow startup.

        :returns: Initialized EasyOCR reader.
        :rtype: easyocr.Reader
        """
        if self._ocr_reader is None:
            import easyocr
            logger.info("ocr_init", extra={"languages": self.config.languages})
            self._ocr_reader = easyocr.Reader(self.config.languages, verbose=False)
        return self._ocr_reader

    def analyze(self, image_path: str | Path) -> ScrabbleBoard:
        """
        Analyze a screenshot and extract the board state.

        :param image_path: Path to the screenshot image.
        :type image_path: str | Path
        :returns: ScrabbleBoard representing the detected state.
        :rtype: ScrabbleBoard
        :raises FileNotFoundError: If image path does not exist.
        :raises ValueError: If board grid cannot be detected.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info("analyze_start", extra={"image_path": str(image_path)})

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Detect and extract the board region
        board_image = self._detect_board_region(image)

        # Extract individual cells
        cells = self._extract_cells(board_image)

        # Recognize letters in each cell
        board = ScrabbleBoard()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell_image = cells[row][col]
                letter = self._recognize_cell(cell_image, row, col)
                if letter:
                    board.set(row, col, letter)

        logger.info("analyze_complete", extra={"non_empty_cells": sum(
            1 for r, c, cell in board.iter_cells() if cell.letter
        )})

        return board

    def _detect_board_region(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """
        Detect and extract the Scrabble board region from the image.

        :param image: Input image as numpy array.
        :type image: NDArray[np.uint8]
        :returns: Cropped and perspective-corrected board image.
        :rtype: NDArray[np.uint8]
        :raises ValueError: If board cannot be detected.
        """
        edges = self.preprocessor.process_for_detection(image)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            logger.warning("no_contours_found", extra={"action": "using_full_image"})
            return image

        # Find the largest quadrilateral contour (likely the board)
        board_contour = self._find_board_contour(contours, image.shape)

        if board_contour is None:
            logger.warning("board_contour_not_found", extra={"action": "using_full_image"})
            return image

        # Apply perspective transform to get a square board
        return self._perspective_transform(image, board_contour)

    def _find_board_contour(
        self, contours: list[NDArray[np.int32]], image_shape: tuple[int, ...]
    ) -> NDArray[np.float32] | None:
        """
        Find the contour most likely to be the Scrabble board.

        :param contours: List of detected contours.
        :type contours: list[NDArray[np.int32]]
        :param image_shape: Shape of the source image.
        :type image_shape: tuple[int, ...]
        :returns: Four corner points of the board, or None if not found.
        :rtype: NDArray[np.float32] | None
        """
        image_area = image_shape[0] * image_shape[1]
        min_board_area = image_area * 0.1  # Board should be at least 10% of image

        candidates: list[tuple[float, NDArray[np.float32]]] = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_board_area:
                continue

            # Approximate the contour to a polygon
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            # We want a quadrilateral
            if len(approx) == 4:
                candidates.append((area, approx.reshape(4, 2).astype(np.float32)))

        if not candidates:
            return None

        # Return the largest quadrilateral
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def _perspective_transform(
        self, image: NDArray[np.uint8], corners: NDArray[np.float32]
    ) -> NDArray[np.uint8]:
        """
        Apply perspective transform to straighten the board.

        :param image: Source image.
        :type image: NDArray[np.uint8]
        :param corners: Four corner points of the board.
        :type corners: NDArray[np.float32]
        :returns: Perspective-corrected square image.
        :rtype: NDArray[np.uint8]
        """
        # Order corners: top-left, top-right, bottom-right, bottom-left
        corners = self._order_corners(corners)

        # Calculate output size based on the largest dimension
        width_top = np.linalg.norm(corners[1] - corners[0])
        width_bottom = np.linalg.norm(corners[2] - corners[3])
        height_left = np.linalg.norm(corners[3] - corners[0])
        height_right = np.linalg.norm(corners[2] - corners[1])

        size = int(max(width_top, width_bottom, height_left, height_right))

        dst_corners = np.array([
            [0, 0],
            [size - 1, 0],
            [size - 1, size - 1],
            [0, size - 1],
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(corners, dst_corners)
        return cv2.warpPerspective(image, matrix, (size, size))

    def _order_corners(self, corners: NDArray[np.float32]) -> NDArray[np.float32]:
        """
        Order corners as: top-left, top-right, bottom-right, bottom-left.

        :param corners: Unordered corner points.
        :type corners: NDArray[np.float32]
        :returns: Ordered corner points.
        :rtype: NDArray[np.float32]
        """
        # Sort by y-coordinate to get top and bottom pairs
        sorted_by_y = corners[np.argsort(corners[:, 1])]
        top_points = sorted_by_y[:2]
        bottom_points = sorted_by_y[2:]

        # Sort each pair by x-coordinate
        top_left, top_right = top_points[np.argsort(top_points[:, 0])]
        bottom_left, bottom_right = bottom_points[np.argsort(bottom_points[:, 0])]

        return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

    def _extract_cells(
        self, board_image: NDArray[np.uint8]
    ) -> list[list[NDArray[np.uint8]]]:
        """
        Extract individual cell images from the board.

        :param board_image: Perspective-corrected board image.
        :type board_image: NDArray[np.uint8]
        :returns: 15x15 list of cell images.
        :rtype: list[list[NDArray[np.uint8]]]
        """
        height, width = board_image.shape[:2]
        cell_height = height // BOARD_SIZE
        cell_width = width // BOARD_SIZE

        cells: list[list[NDArray[np.uint8]]] = []

        for row in range(BOARD_SIZE):
            row_cells: list[NDArray[np.uint8]] = []
            for col in range(BOARD_SIZE):
                y1 = row * cell_height
                y2 = (row + 1) * cell_height
                x1 = col * cell_width
                x2 = (col + 1) * cell_width

                # Add small margin to avoid grid lines
                margin = max(2, min(cell_height, cell_width) // 10)
                y1 = min(y1 + margin, y2 - 1)
                y2 = max(y2 - margin, y1 + 1)
                x1 = min(x1 + margin, x2 - 1)
                x2 = max(x2 - margin, x1 + 1)

                cell = board_image[y1:y2, x1:x2]
                row_cells.append(cell)
            cells.append(row_cells)

        return cells

    def _recognize_cell(
        self, cell_image: NDArray[np.uint8], row: int, col: int
    ) -> str | None:
        """
        Recognize the letter in a cell image.

        :param cell_image: Image of a single cell.
        :type cell_image: NDArray[np.uint8]
        :param row: Row index for logging.
        :type row: int
        :param col: Column index for logging.
        :type col: int
        :returns: Recognized letter, or None if cell is empty.
        :rtype: str | None
        """
        # Check if cell appears empty
        if self._is_cell_empty(cell_image):
            return None

        # Preprocess for OCR
        processed = self._preprocess_for_ocr(cell_image)

        # Run OCR
        results = self.ocr_reader.readtext(processed, detail=1, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        if not results:
            return None

        # Get the best result above confidence threshold
        for bbox, text, confidence in results:
            if confidence >= self.config.ocr_confidence_threshold and text:
                letter = text.strip().upper()
                if len(letter) == 1 and letter.isalpha():
                    logger.debug(
                        "cell_recognized",
                        extra={"row": row, "col": col, "letter": letter, "confidence": confidence},
                    )
                    return letter

        return None

    def _is_cell_empty(self, cell_image: NDArray[np.uint8]) -> bool:
        """
        Determine if a cell appears to be empty (no tile).

        :param cell_image: Image of a single cell.
        :type cell_image: NDArray[np.uint8]
        :returns: True if cell appears empty.
        :rtype: bool
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

        # Check for variance - empty cells or premium squares tend to be uniform
        variance = np.var(gray)
        if variance < 100:
            return True

        # Check if mostly one color (premium square with no tile)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        peak_ratio = np.max(hist) / np.sum(hist)
        if peak_ratio > 0.5:
            return True

        return False

    def _preprocess_for_ocr(self, cell_image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """
        Preprocess cell image for better OCR results.

        :param cell_image: Raw cell image.
        :type cell_image: NDArray[np.uint8]
        :returns: Preprocessed image optimized for OCR.
        :rtype: NDArray[np.uint8]
        """
        return self.preprocessor.process_for_ocr(cell_image)


def analyze_board(image_path: str | Path, config: AnalyzerConfig | None = None) -> ScrabbleBoard:
    """
    Convenience function to analyze a board image.

    :param image_path: Path to the screenshot.
    :type image_path: str | Path
    :param config: Optional analyzer configuration.
    :type config: AnalyzerConfig | None
    :returns: Detected board state.
    :rtype: ScrabbleBoard
    """
    analyzer = BoardAnalyzer(config)
    return analyzer.analyze(image_path)
