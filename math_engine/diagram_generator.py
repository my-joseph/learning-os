import math
import uuid
import json
import ssl
import urllib.request
import os

THEMES = {
    "blue": {
        "primary": "#2563eb",
        "fill": "#eff6ff",
        "stroke": "#3b82f6",
        "badge_bg": "#dbeafe",
        "badge_border": "#93c5fd",
        "badge_text": "#1e40af",
        "accent": "#0284c7"
    },
    "emerald": {
        "primary": "#059669",
        "fill": "#ecfdf5",
        "stroke": "#10b981",
        "badge_bg": "#d1fae5",
        "badge_border": "#6ee7b7",
        "badge_text": "#065f46",
        "accent": "#0d9488"
    },
    "amber": {
        "primary": "#d97706",
        "fill": "#fffbeb",
        "stroke": "#f59e0b",
        "badge_bg": "#fef3c7",
        "badge_border": "#fcd34d",
        "badge_text": "#92400e",
        "accent": "#ea580c"
    },
    "indigo": {
        "primary": "#4f46e5",
        "fill": "#eef2ff",
        "stroke": "#6366f1",
        "badge_bg": "#e0e7ff",
        "badge_border": "#a5b4fc",
        "badge_text": "#3730a3",
        "accent": "#4338ca"
    },
    "purple": {
        "primary": "#7c3aed",
        "fill": "#f5f3ff",
        "stroke": "#8b5cf6",
        "badge_bg": "#ede9fe",
        "badge_border": "#c4b5fd",
        "badge_text": "#5b21b6",
        "accent": "#6d28d9"
    },
    "rose": {
        "primary": "#e11d48",
        "fill": "#fff1f2",
        "stroke": "#f43f5e",
        "badge_bg": "#ffe4e6",
        "badge_border": "#fecdd3",
        "badge_text": "#9f1239",
        "accent": "#be123c"
    }
}

COMMON_STYLES = """
    .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 18px; font-weight: 600; fill: #1f2937; }
    .sublabel { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 14px; fill: #4b5563; }
    .formula { font-family: "KaTeX_Math", "Times New Roman", serif; font-size: 20px; font-weight: bold; }
    .badge-title { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
"""

def draw_right_triangle(base=16.0, height=12.0, label_base=None, label_height=None, label_hypot=None, theme="emerald", formula="a² + b² = c²"):
    """
    Parametric Right Triangle Generator
    Calculates exact aspect ratio, right angle marker, hypotenuse c, and side labels.
    """
    t = THEMES.get(theme, THEMES["emerald"])
    hypot = math.sqrt(base**2 + height**2)
    
    lbl_b = label_base or f"b = {base:g}"
    lbl_a = label_height or f"a = {height:g}"
    lbl_c = label_hypot or f"c = {hypot:g}"

    # Target bounding box inside 520x360
    ox, oy = 90, 290
    max_w, max_h = 320, 210
    
    # Scale coordinates proportionally
    scale = min(max_w / base, max_h / height)
    draw_w = base * scale
    draw_h = height * scale

    ax, ay = ox, oy - draw_h
    bx, by = ox + draw_w, oy
    cx, cy = ox, oy

    # Right angle box size
    box_s = min(26.0, draw_w * 0.15, draw_h * 0.15)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 360" width="100%" height="100%">
  <defs><style>{COMMON_STYLES}</style></defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>
  
  <!-- Right Triangle Polygon -->
  <polygon points="{cx},{cy} {bx},{by} {ax},{ay}" fill="{t['fill']}" stroke="{t['stroke']}" stroke-width="3" stroke-linejoin="round"/>
  
  <!-- Right Angle Square -->
  <rect x="{cx}" y="{cy - box_s}" width="{box_s}" height="{box_s}" fill="none" stroke="{t['primary']}" stroke-width="2"/>
  <circle cx="{cx + box_s/2}" cy="{cy - box_s/2}" r="2" fill="{t['primary']}"/>

  <!-- Labels -->
  <!-- Height / Leg a -->
  <text x="{cx - 20}" y="{cy - draw_h/2}" class="label" text-anchor="end">{lbl_a}</text>
  
  <!-- Base / Leg b -->
  <text x="{cx + draw_w/2}" y="{cy + 30}" class="label" text-anchor="middle">{lbl_b}</text>
  
  <!-- Hypotenuse c -->
  <text x="{cx + draw_w/2 + 25}" y="{cy - draw_h/2 - 10}" class="label" fill="{t['primary']}" text-anchor="middle">{lbl_c}</text>
  
  <!-- Vertices -->
  <circle cx="{cx}" cy="{cy}" r="4" fill="{t['primary']}"/>
  <circle cx="{bx}" cy="{by}" r="4" fill="{t['primary']}"/>
  <circle cx="{ax}" cy="{ay}" r="4" fill="{t['primary']}"/>

  <!-- Formula Badge -->
  <rect x="330" y="25" width="165" height="55" rx="8" fill="{t['badge_bg']}" stroke="{t['badge_border']}" stroke-width="1.5"/>
  <text x="412" y="45" class="badge-title" fill="{t['badge_text']}" text-anchor="middle">Pythagorean Invariant</text>
  <text x="412" y="68" class="formula" fill="{t['primary']}" text-anchor="middle">{formula}</text>
