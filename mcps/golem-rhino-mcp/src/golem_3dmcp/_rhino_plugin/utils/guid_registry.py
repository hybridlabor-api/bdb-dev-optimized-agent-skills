# -*- coding: utf-8 -*-
"""
rhino_plugin/utils/guid_registry.py
=====================================
Lightweight in-process registry that tracks Rhino object GUIDs and associates
optional metadata (name aliases, type labels) with them.

Design notes
------------
* Python 3.9 compatible -- no ``match``/``case``, no ``X | Y`` union syntax.
* Zero external dependencies -- only Python stdlib.
* Runs inside Rhino 3D; ``scriptcontext`` and ``System`` are available there.
* The registry is intentionally an in-memory dict -- it is NOT persisted across
  Rhino sessions.  It is meant as a fast look-up cache for the current session.

Usage example::

    from rhino_plugin.utils.guid_registry import registry

    registry.register("550e8400-e29b-41d4-a716-446655440000", name="my_box")
    guid = registry.lookup_by_name("my_box")  # "550e8400-..."
    registry.validate_guid(guid)              # raises if not in Rhino doc
"""

import datetime
try:
    from typing import Dict, List, Optional
except ImportError:
    pass

try:
    import scriptcontext as sc
    import System
    _RHINO_AVAILABLE = True
except ImportError:
    _RHINO_AVAILABLE = False


class GuidRegistry:
    """
    In-process store that maps GUID strings to lightweight metadata dicts.

    Metadata schema per entry::

        {
            "name":       str | None,   # optional human-readable alias
            "type":       str | None,   # geometry type label (e.g. "brep")
            "created_at": str,          # ISO 8601 UTC timestamp
        }
    """

    def __init__(self):
        # type: () -> None
        # Maps GUID string (lower-case, canonical form) -> metadata dict.
        self._objects = {}  # type: Dict[str, dict]
        # Reverse-index: name -> GUID string (only for entries with a name).
        self._name_index = {}  # type: Dict[str, str]

    # ------------------------------------------------------------------
    # Normalisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(guid):
        # type: (str) -> str
        """Strip braces, lower-case, and validate basic length."""
        if guid is None:
            raise ValueError("GUID cannot be None")
        normalised = str(guid).strip().strip("{}").lower()
        if len(normalised) != 36:
            raise ValueError(
                "Invalid GUID format (expected 36 characters after stripping braces): "
                "'{guid}'".format(guid=guid)
            )
        return normalised

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def register(self, guid, name=None, obj_type=None):
        # type: (str, Optional[str], Optional[str]) -> None
        """
        Store metadata for *guid*.

        Parameters
        ----------
        guid:
            The object GUID as a string.  Braces are stripped automatically.
        name:
            Optional human-readable alias for look-up via
            :meth:`lookup_by_name`.
        obj_type:
            Optional geometry type label (e.g. ``"brep"``, ``"curve"``).
        """
        key = self._normalise(guid)
        metadata = {
            "name": name,
            "type": obj_type,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
        self._objects[key] = metadata

        if name is not None:
            # Remove any previous GUID that had this name so the index stays
            # consistent (last-write-wins semantics).
            self._name_index[name] = key

    def unregister(self, guid):
        # type: (str) -> bool
        """
        Remove the entry for *guid* from the registry.

        Returns
        -------
        bool
            ``True`` if the entry existed and was removed; ``False`` if the
            GUID was not in the registry.
        """
        try:
            key = self._normalise(guid)
        except ValueError:
            return False

        if key not in self._objects:
            return False

        metadata = self._objects.pop(key)
        name = metadata.get("name")
        if name is not None and self._name_index.get(name) == key:
            del self._name_index[name]

        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def lookup_by_name(self, name):
        # type: (str) -> Optional[str]
        """
        Find the GUID associated with *name*.

        Returns
        -------
        str | None
            The GUID string, or ``None`` if no object with that name is
            registered.
        """
        return self._name_index.get(name)

    def get_metadata(self, guid):
        # type: (str) -> Optional[dict]
        """Return the metadata dict for *guid*, or ``None`` if not registered."""
        try:
            key = self._normalise(guid)
        except ValueError:
            return None
        return self._objects.get(key)

    def all_guids(self):
        # type: () -> List[str]
        """Return all registered GUID strings (copy of keys)."""
        return list(self._objects.keys())

    # ------------------------------------------------------------------
    # Rhino-document validation
    # ------------------------------------------------------------------

    def exists(self, guid):
        # type: (str) -> bool
        """
        Check whether *guid* refers to an object that currently exists in the
        active Rhino document.

        This does NOT require the GUID to be in the local registry -- it
        queries the Rhino document directly.

        Returns
        -------
        bool
            ``True`` if the object is found in the document; ``False``
            otherwise (not found, invalid GUID format, or Rhino not
            available).
        """
        if not _RHINO_AVAILABLE:
            return False
        try:
            key = self._normalise(guid)
            sys_guid = System.Guid(key)
            obj = sc.doc.Objects.FindId(sys_guid)
            return obj is not None
        except Exception:
            return False

    def validate_guid(self, guid):
        # type: (str) -> str
        """
        Validate that *guid* refers to an existing object in the Rhino
        document.

        Parameters
        ----------
        guid:
            The object GUID as a string.

        Returns
        -------
        str
            The normalised (lower-case, brace-stripped) GUID string.

        Raises
        ------
        ValueError
            If the GUID format is invalid.
        KeyError
            If the object does not exist in the current Rhino document.
            The error message contains ``"not found"`` so that
            :func:`~rhino_plugin.utils.error_handler.wrap_handler` can
            map it to ``OBJECT_NOT_FOUND``.
        """
        key = self._normalise(guid)
        if not self.exists(key):
            raise KeyError(
                "Object not found in Rhino document: '{guid}'".format(guid=guid)
            )
        return key

    def validate_guids(self, guids):
        # type: (List[str]) -> List[str]
        """
        Validate a list of GUIDs, raising on the first one that does not
        exist in the Rhino document.

        Returns
        -------
        list[str]
            Normalised GUID strings in the same order as *guids*.

        Raises
        ------
        KeyError
            On the first GUID that is not found (message contains
            ``"not found"``).
        """
        return [self.validate_guid(g) for g in guids]

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    def clear(self):
        # type: () -> None
        """Remove all entries from the registry (useful for testing)."""
        self._objects.clear()
        self._name_index.clear()

    def purge_deleted(self):
        # type: () -> List[str]
        """
        Remove all registry entries whose GUIDs no longer exist in the Rhino
        document.

        Returns
        -------
        list[str]
            The GUID strings that were removed.
        """
        to_remove = [g for g in self._objects if not self.exists(g)]
        for g in to_remove:
            self.unregister(g)
        return to_remove

    def __len__(self):
        # type: () -> int
        return len(self._objects)

    def __contains__(self, guid):
        # type: (str) -> bool
        try:
            key = self._normalise(guid)
            return key in self._objects
        except ValueError:
            return False


# Module-level singleton -- import and use directly:
#   from rhino_plugin.utils.guid_registry import registry
registry = GuidRegistry()
