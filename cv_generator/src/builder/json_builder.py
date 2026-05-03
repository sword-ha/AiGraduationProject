"""
json_builder.py
---------------
Exports the CV data to a versioned JSON file.

Features:
  - Saves a human-readable, UTF-8 encoded JSON file
  - Embeds a version number and creation timestamp in the meta block
  - Provides load_version() to reload a previously saved CV version
  - Provides list_versions() to enumerate all saved CV files

JSON is also the interchange format for saving multiple CV versions.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class JSONBuilder:
    """
    Exports CV data to JSON and manages multiple saved versions.

    Usage
    -----
        builder = JSONBuilder(output_dir="output")

        # Save
        path = builder.build(cv_data)

        # List saved versions
        versions = builder.list_versions()

        # Load a specific version
        data = builder.load_version("john_doe_cv_v2_20240115.json")
    """

    def __init__(self, output_dir: str = "output") -> None:
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Build (save)                                                        #
    # ------------------------------------------------------------------ #

    def build(
        self,
        cv_data: Dict[str, Any],
        output_dir: Optional[str] = None,
        version_label: Optional[str] = None,
    ) -> str:
        """
        Serialise cv_data to a JSON file and return the file path.

        Parameters
        ----------
        cv_data       : validated & processed CV dictionary
        output_dir    : override instance-level output directory
        version_label : optional short label (e.g. "v2", "senior_role")
                        appended to the filename for easy identification
        """
        out_dir = output_dir or self._output_dir
        os.makedirs(out_dir, exist_ok=True)

        # Stamp metadata
        now = datetime.now()
        cv_data.setdefault("meta", {})
        cv_data["meta"]["exported_at"] = now.isoformat()
        if version_label:
            cv_data["meta"]["version_label"] = version_label

        # Build filename
        name_slug  = self._slug(cv_data.get("personal", {}).get("name", "cv"))
        timestamp  = now.strftime("%Y%m%d_%H%M%S")
        label_part = f"_{version_label}" if version_label else ""
        filename   = f"{name_slug}_cv{label_part}_{timestamp}.json"
        filepath   = os.path.join(out_dir, filename)

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(cv_data, fh, ensure_ascii=False, indent=2)

        return filepath

    # ------------------------------------------------------------------ #
    #  Version management                                                  #
    # ------------------------------------------------------------------ #

    def list_versions(self, output_dir: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Return a list of saved CV JSON files with metadata.

        Each item is a dict with keys: filename, path, name, exported_at.
        """
        out_dir = output_dir or self._output_dir
        if not os.path.isdir(out_dir):
            return []

        versions: List[Dict[str, str]] = []
        for fname in sorted(os.listdir(out_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(out_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                meta     = data.get("meta", {})
                personal = data.get("personal", {})
                versions.append({
                    "filename":    fname,
                    "path":        fpath,
                    "name":        personal.get("name", "Unknown"),
                    "exported_at": meta.get("exported_at", ""),
                    "version_label": meta.get("version_label", ""),
                    "job_title":   meta.get("target_job_title", ""),
                })
            except (json.JSONDecodeError, OSError):
                # Skip malformed or unreadable files
                continue

        return versions

    def load_version(
        self,
        filename: str,
        output_dir: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a previously saved CV JSON file.

        Parameters
        ----------
        filename   : filename (not full path) of the JSON file
        output_dir : directory to look in (defaults to instance output_dir)

        Returns the parsed dict, or None if the file does not exist.
        """
        out_dir = output_dir or self._output_dir
        fpath   = os.path.join(out_dir, filename)
        if not os.path.isfile(fpath):
            return None
        with open(fpath, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------ #
    #  Utilities                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slug(text: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
