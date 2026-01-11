"""
Color utilities for market breadth analyzer GUI
Provides color mapping functions for visual indicators
"""

from PyQt6.QtGui import QColor


def get_up_4_5_color(value: int) -> QColor:
    """Get banded color for Up 4.5% values (10-point ranges)"""
    # 150+: Dark Green (same shade)
    if value >= 150:
        return QColor(0, 100, 0)
    # 140-149: Dark Green
    elif value >= 140:
        return QColor(0, 120, 0)
    # 130-139: Green
    elif value >= 130:
        return QColor(0, 150, 0)
    # 120-129: Light Green
    elif value >= 120:
        return QColor(50, 180, 50)
    # 110-119: Light Green
    elif value >= 110:
        return QColor(100, 200, 100)
    # 100-109: Yellow
    elif value >= 100:
        return QColor(200, 200, 0)
    # 90-99: Yellow-Orange
    elif value >= 90:
        return QColor(220, 160, 0)
    # 80-89: Orange
    elif value >= 80:
        return QColor(220, 120, 0)
    # 70-79: Dark Orange
    elif value >= 70:
        return QColor(200, 80, 0)
    # 60-69: Dark Orange
    elif value >= 60:
        return QColor(180, 60, 0)
    # 50-59: Dark Orange
    elif value >= 50:
        return QColor(160, 40, 0)
    # 0-49: Darkest Orange (same shade)
    else:
        return QColor(140, 20, 0)
