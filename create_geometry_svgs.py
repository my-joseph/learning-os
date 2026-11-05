import os

os.makedirs('assets/geometry', exist_ok=True)

# 1. Right Triangle SVG
svg_right_triangle = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 380" width="100%" height="100%">
  <defs>
    <style>
      .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 20px; font-weight: 600; fill: #1f2937; }
      .sublabel { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; fill: #4b5563; }
      .formula { font-family: "KaTeX_Math", "Times New Roman", serif; font-size: 22px; font-style: italic; font-weight: bold; fill: #2563eb; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>
  
  <!-- Triangle Path -->
  <polygon points="100,300 400,300 100,80" fill="#e0f2fe" stroke="#0284c7" stroke-width="3" stroke-linejoin="round"/>
  
  <!-- Right Angle Square -->
  <rect x="100" y="270" width="30" height="30" fill="none" stroke="#0369a1" stroke-width="2.5"/>
  <circle cx="115" cy="285" r="2.5" fill="#0369a1"/>
  
  <!-- Labels -->
  <!-- Leg a (Vertical) -->
  <text x="65" y="195" class="label" text-anchor="middle">Leg a</text>
  <text x="65" y="220" class="sublabel" text-anchor="middle">(altitude)</text>
  
  <!-- Leg b (Horizontal) -->
  <text x="250" y="335" class="label" text-anchor="middle">Leg b (base)</text>
  
  <!-- Hypotenuse c (Diagonal) -->
  <text x="275" y="175" class="label" fill="#2563eb" text-anchor="middle">Hypotenuse c</text>
  <text x="275" y="200" class="sublabel" fill="#0284c7" text-anchor="middle">(opposite 90° angle, longest side)</text>
  
  <!-- Vertices -->
  <circle cx="100" cy="300" r="4" fill="#0369a1"/>
  <circle cx="400" cy="300" r="4" fill="#0369a1"/>
  <circle cx="100" cy="80" r="4" fill="#0369a1"/>
  <text x="85" y="320" class="label" font-size="16">C (90°)</text>
  <text x="410" y="315" class="label" font-size="16">B</text>
  <text x="85" y="70" class="label" font-size="16">A</text>

  <!-- Formula Banner -->
  <rect x="160" y="20" width="180" height="40" rx="8" fill="#dbeafe" stroke="#3b82f6" stroke-width="1.5"/>
  <text x="250" y="47" class="formula" text-anchor="middle">a² + b² = c²</text>
</svg>'''

with open('assets/geometry/right_triangle.svg', 'w') as f:
    f.write(svg_right_triangle)

# 2. Complementary Angles SVG
svg_angles = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 380" width="100%" height="100%">
  <defs>
    <style>
      .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 19px; font-weight: 600; fill: #1f2937; }
      .formula { font-family: "KaTeX_Math", "Times New Roman", serif; font-size: 21px; font-weight: bold; fill: #059669; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>
  
  <!-- Right Angle Box at Origin (100, 300) -->
  <rect x="100" y="260" width="40" height="40" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>
  
  <!-- Shaded Angle Sectors -->
  <!-- Angle 1 Sector (0 to 35 deg) -->
  <path d="M 100,300 L 350,300 A 180 180 0 0 0 312,175 Z" fill="#fed7aa" opacity="0.6"/>
  <!-- Angle 2 Sector (35 to 90 deg) -->
  <path d="M 100,300 L 312,175 A 180 180 0 0 0 100,120 Z" fill="#bfdbfe" opacity="0.6"/>

  <!-- Rays -->
  <!-- Horizontal Ray -->
  <line x1="100" y1="300" x2="420" y2="300" stroke="#1f2937" stroke-width="3.5" marker-end="url(#arrow)"/>
  <!-- Vertical Ray -->
  <line x1="100" y1="300" x2="100" y2="60" stroke="#1f2937" stroke-width="3.5"/>
  <!-- Dividing Ray at 35 degrees -->
  <line x1="100" y1="300" x2="360" y2="140" stroke="#d97706" stroke-width="3.5" stroke-dasharray="2,2"/>
  
  <!-- Ray Arrows -->
  <polygon points="420,300 405,293 405,307" fill="#1f2937"/>
  <polygon points="100,60 93,75 107,75" fill="#1f2937"/>
  <polygon points="360,140 344,142 353,155" fill="#d97706"/>

  <!-- Angle Labels -->
  <text x="240" y="275" class="label" fill="#c2410c">∠1 (35°)</text>
  <text x="175" y="195" class="label" fill="#1d4ed8">∠2 (55°)</text>
  
  <!-- Origin -->
  <circle cx="100" cy="300" r="5" fill="#1f2937"/>
  <text x="75" y="325" class="label" font-size="17">Vertex O</text>

  <!-- Formula Banner -->
  <rect x="130" y="20" width="240" height="42" rx="8" fill="#dcfce7" stroke="#10b981" stroke-width="1.5"/>
  <text x="250" y="48" class="formula" text-anchor="middle">∠1 + ∠2 = 90° (Complementary)</text>
</svg>'''

with open('assets/geometry/complementary_angles.svg', 'w') as f:
    f.write(svg_angles)

# 3. Circle Radius vs Diameter SVG
svg_circle = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 380" width="100%" height="100%">
  <defs>
    <style>
      .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 19px; font-weight: 600; fill: #1f2937; }
      .formula { font-family: "KaTeX_Math", "Times New Roman", serif; font-size: 20px; font-weight: bold; fill: #b91c1c; }
      .warn { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 15px; font-weight: 700; fill: #b91c1c; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>
  
  <!-- The Circle -->
  <circle cx="200" cy="200" r="140" fill="#f0fdf4" stroke="#16a34a" stroke-width="3"/>
  
  <!-- Center Point O -->
  <circle cx="200" cy="200" r="5" fill="#1f2937"/>
  <text x="195" y="185" class="label" font-size="16">Center O</text>
  
  <!-- Diameter Line (dashed top across) -->
  <line x1="60" y1="200" x2="340" y2="200" stroke="#ea580c" stroke-width="3"/>
  <!-- Diameter Arrow Endcaps -->
  <circle cx="60" cy="200" r="4" fill="#ea580c"/>
  <circle cx="340" cy="200" r="4" fill="#ea580c"/>
  
  <!-- Radius Line (highlighted angled upwards) -->
  <line x1="200" y1="200" x2="299" y2="101" stroke="#2563eb" stroke-width="3.5"/>
  <circle cx="299" cy="101" r="4" fill="#2563eb"/>
  
  <!-- Radius Label -->
  <text x="235" y="140" class="label" fill="#2563eb">Radius r</text>
  
  <!-- Diameter Label -->
  <text x="120" y="235" class="label" fill="#ea580c">Diameter d = 2r</text>
  
  <!-- Circumference Callout -->
  <path d="M 330,150 Q 360,170 380,200" fill="none" stroke="#16a34a" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="360" y="150" class="label" fill="#16a34a" font-size="17">Circumference C = 2πr = πd</text>

  <!-- Formula Panel on Right -->
  <rect x="360" y="230" width="165" height="110" rx="8" fill="#fef2f2" stroke="#f87171" stroke-width="1.5"/>
  <text x="442" y="258" class="warn" text-anchor="middle">CRITICAL RULE:</text>
  <text x="442" y="285" class="formula" text-anchor="middle" font-size="18">r = d / 2</text>
  <text x="442" y="315" class="formula" text-anchor="middle" font-size="18">A = π r²</text>
  <text x="442" y="332" class="warn" text-anchor="middle" font-size="11" fill="#7f1d1d">Never square d directly!</text>
</svg>'''

with open('assets/geometry/circle_geometry.svg', 'w') as f:
    f.write(svg_circle)

# 4. Cylinder Geometry SVG
svg_cylinder = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 380" width="100%" height="100%">
  <defs>
    <style>
      .label { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 19px; font-weight: 600; fill: #1f2937; }
      .formula { font-family: "KaTeX_Math", "Times New Roman", serif; font-size: 20px; font-weight: bold; fill: #6366f1; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#f8fafc" rx="12"/>
  
  <!-- Cylinder Body Outline -->
  <!-- Top Ellipse -->
  <ellipse cx="180" cy="90" rx="90" ry="30" fill="#e0e7ff" stroke="#4f46e5" stroke-width="3"/>
  
  <!-- Lateral Body -->
  <path d="M 90,90 L 90,270 A 90 30 0 0 0 270,270 L 270,90 Z" fill="#eef2ff" stroke="none"/>
  <!-- Lateral Left/Right Borders -->
  <line x1="90" y1="90" x2="90" y2="270" stroke="#4f46e5" stroke-width="3"/>
  <line x1="270" y1="90" x2="270" y2="270" stroke="#4f46e5" stroke-width="3"/>
  
  <!-- Bottom Ellipse (Front half solid, back half dashed) -->
  <path d="M 90,270 A 90 30 0 0 0 270,270" fill="none" stroke="#4f46e5" stroke-width="3"/>
  <path d="M 90,270 A 90 30 0 0 1 270,270" fill="none" stroke="#a5b4fc" stroke-width="2" stroke-dasharray="5,5"/>
  
  <!-- Top Radius Dimension -->
  <line x1="180" y1="90" x2="270" y2="90" stroke="#dc2626" stroke-width="3"/>
  <circle cx="180" cy="90" r="4" fill="#1f2937"/>
  <circle cx="270" cy="90" r="4" fill="#dc2626"/>
  <text x="225" y="80" class="label" fill="#dc2626" text-anchor="middle">Radius r</text>
  
  <!-- Height Dimension (on right) -->
  <line x1="290" y1="90" x2="290" y2="270" stroke="#2563eb" stroke-width="2.5"/>
  <line x1="280" y1="90" x2="300" y2="90" stroke="#2563eb" stroke-width="2"/>
  <line x1="280" y1="270" x2="300" y2="270" stroke="#2563eb" stroke-width="2"/>
  <text x="325" y="185" class="label" fill="#2563eb">Height h</text>

  <!-- Formula Panel -->
  <rect x="330" y="40" width="170" height="110" rx="8" fill="#f5f3ff" stroke="#818cf8" stroke-width="1.5"/>
  <text x="415" y="70" class="label" text-anchor="middle" font-size="16">3D Cylinder</text>
  <text x="415" y="105" class="formula" text-anchor="middle">V = π r² h</text>
  <text x="415" y="135" class="formula" text-anchor="middle" font-size="16">A = 2πr² + 2πrh</text>
</svg>'''

with open('assets/geometry/cylinder_geometry.svg', 'w') as f:
    f.write(svg_cylinder)

print("Created all 4 custom SVG geometry diagrams successfully in assets/geometry/!")
