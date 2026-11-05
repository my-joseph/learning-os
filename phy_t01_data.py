# -*- coding: utf-8 -*-
"""
Instructional Data & Practice Blueprint for PHY-T01 (Physics High School):
Focus: Phase 1 — Prealgebra-Compatible Classical Mechanics (Chapters C01 through C04: 13 Units).
Strictly adheres to:
- OpenStax Physics (High School) & OpenStax College Physics.
- 100% Prealgebra mathematical prerequisite bounds (MTH-T01).
- No trigonometry or calculus.
- Comprehensive 4-dimension Practice Guides.
"""

# === TOPIC METADATA ===
PHY_TOPIC_DATA = {
    "full_id": "PHY-T01",
    "title": "Physics High School",
    "goal": "Master foundational classical physics from measurement, one-dimensional kinematics, and Newton's laws through thermodynamics, electromagnetism, optics, and introductory modern physics with rigorous mathematical models and error analysis.",
    "source_id": "R037",
    "source_label": "OpenStax – Physics",
    "overview": [
        "Physics is the fundamental science that investigates the principles governing energy, matter, space, and time. In [[PHY-T01]], we ground abstract mathematical tools in observable physical reality, translating physical phenomena into predictive algebraic models and computational algorithms.",
        "To ensure a rigorous, scaffolded learning progression, the curriculum is organized into two distinct mathematical phases:\n"
        "• **Phase 1 — Prealgebra-Compatible Mechanics (Chapters C01–C04):** Covers SI measurement, metric dimensional analysis, one-dimensional position, displacement, speed, velocity, linear acceleration, and Newton's laws of motion. This entire phase relies strictly on arithmetic, signed integers, linear equations, unit rates, and basic rectangular/triangular geometry from [[MTH-T01]].\n"
        "• **Phase 2 — Trigonometry-Dependent Physics (Chapters C05–C23):** Extends mechanics to two dimensions (vector resolution, projectile motion, circular motion) and advances through thermodynamics, waves, optics, electromagnetism, and modern physics. This phase is deliberately sequenced after mastering [[MTH-T02]] (Algebra and Trigonometry).",
        "Every Unit in [[PHY-T01]] utilizes a Subject-Adaptive Physical-Mathematical Design: intuitive conceptual models, formal LaTeX equations, step-by-step worked numerical examples, four-dimension Practice Guides, Active Recall toggles, and a dedicated 'My Implementation & Mistake Log' to track experimental uncertainties and calculation slips."
    ],
    "outcomes": [
        "Execute dimensional analysis, scientific notation conversions, and order-of-magnitude estimations across SI metric units with strict significant figure discipline.",
        "Model one-dimensional rectilinear motion by interpreting and translating among position-time ($x-t$) graphs, velocity-time ($v-t$) graphs, signed vectors, and kinematic equations.",
        "Apply Newton's Three Laws of Motion to single-body and multi-body systems in one dimension, constructing free-body diagrams (FBDs) and solving for net force, mass, and acceleration ($F_{\\text{net}} = ma$).",
        "Diagnose physical calculation pitfalls (sign errors in deceleration vs. acceleration, confusion between distance and displacement, action-reaction pair misconceptions) and connect physical models to software engineering physics simulations in [[PRG-T01]]."
    ],
    "chapters_summary": [
        ("PHY-T01-C01", "What is Physics?", 3, "Scope of physics, the scientific method, fundamental SI base units, metric prefixes, dimensional analysis, and significant figures. (Phase 1 — Prealgebra Ready)"),
        ("PHY-T01-C02", "Motion in One Dimension", 4, "Reference frames, coordinate axes, scalar distance vs. vector displacement, speed vs. velocity, and slope/area interpretation of linear motion graphs. (Phase 1 — Prealgebra Ready)"),
        ("PHY-T01-C03", "Acceleration", 2, "Definition of average acceleration, sign conventions for speeding up vs. slowing down, linear velocity equations, and constant-acceleration free fall from rest. (Phase 1 — Prealgebra Ready)"),
        ("PHY-T01-C04", "Forces and Newton’s Laws of Motion", 4, "Concept of force, 1D net force vectors, Newton's first law (inertia & equilibrium), second law ($F = ma$ & weight), and third law (action-reaction pairs). (Phase 1 — Prealgebra Ready)"),
        ("PHY-T01-C05", "Motion in Two Dimensions", 4, "Vector addition/subtraction, component resolution, projectile motion, and inclined planes. *(Phase 2 — Deferred until MTH-T02 Trigonometry)*"),
        ("PHY-T01-C06", "Circular and Rotational Motion", 4, "Radian measure, centripetal acceleration, circular dynamics, and torque. *(Phase 2 — Deferred until MTH-T02 Trigonometry)*"),
        ("PHY-T01-C07", "Newton’s Law of Gravitation", 2, "Universal gravitation inverse-square law, gravitational fields, and Kepler's laws. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C08", "Momentum", 4, "Linear momentum, impulse-momentum theorem, and 1D/2D conservation of momentum. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C09", "Work, Energy, and Simple Machines", 4, "Mechanical work ($W = Fd\\cos\\theta$), kinetic/potential energy, work-energy theorem, and conservation of mechanical energy. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C10", "Special Relativity", 2, "Invariance of the speed of light, time dilation, length contraction, and relativistic mass-energy equivalence. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C11", "Thermal Energy, Heat, and Work", 4, "Temperature scales, thermal expansion, specific heat capacity, and phase transitions. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C12", "Thermodynamics", 3, "First law of thermodynamics, heat engines, second law, and entropy. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C13", "Waves and Their Properties", 4, "Mechanical waves, wave speed, superposition, interference, and standing waves. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C14", "Sound", 3, "Speed of sound, sound intensity/decibels, Doppler effect, and resonance in pipes. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C15", "Light", 4, "Electromagnetic spectrum, speed of light, ray optics, reflection, and refraction (Snell's Law). *(Phase 2 — Deferred)*"),
        ("PHY-T01-C16", "Mirrors and Lenses", 3, "Plane mirrors, concave/convex spherical mirrors, thin lenses, and ray tracing. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C17", "Diffraction and Interference", 3, "Young's double-slit experiment, diffraction gratings, and thin-film interference. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C18", "Static Electricity", 4, "Coulomb's Law, electric field, electric potential, and capacitance. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C19", "Electrical Circuits", 4, "Current, Ohm's Law ($V = IR$), series/parallel resistors, and Kirchhoff's circuit rules. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C20", "Magnetism", 4, "Magnetic poles, magnetic fields, Lorentz force on moving charges ($F = qvB\\sin\\theta$), and electromagnetic induction. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C21", "The Quantum Nature of Light", 4, "Photoelectric effect, Planck's constant, photons, and wave-particle duality. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C22", "The Atom", 4, "Rutherford nuclear model, Bohr hydrogen atom, atomic emission spectra, and quantum numbers. *(Phase 2 — Deferred)*"),
        ("PHY-T01-C23", "Particle Physics", 4, "Standard Model of quarks and leptons, fundamental forces, nuclear decay, and radioactivity. *(Phase 2 — Deferred)*"),
    ],
    "final_review": [
        "Can you verify the dimensional consistency of any physical formula by substituting base SI dimensions $[M]$, $[L]$, $[T]$ for all variables?",
        "Can you differentiate between a negative acceleration that increases speed versus a negative acceleration that decreases speed?",
        "Can you identify why action-reaction force pairs never cancel each other into translational equilibrium?",
        "Audit all Phase 1 Units in PHY-T01: ensure every completed Unit has an honest 'Mastery (0-4)' score, recorded pitfalls in the Mistake Log, and scheduled spaced review."
    ]
}

