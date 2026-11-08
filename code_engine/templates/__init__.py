# -*- coding: utf-8 -*-
"""Auto-discovering Registry of Programming Unit/Chapter template modules."""
import importlib
import os
import pkgutil
from types import ModuleType
from typing import Any

_CACHE: dict[str, ModuleType] = {}
_MODULE_MAP: dict[str, str] = {}


def discover_units(force_refresh: bool = False) -> dict[str, ModuleType]:
    """Dynamically scan code_engine/templates for all modules defining TEMPLATES."""
    global _CACHE, _MODULE_MAP
    if _CACHE and not force_refresh:
        return _CACHE

    discovered: dict[str, ModuleType] = {}
    mod_map: dict[str, str] = {}
    pkg_dir = os.path.dirname(__file__)

    for _, modname, ispkg in pkgutil.iter_modules([pkg_dir]):
        if ispkg or modname.startswith("_") or modname.startswith("."):
            continue
        try:
            full_mod_name = f"code_engine.templates.{modname}"
            if force_refresh and full_mod_name in importlib.sys.modules:
                mod = importlib.reload(importlib.sys.modules[full_mod_name])
            else:
                mod = importlib.import_module(full_mod_name)

            if not hasattr(mod, "TEMPLATES"):
                continue

            chapter = getattr(mod, "CHAPTER_CODE", None)
            unit = getattr(mod, "UNIT", None)
            units = getattr(mod, "UNITS", None)

            unit_codes = []
            if units:
                unit_codes.extend(units if isinstance(units, (list, tuple, set)) else [units])
            if unit:
                unit_codes.append(unit)
            if chapter:
                unit_codes.append(chapter)
                for i in range(1, 9):
                    unit_codes.append(f"{chapter}-U{i:02d}")
            if not unit_codes:
                derived = modname.upper().replace("_", "-")
                unit_codes.append(derived)

            for ucode in unit_codes:
                discovered[ucode] = mod
                mod_map[ucode] = full_mod_name
        except Exception:
            continue

    _CACHE = discovered
    _MODULE_MAP = mod_map
    return _CACHE


class _UnitModulesDict(dict):
    """Backwards-compatible dynamic dict proxy for UNIT_MODULES."""

    def _sync(self):
        discover_units()
        self.clear()
        self.update(_MODULE_MAP)

    def __getitem__(self, key):
        self._sync()
        if key not in self:
            discover_units(force_refresh=True)
            self.clear()
            self.update(_MODULE_MAP)
        return super().__getitem__(key)

    def __contains__(self, key):
        self._sync()
        if super().__contains__(key):
            return True
        discover_units(force_refresh=True)
        self.clear()
        self.update(_MODULE_MAP)
        return super().__contains__(key)

    def __iter__(self):
        self._sync()
        return super().__iter__()

    def keys(self):
        self._sync()
        return super().keys()

    def values(self):
        self._sync()
        return super().values()

    def items(self):
        self._sync()
        return super().items()


UNIT_MODULES = _UnitModulesDict()


def load_unit(unit_code: str) -> ModuleType:
    units = discover_units()
    if unit_code not in units:
        units = discover_units(force_refresh=True)
    if unit_code not in units:
        raise KeyError(
            f"No programming templates registered for {unit_code}. "
            f"Registered: {', '.join(sorted(units.keys()))}"
        )
    return units[unit_code]


def get_all_unit_templates() -> list[tuple[str, list[dict[str, Any]]]]:
    """Returns [(unit_code, TEMPLATES), ...] for all registered code units."""
    units = discover_units()
    result = []
    seen_mods = set()
    for ucode, mod in sorted(units.items()):
        if mod in seen_mods:
            continue
        code = getattr(mod, "CHAPTER_CODE", getattr(mod, "UNIT", ucode))
        seen_mods.add(mod)
        result.append((code, getattr(mod, "TEMPLATES", [])))
    return result


def get_all_unit_modules() -> list[tuple[str, ModuleType]]:
    """Returns [(unit_code, module), ...] for all registered code units."""
    units = discover_units()
    result = []
    seen_mods = set()
    for ucode, mod in sorted(units.items()):
        if mod in seen_mods:
            continue
        code = getattr(mod, "CHAPTER_CODE", getattr(mod, "UNIT", ucode))
        seen_mods.add(mod)
        result.append((code, mod))
    return result
