# -*- coding: utf-8 -*-
"""
Full upgrade script for PRG-T00 (Foundation Audit):
Coordinates generation, block validation, and Notion updates for all 25 pages:
- PRG-T00 (Topic)
- PRG-T00-C01 (Chapter) + U01..U08 (8 Units)
- PRG-T00-C02 (Chapter) + U01..U07 (7 Units)
- PRG-T00-C03 (Chapter) + U01..U06 (6 Units)
"""
import sys
import json
import time
from apply_rules_and_test_pages import (
    load_env,
    validate_blocks_clean,
    replace_page_blocks,
)
from prg_t00_builder import (
    build_prg_t00_topic,
    build_prg_t00_c01,
    build_prg_t00_c01_u01,
    build_prg_t00_c01_u02,
    build_prg_t00_c01_u03,
    build_prg_t00_c01_u04,
    build_prg_t00_c01_u05,
    build_prg_t00_c01_u06,
    build_prg_t00_c01_u07,
    build_prg_t00_c01_u08,
)
from prg_t00_c02_builder import (
    build_prg_t00_c02,
    build_prg_t00_c02_u01,
    build_prg_t00_c02_u02,
    build_prg_t00_c02_u03,
    build_prg_t00_c02_u04,
    build_prg_t00_c02_u05,
    build_prg_t00_c02_u06,
    build_prg_t00_c02_u07,
)
from prg_t00_c03_builder import (
    build_prg_t00_c03,
    build_prg_t00_c03_u01,
    build_prg_t00_c03_u02,
    build_prg_t00_c03_u03,
    build_prg_t00_c03_u04,
    build_prg_t00_c03_u05,
    build_prg_t00_c03_u06,
)

PAGE_GENERATORS = [
    # Topic
    ("PRG-T00", build_prg_t00_topic),
    # C01 & Units
    ("PRG-T00-C01", build_prg_t00_c01),
    ("PRG-T00-C01-U01", build_prg_t00_c01_u01),
    ("PRG-T00-C01-U02", build_prg_t00_c01_u02),
    ("PRG-T00-C01-U03", build_prg_t00_c01_u03),
    ("PRG-T00-C01-U04", build_prg_t00_c01_u04),
    ("PRG-T00-C01-U05", build_prg_t00_c01_u05),
    ("PRG-T00-C01-U06", build_prg_t00_c01_u06),
    ("PRG-T00-C01-U07", build_prg_t00_c01_u07),
    ("PRG-T00-C01-U08", build_prg_t00_c01_u08),
    # C02 & Units
    ("PRG-T00-C02", build_prg_t00_c02),
    ("PRG-T00-C02-U01", build_prg_t00_c02_u01),
    ("PRG-T00-C02-U02", build_prg_t00_c02_u02),
    ("PRG-T00-C02-U03", build_prg_t00_c02_u03),
    ("PRG-T00-C02-U04", build_prg_t00_c02_u04),
    ("PRG-T00-C02-U05", build_prg_t00_c02_u05),
    ("PRG-T00-C02-U06", build_prg_t00_c02_u06),
    ("PRG-T00-C02-U07", build_prg_t00_c02_u07),
    # C03 & Units
    ("PRG-T00-C03", build_prg_t00_c03),
    ("PRG-T00-C03-U01", build_prg_t00_c03_u01),
    ("PRG-T00-C03-U02", build_prg_t00_c03_u02),
    ("PRG-T00-C03-U03", build_prg_t00_c03_u03),
    ("PRG-T00-C03-U04", build_prg_t00_c03_u04),
    ("PRG-T00-C03-U05", build_prg_t00_c03_u05),
    ("PRG-T00-C03-U06", build_prg_t00_c03_u06),
]

def main(dry_run=True):
    with open("id_map.json") as f:
        id_map = json.load(f)

    env = load_env(".env")
    token = env.get("NOTION_TOKEN")
    if not token and not dry_run:
        print("ERROR: NOTION_TOKEN not found in .env")
        sys.exit(1)

    print(f"Loaded id_map with {len(id_map)} entries.")
    print(f"Total pages to process: {len(PAGE_GENERATORS)}")

    # Stage 1: Validate blocks and link resolution across all pages
    all_blocks = {}
    validation_failures = 0

    for key, gen_func in PAGE_GENERATORS:
        if key not in id_map:
            print(f"❌ ERROR: Key {key} not found in id_map.json")
            validation_failures += 1
            continue

        page_meta = id_map[key]
        page_id = page_meta["id"] if isinstance(page_meta, dict) else page_meta
        title = page_meta.get("title", key) if isinstance(page_meta, dict) else key

        blocks = gen_func(id_map)
        try:
            validate_blocks_clean(blocks, label=key)
            print(f"  ✓ {key:<16} | Blocks: {len(blocks):<3} | Unlinked: 0 | ID: {page_id}")
            all_blocks[key] = (page_id, blocks)
        except AssertionError as err:
            print(f"❌ VALIDATION FAIL for {key} ({title}): {err}")
            validation_failures += 1

    if validation_failures > 0:
        print(f"\n❌ Aborting due to {validation_failures} validation failure(s).")
        sys.exit(1)

    print(f"\n✅ All {len(PAGE_GENERATORS)} pages PASSED strict block validation!")

    if dry_run:
        print("\n[DRY RUN COMPLETE] No Notion updates were sent. Pass --execute to push to Notion.")
        return

    # Stage 2: Push updates to Notion API
    print("\n--- PUSHING TO NOTION API ---")
    start_time = time.time()
    for idx, (key, (page_id, blocks)) in enumerate(all_blocks.items(), 1):
        print(f"[{idx}/{len(all_blocks)}] Updating {key} ({page_id})...", end="", flush=True)
        try:
            replace_page_blocks(page_id, blocks, key, token)
            print(" DONE")
        except Exception as e:
            print(f" FAILED: {e}")
            raise
        time.sleep(0.3)

    elapsed = time.time() - start_time
    print(f"\n🎉 Successfully updated all {len(all_blocks)} pages in {elapsed:.1f}s!")

if __name__ == "__main__":
    is_dry_run = "--execute" not in sys.argv
    main(dry_run=is_dry_run)
