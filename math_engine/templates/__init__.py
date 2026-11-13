# -*- coding: utf-8 -*-
"""Registry of Unit template modules. Add one line per new Unit template module."""

import importlib

UNIT_MODULES = {
    "MTH-T02-C01-U01": "math_engine.templates.mth_t02_c01_u01",
    "MTH-T01-C12": "math_engine.templates.mth_t01_c12",
}


def load_unit(unit_code):
    if unit_code not in UNIT_MODULES:
        raise KeyError(f"No Math templates registered for {unit_code}. Registered: {', '.join(UNIT_MODULES)}")
    return importlib.import_module(UNIT_MODULES[unit_code])