</svg>'''
    return svg

def draw_circle(radius=7.0, diameter=None, show_diameter=True, label_radius=None, label_diameter=None, theme="amber"):
    """
    Parametric Circle Generator with Radius vs Diameter highlight.
    """
    t = THEMES.get(theme, THEMES["amber"])
    d_val = diameter if diameter is not None else radius * 2
    r_val = radius if radius is not None else d_val / 2
    
    lbl_r = label_radius or f"Radius r = {r_val:g}"
    lbl_d = label_diameter or f"Diameter d = {d_val:g}"

    cx, cy = 190, 190
    draw_r = 120

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 360" width="100%" height="100%">
  <defs><style>{COMMON_STYLES}</style></defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>

  <!-- Circle Perimeter and Area -->
  <circle cx="{cx}" cy="{cy}" r="{draw_r}" fill="{t['fill']}" stroke="{t['stroke']}" stroke-width="3"/>
  <circle cx="{cx}" cy="{cy}" r="5" fill="#1f2937"/>
  <text x="{cx - 10}" y="{cy - 12}" class="label" font-size="15">Center O</text>

  <!-- Horizontal Diameter Chord -->
  <line x1="{cx - draw_r}" y1="{cy}" x2="{cx + draw_r}" y2="{cy}" stroke="{t['accent']}" stroke-width="2.5" stroke-dasharray="4,3"/>
  <circle cx="{cx - draw_r}" cy="{cy}" r="4" fill="{t['accent']}"/>
  <circle cx="{cx + draw_r}" cy="{cy}" r="4" fill="{t['accent']}"/>
  <text x="{cx - draw_r/2}" y="{cy + 24}" class="label" fill="{t['accent']}" text-anchor="middle">{lbl_d}</text>

  <!-- Slanted Radius Ray -->
  <line x1="{cx}" y1="{cy}" x2="{cx + draw_r * 0.707}" y2="{cy - draw_r * 0.707}" stroke="{t['primary']}" stroke-width="3.5"/>
  <circle cx="{cx + draw_r * 0.707}" cy="{cy - draw_r * 0.707}" r="4" fill="{t['primary']}"/>
  <text x="{cx + draw_r * 0.35 + 20}" y="{cy - draw_r * 0.35 - 5}" class="label" fill="{t['primary']}" text-anchor="middle">{lbl_r}</text>

  <!-- Formula Panel -->
  <rect x="350" y="80" width="170" height="190" rx="8" fill="{t['badge_bg']}" stroke="{t['badge_border']}" stroke-width="1.5"/>
  <text x="435" y="108" class="badge-title" fill="{t['badge_text']}" text-anchor="middle">Circle Invariants</text>
  <text x="435" y="145" class="formula" fill="{t['primary']}" text-anchor="middle">r = d / 2</text>
  <text x="435" y="180" class="formula" fill="{t['primary']}" text-anchor="middle">C = 2πr = πd</text>
  <text x="435" y="215" class="formula" fill="{t['primary']}" text-anchor="middle">A = π r²</text>
  <rect x="365" y="235" width="140" height="24" rx="4" fill="#fee2e2"/>
  <text x="435" y="251" class="badge-title" fill="#b91c1c" text-anchor="middle" font-size="10">Never square d directly!</text>
</svg>'''
    return svg

