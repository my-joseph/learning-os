import json
from apply_rules_and_test_pages import load_env, notion_request, get_all_blocks, parse_rt

env = load_env()
token = env['NOTION_TOKEN']
rules_id = '40c3818f-8ba0-8002-92f1-e971793125e3'
with open('id_map.json') as f:
    id_map = json.load(f)

blocks = get_all_blocks(rules_id, token)

# Find the 4 blocks
for i, b in enumerate(blocks):
    bt = b['type']
    txt = ''.join(t.get('plain_text', '') for t in b.get(bt, {}).get('rich_text', []))
    if 'Parametric Educational Diagram' in txt:
        # Patch blocks i, i+1, i+2, i+3
        b_h3 = blocks[i]
        b_b1 = blocks[i+1]
        b_b2 = blocks[i+2]
        b_b3 = blocks[i+3]
        
        t1 = "**Mandatory Parametric Diagram Generation for Spatial & Physical Content:** Whenever illustrating geometric configurations (triangles, angles, circles, polygons, 3D solids), coordinate graphs, or physics diagrams (force vectors, free-body diagrams), AI must generate visual assets programmatically using structured mathematical parameters (via `math_engine.diagram_generator`) rather than manually drawing static arbitrary coordinates. All parametric diagrams must enforce the unified design system: system typography (`-apple-system`), clean pastel card background (`#f8fafc`, `rx=\"12\"`), crisp proportional scaling, clear right-angle markers, and dedicated formula/trap alert badges."
        
        t2 = "**Strict Prohibition of External Image Hotlinking (Error 429 & 403 Prevention):** AI must NEVER hotlink external third-party image URLs (such as `upload.wikimedia.org`, Wikipedia, or unauthenticated web servers) inside Notion image blocks. External hotlinks trigger aggressive automated rate-limiting (HTTP 429 Too Many Requests) and permission blocks (HTTP 403 Forbidden) on Notion clients, causing broken image placeholders for users."
        
        t3 = "**Mandatory Native Notion File Upload API (`/v1/file_uploads`):** All visual assets must be uploaded directly to Notion's official cloud storage using the Notion File Upload API (`POST /v1/file_uploads` with `mode: \"single_part\"` followed by multipart binary delivery to `upload_url`). Images must be attached as native Notion-hosted files (`type: \"file_upload\"` / `type: \"file\"`), guaranteeing instant loading, zero rate-limiting, and 100% vector sharpness."

        notion_request("PATCH", f"blocks/{b_b1['id']}", token, {
            "bulleted_list_item": {"rich_text": parse_rt(t1, id_map)}
        })
        notion_request("PATCH", f"blocks/{b_b2['id']}", token, {
            "bulleted_list_item": {"rich_text": parse_rt(t2, id_map)}
        })
        notion_request("PATCH", f"blocks/{b_b3['id']}", token, {
            "bulleted_list_item": {"rich_text": parse_rt(t3, id_map)}
        })
        print("Successfully patched rule blocks cleanly without shell escaping!")
        break
