# Vait — Infinite Canvas Whiteboard Desktop Application

A modern, high-performance Windows desktop application built with Python and PySide6 (Qt for Python). Centered around an **infinite, pannable, zoomable canvas** where you can freely organize images, text, freehand drawings, and geometric shapes.

---

## Quick Start

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Agnivesh-Anil-Warrier/Vait.git
   cd Vait
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

### Launch the Application

Run the application:

```powershell
python main.py
```

### Run Automated Tests

Run the test suite with `pytest`:

```powershell
pytest -v
```

---

## Core Features

### 1. Infinite Canvas & Navigation
- **Infinite Space**: Limitless sheet of paper with coordinate tracking.
- **Pan**: Hold `Space` and Left-Click Drag, or drag with the **Middle Mouse Button** (MMB), or use the **Hand Tool** (`H`).
- **Zoom**: Smooth zooming anchored directly under the mouse pointer with the mouse wheel.
- **Zoom Controls**: Reset view (`Ctrl+0`), Fit All Content (`Shift+1`), Zoom In (`Ctrl++`), Zoom Out (`Ctrl+-`).
- **Adaptive Grid**: Toggle between subtle dot-grid, line-grid, or blank canvas. Grid density smoothly adapts to zoom levels.

### 2. Selection & Manipulation
- **Single & Multi-Select**: Click to select, `Shift+Click` to toggle selection, or drag across empty canvas for **rubber-band marquee selection**.
- **Transformation Handles**: 8-point resize handles + rotation stem. Handles scale inversely with zoom so they remain crisp and accurately clickable at any zoom level.
- **Aspect Ratio Locking**: Preserved by default for images; hold `Shift` to constrain shapes to 1:1 squares, circles, or 45° angles.
- **Layer Arrangement**: Bring to Front and Send to Back options in the properties bar.

### 3. Image Support
- **Import Formats**: PNG, JPG, JPEG, BMP, and WebP via native file dialog.
- **Drag-and-Drop**: Drag image files directly from Windows File Explorer onto the canvas.
- **Windows Clipboard**: Copy and paste images directly from web browsers, Photoshop, Paint, or Explorer.
- **Self-Contained Storage**: Images are bundled directly inside `.canvas` project files, ensuring projects never break if source images are moved or deleted.

### 4. Freehand Drawing & Eraser
- **Pen Tool (`P`)**: Continuous, smooth strokes using Catmull-Rom/Bezier quadratic curve smoothing.
- **Eraser Tool (`E`)**: Click or drag across strokes to erase them.
- **Customizable Styling**: Stroke color picker and width slider.
- **Full Item Support**: Strokes can be moved, selected, duplicated, copied, and deleted.

### 5. Text Boxes
- **Text Tool (`T`)**: Click to place text anywhere on the canvas.
- **Inline Editing**: Double-click any text box to type multiline text directly.
- **Auto-Wrapping & Resizing**: Drag width handles to adjust text wrapping; height automatically fits content.
- **Rich Formatting**: Font family dropdown, font size, bold (`B`), italic (`I`), alignment (Left, Center, Right), and text colors.
- **Shortcut Isolation**: Canvas keyboard shortcuts are temporarily disabled while typing to prevent accidental triggers.

### 6. Geometric Shapes
- **Available Shapes**:
  - Rectangle (`R`)
  - Rounded Rectangle (with corner radius)
  - Ellipse / Circle (`O`)
  - Line (`L`) with draggable endpoints
  - Arrow (`A`) with directional arrowhead
  - Triangle
  - Diamond
- **Fills & Outlines**: Customizable outline color, thickness, fill color, and transparent fill option.

### 7. Native Clipboard Interoperability
- **Internal Serialization**: Uses custom MIME type `application/x-vait-canvas-items+json` preserving all properties, relative positions, and styles.
- **External Interop**:
  - Copying items also places high-resolution rendered imagery and plain text onto the Windows clipboard for pasting into Word, Paint, Discord, etc.
  - Pasting external images or text automatically creates corresponding canvas items at the cursor position.
- **Shortcuts**: `Ctrl+C` (Copy), `Ctrl+V` (Paste), `Ctrl+X` (Cut), `Ctrl+D` (Duplicate).

### 8. Undo & Redo System
- Powered by `QUndoStack` and granular `QUndoCommand` implementations.
- Tracks item creation, deletion, dragging/moving, resizing, rotation, text edits, property changes, and drawing/erasing.
- `Ctrl+Z` (Undo), `Ctrl+Y` / `Ctrl+Shift+Z` (Redo).

