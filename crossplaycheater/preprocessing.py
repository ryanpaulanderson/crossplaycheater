"""Image preprocessing utilities for board analysis."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray


@dataclass
class PreprocessingConfig:
    """
    Configuration for image preprocessing.

    :param ocr_resize_target: Target size (width/height) for cell resizing.
    :type ocr_resize_target: int
    :param ocr_threshold_block_size: Block size for adaptive thresholding.
    :type ocr_threshold_block_size: int
    :param ocr_threshold_c: Constant C for adaptive thresholding.
    :type ocr_threshold_c: int
    :param ocr_denoise_h: Denoising strength (h).
    :type ocr_denoise_h: float
    :param ocr_denoise_template_window: Template window size for denoising.
    :type ocr_denoise_template_window: int
    :param ocr_denoise_search_window: Search window size for denoising.
    :type ocr_denoise_search_window: int
    :param detect_blur_kernel_size: Kernel size for Gaussian blur in board detection.
    :type detect_blur_kernel_size: int
    :param detect_canny_low: Lower threshold for Canny edge detection.
    :type detect_canny_low: int
    :param detect_canny_high: Upper threshold for Canny edge detection.
    :type detect_canny_high: int
    """

    # OCR Preprocessing
    ocr_resize_target: int = 64
    ocr_threshold_block_size: int = 11
    ocr_threshold_c: int = 2
    ocr_denoise_h: float = 10.0
    ocr_denoise_template_window: int = 7
    ocr_denoise_search_window: int = 21

    # Board Detection Preprocessing
    detect_blur_kernel_size: int = 5
    detect_canny_low: int = 50
    detect_canny_high: int = 150


class ImagePreprocessor:
    """
    Handles image preprocessing steps for board analysis.

    :param config: Configuration for preprocessing parameters.
    :type config: PreprocessingConfig
    """

    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        """
        Initialize the image preprocessor.

        :param config: Configuration for preprocessing parameters.
        :type config: PreprocessingConfig | None
        """
        self.config = config or PreprocessingConfig()

    def process_for_ocr(self, cell_image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """
        Preprocess cell image for better OCR results.

        :param cell_image: Raw cell image.
        :type cell_image: NDArray[np.uint8]
        :returns: Preprocessed image optimized for OCR.
        :rtype: NDArray[np.uint8]
        """
        # Convert to grayscale
        gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

        # Resize to consistent size for OCR
        target_size = self.config.ocr_resize_target
        gray = cv2.resize(gray, (target_size, target_size), interpolation=cv2.INTER_CUBIC)

        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            self.config.ocr_threshold_block_size,
            self.config.ocr_threshold_c,
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(
            binary,
            None,
            self.config.ocr_denoise_h,
            self.config.ocr_denoise_template_window,
            self.config.ocr_denoise_search_window,
        )

        return denoised

    def process_for_detection(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """
        Preprocess image for board boundary detection.

        :param image: Input image.
        :type image: NDArray[np.uint8]
        :returns: Edge-detected image suitable for contour finding.
        :rtype: NDArray[np.uint8]
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        kernel_size = self.config.detect_blur_kernel_size
        blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
        
        edges = cv2.Canny(
            blurred,
            self.config.detect_canny_low,
            self.config.detect_canny_high
        )
        return edges
