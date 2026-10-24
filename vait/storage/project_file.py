"""Project file persistence: self-contained ZIP-based .canvas format."""

import io
import json
import os
import shutil
import tempfile
import time
import zipfile
from typing import Optional, Sequence, Any
from PySide6.QtCore import QPointF

from vait.constants import APP_NAME, APP_VERSION
from vait.items import BaseCanvasItem, ImageItem, item_from_dict

class ProjectFileManager:
    """Handles saving and loading whiteboard projects in self-contained .canvas archives."""

    @staticmethod
    def save_project(
        filepath: str,
        items: Sequence[BaseCanvasItem],
        view_state: dict,
    ) -> bool:
        """Save canvas items and view state into a self-contained ZIP archive."""
        temp_dir = tempfile.mkdtemp(prefix="vait_save_")
        temp_zip = os.path.join(temp_dir, "canvas_temp.zip")

        try:
            with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                # 1. Manifest
                manifest = {
                    "app": APP_NAME,
                    "version": APP_VERSION,
                    "saved_at": time.time(),
                }
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))

                # 2. Serialize items and store image assets
                serialized_items = []
                for item in items:
                    item_dict = item.to_dict()

                    # If image item, save binary asset inside assets/ folder
                    if isinstance(item, ImageItem) and item.raw_bytes:
                        asset_filename = f"assets/{item.item_id}.png"
                        zf.writestr(asset_filename, item.raw_bytes)
                        item_dict["asset_id"] = item.item_id
                        # Clear base64 from json to keep json light and fast
                        item_dict["raw_bytes_b64"] = ""

                    serialized_items.append(item_dict)

                # 3. Canvas document
                doc = {
                    "view": view_state,
                    "items": serialized_items,
                }
                zf.writestr("canvas.json", json.dumps(doc, indent=2))

            # Atomic rename / overwrite
            if os.path.exists(filepath):
                os.replace(temp_zip, filepath)
            else:
                shutil.move(temp_zip, filepath)

            return True
        except Exception as e:
            print(f"Error saving project to {filepath}: {e}")
            raise e
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def load_project(filepath: str) -> tuple[list[BaseCanvasItem], dict]:
        """
        Load project from .canvas file.
        Returns tuple of (items_list, view_state).
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        if not zipfile.is_zipfile(filepath):
            raise ValueError("The selected file is not a valid Vait .canvas project.")

        with zipfile.ZipFile(filepath, "r") as zf:
            namelist = zf.namelist()

            if "canvas.json" not in namelist:
                raise ValueError("Project file is corrupted: missing canvas.json.")

            canvas_json_bytes = zf.read("canvas.json")
            doc = json.loads(canvas_json_bytes.decode("utf-8"))

            view_state = doc.get("view", {})
            items_data = doc.get("items", [])

            loaded_items: list[BaseCanvasItem] = []
            for d in items_data:
                item_type = d.get("type")
                if item_type == "image":
                    asset_id = d.get("asset_id", d.get("id"))
                    asset_path = f"assets/{asset_id}.png"
                    if asset_path in namelist:
                        img_bytes = zf.read(asset_path)
                        img_item = ImageItem(raw_bytes=img_bytes)
                        img_item.from_dict(d)
                        loaded_items.append(img_item)
                        continue

                # Normal item creation
                item = item_from_dict(d)
                if item:
                    loaded_items.append(item)

            return loaded_items, view_state