### 9. Project Persistence (`.canvas`)
- **Self-Contained ZIP Bundle**:
  - `manifest.json`: metadata, version.
  - `canvas.json`: viewport coordinates, zoom level, grid settings, and item hierarchy.
  - `assets/`: embedded raw image files.
- **Safe Atomic Saving**: Writes to a temporary archive and atomically renames to prevent corruption.
- **Dirty State Tracking**: Warns before discarding unsaved changes.
- **Recent Projects**: Remembers recently opened projects in `File > Recent Projects`.

### 10. High-Resolution Export
- Export to high-res PNG or JPG images (`Ctrl+E`).
- Choose scope: Entire canvas contents, visible viewport, or selected items.
- Anti-aliased 2x high-DPI rendering without application UI chrome.

---

## Keyboard Shortcuts Cheatsheet

| Category | Shortcut | Action |
| :--- | :--- | :--- |
| **Canvas** | `Space + Drag` / `MMB` | Pan canvas |
| | `Mouse Wheel` | Zoom in / Zoom out |
| | `Ctrl+0` | Reset zoom to 100% |
| | `Shift+1` | Fit all content in view |
| **Tools** | `V` | Select & Move tool |
| | `H` | Hand / Pan tool |
| | `P` | Freehand Pen tool |
| | `E` | Stroke Eraser tool |
| | `T` | Text Box tool |
| | `R` / `O` / `L` / `A` | Rectangle / Ellipse / Line / Arrow |
| | `I` | Insert Image dialog |
| **Edit** | `Ctrl+Z` | Undo |
| | `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| | `Ctrl+C` / `Ctrl+V` | Copy / Paste |
| | `Ctrl+X` | Cut |
| | `Ctrl+D` | Duplicate selection |
| | `Ctrl+A` | Select all objects |
| | `Delete` / `Backspace` | Delete selected objects |
| | `Escape` | Clear selection / Cancel tool |
| **File** | `Ctrl+N` | New canvas |
| | `Ctrl+O` | Open `.canvas` project |
| | `Ctrl+S` | Save project |
| | `Ctrl+Shift+S` | Save As... |
| | `Ctrl+E` | Export to PNG/JPG image |

---

## Project Structure

```
Vait/
├── .gitignore                  # Git ignore definitions
├── requirements.txt            # Project dependencies (PySide6, pytest)
├── main.py                     # Application entry point
├── README.md                   # Documentation and usage guide
├── assets/                     # Application icons (PNG, ICO)
├── vait/
│   ├── __init__.py
│   ├── constants.py            # App enums, defaults, and MIME types
│   ├── canvas/
│   │   ├── canvas_scene.py     # QGraphicsScene with infinite grid & tool handling
│   │   └── canvas_view.py      # QGraphicsView with smooth pan, zoom, marquee
│   ├── items/
│   │   ├── handles.py          # Interactive selection, resize, and rotation handles
│   │   ├── base_item.py        # BaseCanvasItem with geometry, serialization, undo hooks
│   │   ├── shape_item.py       # Geometric shapes (Rect, Ellipse, Line, Arrow, etc.)
│   │   ├── text_item.py        # Multiline editable text with inline formatting
│   │   ├── stroke_item.py      # Freehand bezier smoothed drawing strokes
│   │   └── image_item.py       # High quality scalable image item
│   ├── commands/
│   │   └── undo_commands.py    # QUndoCommand subclasses (Add, Delete, Move, Transform, etc.)
│   ├── clipboard/
│   │   └── clipboard_manager.py# System QClipboard interop & JSON serialization
│   ├── storage/
│   │   ├── project_file.py     # Self-contained ZIP .canvas file manager
│   │   └── exporter.py         # High-resolution PNG/JPG exporter
│   └── ui/
│       ├── icons.py            # Programmatic crisp vector icons
│       ├── theme.py            # Modern Windows desktop dark stylesheet
│       ├── properties_panel.py # Contextual property toolbar for shapes, text, pen
│       ├── status_bar.py       # Zoom menu, coordinates, selection readout
│       └── main_window.py      # Main window assembly
└── tests/
    ├── conftest.py             # Pytest setup and offscreen QApplication fixture
    ├── test_items.py           # Unit tests for canvas items
    ├── test_undo_redo.py       # Unit tests for undo/redo stack
    ├── test_storage.py         # Unit tests for .canvas saving/loading and export
    ├── test_clipboard.py       # Unit tests for clipboard copy/paste/duplicate
    ├── test_drawing_and_resizing.py # Tests for interaction, handles, and resizing
    └── test_integration.py     # End-to-end integration test
```