# === CHAPTER DATA (C01 - C04) ===
PHY_CHAPTERS_DATA = {
    "PHY-T01-C01": {
        "title": "What is Physics?",
        "objective": "Understand the foundational scope of physics, the empirical scientific method, and master the metric SI system of units, metric prefixes, dimensional analysis, and significant figures.",
        "criteria": "Execute unit conversions using the factor-label method, verify equation dimensional homogeneity, and report calculations to the correct number of significant figures without computational aids.",
        "role": "Serves as the indispensable quantitative foundation for all physics and engineering studies. Establishes the standard vocabulary of measurement, precision, and physical dimensions that underpins kinematics, dynamics, energy, and electromagnetism.",
        "source_section": "OpenStax Physics — Chapter 1: What is Physics? (Sections 1.1–1.3)",
        "prereqs": "[[MTH-T01-C01]] (Whole Numbers), [[MTH-T01-C05]] (Decimals), [[MTH-T01-C07]] (Ratios & Proportions), [[MTH-T01-C08]] (Exponents & Scientific Notation), [[MTH-T01-C10]] (Properties of Real Numbers)",
        "concepts": [
            "The Metric SI System: Physical reality is quantified using seven fundamental base dimensions. In classical mechanics, three suffice: Length ($[L]$ in meters, $\\text{m}$), Mass ($[M]$ in kilograms, $\\text{kg}$), and Time ($[T]$ in seconds, $\\text{s}$). All other mechanical quantities (velocity, acceleration, force, energy, power) are derived units.",
            "Dimensional Homogeneity: A physical equation is valid ONLY if both sides have identical net dimensions. You can only add, subtract, or equate quantities with the same dimensions ($[L] + [L] = [L]$); multiplying and dividing creates derived dimensional products.",
            "Significant Figures & Experimental Uncertainty: Every measurement carries uncertainty. Calculations must never imply greater precision than the least precise input operand (Multiplication/Division: fewest sig figs; Addition/Subtraction: fewest decimal places)."
        ],
        "units": [
            ("PHY-T01-C01-U01", "Physics: Definitions and Applications", "The realm of physics, classical vs. modern paradigms, scientific models, laws vs. theories, and how physical laws govern natural and computational phenomena."),
            ("PHY-T01-C01-U02", "The Scientific Methods", "Empirical observation, hypothesis formulation, controlled experimentation, falsification, peer review, and verification protocols."),
            ("PHY-T01-C01-U03", "The Language of Physics: Physical Quantities and Units", "SI base units, metric prefixes ($10^{-9}$ to $10^9$), factor-label conversion method, dimensional analysis, and significant figure rules in arithmetic."),
        ],
        "challenge": [
            "Convert a vehicle speed of $108\\text{ km/h}$ to meters per second ($\\text{m/s}$) using dimensional analysis and verify that $[v] = [L][T]^{-1}$.",
            "Use dimensional analysis to determine whether the formula for the period of a simple pendulum $T = 2\\pi \\sqrt{\\frac{L}{g}}$ is dimensionally consistent (where $L$ is length in $\\text{m}$ and $g$ is acceleration in $\\text{m/s}^2$).",
            "Evaluate $(4.50 \\times 10^3\\text{ kg}) \\times (2.0\\text{ m/s}) \\div (1.250\\text{ s})$ and express the result in proper scientific notation with the correct number of significant figures."
        ],
        "practice": {
            "title": "Chapter Practice Guide — What is Physics?",
            "mixed": "Drill mixed unit conversion chains (e.g. $\\text{g/cm}^3 \\to \\text{kg/m}^3$, $\\text{km/h} \\to \\text{m/s}$), verify dimensional consistency of unknown algebraic physics formulas, and diagnose significant figure propagation errors in multi-step arithmetic.",
            "combine": "Combine powers of 10 and scientific notation [[MTH-T01-C08]] with fraction cross-cancellation [[MTH-T01-C04]] to execute multi-step factor-label conversions without intermediate rounding.",
            "traps": "Missing unit cancellation trap, confusing mass ($\\\\text{kg}$) with weight ($\\\\text{N}$), and over-reporting calculated decimal digits beyond measured significant figures.",
            "cross": "Programming ([[PRG-T01]]): Floating-point precision hazards (`0.1 + 0.2 !== 0.3`), defining strict TypeScript branded types for units (e.g. `type Meters = number & { readonly __brand: unique symbol }`), and telemetry parsing."
        }
    },
    "PHY-T01-C02": {
        "title": "Motion in One Dimension",
        "objective": "Model rectilinear motion along a single coordinate axis using position, distance, displacement, average speed, and average velocity, and interpret motion graphically via position-time and velocity-time curves.",
        "criteria": "Calculate displacement and velocity from coordinate data, compute the slope of linear position-time curves, and determine displacement from the area under velocity-time curves without a calculator.",
        "role": "Introduces 1D kinematics—the mathematical description of motion without considering its causes. Establishes the coordinate foundation for all future kinematic and dynamic analysis in mechanics.",
        "source_section": "OpenStax Physics — Chapter 2: Motion in One Dimension (Sections 2.1–2.4)",
        "prereqs": "[[PHY-T01-C01]], [[MTH-T01-C03]] (Integers & Signed Arithmetic), [[MTH-T01-C07]] (Rates), [[MTH-T01-C11]] (Linear Equations), [[MTH-T01-C12]] (Rectangular Area), [[MTH-T01-C14]] (Linear Graphs & Slope)",
        "concepts": [
            "Reference Frames & Coordinate Direction: Motion is strictly relative to a chosen origin $x = 0$ and axis direction. By universal convention in 1D, movement to the right (or upward) is defined as positive ($+$), and movement to the left (or downward) is negative ($-$).",
            "Distance vs. Displacement: Distance ($d$) is a scalar representing the total length of the path traveled ($d \\ge 0$). Displacement ($\\Delta x = x_f - x_i$) is a vector representing the net change in position from start to finish, complete with sign.",
            "Average Speed vs. Average Velocity: Average speed is $\\frac{\\text{total distance}}{\\Delta t}$. Average velocity is $\\vec{v}_{\\text{avg}} = \\frac{\\Delta x}{\\Delta t}$. An object returning to its starting point has $\\vec{v}_{\\text{avg}} = 0$ regardless of total distance traveled or peak speed."
        ],
        "units": [
            ("PHY-T01-C02-U01", "Relative Motion, Distance, and Displacement", "Reference frames, coordinate systems, scalar distance vs. signed vector displacement $\\Delta x = x_f - x_i$ on a 1D axis."),
            ("PHY-T01-C02-U02", "Speed and Velocity", "Scalar average speed vs. signed vector average velocity $v_{\\text{avg}} = \\frac{\\Delta x}{\\Delta t}$, instantaneous velocity, and constant velocity models."),
            ("PHY-T01-C02-U03", "Position vs. Time Graphs", "Interpreting $x-t$ graphs: stationary states, constant velocity slopes $m = \\frac{\\Delta x}{\\Delta t}$, and extracting direction from slope signs."),
            ("PHY-T01-C02-U04", "Velocity vs. Time Graphs", "Interpreting $v-t$ graphs for uniform motion: zero slope = zero acceleration, and calculating net displacement as geometric area $\\Delta x = v \\cdot \\Delta t$."),
        ],
        "challenge": [
            "A runner sprints $120\\text{ m}$ east in $20\\text{ s}$, stops for $10\\text{ s}$, and walks $50\\text{ m}$ west in $20\\text{ s}$. Compute (a) total distance, (b) net displacement, (c) average speed, and (d) average velocity over the entire $50\\text{ s}$ interval.",
            "A train moves according to the position-time coordinates $(t=0\\text{ s}, x=-40\\text{ m})$ and $(t=8\\text{ s}, x=+80\\text{ m})$. Graph this segment and calculate the train's velocity from the slope of the line.",
            "Given a piecewise velocity-time graph with $v = +15\\text{ m/s}$ from $t=0$ to $4\\text{ s}$ and $v = -10\\text{ m/s}$ from $t=4$ to $10\\text{ s}$, calculate the total distance and final displacement using rectangular geometric areas."
        ],
        "practice": {
            "title": "Chapter Practice Guide — Motion in One Dimension",
            "mixed": "Interleave displacement calculations across positive/negative coordinates, multi-stage average speed vs. velocity comparisons, and translation back-and-forth between verbal motion scenarios, tables, and $x-t$ / $v-t$ graphs.",
            "combine": "Combine signed integer subtraction [[MTH-T01-C03]] with linear rate-of-change formulas [[MTH-T01-C07]] and coordinate slope [[MTH-T01-C14]] to analyze multi-segment journeys.",
            "traps": "Averaging velocities directly without weighting by time intervals ($v_{\\text{avg}} \\ne \\frac{v_1 + v_2}{2}$ if times differ), confusing positive position with forward motion (a body at $x = +100\\text{ m}$ moving left has negative velocity), and omitting vector signs.",
            "cross": "Programming ([[PRG-T01]]): Position update loops in 2D game loops (`player.x += player.vx * dt`), accumulator patterns over waypoint vectors, and bounding box collision checks."
        }
    },
    "PHY-T01-C03": {
        "title": "Acceleration",
        "objective": "Define average acceleration as the time rate of change of velocity, interpret acceleration signs for speeding up versus slowing down, and apply linear kinematic equations and graph slopes to uniform acceleration and free fall from rest.",
        "criteria": "Calculate acceleration from velocity-time data, correctly classify speeding up vs. slowing down from sign pairs of $v$ and $a$, and solve constant-acceleration kinematics problems from rest using linear equations and square roots.",
        "role": "Bridges kinematics to dynamics by analyzing how velocity changes over time. Sets the prerequisite kinematic stage for Newton's Second Law ($F = ma$) in Chapter 4.",
        "source_section": "OpenStax Physics — Chapter 3: Acceleration (Sections 3.1–3.2)",
        "prereqs": "[[PHY-T01-C02]], [[MTH-T01-C03]] (Signed Arithmetic), [[MTH-T01-C09]] (Square Roots), [[MTH-T01-C11]] (Linear Equations), [[MTH-T01-C12]] (Triangular Area)",
        "concepts": [
            "Acceleration as Rate of Velocity Change: Acceleration is the vector rate of change of velocity: $\\vec{a}_{\\text{avg}} = \\frac{\\Delta \\vec{v}}{\\Delta t} = \\frac{\\vec{v}_f - \\vec{v}_0}{\\Delta t}$, measured in $(\\text{m/s})/\\text{s} = \\text{m/s}^2$. An acceleration of $3\\text{ m/s}^2$ means velocity changes by $3\\text{ m/s}$ every single second.",
            "The Golden Sign Rule of Acceleration: A negative acceleration does NOT necessarily mean 'slowing down':\n• **Speeding Up:** Velocity and acceleration share the SAME sign ($v > 0, a > 0$ OR $v < 0, a < 0$).\n• **Slowing Down (Deceleration):** Velocity and acceleration have OPPOSITE signs ($v > 0, a < 0$ OR $v < 0, a > 0$).",
            "Geometric Interpretation of Accelerated Motion: On a $v-t$ graph, the slope is constant acceleration $a$. The displacement $\\Delta x$ under a constant acceleration curve starting from rest ($v_0 = 0$) is the area of a right triangle: $\\Delta x = \\frac{1}{2} b h = \\frac{1}{2} t (at) = \\frac{1}{2}at^2$."
        ],
        "units": [
            ("PHY-T01-C03-U01", "Acceleration", "Average acceleration definition $a = \\frac{\\Delta v}{\\Delta t}$, units $\\text{m/s}^2$, and determining speeding up vs. slowing down from sign combinations of $v$ and $a$."),
            ("PHY-T01-C03-U02", "Representing Acceleration with Equations and Graphs", "Linear kinematics formula $v_f = v_0 + at$, triangular area displacement $\\Delta x = \\frac{1}{2}at^2$ for motion from rest, and gravitational free fall near Earth ($g = 9.8\\text{ m/s}^2$)."),
        ],
        "challenge": [
            "A car traveling east at $28\\text{ m/s}$ applies brakes and decelerates uniformly at $4.0\\text{ m/s}^2$ to a full stop. (a) State the signs of $v_0$ and $a$. (b) Calculate the time required to stop. (c) Calculate the braking distance using the average velocity formula $\\Delta x = \\frac{v_0 + v_f}{2} \\cdot t$.",
            "A rock is dropped from rest from a bridge into a gorge. It hits the water after $3.0\\text{ s}$. Assuming $g = 9.8\\text{ m/s}^2$ and zero air drag, compute (a) its impact velocity and (b) the height of the bridge using $\\Delta y = \\frac{1}{2}gt^2$.",
            "Sketch a velocity-time graph for an object thrown straight up that reaches its peak and falls back down. Identify the slope at the exact moment the object is momentarily stationary at its peak."
        ],
        "practice": {
            "title": "Chapter Practice Guide — Acceleration",
            "mixed": "Generate mixed kinematics problem sets testing 1D acceleration, deceleration stopping times, sign-pair identification (speeding up vs slowing down), and free-fall drops from rest.",
            "combine": "Combine signed velocity subtraction [[PHY-T01-C02-U02]] with one-step linear equation solving [[MTH-T01-C11]] and square-root evaluation [[MTH-T01-C09]] for drop times ($t = \\sqrt{\\frac{2h}{g}}$).",
            "traps": "The 'Zero Velocity = Zero Acceleration' Trap: Believing that when an object momentarily stops at its peak, its acceleration is zero (gravity $g = -9.8\\text{ m/s}^2$ acts continuously!). Deceleration sign trap: assuming deceleration must always be mathematically negative.",
            "cross": "Programming ([[PRG-T01]]): Euler integration in physics engines (`velocity += acceleration * dt; position += velocity * dt`), and handling floating-point roundoff at velocity sign flips."
        }
    },
    "PHY-T01-C04": {
        "title": "Forces and Newton’s Laws of Motion",
        "objective": "Understand force as an interaction, master 1D free-body diagrams, and apply Newton’s Three Laws of Motion to explain equilibrium, compute acceleration via $F_{\\text{net}} = ma$, and identify action-reaction pairs.",
        "criteria": "Construct 1D free-body diagrams, calculate net force by vector addition of signed forces, apply $F_{\\text{net}} = ma$ to determine mass/acceleration/weight, and identify action-reaction pairs without third-law fallacies.",
        "role": "Introduces Dynamics—the study of the causes of motion. Unifies kinematics (Chapters 2 & 3) with physical interactions, establishing the core framework of classical mechanics.",
        "source_section": "OpenStax Physics — Chapter 4: Forces and Newton's Laws of Motion (Sections 4.1–4.4)",
        "prereqs": "[[PHY-T01-C02]], [[PHY-T01-C03]], [[MTH-T01-C03]] (Signed Arithmetic), [[MTH-T01-C07]] (Direct & Inverse Variation), [[MTH-T01-C11]] (Linear Equations)",
        "concepts": [
            "Force as an Interaction Vector: A force is a push or pull resulting from an interaction between two objects. Forces are vectors with magnitude and direction, measured in Newtons ($\\text{N} = \\text{kg}\\cdot\\text{m/s}^2$). In 1D, net force is the algebraic sum of all external forces: $F_{\\text{net}} = \\Sigma F = F_1 + F_2 + \\dots$.",
            "Newton's First Law (Law of Inertia): An object at rest remains at rest, and an object in uniform rectilinear motion continues at constant velocity, UNLESS acted upon by a nonzero net external force. When $F_{\\text{net}} = 0$, the system is in translational equilibrium ($a = 0$). Mass ($m$) is the quantitative scalar measure of inertia.",
            "Newton's Second Law ($F_{\\text{net}} = ma$): The acceleration of an object is directly proportional to the net external force acting upon it and inversely proportional to its mass: $a = \\frac{F_{\\text{net}}}{m} \\iff F_{\\text{net}} = ma$. Weight is the gravitational force $w = mg$.",
            "Newton's Third Law (Action-Reaction): Whenever object A exerts a force on object B, object B simultaneously exerts an equal in magnitude and opposite in direction force on object A ($F_{A\\text{ on }B} = -F_{B\\text{ on }A}$). These two forces act on DIFFERENT objects and therefore NEVER cancel each other out."
        ],
        "units": [
            ("PHY-T01-C04-U01", "Force", "Contact vs. field forces, 1D force vectors, drawing 1D Free-Body Diagrams (FBDs), and computing net force $\\Sigma F$ via signed addition."),
            ("PHY-T01-C04-U02", "Newton's First Law of Motion: Inertia", "The concept of inertia, mass as quantitative inertia, translational equilibrium $\\Sigma F = 0$, and distinguishing constant velocity from zero force."),
            ("PHY-T01-C04-U03", "Newton's Second Law of Motion", "Mathematical formulation $F_{\\text{net}} = ma$, the Newton unit definition, direct/inverse variation, and calculating weight $w = mg$."),
            ("PHY-T01-C04-U04", "Newton's Third Law of Motion", "Action-reaction pairs $F_{A\\text{ on }B} = -F_{B\\text{ on }A}$, interaction pairs vs. balanced forces, and why action-reaction pairs never cancel each other."),
        ],
        "challenge": [
            "A $1,200\\text{ kg}$ car accelerates from rest to $20\\text{ m/s}$ in $5.0\\text{ s}$ along a horizontal road. A constant frictional rolling resistance of $400\\text{ N}$ opposes the motion. (a) Find the car's acceleration. (b) Find the net force required. (c) Calculate the forward tractive force exerted by the tires on the road.",
            "An astronaut with a mass of $80\\text{ kg}$ (including suit) stands on the Moon ($g_{\\text{Moon}} = 1.62\\text{ m/s}^2$). Compute (a) the astronaut's mass on the Moon, (b) the astronaut's weight on Earth, and (c) the astronaut's weight on the Moon.",
            "A horse pulls a cart forward. The horse says: 'By Newton's Third Law, the cart pulls back on me with an equal force, so the forces cancel and I cannot move the cart.' Explain the exact physical flaw in the horse's reasoning."
        ],
        "practice": {
            "title": "Chapter Practice Guide — Forces and Newton’s Laws of Motion",
            "mixed": "Interleave 1D Free-Body Diagram construction, net force algebraic sums, $F_{\\text{net}} = ma$ solving for unknown force or mass, mass vs. weight conversions, and Third Law action-reaction identification.",
            "combine": "Combine kinematics acceleration calculations [[PHY-T01-C03-U01]] with Newton's Second Law [[PHY-T01-C04-U03]] to solve two-step force-from-motion word problems.",
            "traps": "The Normal Force Myth: assuming normal force always equals weight $N = mg$ (only true on a flat horizontal plane with no vertical applied forces!). Third Law cancellation trap: believing action and reaction cancel into equilibrium (they act on separate bodies!).",
            "cross": "Programming ([[PRG-T01]]): Rigid-body physics engine architecture (force accumulators, `applyForce(f) { this.netForce.add(f); }`, `integrate() { this.a = this.netForce / this.m; this.netForce.zero(); }`)."
        }
    }
}

