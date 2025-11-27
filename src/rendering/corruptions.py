"""Image corruption pipeline for testing VLM robustness.

This module provides various image corruptions to test model performance
under adverse visual conditions, similar to ImageNet-C but tailored for
architectural floorplan diagrams.
"""

from PIL import Image, ImageFilter, ImageEnhance
from enum import Enum
from typing import Tuple
import io


class CorruptionType(Enum):
    """Types of image corruptions."""
    NONE = "none"
    BLUR = "blur"
    CONTRAST = "contrast"
    JPEG = "jpeg"
    SKEW = "skew"


def apply_blur(image: Image.Image, severity: int = 3) -> Image.Image:
    """
    Apply Gaussian blur corruption.
    
    Severity levels:
    - 1: σ = 1.0 (slight blur)
    - 3: σ = 3.0 (medium blur)
    - 5: σ = 5.0 (strong blur)
    
    Args:
        image: Input PIL Image
        severity: Blur severity (1, 3, or 5)
    
    Returns:
        Blurred image
    """
    sigma = float(severity)
    return image.filter(ImageFilter.GaussianBlur(radius=sigma))


def apply_contrast_reduction(image: Image.Image, severity: int = 50) -> Image.Image:
    """
    Reduce image contrast.
    
    Severity levels:
    - 75: 0.75x contrast (slight reduction)
    - 50: 0.50x contrast (medium reduction)
    - 25: 0.25x contrast (strong reduction)
    
    Args:
        image: Input PIL Image
        severity: Contrast percentage (75, 50, or 25)
    
    Returns:
        Contrast-reduced image
    """
    factor = severity / 100.0
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def apply_jpeg_artifacts(image: Image.Image, severity: int = 50) -> Image.Image:
    """
    Add JPEG compression artifacts.
    
    Severity levels:
    - 80: High quality (slight artifacts)
    - 50: Medium quality (noticeable artifacts)
    - 20: Low quality (strong artifacts)
    
    Args:
        image: Input PIL Image
        severity: JPEG quality (80, 50, or 20)
    
    Returns:
        JPEG-compressed image
    """
    # Save to bytes buffer with JPEG compression
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=severity)
    buffer.seek(0)
    return Image.open(buffer)


def apply_skew(image: Image.Image, severity: int = 10) -> Image.Image:
    """
    Apply rotation/skew to simulate misaligned scans.
    
    Severity levels:
    - 5: ±5° rotation (slight)
    - 10: ±10° rotation (medium)
    - 15: ±15° rotation (strong)
    
    Args:
        image: Input PIL Image
        severity: Rotation angle in degrees (5, 10, or 15)
    
    Returns:
        Rotated image
    """
    # Negative angle for counter-clockwise rotation
    angle = -severity
    # Rotate with expand to keep full image
    return image.rotate(angle, expand=True, fillcolor='white')


def apply_corruption(
    image: Image.Image,
    corruption_type: CorruptionType,
    severity: int
) -> Tuple[Image.Image, dict]:
    """
    Apply a specific corruption to an image.
    
    Args:
        image: Input PIL Image
        corruption_type: Type of corruption to apply
        severity: Corruption severity level
    
    Returns:
        Tuple of (corrupted_image, metadata_dict)
    """
    metadata = {
        "corruption": corruption_type.value,
        "severity": severity
    }
    
    if corruption_type == CorruptionType.NONE:
        return image.copy(), metadata
    elif corruption_type == CorruptionType.BLUR:
        return apply_blur(image, severity), metadata
    elif corruption_type == CorruptionType.CONTRAST:
        return apply_contrast_reduction(image, severity), metadata
    elif corruption_type == CorruptionType.JPEG:
        return apply_jpeg_artifacts(image, severity), metadata
    elif corruption_type == CorruptionType.SKEW:
        return apply_skew(image, severity), metadata
    else:
        raise ValueError(f"Unknown corruption type: {corruption_type}")


# Standard severity presets for publication-grade benchmark
CORRUPTION_PRESETS = {
    CorruptionType.BLUR: {
        "slight": 1,
        "medium": 3,
        "extreme": 5
    },
    CorruptionType.CONTRAST: {
        "slight": 75,
        "medium": 50,
        "extreme": 25
    },
    CorruptionType.JPEG: {
        "slight": 80,
        "medium": 50,
        "extreme": 20
    },
    CorruptionType.SKEW: {
        "slight": 5,
        "medium": 10,
        "extreme": 15
    }
}


def get_corruption_severity(corruption_type: CorruptionType, level: str) -> int:
    """
    Get standard severity value for a corruption type and level.
    
    Args:
        corruption_type: Type of corruption
        level: Severity level ("slight", "medium", "extreme")
    
    Returns:
        Severity value
    """
    if corruption_type == CorruptionType.NONE:
        return 0
    return CORRUPTION_PRESETS[corruption_type][level]
