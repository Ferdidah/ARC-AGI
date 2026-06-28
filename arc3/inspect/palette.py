"""
palette — the 16-colour ARC palette the inspector renders with.

Kept here (not imported from viz) so the inspector is self-contained and does
not break if viz.py's palette constant is named differently. If a REAL game's
colours look wrong in the GUI, adjust these hex values to match the official
ARC-AGI-3 renderer — segmentation is colour-agnostic so only the picture
changes, not the analysis.
"""

ARC_COLORS = (
    "#000000",  # 0  black
    "#0074D9",  # 1  blue
    "#FF4136",  # 2  red
    "#2ECC40",  # 3  green
    "#FFDC00",  # 4  yellow
    "#AAAAAA",  # 5  grey
    "#F012BE",  # 6  magenta
    "#FF851B",  # 7  orange
    "#7FDBFF",  # 8  cyan
    "#870C25",  # 9  maroon
    "#FFFFFF",  # 10 white
    "#39CCCC",  # 11 teal
    "#B10DC9",  # 12 purple
    "#85144B",  # 13 plum
    "#3D9970",  # 14 olive
    "#111111",  # 15 near-black
)