def draw_trapezoid(b1=14.0, b2=8.0, h=6.0, label_b1=None, label_b2=None, label_h=None, theme="indigo"):
    """
    Parametric Trapezoid Generator
    Generates standard trapezoid with bases b1, b2, altitude h, and area formula badge.
    """
    t = THEMES.get(theme, THEMES["indigo"])
    lbl_1 = label_b1 or f"b₁ = {b1:g}"
    lbl_2 = label_b2 or f"b₂ = {b2:g}"
    lbl_h = label_h or f"h = {h:g}"

    # Target canvas 520x360
    ox, oy = 80, 270
    max_w, max_h = 280, 160
    
    scale_x = max_w / max(b1, b2)
    scale_y = max_h / h
    scale = min(scale_x, scale_y)

    w1 = b1 * scale
    w2 = b2 * scale
    draw_h = h * scale

    # Symmetrical trapezoid layout
    offset_x = (w1 - w2) / 2
    p1 = (ox, oy)                      # bottom left
    p2 = (ox + w1, oy)                 # bottom right
    p3 = (ox + offset_x + w2, oy - draw_h)  # top right
    p4 = (ox + offset_x, oy - draw_h)       # top left

    # Altitude drop line from p4 down to base
    alt_x = p4[0]
    box_s = min(18.0, draw_h * 0.15)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 360" width="100%" height="100%">
  <defs><style>{COMMON_STYLES}</style></defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>

  <!-- Trapezoid Polygon -->
  <polygon points="{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]} {p4[0]},{p4[1]}" fill="{t['fill']}" stroke="{t['stroke']}" stroke-width="3" stroke-linejoin="round"/>

  <!-- Altitude Dashed Line -->
  <line x1="{alt_x}" y1="{p4[1]}" x2="{alt_x}" y2="{p1[1]}" stroke="{t['primary']}" stroke-width="2.5" stroke-dasharray="4,3"/>
  <rect x="{alt_x}" y="{p1[1] - box_s}" width="{box_s}" height="{box_s}" fill="none" stroke="{t['primary']}" stroke-width="1.5"/>
  <text x="{alt_x - 12}" y="{oy - draw_h/2 + 5}" class="label" fill="{t['primary']}" text-anchor="end">{lbl_h}</text>

  <!-- Base Labels -->
  <!-- Top Base b2 -->
  <text x="{ox + offset_x + w2/2}" y="{p4[1] - 14}" class="label" text-anchor="middle">{lbl_2}</text>
  <!-- Bottom Base b1 -->
  <text x="{ox + w1/2}" y="{oy + 30}" class="label" text-anchor="middle">{lbl_1}</text>

  <!-- Formula Panel -->
  <rect x="340" y="40" width="165" height="130" rx="8" fill="{t['badge_bg']}" stroke="{t['badge_border']}" stroke-width="1.5"/>
  <text x="422" y="68" class="badge-title" fill="{t['badge_text']}" text-anchor="middle">Trapezoid Area</text>
  <text x="422" y="105" class="formula" fill="{t['primary']}" text-anchor="middle" font-size="18">A = ½ h(b₁ + b₂)</text>
  <text x="422" y="140" class="sublabel" text-anchor="middle" font-size="12">Decomposes to:</text>
  <text x="422" y="156" class="sublabel" text-anchor="middle" font-size="12">Triangle + Rectangle</text>
