"""Constants and enumerations for Vait Infinite Canvas."""

from enum import Enum, auto

APP_NAME = "Vait Whiteboard"
APP_VERSION = "1.0.0"
PROJECT_FILE_EXTENSION = ".canvas"
PROJECT_FILE_FILTER = "Vait Canvas (*.canvas);;All Files (*.*)"
EXPORT_IMAGE_FILTER = "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;All Files (*.*)"

CUSTOM_MIME_TYPE = "application/x-vait-canvas-items+json"

# Scene boundary (practical infinite canvas)
SCENE_EXTENT = 1_000_000  # -500,000 to +500,000 in both axes
MIN_ZOOM = 0.02  # 2%
MAX_ZOOM = 32.0  # 3200%
DEFAULT_ZOOM = 1.0

# Grid parameters
GRID_BASE_SIZE = 24  # Base distance between dots
GRID_DOT_RADIUS = 1.2
GRID_COLOR_DARK = "#3a3f4b"
GRID_COLOR_LIGHT = "#cbd5e1"
CANVAS_BG_DARK = "#181a1f"
CANVAS_BG_LIGHT = "#f8fafc"

# Z-index ranges
Z_BACKGROUND = -100
Z_IMAGE = 10
Z_SHAPE = 20
Z_TEXT = 30
Z_STROKE = 100
Z_SELECTION_FRAME = 9999

class ToolMode(Enum):
    SELECT = "select"
    PAN = "pan"
    PEN = "pen"
    ERASER = "eraser"
    TEXT = "text"
    SHAPE = "shape"
    IMAGE = "image"

class ShapeType(Enum):
    RECTANGLE = "rectangle"
    ROUNDED_RECT = "rounded_rect"
    ELLIPSE = "ellipse"
    LINE = "line"
    ARROW = "arrow"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"

class GridStyle(Enum):
    DOTS = "dots"
    LINES = "lines"
    NONE = "none"

# Default styles
DEFAULT_STROKE_COLOR = "#000000"
DEFAULT_FILL_COLOR = "#3b82f6"  # Blue
DEFAULT_FILL_TRANSPARENT = True
DEFAULT_STROKE_WIDTH = 2
DEFAULT_PEN_WIDTH = 4
DEFAULT_PEN_COLOR = "#2563eb"
DEFAULT_FONT_FAMILY = "Segoe UI"
DEFAULT_FONT_SIZE = 16
DEFAULT_TEXT_COLOR = "#0f172a"
