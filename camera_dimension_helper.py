#!/usr/bin/env python3
"""
Camera Dimension Helper
Utility to help determine the best 2D dimensions for 1D image arrays
"""

import numpy as np

def find_best_camera_dimensions(total_pixels, max_dimension=4000, min_dimension=100):
    """
    Find the best 2D dimensions for a given number of pixels.
    
    Args:
        total_pixels: Total number of pixels in the 1D array
        max_dimension: Maximum reasonable dimension (default: 4000)
        min_dimension: Minimum reasonable dimension (default: 100)
    
    Returns:
        List of (height, width) tuples sorted by likelihood
    """
    # Calculate all possible factor pairs
    factors = []
    for i in range(1, int(np.sqrt(total_pixels)) + 1):
        if total_pixels % i == 0:
            factors.append((i, total_pixels // i))
            if i != total_pixels // i:  # Avoid duplicate square factors
                factors.append((total_pixels // i, i))
    
    # Filter by reasonable camera dimensions
    reasonable_factors = [
        (h, w) for h, w in factors 
        if min_dimension <= h <= max_dimension and min_dimension <= w <= max_dimension
    ]
    
    # Sort by aspect ratio closeness to common camera ratios
    def aspect_ratio_score(dim):
        h, w = dim
        ratio = h / w
        # Common camera aspect ratios: 4:3, 16:9, 1:1, 3:2, 5:4
        common_ratios = [4/3, 16/9, 1, 3/2, 5/4]
        return min(abs(ratio - r) for r in common_ratios)
    
    reasonable_factors.sort(key=aspect_ratio_score)
    
    return reasonable_factors

def analyze_image_dimensions(total_pixels):
    """
    Analyze and suggest the best dimensions for an image array.
    
    Args:
        total_pixels: Total number of pixels
    
    Returns:
        Dictionary with analysis results
    """
    print(f"Analyzing {total_pixels:,} pixels...")
    print("=" * 50)
    
    # Check if it's a perfect square
    side_length = int(np.sqrt(total_pixels))
    if side_length * side_length == total_pixels:
        print(f"✓ Perfect square: {side_length} x {side_length}")
        return {"type": "square", "dimensions": (side_length, side_length)}
    
    # Find best dimensions
    candidates = find_best_camera_dimensions(total_pixels)
    
    if not candidates:
        print("✗ No reasonable camera dimensions found")
        return {"type": "none", "dimensions": None}
    
    print("Top 10 most likely dimensions:")
    print("-" * 30)
    
    for i, (h, w) in enumerate(candidates[:10]):
        ratio = h / w
        print(f"{i+1:2d}. {h:4d} x {w:4d} (ratio: {ratio:.3f})")
    
    # Determine the most likely
    best = candidates[0]
    h, w = best
    ratio = h / w
    
    # Classify the aspect ratio
    if abs(ratio - 1.0) < 0.1:
        ratio_type = "square (1:1)"
    elif abs(ratio - 4/3) < 0.1:
        ratio_type = "standard (4:3)"
    elif abs(ratio - 16/9) < 0.1:
        ratio_type = "widescreen (16:9)"
    elif abs(ratio - 3/2) < 0.1:
        ratio_type = "photo (3:2)"
    elif abs(ratio - 5/4) < 0.1:
        ratio_type = "large format (5:4)"
    else:
        ratio_type = f"custom ({ratio:.3f})"
    
    print(f"\nRecommended: {h} x {w} ({ratio_type})")
    
    return {
        "type": "rectangular",
        "dimensions": best,
        "aspect_ratio": ratio,
        "ratio_type": ratio_type,
        "all_candidates": candidates
    }

def test_common_camera_sizes():
    """Test the function with common camera pixel counts"""
    test_sizes = [
        307200,    # 640x480 (VGA)
        786432,    # 1024x768 (XGA)
        1048576,   # 1024x1024 (1MP square)
        2073600,   # 1920x1080 (Full HD)
        3145728,   # 2048x1536 (2MP)
        4194304,   # 2048x2048 (4MP square)
        8294400,   # 3840x2160 (4K)
        1241632,   # Your camera
    ]
    
    print("Testing common camera sizes:")
    print("=" * 50)
    
    for size in test_sizes:
        result = analyze_image_dimensions(size)
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            pixels = int(sys.argv[1])
            analyze_image_dimensions(pixels)
        except ValueError:
            print("Please provide a valid number of pixels")
    else:
        test_common_camera_sizes()