</svg>'''
    return svg

def draw_cylinder(radius=5.0, height=12.0, label_radius=None, label_height=None, theme="purple"):
    """
    Parametric 3D Cylinder Generator
    Generates right circular cylinder with top/bottom ellipses, height, radius, and volume/surface area.
    """
    t = THEMES.get(theme, THEMES["purple"])
    lbl_r = label_radius or f"r = {radius:g}"
    lbl_h = label_height or f"h = {height:g}"

    cx, top_y = 170, 90
    rx, ry = 85, 26
    draw_h = 170
    bot_y = top_y + draw_h

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 360" width="100%" height="100%">
  <defs><style>{COMMON_STYLES}</style></defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>

  <!-- Top Ellipse -->
  <ellipse cx="{cx}" cy="{top_y}" rx="{rx}" ry="{ry}" fill="{t['badge_bg']}" stroke="{t['stroke']}" stroke-width="3"/>
  
  <!-- Cylinder Lateral Body Fill -->
  <path d="M {cx - rx},{top_y} L {cx - rx},{bot_y} A {rx} {ry} 0 0 0 {cx + rx},{bot_y} L {cx + rx},{top_y} Z" fill="{t['fill']}" stroke="none"/>
  <!-- Lateral Side Lines -->
  <line x1="{cx - rx}" y1="{top_y}" x2="{cx - rx}" y2="{bot_y}" stroke="{t['stroke']}" stroke-width="3"/>
  <line x1="{cx + rx}" y1="{top_y}" x2="{cx + rx}" y2="{bot_y}" stroke="{t['stroke']}" stroke-width="3"/>

  <!-- Bottom Ellipse -->
  <!-- Front half (solid) -->
  <path d="M {cx - rx},{bot_y} A {rx} {ry} 0 0 0 {cx + rx},{bot_y}" fill="none" stroke="{t['stroke']}" stroke-width="3"/>
  <!-- Back half (dashed hidden line) -->
  <path d="M {cx - rx},{bot_y} A {rx} {ry} 0 0 1 {cx + rx},{bot_y}" fill="none" stroke="{t['stroke']}" stroke-width="2" stroke-dasharray="4,4"/>

  <!-- Radius Marker on Top Base -->
  <line x1="{cx}" y1="{top_y}" x2="{cx + rx}" y2="{top_y}" stroke="{t['primary']}" stroke-width="3"/>
  <circle cx="{cx}" cy="{top_y}" r="3" fill="#1f2937"/>
  <circle cx="{cx + rx}" cy="{top_y}" r="3" fill="{t['primary']}"/>
  <text x="{cx + rx/2}" y="{top_y - 10}" class="label" fill="{t['primary']}" text-anchor="middle">{lbl_r}</text>

  <!-- Height Marker on Right -->
  <line x1="{cx + rx + 25}" y1="{top_y}" x2="{cx + rx + 25}" y2="{bot_y}" stroke="{t['accent']}" stroke-width="2.5"/>
  <line x1="{cx + rx + 18}" y1="{top_y}" x2="{cx + rx + 32}" y2="{top_y}" stroke="{t['accent']}" stroke-width="2"/>
  <line x1="{cx + rx + 18}" y1="{bot_y}" x2="{cx + rx + 32}" y2="{bot_y}" stroke="{t['accent']}" stroke-width="2"/>
  <text x="{cx + rx + 55}" y="{top_y + draw_h/2 + 5}" class="label" fill="{t['accent']}" text-anchor="middle">{lbl_h}</text>

  <!-- Formula Panel -->
  <rect x="330" y="45" width="170" height="150" rx="8" fill="{t['badge_bg']}" stroke="{t['badge_border']}" stroke-width="1.5"/>
  <text x="415" y="73" class="badge-title" fill="{t['badge_text']}" text-anchor="middle">3D Cylinder Invariants</text>
  <text x="415" y="105" class="formula" fill="{t['primary']}" text-anchor="middle">V = π r² h</text>
  <text x="415" y="140" class="formula" fill="{t['primary']}" text-anchor="middle" font-size="16">A_lat = 2πrh</text>
  <text x="415" y="170" class="formula" fill="{t['primary']}" text-anchor="middle" font-size="16">A_tot = 2πr² + 2πrh</text>
</svg>'''
    return svg

def upload_svg_to_notion(svg_str, filename, token):
    """
    Directly uploads an in-memory SVG string to Notion's official file storage
    via Notion File Upload API (/v1/file_uploads).
    Returns the file_upload_id.
    """
    from notion_client import notion_request
    
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    init_res = notion_request('POST', 'file_uploads', token, {
        'mode': 'single_part',
        'filename': filename,
        'content_type': 'image/svg+xml'
    })
    f_id = init_res['id']
    upload_url = init_res['upload_url']

    boundary = uuid.uuid4().hex
    svg_bytes = svg_str.encode('utf-8')
    multipart_data = (
        f'--{boundary}\r\n'.encode() +
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode() +
        b'Content-Type: image/svg+xml\r\n\r\n' +
        svg_bytes +
        b'\r\n' +
        f'--{boundary}--\r\n'.encode()
    )

    req = urllib.request.Request(
        upload_url,
        data=multipart_data,
        headers={
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        },
        method='POST'
    )

    with urllib.request.urlopen(req, context=ssl_ctx) as resp:
        if resp.status != 200:
            raise RuntimeError(f'Failed to upload SVG to Notion: HTTP {resp.status}')
    return f_id
