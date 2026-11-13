# -*- coding: utf-8 -*-
"""Registry of Programming Unit/Chapter template modules."""

import importlib

UNIT_MODULES = {
    "PRG-T01-C01": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U01": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U02": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U03": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U04": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U05": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U06": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U07": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C01-U08": "code_engine.templates.prg_t01_c01",
    "PRG-T01-C03": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U01": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U02": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U03": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U04": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U05": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U06": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U07": "code_engine.templates.prg_t01_c03",
    "PRG-T01-C03-U08": "code_engine.templates.prg_t01_c03",
}


def load_unit(unit_code: str):
    if unit_code not in UNIT_MODULES:
        raise KeyError(f"No programming templates registered for {unit_code}. Registered: {', '.join(UNIT_MODULES)}")
    return importlib.import_module(UNIT_MODULES[unit_code])