# === 13 UNITS CONTENT DEFINITION ===
PHY_UNITS_DATA = {
    # =========================================================================
    # CHAPTER C01: What is Physics? (3 Units)
    # =========================================================================
    "PHY-T01-C01-U01": {
        "title": "Physics: Definitions and Applications",
        "chapter": "PHY-T01-C01",
        "obj": "Define physics as the study of matter, energy, space, and time, distinguish classical from modern physics paradigms, and explain the roles of models, physical theories, and scientific laws.",
        "out": "Differentiate between physical observations, models, theories, and laws, and classify physical phenomena into classical vs. modern domains.",
        "prereq": "None (Foundational Physical Sciences)",
        "next": "[[PHY-T01-C01-U02]]",
        "source": "OpenStax Physics — Section 1.1: Physics: Definitions and Applications",
        "concepts": [
            "The Scope of Physics: Physics is the most fundamental natural science, providing the foundational principles and mathematical structures for chemistry, geology, biology, astronomy, and modern engineering.",
            "Classical vs. Modern Physics: Classical physics (Newtonian mechanics, thermodynamics, Maxwellian electromagnetism) applies to macro-scale objects moving much slower than the speed of light ($v \\ll c$) with dimensions much larger than atoms ($d \\gg 10^{-9}\\text{ m}$). Modern physics (Special/General Relativity and Quantum Mechanics) governs speeds approaching light ($c \\approx 3 \\times 10^8\\text{ m/s}$) and subatomic scales.",
            "Models, Theories, and Laws: A **model** is a simplified representation of a complex system (e.g. treating an automobile as a single point mass). A **theory** is an extensively tested, comprehensive explanation of natural phenomena. A **law** is a concise, universal description—often expressed as a mathematical equation (e.g. $F = ma$)—of how nature behaves under specified conditions."
        ],
        "formulas": [
            "\\text{Classical Domain Criteria: } v \\ll c \\quad (c \\approx 3.00 \\times 10^8\\text{ m/s}), \\quad d \\gg 10^{-9}\\text{ m}"
        ],
        "worked": "Scenario: Classify whether Newtonian classical physics or modern physics is required to model the following systems:\n(a) A $1,200\\text{ kg}$ satellite orbiting Earth at $7,800\\text{ m/s}$.\n(b) An electron moving inside a semiconductor transistor at $2.0 \\times 10^6\\text{ m/s}$ with a gate width of $3\\text{ nm}$.\n\nStep 1: For the satellite: Speed $v = 7.8 \\times 10^3\\text{ m/s} \\ll 3 \\times 10^8\\text{ m/s}$ ($v/c \\approx 0.0026\\%$) and size $\\approx 2\\text{ m} \\gg 10^{-9}\\text{ m}$. Classical mechanics is fully valid.\nStep 2: For the electron in the transistor: Gate width $d = 3 \\times 10^{-9}\\text{ m}$ is at the nanometer scale where quantum wave-particle effects dominate. Modern quantum physics is strictly required.\nConclusion: Scale and speed dictate the governing domain.",
        "practice": {
            "title": "Practice Guide — Physics: Definitions and Applications",
            "core": "Drill classifying physical scenarios into classical vs modern physics domains using the speed threshold ($v < 0.01c$) and spatial threshold ($d > 10^{-9}\\text{ m}$). Define and distinguish physical models, theories, and universal laws.",
            "combine": "Foundational unit; directly prepares for the empirical validation cycle in [[PHY-T01-C01-U02]] and physical quantity measurement in [[PHY-T01-C01-U03]].",
            "traps": "Theory vs. Guess Trap: Confusing the colloquial use of 'theory' (an untested hunch) with a scientific theory (an intensely verified, predictive explanatory framework). Law Infallibility Trap: Assuming a scientific law is immune to boundary conditions (e.g., $F = ma$ fails as speeds approach $c$).",
            "cross": "Programming ([[PRG-T01]]): System modeling and abstraction boundaries—treating complex objects as simplified state objects (`PointMass { x, y, m }`) mirrors physics point-particle modeling."
        },
        "recall": [
            ("What are the two quantitative criteria that determine whether a physical phenomenon can be modeled using classical mechanics rather than relativity or quantum mechanics?", "The object must move at speeds much slower than the speed of light ($v \\ll c$, typically $v < 1\\%\\, c$) and its dimensions must be significantly larger than subatomic scales ($d \\gg 10^{-9}\\text{ m}$)."),
            ("What is the fundamental difference between a scientific theory and a scientific law?", "A scientific law is a concise, universal description of WHAT nature does under specific conditions (often an algebraic formula), whereas a scientific theory is an overarching, thoroughly tested explanatory mechanism of WHY and HOW nature behaves that way.")
        ]
    },

    "PHY-T01-C01-U02": {
        "title": "The Scientific Methods",
        "chapter": "PHY-T01-C01",
        "obj": "Outline the cyclical steps of the empirical scientific method, explain the necessity of controlled experiments, and understand falsifiability and peer review.",
        "out": "Formulate testable, falsifiable scientific hypotheses and design single-variable controlled experimental procedures to test them.",
        "prereq": "[[PHY-T01-C01-U01]]",
        "next": "[[PHY-T01-C01-U03]]",
        "source": "OpenStax Physics — Section 1.2: The Scientific Methods",
        "concepts": [
            "The Empirical Cycle: Science progresses through an iterative loop: Observation $\\to$ Question $\\to$ Hypothesis $\\to$ Controlled Experiment $\\to$ Data Analysis $\\to$ Conclusion $\\to$ Theory Revision. A hypothesis is never 'proven'; it is either supported by evidence or falsified.",
            "Controlled Experimentation: To determine cause-and-effect, an experiment must isolate a single Independent Variable (manipulated), observe the Dependent Variable (measured outcome), and hold all other Controlled Variables strictly constant.",
            "Falsifiability & Reproducibility: A statement is scientifically valid only if it is falsifiable—there must exist a conceivable empirical observation that could disprove it. Results must be independently reproducible by peer laboratories."
        ],
        "formulas": [
            "\\text{Experimental Invariant: } \\text{Independent Variable} \\xrightarrow{\\text{controls held constant}} \\text{Dependent Variable}"
        ],
        "worked": "Scenario: A student claims: 'Heavier objects always fall faster than lighter objects because of gravity.' Design a controlled test to evaluate this claim.\n\nStep 1: Identify variables: Independent variable = Mass of falling objects. Dependent variable = Time to fall a fixed height $h$. Controlled variables = Height $h$, aerodynamic shape/surface area, and release mechanism.\nStep 2: Procedure: Drop two spheres of identical diameter and surface texture (one solid steel $500\\text{ g}$, one hollow plastic $50\\text{ g}$) simultaneously from $h = 2.0\\text{ m}$ in an evacuated drop tube (zero air resistance).\nStep 3: Observation: Both spheres strike the ground at the exact same millisecond ($t = \\sqrt{2h/g} \\approx 0.64\\text{ s}$).\nConclusion: The hypothesis is falsified. Gravitational acceleration is independent of object mass.",
        "practice": {
            "title": "Practice Guide — The Scientific Methods",
            "core": "Drill formulating testable, falsifiable hypotheses from physical observations, identifying independent, dependent, and controlled variables in laboratory setups, and evaluating whether an experiment cleanly isolates cause-and-effect.",
            "combine": "Combine scientific inquiry with SI physical quantity measurement [[PHY-T01-C01-U03]] to gather quantitative experimental data.",
            "traps": "Multi-Variable Contamination Trap: Changing both mass and shape in a drop test, mistaking air resistance effects for gravitational differences. Confirmation Bias Trap: Discarding anomalous data that contradicts the preferred hypothesis rather than investigating systematic errors.",
            "cross": "Programming ([[PRG-T01]]): Automated test suites and regression testing—unit tests isolate a single variable (input parameter) and assert on an expected invariant under controlled mock environments."
        },
        "recall": [
            ("Why must all variables other than the independent variable be strictly held constant in a scientific experiment?", "To guarantee that any measured change in the dependent variable is caused solely by the manipulation of the independent variable, preventing confounding factors from invalidating the causal link."),
            ("What makes a hypothesis scientifically useful?", "It must be predictive, testable through empirical observation, and strictly falsifiable (capable of being proven false by contradictory evidence).")
        ]
    },

    "PHY-T01-C01-U03": {
        "title": "The Language of Physics: Physical Quantities and Units",
        "chapter": "PHY-T01-C01",
        "obj": "Use the SI metric system, convert derived units to base dimensions $[M][L][T]$, execute unit conversions via the factor-label method, apply metric prefixes, and enforce significant figure rules in multi-step arithmetic.",
        "out": "Convert complex physical units across metric prefixes, verify dimensional homogeneity of algebraic physics formulas, and report computed results with correct significant figures.",
        "prereq": "[[PHY-T01-C01-U02]], [[MTH-T01-C01-U01]], [[MTH-T01-C07-U01]], [[MTH-T01-C08-U01]], [[MTH-T01-C10-U01]]",
        "next": "[[PHY-T01-C02-U01]]",
        "source": "OpenStax Physics — Section 1.3: The Language of Physics: Physical Quantities and Units",
        "concepts": [
            "SI Base Units & Metric Prefixes: Standard units: Length (meter, $\\text{m}$), Mass (kilogram, $\\text{kg}$), Time (second, $\\text{s}$). Metric prefixes scale by powers of 10: nano- ($10^{-9}$, $\\text{n}$), micro- ($10^{-6}$, $\\mu$), milli- ($10^{-3}$, $\\text{m}$), centi- ($10^{-2}$, $\\text{c}$), kilo- ($10^{3}$, $\\text{k}$), mega- ($10^{6}$, $\\text{M}$), giga- ($10^{9}$, $\\text{G}$).",
            "Dimensional Analysis: Every mechanical quantity has dimensions $[M]^a [L]^b [T]^c$. For example, Velocity has dimension $[L][T]^{-1}$ ($\\text{m/s}$), Acceleration has $[L][T]^{-2}$ ($\\text{m/s}^2$), Force has $[M][L][T]^{-2}$ ($\\text{kg}\\cdot\\text{m/s}^2 = \\text{N}$), and Energy has $[M][L]^2[T]^{-2}$ ($\\text{kg}\\cdot\\text{m}^2\\text{/s}^2 = \\text{J}$). Dimensional consistency is mandatory for any physics formula.",
            "The Factor-Label Conversion Method: Multiply the initial measurement by conversion ratios equal to 1, arranging units algebraically so unwanted units cancel in numerators and denominators.",
            "Significant Figure Rules: Nonzero digits and captured zeros are significant; leading zeros are never significant; trailing zeros are significant ONLY if a decimal point is explicitly present. In multiplication/division, keep the fewest significant figures of any operand."
        ],
        "formulas": [
            "\\text{Velocity Dimension: } [v] = \\frac{[L]}{[T]} = [L][T]^{-1} \\quad (\\text{m/s})",
            "\\text{Acceleration Dimension: } [a] = \\frac{[L]}{[T]^2} = [L][T]^{-2} \\quad (\\text{m/s}^2)",
            "\\text{Force Dimension: } [F] = [M] \\cdot [a] = [M][L][T]^{-2} \\quad (\\text{kg}\\cdot\\text{m/s}^2 = \\text{N})",
            "\\text{Factor-Label Unity: } 1 = \\left(\\frac{10^3\\text{ m}}{1\\text{ km}}\\right) = \\left(\\frac{1\\text{ h}}{3,600\\text{ s}}\\right)"
        ],
        "worked": "Example: A bullet travels at $720\\text{ km/h}$.\n(a) Convert this speed to $\\text{m/s}$ using the factor-label method.\n(b) Verify that the kinetic energy formula $KE = \\frac{1}{2}mv^2$ has the dimensions of work ($W = F \\cdot d$).\n\nPart (a):\nStep 1: Set up the conversion chain with unity factors:\n$v = 720\\text{ }\\frac{\\text{km}}{\\text{h}} \\times \\left(\\frac{10^3\\text{ m}}{1\\text{ km}}\\right) \\times \\left(\\frac{1\\text{ h}}{3,600\\text{ s}}\\right)$\nStep 2: Cancel units: $\\text{km}$ cancels $\\text{km}$; $\\text{h}$ cancels $\\text{h}$, leaving $\\text{m/s}$:\n$v = \\frac{720 \\times 10^3}{3,600}\\text{ m/s} = \\frac{720,000}{3,600}\\text{ m/s} = 200\\text{ m/s}$\n\nPart (b):\nStep 1: Dimensions of $KE = \\frac{1}{2}mv^2$: Constant $\\frac{1}{2}$ is dimensionless. Dimension of $m$ is $[M]$. Dimension of $v^2$ is $([L][T]^{-1})^2 = [L]^2[T]^{-2}$. Therefore: $[KE] = [M][L]^2[T]^{-2}$.\nStep 2: Dimensions of $W = F \\cdot d$: $[F] = [M][L][T]^{-2}$ and $[d] = [L]$. Therefore: $[W] = [M][L][T]^{-2} \\cdot [L] = [M][L]^2[T]^{-2}$.\nConclusion: Both expressions share identical net dimensions $[M][L]^2[T]^{-2}$, confirming dimensional homogeneity.",
        "practice": {
            "title": "Practice Guide — Physical Quantities and Units",
            "core": "Drill multi-stage metric conversions using factor-label cancellation, verify dimensional homogeneity of kinematics and dynamic formulas by decomposing variables into base dimensions $[M][L][T]$, and apply sig fig rules in arithmetic.",
            "combine": "Combine powers of 10 and scientific notation [[MTH-T01-C08-U01]] with fraction multiplication cross-cancellation [[MTH-T01-C04-U02]] to cancel units cleanly.",
            "traps": "Inverted Conversion Ratio Trap: Multiplying by $\\frac{1\\text{ km}}{10^3\\text{ m}}$ instead of $\\frac{10^3\\text{ m}}{1\\text{ km}}$, producing an incorrect unit power. Squared/Cubed Unit Trap: When converting $5\\text{ m}^2$ to $\\text{cm}^2$, forgetting to square the conversion factor ($1\\text{ m} = 100\\text{ cm} \\implies 1\\text{ m}^2 = 10,000\\text{ cm}^2$).",
            "cross": "Programming ([[PRG-T01]]): Mars Climate Orbiter crash prevention—strongly typing units in software engineering to prevent mismatched imperial/metric data passing between microservices."
        },
        "recall": [
            ("Why is dimensional analysis alone insufficient to prove that a physics equation is completely correct?", "Dimensional analysis can verify that units on both sides match, but it cannot detect dimensionless constant multipliers (such as the $\\frac{1}{2}$ in $\\frac{1}{2}at^2$) or missing dimensionless scalar terms."),
            ("How many significant figures are in the measurement $0.005040\\text{ kg}$, and what is its value in scientific notation?", "It has 4 significant figures (the leading zeros are place-holders; the 5, 0, 4, and trailing 0 are significant). In scientific notation: $5.040 \\times 10^{-3}\\text{ kg}$.")
        ]
    },

    # =========================================================================
    # CHAPTER C02: Motion in One Dimension (4 Units)
    # =========================================================================
    "PHY-T01-C02-U01": {
        "title": "Relative Motion, Distance, and Displacement",
        "chapter": "PHY-T01-C02",
        "obj": "Distinguish between reference frames, scalar distance, and signed vector displacement $\\Delta x = x_f - x_i$ along a one-dimensional coordinate axis.",
        "out": "Compute scalar distance and vector displacement for multi-stage 1D journeys and represent position vectors on a signed number line.",
        "prereq": "[[PHY-T01-C01-U03]], [[MTH-T01-C03-U01]]",
        "next": "[[PHY-T01-C02-U02]]",
        "source": "OpenStax Physics — Section 2.1: Relative Motion, Distance, and Displacement",
        "concepts": [
            "Frames of Reference: All motion is relative. A frame of reference defines an origin $x = 0$, a positive direction, and a clock starting at $t = 0$.",
            "Distance (Scalar): Distance $d$ is the total length of the path traveled. It is always positive or zero ($d \\ge 0$) and has no direction.",
            "Displacement (Vector): Displacement $\\Delta x$ is the direct net change in position: $\\Delta x = x_f - x_i$ ($x_f$: final position, $x_i$: initial position). In 1D, direction is communicated solely by the sign: $+ \\Delta x$ indicates motion in the positive direction (right/east/up); $- \\Delta x$ indicates motion in the negative direction (left/west/down)."
        ],
        "formulas": [
            "\\text{Displacement Definition: } \\Delta x = x_f - x_i",
            "\\text{Total Distance: } d = \\sum |\\Delta x_k| = |\\Delta x_1| + |\\Delta x_2| + \\dots + |\\Delta x_n|"
        ],
        "worked": "Example: A warehouse robot starts at charging dock $x_0 = +15\\text{ m}$. It moves to pick up a package at $x_1 = +45\\text{ m}$, then delivers it to packing station $x_2 = -25\\text{ m}$.\n(a) What is the robot's net displacement for the entire trip?\n(b) What is the total distance traveled by the robot?\n\nPart (a) Displacement:\n$\\Delta x = x_f - x_i = x_2 - x_0 = (-25\\text{ m}) - (+15\\text{ m}) = -40\\text{ m}$\nThe net displacement is $40\\text{ m}$ in the negative direction.\n\nPart (b) Total Distance:\nSegment 1: $|x_1 - x_0| = |45 - 15| = 30\\text{ m}$.\nSegment 2: $|x_2 - x_1| = |-25 - 45| = |-70| = 70\\text{ m}$.\n$d = 30\\text{ m} + 70\\text{ m} = 100\\text{ m}$\nNotice that total distance ($100\\text{ m}$) is significantly larger than the magnitude of net displacement ($|-40\\text{ m}| = 40\\text{ m}$).",
        "practice": {
            "title": "Practice Guide — Relative Motion, Distance, and Displacement",
            "core": "Drill calculating scalar distance ($d = \\Sigma |\\Delta x_k|$) versus vector displacement ($\\Delta x = x_f - x_i$) for multi-segment rectilinear journeys crossing zero on the coordinate axis.",
            "combine": "Combine signed integer subtraction [[MTH-T01-C03-U03]] with absolute value as distance [[MTH-T01-C03-U01]] to ensure directional signs are tracked accurately.",
            "traps": "Initial-Minus-Final Inversion Trap: Computing $x_i - x_f$ instead of $x_f - x_i$, reversing the true vector displacement sign. Displacement-Distance Conflation: Assuming that because an object returned to its origin ($x_f = x_i \\implies \\Delta x = 0$), the distance traveled must also be zero.",
            "cross": "Programming ([[PRG-T01]]): Tracking game character movement vectors vs total odometer telemetry counters in navigation algorithms."
        },
        "recall": [
            ("Can the magnitude of displacement ever exceed the total distance traveled for any physical journey?", "No. Distance is the total path length, while displacement magnitude is the straight-line shortcut between endpoints. Displacement magnitude is always less than or equal to distance: $|\\Delta x| \\le d$."),
            ("If a cyclist rides 3 complete laps around a $400\\text{ m}$ circular track, what are the cyclist's total distance and net displacement?", "Total distance $d = 3 \\times 400\\text{ m} = 1,200\\text{ m}$. Net displacement $\\Delta x = 0\\text{ m}$ because the starting and ending positions are identical.")
        ]
    },

    "PHY-T01-C02-U02": {
        "title": "Speed and Velocity",
        "chapter": "PHY-T01-C02",
        "obj": "Distinguish between average speed and average velocity, compute constant velocity, and relate rate of change to rectilinear motion.",
        "out": "Calculate average speed and average velocity from multi-segment distance/displacement and elapsed time data, solving for time or position.",
        "prereq": "[[PHY-T01-C02-U01]], [[MTH-T01-C07-U02]], [[MTH-T01-C11-U01]]",
        "next": "[[PHY-T01-C02-U03]]",
        "source": "OpenStax Physics — Section 2.2: Speed and Velocity",
        "concepts": [
            "Average Speed (Scalar): Average speed is defined as the total distance traveled divided by the total elapsed time: $s_{\\text{avg}} = \\frac{d}{\\Delta t}$. Speed is strictly non-negative ($s \\ge 0$).",
            "Average Velocity (Vector): Average velocity is defined as the net displacement divided by the elapsed time: $\\vec{v}_{\\text{avg}} = \\frac{\\Delta x}{\\Delta t} = \\frac{x_f - x_i}{t_f - t_i}$. The sign of velocity indicates the direction of motion ($+$ for rightward/upward, $-$ for leftward/downward).",
            "Constant Velocity Model: When an object moves with uniform constant velocity $v$, its position increases linearly with time: $x(t) = x_0 + v t$."
        ],
        "formulas": [
            "\\text{Average Speed: } s_{\\text{avg}} = \\frac{\\text{Total Distance}}{\\Delta t} = \\frac{d}{\\Delta t}",
            "\\text{Average Velocity: } \\vec{v}_{\\text{avg}} = \\frac{\\text{Net Displacement}}{\\Delta t} = \\frac{\\Delta x}{\\Delta t} = \\frac{x_f - x_i}{t_f - t_i}",
            "\\text{Uniform Motion Equation: } x_f = x_i + v \\cdot t \\iff \\Delta x = v \\cdot t"
        ],
        "worked": "Example: A motorist drives $60\\text{ km}$ north at $60\\text{ km/h}$, then immediately drives $60\\text{ km}$ south at $30\\text{ km/h}$.\n(a) Compute the total elapsed time.\n(b) Compute the average speed for the entire round trip.\n(c) Compute the average velocity for the entire round trip.\n\nPart (a) Time for each leg:\n$t_1 = \\frac{d_1}{s_1} = \\frac{60\\text{ km}}{60\\text{ km/h}} = 1.0\\text{ h}$\n$t_2 = \\frac{d_2}{s_2} = \\frac{60\\text{ km}}{30\\text{ km/h}} = 2.0\\text{ h}$\n$\\text{Total time } \\Delta t = t_1 + t_2 = 1.0\\text{ h} + 2.0\\text{ h} = 3.0\\text{ h}$\n\nPart (b) Average Speed:\n$\\text{Total distance } d = 60\\text{ km} + 60\\text{ km} = 120\\text{ km}$\n$s_{\\text{avg}} = \\frac{d}{\\Delta t} = \\frac{120\\text{ km}}{3.0\\text{ h}} = 40\\text{ km/h}$\n*(Notice: $40\\text{ km/h} \\ne \\frac{60 + 30}{2} = 45\\text{ km/h}$ because more time was spent at the slower speed!)*\n\nPart (c) Average Velocity:\n$\\Delta x = (+60\\text{ km}) + (-60\\text{ km}) = 0\\text{ km}$\n$v_{\\text{avg}} = \\frac{\\Delta x}{\\Delta t} = \\frac{0\\text{ km}}{3.0\\text{ h}} = 0\\text{ km/h}$",
        "practice": {
            "title": "Practice Guide — Speed and Velocity",
            "core": "Drill multi-segment trip analysis calculating total time, total distance, net displacement, average speed, and average velocity. Solve for elapsed time or final position in uniform motion ($x_f = x_i + vt$).",
            "combine": "Combine unit rate division [[MTH-T01-C07-U02]] with single-variable linear equation solving [[MTH-T01-C11-U01]] ($t = \\frac{d}{v}$).",
            "traps": "The Simple Average Trap: Averaging $v_1$ and $v_2$ directly as $\\frac{v_1 + v_2}{2}$ without weighting by time. Velocity Sign Loss: Dropping the negative sign when computing displacement from velocity: $\\Delta x = (-15\\text{ m/s}) \\times 4\\text{ s} = -60\\text{ m}$.",
            "cross": "Programming ([[PRG-T01]]): Rate limiting and throughput calculations in network protocols—bytes delivered divided by connection window time mirrors average velocity."
        },
        "recall": [
            ("Why is the average speed of a two-leg trip of equal distances NOT simply the arithmetic mean of the two speeds?", "Because the traveler spends more time traveling during the slower leg than during the faster leg. Average speed must be weighted by time elapsed: $s_{\\text{avg}} = \\frac{d_{\\text{total}}}{t_1 + t_2}$."),
            ("Under what condition are average speed and the magnitude of average velocity exactly equal?", "Only when the object moves along a straight line in a single, unchanging direction without turning back ($d = |\\Delta x|$).")
        ]
    },

    "PHY-T01-C02-U03": {
        "title": "Position vs. Time Graphs",
        "chapter": "PHY-T01-C02",
        "obj": "Extract physical motion details from position-time ($x-t$) graphs, compute slope as velocity, and translate between graphical and verbal descriptions.",
        "out": "Determine velocity and direction of motion by calculating the rise-over-run slope of position-time graphs and sketch graphs from motion scenarios.",
        "prereq": "[[PHY-T01-C02-U02]], [[MTH-T01-C14-U01]], [[MTH-T01-C14-U04]]",
        "next": "[[PHY-T01-C02-U04]]",
        "source": "OpenStax Physics — Section 2.3: Position vs. Time Graphs",
        "concepts": [
            "Slope Equals Velocity: On a position-time ($x-t$) graph, position $x$ is on the vertical axis and time $t$ is on the horizontal axis. The slope of the line is the velocity:\n$\\text{Slope} = \\frac{\\Delta x}{\\Delta t} = \\frac{x_2 - x_1}{t_2 - t_1} = v$\n",
            "Interpreting Graph Topologies:\n• **Horizontal Flat Line (Slope = 0):** The object is stationary (at rest).\n• **Straight Diagonal Upward (Positive Slope):** Moving in the positive direction at constant velocity.\n• **Straight Diagonal Downward (Negative Slope):** Moving in the negative direction at constant velocity.\n• **Steepness:** The steeper the slope, the greater the speed.",
            "Sign of Position vs. Sign of Velocity: A body can have a positive position ($x > 0$, above the t-axis) while possessing a negative velocity (downward slope, moving towards origin)."
        ],
        "formulas": [
            "\\text{Graph Slope Equation: } v = \\text{Slope} = \\frac{\\text{Rise}}{\\text{Run}} = \\frac{x_2 - x_1}{t_2 - t_1}"
        ],
        "worked": "Example: A position-time graph has three linear segments:\nSegment A: From $(t=0\\text{ s}, x=0\\text{ m})$ to $(t=4\\text{ s}, x=24\\text{ m})$.\nSegment B: From $(t=4\\text{ s}, x=24\\text{ m})$ to $(t=7\\text{ s}, x=24\\text{ m})$.\nSegment C: From $(t=7\\text{ s}, x=24\\text{ m})$ to $(t=9\\text{ s}, x=0\\text{ m})$.\nCalculate the velocity for each segment.\n\nSegment A:\n$v_A = \\frac{x_2 - x_1}{t_2 - t_1} = \\frac{24 - 0}{4 - 0} = +6.0\\text{ m/s} \\quad (\\text{Moving forward at } 6\\text{ m/s})$\n\nSegment B:\n$v_B = \\frac{24 - 24}{7 - 4} = \\frac{0}{3} = 0.0\\text{ m/s} \\quad (\\text{At rest for } 3\\text{ seconds})$\n\nSegment C:\n$v_C = \\frac{0 - 24}{9 - 7} = \\frac{-24}{2} = -12.0\\text{ m/s} \\quad (\\text{Moving backward towards origin at } 12\\text{ m/s})$",
        "practice": {
            "title": "Practice Guide — Position vs. Time Graphs",
            "core": "Drill calculating velocities from linear segments on $x-t$ graphs using rise-over-run slope formula. Translate piecewise $x-t$ graphs into verbal motion stories and identify stationary intervals.",
            "combine": "Combine Cartesian slope calculation [[MTH-T01-C14-U04]] ($m = \\frac{y_2 - y_1}{x_2 - x_1}$) with signed coordinate navigation [[PHY-T01-C02-U01]].",
            "traps": "The Trajectory Confusion Trap: Viewing an $x-t$ graph as a physical roller-coaster path or curved hill in space (it is a plot of 1D line position versus elapsed time!). Slope Inversion: Dividing time run by position rise ($\\frac{\\Delta t}{\\Delta x}$) instead of rise over run.",
            "cross": "Programming ([[PRG-T01]]): Chart rendering libraries (D3.js, Chart.js) and interpolating keyframe animations across timeline curves."
        },
        "recall": [
            ("What does the vertical intercept (y-intercept) represent on a position-time graph?", "It represents the initial position of the object ($x_0$) at time $t = 0$."),
            ("If an object on an $x-t$ graph is located at $x = -50\\text{ m}$ but the slope of the line is $+10\\text{ m/s}$, where is the object moving?", "The object is currently located on the negative side of the origin but is moving forward (in the positive direction) towards the origin at $10\\text{ m/s}$.")
        ]
    },

    "PHY-T01-C02-U04": {
        "title": "Velocity vs. Time Graphs",
        "chapter": "PHY-T01-C02",
        "obj": "Interpret velocity-time ($v-t$) graphs for uniform motion, explain why horizontal lines represent zero acceleration, and compute displacement from the area under the curve.",
        "out": "Calculate displacement by evaluating rectangular geometric areas under horizontal velocity-time graphs, tracking positive and negative area signs.",
        "prereq": "[[PHY-T01-C02-U03]], [[MTH-T01-C12-U01]]",
        "next": "[[PHY-T01-C03-U01]]",
        "source": "OpenStax Physics — Section 2.4: Velocity vs. Time Graphs",
        "concepts": [
            "Uniform Motion on $v-t$ Graphs: When an object moves with constant velocity, its velocity does not change over time. Its $v-t$ graph is a horizontal line with slope equal to zero (acceleration $a = 0$).",
            "Displacement Equals Area Under the Curve: For any velocity-time graph, the area between the velocity curve and the horizontal time axis represents displacement:\n$\\text{Displacement } \\Delta x = \\text{Area} = v \\cdot \\Delta t$\n",
            "Sign of Geometric Area:\n• Area above the time axis ($v > 0$) represents positive displacement ($+ \\Delta x$).\n• Area below the time axis ($v < 0$) represents negative displacement ($- \\Delta x$).\n• Net displacement is the algebraic sum of positive and negative areas: $\\Delta x = A_{\\text{above}} - A_{\\text{below}}$."
        ],
        "formulas": [
            "\\text{Displacement as Area: } \\Delta x = \\text{Base} \\times \\text{Height} = \\Delta t \\times v"
        ],
        "worked": "Example: A laboratory cart moves along a track with the following velocity profile:\nSegment 1: $v = +4.0\\text{ m/s}$ from $t = 0\\text{ s}$ to $t = 5\\text{ s}$.\nSegment 2: $v = 0.0\\text{ m/s}$ from $t = 5\\text{ s}$ to $t = 8\\text{ s}$.\nSegment 3: $v = -2.0\\text{ m/s}$ from $t = 8\\text{ s}$ to $t = 12\\text{ s}$.\nCompute the cart's net displacement and total distance traveled.\n\nStep 1: Calculate area of each rectangle:\n$\\text{Area}_1 = v_1 \\cdot \\Delta t_1 = (+4.0\\text{ m/s}) \\times (5 - 0\\text{ s}) = +20.0\\text{ m}$\n$\\text{Area}_2 = v_2 \\cdot \\Delta t_2 = (0.0\\text{ m/s}) \\times (8 - 5\\text{ s}) = 0.0\\text{ m}$\n$\\text{Area}_3 = v_3 \\cdot \\Delta t_3 = (-2.0\\text{ m/s}) \\times (12 - 8\\text{ s}) = -8.0\\text{ m}$\n\nStep 2: Net displacement is algebraic sum:\n$\\Delta x = (+20.0\\text{ m}) + 0.0\\text{ m} + (-8.0\\text{ m}) = +12.0\\text{ m}$\n\nStep 3: Total distance is sum of absolute areas:\n$d = |+20.0\\text{ m}| + 0.0\\text{ m} + |-8.0\\text{ m}| = 20.0\\text{ m} + 8.0\\text{ m} = 28.0\\text{ m}$",
        "practice": {
            "title": "Practice Guide — Velocity vs. Time Graphs",
            "core": "Drill computing net displacement and total distance from piecewise horizontal $v-t$ graphs by calculating rectangular areas above and below the time axis. Correlate $x-t$ slope with $v-t$ height.",
            "combine": "Combine geometric rectangle area [[MTH-T01-C12-U01]] ($A = l \\cdot w$) with signed integer summation [[MTH-T01-C03-U02]].",
            "traps": "Missing Negative Area Trap: Adding negative areas as positive when computing net displacement, confusing displacement with distance. Confusing $x-t$ and $v-t$ Meaning: Thinking a horizontal line on a $v-t$ graph means the object is stationary (it is moving at constant velocity!).",
            "cross": "Programming ([[PRG-T01]]): Numerical integration (Riemann sum) in simulation physics—approximating continuous integrals by summing discrete rectangular slices $\\sum v_i \\Delta t$."
        },
        "recall": [
            ("What physical quantity is represented by the slope of a velocity-time graph?", "Acceleration (the time rate of change of velocity: $a = \\frac{\\Delta v}{\\Delta t}$)."),
            ("On a $v-t$ graph, what does a horizontal line at $v = -5\\text{ m/s}$ indicate about the object's motion?", "The object is moving backwards (in the negative direction) at a steady, constant speed of $5\\text{ m/s}$ with zero acceleration.")
        ]
    },

    # =========================================================================
    # CHAPTER C03: Acceleration (2 Units)
    # =========================================================================
    "PHY-T01-C03-U01": {
        "title": "Acceleration",
        "chapter": "PHY-T01-C03",
        "obj": "Define average acceleration as $a_{\\text{avg}} = \\frac{\\Delta v}{\\Delta t}$, understand SI units $\\text{m/s}^2$, and determine whether an object is speeding up or slowing down by comparing the signs of $v$ and $a$.",
        "out": "Compute average acceleration from initial/final velocities and elapsed time, and correctly classify motion as speeding up or slowing down from sign pairs.",
        "prereq": "[[PHY-T01-C02-U04]], [[MTH-T01-C03-U03]], [[MTH-T01-C11-U02]]",
        "next": "[[PHY-T01-C03-U02]]",
        "source": "OpenStax Physics — Section 3.1: Acceleration",
        "concepts": [
            "Definition of Acceleration: Acceleration is the vector rate at which velocity changes over time: $\\vec{a}_{\\text{avg}} = \\frac{\\Delta \\vec{v}}{\\Delta t} = \\frac{\\vec{v}_f - \\vec{v}_0}{\\Delta t}$. Its SI unit is meters per second squared ($\\text{m/s}^2$). An acceleration of $+4\\text{ m/s}^2$ means the velocity increases by $4\\text{ m/s}$ every second.",
            "The Four Sign Scenarios of Acceleration:\n1. $v > 0, a > 0$: Moving in positive direction and **speeding up**.\n2. $v > 0, a < 0$: Moving in positive direction and **slowing down** (decelerating).\n3. $v < 0, a < 0$: Moving in negative direction and **speeding up** (becoming more negative).\n4. $v < 0, a > 0$: Moving in negative direction and **slowing down** (approaching zero).",
            "Key Principle: An object **speeds up** when velocity and acceleration have the **same sign**; an object **slows down** when velocity and acceleration have **opposite signs**."
        ],
        "formulas": [
            "\\text{Average Acceleration: } \\vec{a}_{\\text{avg}} = \\frac{\\Delta \\vec{v}}{\\Delta t} = \\frac{\\vec{v}_f - \\vec{v}_0}{t_f - t_0}",
            "\\text{Rearranged for Final Velocity: } \\vec{v}_f = \\vec{v}_0 + \\vec{a} \\cdot t"
        ],
        "worked": "Example: Analyze the acceleration and motion type for the following two independent scenarios:\n(a) A motorcycle traveling east at $+10\\text{ m/s}$ speeds up to $+26\\text{ m/s}$ in $4.0\\text{ s}$.\n(b) A train moving west at $-30\\text{ m/s}$ brakes to $-10\\text{ m/s}$ in $5.0\\text{ s}$.\n\nScenario (a):\n$a_a = \\frac{v_f - v_0}{\\Delta t} = \\frac{26 - 10}{4.0} = \\frac{+16\\text{ m/s}}{4.0\\text{ s}} = +4.0\\text{ m/s}^2$\nSince $v > 0$ and $a > 0$ share the same sign, the motorcycle is **speeding up** in the positive direction.\n\nScenario (b):\n$a_b = \\frac{(-10) - (-30)}{5.0} = \\frac{-10 + 30}{5.0} = \\frac{+20\\text{ m/s}}{5.0\\text{ s}} = +4.0\\text{ m/s}^2$\nNotice: Acceleration is $+4.0\\text{ m/s}^2$ (positive!), while velocity is negative ($v < 0$). Because $v$ and $a$ have opposite signs, the train is **slowing down** while traveling in the negative direction.",
        "practice": {
            "title": "Practice Guide — Acceleration",
            "core": "Drill computing average acceleration with signed initial and final velocities. Test sign combinations ($++$, $+-$, $--$, $-+$) to instantly classify whether a body is speeding up or slowing down without relying on intuition.",
            "combine": "Combine signed integer subtraction [[MTH-T01-C03-U03]] ($v_f - v_0$) with linear equation solving [[MTH-T01-C11-U02]] ($v_f = v_0 + at$).",
            "traps": "The Deceleration-is-Negative Fallacy: Believing deceleration must always have a negative sign (Scenario (b) proves that an object moving in the negative direction slows down with a POSITIVE acceleration!). Zero Velocity Myth: Assuming zero velocity implies zero acceleration.",
            "cross": "Programming ([[PRG-T01]]): Designing vehicle throttle and brake dynamics in game development—decoupling velocity vectors from acceleration vectors."
        },
        "recall": [
            ("If a car has a negative velocity and a negative acceleration ($v < 0, a < 0$), is its speed increasing or decreasing?", "Its speed is INCREASING (it is speeding up in the negative direction, because velocity and acceleration share the same sign)."),
            ("Can an object have a northward velocity while experiencing a southward acceleration?", "Yes. When an object moves northward ($v > 0$) while braking or slowing down, its acceleration points southward ($a < 0$, opposite to velocity).")
        ]
    },

    "PHY-T01-C03-U02": {
        "title": "Representing Acceleration with Equations and Graphs",
        "chapter": "PHY-T01-C03",
        "obj": "Apply the linear kinematics equation $v_f = v_0 + at$, interpret slope on $v-t$ graphs as acceleration, compute displacement from triangular areas for motion from rest $\\Delta x = \\frac{1}{2}at^2$, and solve free-fall drop problems.",
        "out": "Solve single-variable linear and square-root kinematic problems for bodies under uniform acceleration starting from rest, and extract acceleration from slopes of $v-t$ graphs.",
        "prereq": "[[PHY-T01-C03-U01]], [[MTH-T01-C09-U01]], [[MTH-T01-C12-U02]], [[MTH-T01-C14-U04]]",
        "next": "[[PHY-T01-C04-U01]]",
        "source": "OpenStax Physics — Section 3.2: Representing Acceleration with Equations and Graphs",
        "concepts": [
            "Slope of $v-t$ Graph: On any velocity-time graph, the slope is the instantaneous or average acceleration:\n$\\text{Slope} = \\frac{\\Delta v}{\\Delta t} = a$\n",
            "Motion Starting from Rest ($v_0 = 0$): When an object starts from rest and accelerates uniformly at $a$:\n• Final velocity after time $t$: $v_f = a \\cdot t$\n• On a $v-t$ graph, the area is a right triangle with base $t$ and height $v_f = at$:\n$\\Delta x = \\text{Area} = \\frac{1}{2} \\times \\text{base} \\times \\text{height} = \\frac{1}{2} \\cdot t \\cdot (at) = \\frac{1}{2}at^2$\n",
            "Free Fall Under Gravity: Near Earth's surface, all objects in free fall experience constant downward gravitational acceleration $g = 9.8\\text{ m/s}^2 \\approx 10\\text{ m/s}^2$ (taking downward as positive: $v_f = gt$, $h = \\frac{1}{2}gt^2$). Solving for drop time requires the square root: $t = \\sqrt{\\frac{2h}{g}}$."
        ],
        "formulas": [
            "\\text{Linear Kinematic Equation: } v_f = v_0 + a \\cdot t",
            "\\text{Displacement from Rest: } \\Delta x = \\frac{1}{2} a t^2 \\quad (v_0 = 0)",
            "\\text{Free Fall Drop Time: } t = \\sqrt{\\frac{2h}{g}} \\quad (v_0 = 0, \\text{ downward direction})"
        ],
        "worked": "Example: An engineering drone drops a calibration weight from rest ($v_0 = 0$) from a hovering altitude of $h = 45\\text{ m}$. Assume $g = 10\\text{ m/s}^2$ and negligible air resistance.\n(a) How long does the weight take to reach the ground?\n(b) What is its impact velocity right before striking the ground?\n\nPart (a) Drop Time:\nUsing $h = \\frac{1}{2}gt^2$ with $h = 45\\text{ m}$ and $g = 10\\text{ m/s}^2$:\n$45 = \\frac{1}{2}(10) t^2 \\implies 45 = 5 t^2$\nDivide both sides by 5:\n$t^2 = \\frac{45}{5} = 9$\nTake the principal square root [[MTH-T01-C09-U01]]:\n$t = \\sqrt{9} = 3.0\\text{ s}$\n\nPart (b) Impact Velocity:\nUsing $v_f = v_0 + gt$:\n$v_f = 0 + (10\\text{ m/s}^2)(3.0\\text{ s}) = 30\\text{ m/s}$\nSanity Check: Average velocity $v_{\\text{avg}} = \\frac{0 + 30}{2} = 15\\text{ m/s}$. Displacement $h = v_{\\text{avg}} \\times t = 15\\text{ m/s} \\times 3\\text{ s} = 45\\text{ m}$. Matches perfectly!",
        "practice": {
            "title": "Practice Guide — Representing Acceleration with Equations and Graphs",
            "core": "Drill computing acceleration from slopes of linear $v-t$ segments. Solve for drop time ($t = \\sqrt{2h/g}$) and impact velocity for bodies accelerated from rest under constant acceleration without quadratic formula complexity.",
            "combine": "Combine triangular area geometry [[MTH-T01-C12-U02]] ($A = \\frac{1}{2}bh$) with square-root evaluation [[MTH-T01-C09-U01]] to isolate $t$.",
            "traps": "Missing Half Factor: Writing $\\Delta x = at^2$ instead of $\\frac{1}{2}at^2$, doubling the true displacement. Non-Zero $v_0$ Extension Note: Attempting to use $\\Delta x = \\frac{1}{2}at^2$ when $v_0 \\ne 0$ (when $v_0 \\ne 0$, solving for $t$ requires the quadratic formula, which is deferred to [[MTH-T02-C01]]).",
            "cross": "Programming ([[PRG-T01]]): Designing jump mechanics in platformer video games—gravity constants and terminal velocity clamps."
        },
        "recall": [
            ("Why is the displacement under a linear $v-t$ graph starting from rest equal to $\\frac{1}{2}at^2$ rather than $at^2$?", "Because the velocity increases linearly from $0$ to $at$. The area under the graph is a triangle with base $t$ and height $at$: $\\text{Area} = \\frac{1}{2} \\times \\text{base} \\times \\text{height} = \\frac{1}{2}at^2$."),
            ("If you drop an object from a height of $4h$ instead of $h$, how many times longer does it take to hit the ground?", "It takes $\\sqrt{4} = 2$ times as long, because drop time is proportional to the square root of height ($t = \\sqrt{\\frac{2h}{g}}$).")
        ]
    },

    # =========================================================================
    # CHAPTER C04: Forces and Newton's Laws of Motion (4 Units)
    # =========================================================================
    "PHY-T01-C04-U01": {
        "title": "Force",
        "chapter": "PHY-T01-C04",
        "obj": "Define force as a vector interaction (push or pull), distinguish contact from field forces, draw 1D Free-Body Diagrams (FBDs), and compute net force via signed addition.",
        "out": "Construct 1D Free-Body Diagrams showing all collinear forces and calculate net force $F_{\\text{net}} = \\Sigma F$ with directional signs.",
        "prereq": "[[PHY-T01-C02-U01]], [[MTH-T01-C03-U02]]",
        "next": "[[PHY-T01-C04-U02]]",
        "source": "OpenStax Physics — Section 4.1: Force",
        "concepts": [
            "Force as a Vector: A force is a push or pull that can cause an object with mass to change its velocity (accelerate). Force is a vector quantity with magnitude and direction, measured in Newtons ($\\text{N}$).",
            "Contact vs. Field Forces:\n• **Contact Forces:** Arise from physical contact between surfaces (applied force $F_{\\text{app}}$, normal force $F_N$, friction $f$, tension $T$).\n• **Field (Non-Contact) Forces:** Act over distance without physical contact (gravitational force/weight $w$, electrostatic force, magnetic force).",
            "1D Free-Body Diagrams (FBDs): An FBD isolates a single body as a point and draws all external forces acting ON that body as vector arrows pointing away from the center. In 1D, forces are signed (+ for right/up, - for left/down).",
            "Net Force: Net force is the single vector sum of all collinear forces acting on the object: $F_{\\text{net}} = \\Sigma F = F_1 + F_2 + \\dots + F_n$."
        ],
        "formulas": [
            "\\text{1D Net Force: } F_{\\text{net}} = \\sum F = F_{\\text{right}} - F_{\\text{left}}"
        ],
        "worked": "Example: A $20\\text{ kg}$ box rests on a warehouse floor. Worker A pushes to the right with $F_1 = +85\\text{ N}$. Worker B pushes to the right with $F_2 = +60\\text{ N}$. A opposing kinetic friction force of $f = 45\\text{ N}$ acts to the left.\n(a) Sketch the 1D horizontal Free-Body Diagram.\n(b) Calculate the net horizontal force acting on the box.\n\nStep 1: Assign signs based on coordinate direction (right $= +$, left $= -$):\n$F_1 = +85\\text{ N}, \\quad F_2 = +60\\text{ N}, \\quad f = -45\\text{ N}$\n\nStep 2: Compute net force via algebraic sum [[MTH-T01-C03-U02]]:\n$F_{\\text{net}} = \\Sigma F = F_1 + F_2 + f$\n$F_{\\text{net}} = (+85\\text{ N}) + (+60\\text{ N}) + (-45\\text{ N}) = 145\\text{ N} - 45\\text{ N} = +100\\text{ N}$\nThe net force is $100\\text{ N}$ directed to the right.",
        "practice": {
            "title": "Practice Guide — Force",
            "core": "Drill constructing 1D horizontal and vertical Free-Body Diagrams. Calculate net force $F_{\\text{net}} = \\Sigma F$ by summing signed contact and field forces and identifying equilibrium states ($F_{\\text{net}} = 0$).",
            "combine": "Combine signed integer addition [[MTH-T01-C03-U02]] with 1D vector directional signs [[PHY-T01-C02-U01]].",
            "traps": "Internal Force Trap: Including internal forces (forces objects exert on themselves or between internal components) on an FBD (only external forces acting ON the body belong on an FBD!). Unbalanced Normal Force assumption: assuming $F_N$ always acts upwards regardless of contact plane.",
            "cross": "Programming ([[PRG-T01]]): Force accumulators in physics engines—`applyForce(forceVector)` summing into `netForce` before each Euler step."
        },
        "recall": [
            ("What is the difference between a contact force and a field force? Give one example of each.", "A contact force requires physical contact between surfaces (e.g. friction or push force), whereas a field force acts across empty space without contact (e.g. gravity)."),
            ("If an object experiences a forward force of $50\\text{ N}$ and a backward resistive force of $50\\text{ N}$, what is the net force acting on the object?", "The net force is $F_{\\text{net}} = +50\\text{ N} - 50\\text{ N} = 0\\text{ N}$ (the forces are balanced).")
        ]
    },

    "PHY-T01-C04-U02": {
        "title": "Newton's First Law of Motion: Inertia",
        "chapter": "PHY-T01-C04",
        "obj": "State Newton's First Law of Motion, explain inertia and its relationship to mass, define translational equilibrium $\\Sigma F = 0$, and distinguish between zero velocity and constant velocity.",
        "out": "Apply Newton's First Law to analyze objects in equilibrium ($F_{\\text{net}} = 0$) and explain physical everyday scenarios using the principle of inertia.",
        "prereq": "[[PHY-T01-C04-U01]], [[MTH-T01-C02-U03]], [[MTH-T01-C11-U01]]",
        "next": "[[PHY-T01-C04-U03]]",
        "source": "OpenStax Physics — Section 4.2: Newton's First Law of Motion: Inertia",
        "concepts": [
            "Newton's First Law of Motion (Law of Inertia): An object at rest remains at rest, and an object in motion continues in motion at a constant velocity (constant speed in a straight line), unless acted upon by a nonzero net external force.",
            "Inertia and Mass: Inertia is the natural resistance of any physical object to any change in its state of motion (velocity). Mass ($m$) is the quantitative scalar measure of inertia. The more mass an object has, the greater its inertia, and the harder it is to change its velocity.",
            "Translational Equilibrium: When the net force acting on an object is zero ($F_{\\text{net}} = \\Sigma F = 0$), the object is in translational equilibrium. This means acceleration is strictly zero ($a = 0$):\n• **Static Equilibrium:** The object is at rest ($v = 0, a = 0$).\n• **Dynamic Equilibrium:** The object moves at constant velocity in a straight line ($v = \\text{constant} \\ne 0, a = 0$).",
            "Aristotle vs. Galileo/Newton: A force is NOT required to keep an object moving! In the absence of friction, an object keeps moving forever on its own. Force is required only to CHANGE motion."
        ],
        "formulas": [
            "\\text{Condition for Translational Equilibrium: } F_{\\text{net}} = \\sum F = 0 \\iff a = 0 \\iff v = \\text{constant}"
        ],
        "worked": "Example: A heavy $80\\text{ kg}$ crate is pushed across a rough warehouse floor at a constant speed of $2.0\\text{ m/s}$ in a straight line. The worker applies a constant horizontal forward force of $250\\text{ N}$.\n(a) What is the acceleration of the crate?\n(b) What is the net force acting on the crate?\n(c) What is the magnitude of the friction force opposing the crate?\n\nStep 1: Check the motion state: The crate moves at 'constant speed in a straight line'. By definition, constant velocity means acceleration is zero: $a = 0\\text{ m/s}^2$.\nStep 2: By Newton's First Law, zero acceleration implies net force is zero: $F_{\\text{net}} = 0\\text{ N}$.\nStep 3: Set up the 1D equilibrium equation [[MTH-T01-C11-U01]]:\n$F_{\\text{net}} = F_{\\text{push}} - f = 0$\n$250\\text{ N} - f = 0 \\implies f = 250\\text{ N}$\nThe friction force is exactly $250\\text{ N}$ backwards. The forces balance out completely, allowing constant velocity motion.",
        "practice": {
            "title": "Practice Guide — Newton's First Law of Motion: Inertia",
            "core": "Drill identifying equilibrium states ($F_{\\text{net}} = 0$) from verbal descriptions (at rest or constant velocity). Solve for unknown balancing forces using 1-step balance equations ($F_{\\text{forward}} = F_{\\text{friction}}$).",
            "combine": "Combine one-step linear equation balance [[MTH-T01-C02-U03]] with uniform motion speed concepts [[PHY-T01-C02-U02]].",
            "traps": "The Aristotelian Motion Trap: Believing that because a car is moving forward at $100\\text{ km/h}$, there must be a forward net force (if speed is constant, net force is EXACTLY ZERO!). Seatbelt Misconception: Thinking passengers get thrown forward by an 'imaginary forward force' during sudden braking (passengers continue forward because of their own inertia!).",
            "cross": "Programming ([[PRG-T01]]): Invariant checking and state machines—an object maintains its current velocity state across frame ticks unless a force input event triggers state transition."
        },
        "recall": [
            ("A hockey puck glides across frictionless ice at $15\\text{ m/s}$. What horizontal force is required to keep it moving at $15\\text{ m/s}$?", "Zero force. By Newton's First Law, an object in motion continues at constant velocity indefinitely when no net external force acts upon it."),
            ("What is the difference between static equilibrium and dynamic equilibrium?", "Static equilibrium occurs when an object is at rest ($v = 0, a = 0, F_{\\text{net}} = 0$). Dynamic equilibrium occurs when an object is moving at constant velocity ($v \\ne 0, a = 0, F_{\\text{net}} = 0$).")
        ]
    },

    "PHY-T01-C04-U03": {
        "title": "Newton's Second Law of Motion",
        "chapter": "PHY-T01-C04",
        "obj": "State Newton's Second Law ($F_{\\text{net}} = ma$), explain direct variation between force and acceleration, inverse variation between mass and acceleration, and calculate mass, acceleration, and weight $w = mg$.",
        "out": "Solve for force, mass, or acceleration using $F_{\\text{net}} = ma$ and calculate gravitational weight on various planetary surfaces.",
        "prereq": "[[PHY-T01-C04-U02]], [[PHY-T01-C03-U01]], [[MTH-T01-C07-U03]], [[MTH-T01-C11-U01]]",
        "next": "[[PHY-T01-C04-U04]]",
        "source": "OpenStax Physics — Section 4.3: Newton's Second Law of Motion",
        "concepts": [
            "Mathematical Law: The acceleration of an object is directly proportional to the net external force acting on it and inversely proportional to its mass:\n$a = \\frac{F_{\\text{net}}}{m} \\iff F_{\\text{net}} = m \\cdot a$\n",
            "The Newton Unit: One Newton ($1\\text{ N}$) is defined as the force required to accelerate a $1\\text{ kg}$ mass at $1\\text{ m/s}^2$ ($1\\text{ N} = 1\\text{ kg}\\cdot\\text{m/s}^2$).",
            "Mass vs. Weight:\n• **Mass ($m$):** An intrinsic property of matter representing its inertia (measured in kilograms, $\\text{kg}$). Mass is constant anywhere in the universe.\n• **Weight ($w$):** The gravitational force exerted on a mass by a planetary body: $w = mg$, measured in Newtons ($\\text{N}$). Weight varies with local gravitational field strength $g$ ($g_{\\text{Earth}} \\approx 9.8\\text{ m/s}^2$, $g_{\\text{Moon}} \\approx 1.6\\text{ m/s}^2$)."
        ],
        "formulas": [
            "\\text{Newton's Second Law: } F_{\\text{net}} = m \\cdot a \\iff a = \\frac{F_{\\text{net}}}{m} \\iff m = \\frac{F_{\\text{net}}}{a}",
            "\\text{Gravitational Weight: } w = m \\cdot g \\quad (g_{\\text{Earth}} = 9.8\\text{ m/s}^2 \\approx 10\\text{ m/s}^2)"
        ],
        "worked": "Example: A $1,500\\text{ kg}$ elevator is suspended by a cable.\n(a) What is the elevator's weight near Earth's surface ($g = 9.8\\text{ m/s}^2$)?\n(b) If the cable pulls upward with a tension of $T = 18,000\\text{ N}$, what is the acceleration of the elevator?\n\nPart (a) Weight:\n$w = mg = (1,500\\text{ kg})(9.8\\text{ m/s}^2) = 14,700\\text{ N}$\n\nPart (b) Acceleration:\nStep 1: Compute 1D vertical net force (taking upward as positive):\n$F_{\\text{net}} = T - w = 18,000\\text{ N} - 14,700\\text{ N} = +3,300\\text{ N}$\nStep 2: Apply Newton's Second Law [[MTH-T01-C11-U01]]:\n$a = \\frac{F_{\\text{net}}}{m} = \\frac{+3,300\\text{ N}}{1,500\\text{ kg}} = +2.2\\text{ m/s}^2$\nThe elevator accelerates upward at $2.2\\text{ m/s}^2$.",
        "practice": {
            "title": "Practice Guide — Newton's Second Law of Motion",
            "core": "Drill calculating $F_{\\text{net}} = ma$ by solving for unknown force, mass, or acceleration. Convert between mass ($m$) and weight ($w = mg$) on different planets.",
            "combine": "Combine kinematics acceleration equations [[PHY-T01-C03-U01]] with $F_{\\text{net}} = ma$ [[MTH-T01-C11-U01]] to solve two-step problems (e.g. finding force required to stop a vehicle in a given time).",
            "traps": "Mass-Weight Unit Trap: Confusing mass ($\\\\text{kg}$) with weight ($\\\\text{N}$) in equations (substituting weight in Newtons into $m$ in $F = ma$!). Gross Force vs. Net Force Trap: Using applied force $F_{\\text{app}}$ instead of NET force $F_{\\text{net}} = F_{\\text{app}} - f$ when calculating acceleration.",
            "cross": "Programming ([[PRG-T01]]): Physics simulation update routines—`object.acceleration = object.netForce / object.mass; object.velocity += object.acceleration * dt`."
        },
        "recall": [
            ("If you double the net force applied to an object while tripling its mass, what happens to its acceleration?", "Its acceleration becomes $\\frac{2}{3}$ of its original value, because $a = \\frac{F}{m} \\implies a' = \\frac{2F}{3m} = \\frac{2}{3}a$."),
            ("Does an astronaut's mass change when traveling from Earth to the Moon? Does their weight change?", "Mass does NOT change (it is an intrinsic quantity of matter). Weight DOES change (it decreases to about $\\frac{1}{6}$ because the Moon's gravity $g$ is weaker).")
        ]
    },

    "PHY-T01-C04-U04": {
        "title": "Newton's Third Law of Motion",
        "chapter": "PHY-T01-C04",
        "obj": "State Newton's Third Law ($F_{A\\text{ on }B} = -F_{B\\text{ on }A}$), identify action-reaction pairs, and explain why action-reaction forces never cancel each other out.",
        "out": "Identify simultaneous action-reaction force pairs for everyday physical interactions and prove mathematically why they do not cancel into equilibrium.",
        "prereq": "[[PHY-T01-C04-U03]], [[MTH-T01-C03-U01]]",
        "next": "[[PHY-T01-C05-U01]]",
        "source": "OpenStax Physics — Section 4.4: Newton's Third Law of Motion",
        "concepts": [
            "Newton's Third Law Statement: Whenever object A exerts a force on object B ($F_{A\\text{ on }B}$), object B simultaneously exerts an equal in magnitude and opposite in direction force on object A ($F_{B\\text{ on }A}$):\n$F_{A\\text{ on }B} = -F_{B\\text{ on }A}$\n",
            "Action-Reaction Pairs: Forces ALWAYS occur in matched pairs. There is no such thing as an isolated single force in the universe.",
            "Why Action-Reaction Pairs Never Cancel: Forces can cancel into equilibrium ($F_{\\text{net}} = 0$) ONLY if they act on the SAME object. Action and reaction forces act on DIFFERENT objects:\n• $F_{\\text{foot on ground}}$ acts ON the ground.\n• $F_{\\text{ground on foot}}$ acts ON the runner.\nThe force accelerating the runner forward is $F_{\\text{ground on foot}}$.",
            "Unequal Acceleration of Interacting Bodies: Although the interaction forces are identical in magnitude, the resulting accelerations depend inversely on each object's mass ($a_A = \\frac{F}{m_A}, a_B = \\frac{F}{m_B}$). When an apple drops, the Earth pulls the apple with $2\\text{ N}$, and the apple pulls the Earth with $2\\text{ N}$; but the Earth's massive inertia ($6 \\times 10^{24}\\text{ kg}$) makes its acceleration imperceptible."
        ],
        "formulas": [
            "\\text{Newton's Third Law: } \\vec{F}_{A\\text{ on }B} = -\\vec{F}_{B\\text{ on }A} \\iff |\\vec{F}_{A\\text{ on }B}| = |\\vec{F}_{B\\text{ on }A}|"
        ],
        "worked": "Example: A massive $2,000\\text{ kg}$ truck rear-ends a stationary $1,000\\text{ kg}$ compact car.\n(a) During the collision, which vehicle experiences a greater impact force magnitude?\n(b) If the collision impact force is $30,000\\text{ N}$, compute the magnitude of instantaneous acceleration experienced by each vehicle.\n\nPart (a) Force Magnitude:\nBy Newton's Third Law, $F_{\\text{truck on car}} = -F_{\\text{car on truck}}$. The force magnitudes are EXACTLY EQUAL ($30,000\\text{ N}$ each). Neither vehicle experiences a larger force!\n\nPart (b) Accelerations:\nFor the car ($m = 1,000\\text{ kg}$):\n$a_{\\text{car}} = \\frac{F}{m_{\\text{car}}} = \\frac{30,000\\text{ N}}{1,000\\text{ kg}} = 30.0\\text{ m/s}^2$\nFor the truck ($m = 2,000\\text{ kg}$):\n$a_{\\text{truck}} = \\frac{F}{m_{\\text{truck}}} = \\frac{30,000\\text{ N}}{2,000\\text{ kg}} = 15.0\\text{ m/s}^2$\nConclusion: The forces are identical, but the lighter car experiences TWICE the acceleration and damage.",
        "practice": {
            "title": "Practice Guide — Newton's Third Law of Motion",
            "core": "Drill identifying Newton's Third Law action-reaction pairs using the exact syntactic formula: 'Force of A on B' paired with 'Force of B on A'. Explain why equal and opposite forces cause different accelerations when masses differ.",
            "combine": "Combine additive inverse properties [[MTH-T01-C03-U01]] ($A = -B$) with $F = ma$ acceleration calculations [[PHY-T01-C04-U03]].",
            "traps": "The Balanced Normal-Weight Fallacy: Confusing the normal force supporting a book on a table ($F_N$) with the book's weight ($w$). They are equal and opposite, but they are NOT an action-reaction pair! (Both act ON the book; the Third Law reaction to Earth's gravity on the book is the book's upward gravitational pull on Earth!).",
            "cross": "Programming ([[PRG-T01]]): Rocket propulsion simulation and particle-recoil mechanics—momentum conservation and equal-opposite impulse application across colliding entities."
        },
        "recall": [
            ("A rifle fires a bullet. The rifle exerts a forward force on the bullet, and the bullet exerts an equal backward force on the rifle (recoil). Why does the bullet accelerate dramatically while the shooter easily absorbs the rifle's recoil?", "By Newton's Second Law ($a = F/m$), both experience identical force magnitudes ($F$), but the bullet has a tiny mass resulting in immense acceleration, while the combined mass of the rifle and shooter is much larger, resulting in a small, controllable acceleration."),
            ("Identify the true Newton's Third Law reaction force to: 'Earth's gravity pulling downward on your body'.", "Your body's gravitational force pulling upward on the Earth with equal magnitude.")
        ]
    }
}
