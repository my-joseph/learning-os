# Trap Telemetry Audit Report: MTH-T01-C01 and MTH-T01-C12

Audited using existing registered templates and forms across 3 deterministic seeds (42, 43, 44).

## Unit: MTH-T01-C01 - Whole Numbers

### Template: `c01-place-value-rounding` | Form: `direct`

#### Seed 42
- **Prompt**: Evaluate the whole-number expression $447 + 167 - 46$.
- **Answer**: `568`
- **trapValue**: `660`
- **trapDerivation**: `447 + 167 + 46`
- **Evaluated Value**: `660`
- **Common Trap Tag**: `c01-subtraction-sign-flip`
- **Tag Description**: Flips a subtraction into addition when chaining multiple arithmetic operations.

#### Seed 43
- **Prompt**: Evaluate the whole-number expression $139 + 256 - 89$.
- **Answer**: `306`
- **trapValue**: `484`
- **trapDerivation**: `139 + 256 + 89`
- **Evaluated Value**: `484`
- **Common Trap Tag**: `c01-subtraction-sign-flip`
- **Tag Description**: Flips a subtraction into addition when chaining multiple arithmetic operations.

#### Seed 44
- **Prompt**: Evaluate the whole-number expression $329 + 376 - 79$.
- **Answer**: `626`
- **trapValue**: `784`
- **trapDerivation**: `329 + 376 + 79`
- **Evaluated Value**: `784`
- **Common Trap Tag**: `c01-subtraction-sign-flip`
- **Tag Description**: Flips a subtraction into addition when chaining multiple arithmetic operations.

### Template: `c01-place-value-rounding` | Form: `contextual`

#### Seed 42
- **Prompt**: A warehouse initially holds $447$ crates. It receives a shipment of $167$ crates and later dispatches $46$ crates. How many crates remain in the warehouse?
- **Answer**: `568`
- **trapValue**: `660`
- **trapDerivation**: `447 + 167 + 46`
- **Evaluated Value**: `660`
- **Common Trap Tag**: `c01-subtraction-sign-flip`
- **Tag Description**: Flips a subtraction into addition when chaining multiple arithmetic operations.

#### Seed 43
- **Prompt**: A warehouse initially holds $139$ crates. It receives a shipment of $256$ crates and later dispatches $89$ crates. How many crates remain in the warehouse?
- **Answer**: `306`
- **trapValue**: `484`
- **trapDerivation**: `139 + 256 + 89`
- **Evaluated Value**: `484`
- **Common Trap Tag**: `c01-subtraction-sign-flip`
- **Tag Description**: Flips a subtraction into addition when chaining multiple arithmetic operations.

#### Seed 44
- **Prompt**: A warehouse initially holds $329$ crates. It receives a shipment of $376$ crates and later dispatches $79$ crates. How many crates remain in the warehouse?
- **Answer**: `626`
- **trapValue**: `784`
- **trapDerivation**: `329 + 376 + 79`
- **Evaluated Value**: `784`
- **Common Trap Tag**: `c01-subtraction-sign-flip`
- **Tag Description**: Flips a subtraction into addition when chaining multiple arithmetic operations.

### Template: `c01-multiply-divide-whole` | Form: `direct`

#### Seed 42
- **Prompt**: When a whole number $N$ is divided by $15$, the quotient is $14$ and the remainder is $7$. Find $N$.
- **Answer**: `217`
- **trapValue**: `210`
- **trapDerivation**: `15 * 14`
- **Evaluated Value**: `210`
- **Common Trap Tag**: `c01-division-remainder-drop`
- **Tag Description**: Drops or forgets the non-zero remainder when reconstructing the dividend in Euclidean division.

#### Seed 43
- **Prompt**: When a whole number $N$ is divided by $13$, the quotient is $22$ and the remainder is $11$. Find $N$.
- **Answer**: `297`
- **trapValue**: `286`
- **trapDerivation**: `13 * 22`
- **Evaluated Value**: `286`
- **Common Trap Tag**: `c01-division-remainder-drop`
- **Tag Description**: Drops or forgets the non-zero remainder when reconstructing the dividend in Euclidean division.

#### Seed 44
- **Prompt**: When a whole number $N$ is divided by $25$, the quotient is $30$ and the remainder is $15$. Find $N$.
- **Answer**: `765`
- **trapValue**: `750`
- **trapDerivation**: `25 * 30`
- **Evaluated Value**: `750`
- **Common Trap Tag**: `c01-division-remainder-drop`
- **Tag Description**: Drops or forgets the non-zero remainder when reconstructing the dividend in Euclidean division.

### Template: `c01-multiply-divide-whole` | Form: `reverse`

#### Seed 42
- **Prompt**: When the whole number $217$ is divided by a positive divisor $d$, the quotient is $14$ and the remainder is $7$. Find the divisor $d$.
- **Answer**: `15`
- **trapValue**: `16`
- **trapDerivation**: `(217 + 7) // 14`
- **Evaluated Value**: `16`
- **Common Trap Tag**: `c01-remainder-addition-slip`
- **Tag Description**: Mistakenly adds remainder to dividend instead of subtracting before dividing to isolate divisor: (N + r) // q.

#### Seed 43
- **Prompt**: When the whole number $297$ is divided by a positive divisor $d$, the quotient is $22$ and the remainder is $11$. Find the divisor $d$.
- **Answer**: `13`
- **trapValue**: `14`
- **trapDerivation**: `(297 + 11) // 22`
- **Evaluated Value**: `14`
- **Common Trap Tag**: `c01-remainder-addition-slip`
- **Tag Description**: Mistakenly adds remainder to dividend instead of subtracting before dividing to isolate divisor: (N + r) // q.

#### Seed 44
- **Prompt**: When the whole number $765$ is divided by a positive divisor $d$, the quotient is $30$ and the remainder is $15$. Find the divisor $d$.
- **Answer**: `25`
- **trapValue**: `26`
- **trapDerivation**: `(765 + 15) // 30`
- **Evaluated Value**: `26`
- **Common Trap Tag**: `c01-remainder-addition-slip`
- **Tag Description**: Mistakenly adds remainder to dividend instead of subtracting before dividing to isolate divisor: (N + r) // q.

### Template: `c01-division-remainder-trap` | Form: `direct`

#### Seed 42
- **Prompt**: An expedition group of $507$ researchers needs transport vans that each hold at most $36$ passengers. What is the minimum whole number of vans required to transport everyone at once?
- **Answer**: `15`
- **trapValue**: `14`
- **trapDerivation**: `507 // 36`
- **Evaluated Value**: `14`
- **Common Trap Tag**: `c01-ceiling-rounding-trap`
- **Tag Description**: Truncates or rounds down to integer quotient when practical packaging requires ceiling rounding.

#### Seed 43
- **Prompt**: An expedition group of $244$ researchers needs transport vans that each hold at most $12$ passengers. What is the minimum whole number of vans required to transport everyone at once?
- **Answer**: `21`
- **trapValue**: `20`
- **trapDerivation**: `244 // 12`
- **Evaluated Value**: `20`
- **Common Trap Tag**: `c01-ceiling-rounding-trap`
- **Tag Description**: Truncates or rounds down to integer quotient when practical packaging requires ceiling rounding.

#### Seed 44
- **Prompt**: An expedition group of $667$ researchers needs transport vans that each hold at most $24$ passengers. What is the minimum whole number of vans required to transport everyone at once?
- **Answer**: `28`
- **trapValue**: `27`
- **trapDerivation**: `667 // 24`
- **Evaluated Value**: `27`
- **Common Trap Tag**: `c01-ceiling-rounding-trap`
- **Tag Description**: Truncates or rounds down to integer quotient when practical packaging requires ceiling rounding.

### Template: `c01-division-remainder-trap` | Form: `edge-case`

#### Seed 42
- **Prompt**: A factory produces $507$ sensors to be packed into crates that hold exactly $36$ sensors each. How many additional sensors must be produced so that the last partially filled crate becomes completely full?
- **Answer**: `33`
- **trapValue**: `3`
- **trapDerivation**: `507 - 36 * (507 // 36)`
- **Evaluated Value**: `3`
- **Common Trap Tag**: `c01-remainder-shortfall-confusion`
- **Tag Description**: Reports leftover remainder rather than the remaining shortfall required to complete the final container.

#### Seed 43
- **Prompt**: A factory produces $244$ sensors to be packed into crates that hold exactly $12$ sensors each. How many additional sensors must be produced so that the last partially filled crate becomes completely full?
- **Answer**: `8`
- **trapValue**: `4`
- **trapDerivation**: `244 - 12 * (244 // 12)`
- **Evaluated Value**: `4`
- **Common Trap Tag**: `c01-remainder-shortfall-confusion`
- **Tag Description**: Reports leftover remainder rather than the remaining shortfall required to complete the final container.

#### Seed 44
- **Prompt**: A factory produces $667$ sensors to be packed into crates that hold exactly $24$ sensors each. How many additional sensors must be produced so that the last partially filled crate becomes completely full?
- **Answer**: `5`
- **trapValue**: `19`
- **trapDerivation**: `667 - 24 * (667 // 24)`
- **Evaluated Value**: `19`
- **Common Trap Tag**: `c01-remainder-shortfall-confusion`
- **Tag Description**: Reports leftover remainder rather than the remaining shortfall required to complete the final container.

### Template: `c01-multi-unit-budget-synthesis` | Form: `direct`

#### Seed 42
- **Prompt**: A school purchases $10$ workbooks at $32$ dollars each and $8$ lab packs at $34$ dollars each, then applies a voucher worth $8$ dollars. If the remaining balance is divided equally into $4$ monthly installments, what is the dollar amount of each installment?
- **Answer**: `146`
- **trapValue**: `148`
- **trapDerivation**: `(10 * 32 + 8 * 34) // 4`
- **Evaluated Value**: `148`
- **Common Trap Tag**: `c01-voucher-omission-trap`
- **Tag Description**: Forgets to subtract voucher discount from total before dividing into installment shares.

#### Seed 43
- **Prompt**: A school purchases $8$ workbooks at $55$ dollars each and $12$ lab packs at $41$ dollars each, then applies a voucher worth $16$ dollars. If the remaining balance is divided equally into $4$ monthly installments, what is the dollar amount of each installment?
- **Answer**: `229`
- **trapValue**: `233`
- **trapDerivation**: `(8 * 55 + 12 * 41) // 4`
- **Evaluated Value**: `233`
- **Common Trap Tag**: `c01-voucher-omission-trap`
- **Tag Description**: Forgets to subtract voucher discount from total before dividing into installment shares.

#### Seed 44
- **Prompt**: A school purchases $8$ workbooks at $33$ dollars each and $8$ lab packs at $54$ dollars each, then applies a voucher worth $48$ dollars. If the remaining balance is divided equally into $8$ monthly installments, what is the dollar amount of each installment?
- **Answer**: `81`
- **trapValue**: `87`
- **trapDerivation**: `(8 * 33 + 8 * 54) // 8`
- **Evaluated Value**: `87`
- **Common Trap Tag**: `c01-voucher-omission-trap`
- **Tag Description**: Forgets to subtract voucher discount from total before dividing into installment shares.

### Template: `c01-multi-unit-budget-synthesis` | Form: `multi-constraint`

#### Seed 42
- **Prompt**: A lab orders $10$ kits at $32$ dollars each and $8$ modules at $34$ dollars each. After receiving a bulk rebate of $8$ dollars and paying a flat shipping fee of $32$ dollars, the total net cost is split equally among $4$ departments. How much does each department pay?
- **Answer**: `154`
- **trapValue**: `146`
- **trapDerivation**: `(10 * 32 + 8 * 34 - 8) // 4`
- **Evaluated Value**: `146`
- **Common Trap Tag**: `c01-fee-omission-trap`
- **Tag Description**: Forgets to add mandatory flat fee to total before allocating per-share costs.

#### Seed 43
- **Prompt**: A lab orders $8$ kits at $55$ dollars each and $12$ modules at $41$ dollars each. After receiving a bulk rebate of $16$ dollars and paying a flat shipping fee of $32$ dollars, the total net cost is split equally among $4$ departments. How much does each department pay?
- **Answer**: `237`
- **trapValue**: `229`
- **trapDerivation**: `(8 * 55 + 12 * 41 - 16) // 4`
- **Evaluated Value**: `229`
- **Common Trap Tag**: `c01-fee-omission-trap`
- **Tag Description**: Forgets to add mandatory flat fee to total before allocating per-share costs.

#### Seed 44
- **Prompt**: A lab orders $8$ kits at $33$ dollars each and $8$ modules at $54$ dollars each. After receiving a bulk rebate of $48$ dollars and paying a flat shipping fee of $24$ dollars, the total net cost is split equally among $8$ departments. How much does each department pay?
- **Answer**: `84`
- **trapValue**: `81`
- **trapDerivation**: `(8 * 33 + 8 * 54 - 48) // 8`
- **Evaluated Value**: `81`
- **Common Trap Tag**: `c01-fee-omission-trap`
- **Tag Description**: Forgets to add mandatory flat fee to total before allocating per-share costs.

## Unit: MTH-T01-C12 - Math Models and Geometry

### Template: `pythagoras-hypotenuse` | Form: `direct`

#### Seed 42
- **Prompt**: Find the length of the hypotenuse $c$ of the right triangle with legs $a = 4$ and $b = 3$.
- **Answer**: `5`
- **trapValue**: `7`
- **trapDerivation**: `4 + 3`
- **Evaluated Value**: `7`
- **Common Trap Tag**: `linear-addition-trap`
- **Tag Description**: Adds right-triangle legs linearly without squaring: c = a + b.

#### Seed 43
- **Prompt**: Find the length of the hypotenuse $c$ of the right triangle with legs $a = 3$ and $b = 4$.
- **Answer**: `5`
- **trapValue**: `7`
- **trapDerivation**: `3 + 4`
- **Evaluated Value**: `7`
- **Common Trap Tag**: `linear-addition-trap`
- **Tag Description**: Adds right-triangle legs linearly without squaring: c = a + b.

#### Seed 44
- **Prompt**: Find the length of the hypotenuse $c$ of the right triangle with legs $a = 15$ and $b = 8$.
- **Answer**: `17`
- **trapValue**: `23`
- **trapDerivation**: `15 + 8`
- **Evaluated Value**: `23`
- **Common Trap Tag**: `linear-addition-trap`
- **Tag Description**: Adds right-triangle legs linearly without squaring: c = a + b.

### Template: `pythagoras-hypotenuse` | Form: `reverse`

#### Seed 42
- **Prompt**: Find the length of the unknown leg $a$ of a right triangle with hypotenuse $c = 5$ and leg $b = 3$.
- **Answer**: `4`
- **trapValue**: `2`
- **trapDerivation**: `5 - 3`
- **Evaluated Value**: `2`
- **Common Trap Tag**: `pythagoras-leg-subtraction`
- **Tag Description**: Subtracts hypotenuse and leg linearly without squaring: a = c - b.

#### Seed 43
- **Prompt**: Find the length of the unknown leg $a$ of a right triangle with hypotenuse $c = 5$ and leg $b = 4$.
- **Answer**: `3`
- **trapValue**: `1`
- **trapDerivation**: `5 - 4`
- **Evaluated Value**: `1`
- **Common Trap Tag**: `pythagoras-leg-subtraction`
- **Tag Description**: Subtracts hypotenuse and leg linearly without squaring: a = c - b.

#### Seed 44
- **Prompt**: Find the length of the unknown leg $a$ of a right triangle with hypotenuse $c = 17$ and leg $b = 8$.
- **Answer**: `15`
- **trapValue**: `9`
- **trapDerivation**: `17 - 8`
- **Evaluated Value**: `9`
- **Common Trap Tag**: `pythagoras-leg-subtraction`
- **Tag Description**: Subtracts hypotenuse and leg linearly without squaring: a = c - b.

### Template: `pythagoras-hypotenuse` | Form: `contextual`

#### Seed 42
- **Prompt**: A guy wire stretches from the top of a $4$-meter vertical pole to a ground anchor $3$ meters from the base. Find the exact length $c$ of the wire.
- **Answer**: `5`
- **trapValue**: `7`
- **trapDerivation**: `4 + 3`
- **Evaluated Value**: `7`
- **Common Trap Tag**: `path-distance-vs-displacement`
- **Tag Description**: Calculates total travel path distance instead of shortest straight-line Pythagorean displacement.

#### Seed 43
- **Prompt**: A guy wire stretches from the top of a $3$-meter vertical pole to a ground anchor $4$ meters from the base. Find the exact length $c$ of the wire.
- **Answer**: `5`
- **trapValue**: `7`
- **trapDerivation**: `3 + 4`
- **Evaluated Value**: `7`
- **Common Trap Tag**: `path-distance-vs-displacement`
- **Tag Description**: Calculates total travel path distance instead of shortest straight-line Pythagorean displacement.

#### Seed 44
- **Prompt**: A guy wire stretches from the top of a $15$-meter vertical pole to a ground anchor $8$ meters from the base. Find the exact length $c$ of the wire.
- **Answer**: `17`
- **trapValue**: `23`
- **trapDerivation**: `15 + 8`
- **Evaluated Value**: `23`
- **Common Trap Tag**: `path-distance-vs-displacement`
- **Tag Description**: Calculates total travel path distance instead of shortest straight-line Pythagorean displacement.

### Template: `trapezoid-area` | Form: `direct`

#### Seed 42
- **Prompt**: Find the area $A$ of the trapezoid with parallel bases $b_1 = 6$, $b_2 = 10$, and height $h = 8$.
- **Answer**: `64`
- **trapValue**: `128`
- **trapDerivation**: `(6 + 10) * 8`
- **Evaluated Value**: `128`
- **Common Trap Tag**: `omitted-half-factor`
- **Tag Description**: Omits the 1/2 factor in the trapezoid area formula: (b1 + b2)*h.

#### Seed 43
- **Prompt**: Find the area $A$ of the trapezoid with parallel bases $b_1 = 6$, $b_2 = 12$, and height $h = 6$.
- **Answer**: `54`
- **trapValue**: `108`
- **trapDerivation**: `(6 + 12) * 6`
- **Evaluated Value**: `108`
- **Common Trap Tag**: `omitted-half-factor`
- **Tag Description**: Omits the 1/2 factor in the trapezoid area formula: (b1 + b2)*h.

#### Seed 44
- **Prompt**: Find the area $A$ of the trapezoid with parallel bases $b_1 = 12$, $b_2 = 20$, and height $h = 4$.
- **Answer**: `64`
- **trapValue**: `128`
- **trapDerivation**: `(12 + 20) * 4`
- **Evaluated Value**: `128`
- **Common Trap Tag**: `omitted-half-factor`
- **Tag Description**: Omits the 1/2 factor in the trapezoid area formula: (b1 + b2)*h.

### Template: `trapezoid-area` | Form: `reverse`

#### Seed 42
- **Prompt**: A trapezoid with parallel bases $b_1 = 6$ and $b_2 = 10$ has an area of $A = 64$. Find its height $h$.
- **Answer**: `8`
- **trapValue**: `4`
- **trapDerivation**: `64 // (6 + 10)`
- **Evaluated Value**: `4`
- **Common Trap Tag**: `trapezoid-reverse-omit-double-factor`
- **Tag Description**: Forgets the factor of 2 in numerator when solving for height from trapezoid area: h = A / (b1 + b2).

#### Seed 43
- **Prompt**: A trapezoid with parallel bases $b_1 = 6$ and $b_2 = 12$ has an area of $A = 54$. Find its height $h$.
- **Answer**: `6`
- **trapValue**: `3`
- **trapDerivation**: `54 // (6 + 12)`
- **Evaluated Value**: `3`
- **Common Trap Tag**: `trapezoid-reverse-omit-double-factor`
- **Tag Description**: Forgets the factor of 2 in numerator when solving for height from trapezoid area: h = A / (b1 + b2).

#### Seed 44
- **Prompt**: A trapezoid with parallel bases $b_1 = 12$ and $b_2 = 20$ has an area of $A = 64$. Find its height $h$.
- **Answer**: `4`
- **trapValue**: `2`
- **trapDerivation**: `64 // (12 + 20)`
- **Evaluated Value**: `2`
- **Common Trap Tag**: `trapezoid-reverse-omit-double-factor`
- **Tag Description**: Forgets the factor of 2 in numerator when solving for height from trapezoid area: h = A / (b1 + b2).

### Template: `circle-area-pi` | Form: `direct`

#### Seed 42
- **Prompt**: Find the exact area $A$ of a circle with radius $r = 4$ and diameter $d = 8$ (in terms of $\pi$).
- **Answer**: `16 pi`
- **trapValue**: `8 pi`
- **trapDerivation**: `(8 // 4) * 4 * pi`
- **Evaluated Value**: `8*pi`
- **Common Trap Tag**: `formula-circumference-area-confusion`
- **Tag Description**: Calculates circumference 2*pi*r instead of circle area pi*r^2.

#### Seed 43
- **Prompt**: Find the exact area $A$ of a circle with radius $r = 3$ and diameter $d = 6$ (in terms of $\pi$).
- **Answer**: `9 pi`
- **trapValue**: `6 pi`
- **trapDerivation**: `(6 // 3) * 3 * pi`
- **Evaluated Value**: `6*pi`
- **Common Trap Tag**: `formula-circumference-area-confusion`
- **Tag Description**: Calculates circumference 2*pi*r instead of circle area pi*r^2.

#### Seed 44
- **Prompt**: Find the exact area $A$ of a circle with radius $r = 9$ and diameter $d = 18$ (in terms of $\pi$).
- **Answer**: `81 pi`
- **trapValue**: `18 pi`
- **trapDerivation**: `(18 // 9) * 9 * pi`
- **Evaluated Value**: `18*pi`
- **Common Trap Tag**: `formula-circumference-area-confusion`
- **Tag Description**: Calculates circumference 2*pi*r instead of circle area pi*r^2.

### Template: `circle-area-pi` | Form: `from-diameter`

#### Seed 42
- **Prompt**: Find the exact area $A$ of a circle with diameter $d = 8$ and radius $r = 4$ (in terms of $\pi$).
- **Answer**: `16 pi`
- **trapValue**: `64 pi`
- **trapDerivation**: `8 * (2 * 4) * pi`
- **Evaluated Value**: `64*pi`
- **Common Trap Tag**: `circle-diameter-as-radius-trap`
- **Tag Description**: Squares diameter directly as radius when computing circle area: pi * d^2.

#### Seed 43
- **Prompt**: Find the exact area $A$ of a circle with diameter $d = 6$ and radius $r = 3$ (in terms of $\pi$).
- **Answer**: `9 pi`
- **trapValue**: `36 pi`
- **trapDerivation**: `6 * (2 * 3) * pi`
- **Evaluated Value**: `36*pi`
- **Common Trap Tag**: `circle-diameter-as-radius-trap`
- **Tag Description**: Squares diameter directly as radius when computing circle area: pi * d^2.

#### Seed 44
- **Prompt**: Find the exact area $A$ of a circle with diameter $d = 18$ and radius $r = 9$ (in terms of $\pi$).
- **Answer**: `81 pi`
- **trapValue**: `324 pi`
- **trapDerivation**: `18 * (2 * 9) * pi`
- **Evaluated Value**: `324*pi`
- **Common Trap Tag**: `circle-diameter-as-radius-trap`
- **Tag Description**: Squares diameter directly as radius when computing circle area: pi * d^2.

### Template: `cylinder-volume` | Form: `direct`

#### Seed 42
- **Prompt**: Find the exact volume $V$ of a right circular cylinder with radius $r = 2$ and height $h = 6$ (in terms of $\pi$).
- **Answer**: `24 pi`
- **trapValue**: `32 pi`
- **trapDerivation**: `(2 * 2 * 6 + 2 * 2**2) * pi`
- **Evaluated Value**: `32*pi`
- **Common Trap Tag**: `volume-surface-area`
- **Tag Description**: Confuses 3D solid volume with total surface area.

#### Seed 43
- **Prompt**: Find the exact volume $V$ of a right circular cylinder with radius $r = 2$ and height $h = 10$ (in terms of $\pi$).
- **Answer**: `40 pi`
- **trapValue**: `48 pi`
- **trapDerivation**: `(2 * 2 * 10 + 2 * 2**2) * pi`
- **Evaluated Value**: `48*pi`
- **Common Trap Tag**: `volume-surface-area`
- **Tag Description**: Confuses 3D solid volume with total surface area.

#### Seed 44
- **Prompt**: Find the exact volume $V$ of a right circular cylinder with radius $r = 5$ and height $h = 6$ (in terms of $\pi$).
- **Answer**: `150 pi`
- **trapValue**: `110 pi`
- **trapDerivation**: `(2 * 5 * 6 + 2 * 5**2) * pi`
- **Evaluated Value**: `110*pi`
- **Common Trap Tag**: `volume-surface-area`
- **Tag Description**: Confuses 3D solid volume with total surface area.

### Template: `cylinder-volume` | Form: `from-diameter`

#### Seed 42
- **Prompt**: Find the exact volume $V$ of a right circular cylinder with diameter $d = 4$ and height $h = 6$ (in terms of $\pi$).
- **Answer**: `24 pi`
- **trapValue**: `96 pi`
- **trapDerivation**: `4**2 * 6 * pi`
- **Evaluated Value**: `96*pi`
- **Common Trap Tag**: `cylinder-diameter-as-radius-trap`
- **Tag Description**: Uses diameter directly as radius in cylinder volume formula: pi * d^2 * h.

#### Seed 43
- **Prompt**: Find the exact volume $V$ of a right circular cylinder with diameter $d = 4$ and height $h = 10$ (in terms of $\pi$).
- **Answer**: `40 pi`
- **trapValue**: `160 pi`
- **trapDerivation**: `4**2 * 10 * pi`
- **Evaluated Value**: `160*pi`
- **Common Trap Tag**: `cylinder-diameter-as-radius-trap`
- **Tag Description**: Uses diameter directly as radius in cylinder volume formula: pi * d^2 * h.

#### Seed 44
- **Prompt**: Find the exact volume $V$ of a right circular cylinder with diameter $d = 10$ and height $h = 6$ (in terms of $\pi$).
- **Answer**: `150 pi`
- **trapValue**: `600 pi`
- **trapDerivation**: `10**2 * 6 * pi`
- **Evaluated Value**: `600*pi`
- **Common Trap Tag**: `cylinder-diameter-as-radius-trap`
- **Tag Description**: Uses diameter directly as radius in cylinder volume formula: pi * d^2 * h.

### Template: `altitude-inradius` | Form: `direct`

#### Seed 42
- **Prompt**: In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = 169$, altitude $CD$ is drawn perpendicular to $AB$, dividing the hypotenuse into two segments $AD = 144$ and $DB = 25$. A circle is inscribed inside triangle $ACD$. Find the radius $r$ of this inscribed circle.
- **Answer**: `24`
- **trapValue**: `26`
- **trapDerivation**: `(sqrt(169 * 144) + sqrt(169 * 25) - 169) / 2`
- **Evaluated Value**: `26`
- **Common Trap Tag**: `whole-triangle-inradius-confusion`
- **Tag Description**: Calculates inradius of the parent right triangle instead of the specified sub-triangle.

#### Seed 43
- **Prompt**: In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = 25$, altitude $CD$ is drawn perpendicular to $AB$, dividing the hypotenuse into two segments $AD = 9$ and $DB = 16$. A circle is inscribed inside triangle $ACD$. Find the radius $r$ of this inscribed circle.
- **Answer**: `3`
- **trapValue**: `5`
- **trapDerivation**: `(sqrt(25 * 9) + sqrt(25 * 16) - 25) / 2`
- **Evaluated Value**: `5`
- **Common Trap Tag**: `whole-triangle-inradius-confusion`
- **Tag Description**: Calculates inradius of the parent right triangle instead of the specified sub-triangle.

#### Seed 44
- **Prompt**: In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = 50$, altitude $CD$ is drawn perpendicular to $AB$, dividing the hypotenuse into two segments $AD = 32$ and $DB = 18$. A circle is inscribed inside triangle $ACD$. Find the radius $r$ of this inscribed circle.
- **Answer**: `8`
- **trapValue**: `10`
- **trapDerivation**: `(sqrt(50 * 32) + sqrt(50 * 18) - 50) / 2`
- **Evaluated Value**: `10`
- **Common Trap Tag**: `whole-triangle-inradius-confusion`
- **Tag Description**: Calculates inradius of the parent right triangle instead of the specified sub-triangle.

### Template: `altitude-inradius` | Form: `missing-segment`

#### Seed 42
- **Prompt**: In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = 169$, altitude $CD$ is drawn perpendicular to $AB$ such that $AD = 144$. A circle is inscribed inside the complementary sub-triangle $BCD$. Find the radius $r$ of this inscribed circle.
- **Answer**: `10`
- **trapValue**: `26`
- **trapDerivation**: `(sqrt(169 * 144) + sqrt(169 * (169 - 144)) - 169) / 2`
- **Evaluated Value**: `26`
- **Common Trap Tag**: `whole-triangle-inradius-confusion`
- **Tag Description**: Calculates inradius of the parent right triangle instead of the specified sub-triangle.

#### Seed 43
- **Prompt**: In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = 25$, altitude $CD$ is drawn perpendicular to $AB$ such that $AD = 9$. A circle is inscribed inside the complementary sub-triangle $BCD$. Find the radius $r$ of this inscribed circle.
- **Answer**: `4`
- **trapValue**: `5`
- **trapDerivation**: `(sqrt(25 * 9) + sqrt(25 * (25 - 9)) - 25) / 2`
- **Evaluated Value**: `5`
- **Common Trap Tag**: `whole-triangle-inradius-confusion`
- **Tag Description**: Calculates inradius of the parent right triangle instead of the specified sub-triangle.

#### Seed 44
- **Prompt**: In a right-angled triangle $ABC$ with right angle at $C$ and hypotenuse $AB = 50$, altitude $CD$ is drawn perpendicular to $AB$ such that $AD = 32$. A circle is inscribed inside the complementary sub-triangle $BCD$. Find the radius $r$ of this inscribed circle.
- **Answer**: `6`
- **trapValue**: `10`
- **trapDerivation**: `(sqrt(50 * 32) + sqrt(50 * (50 - 32)) - 50) / 2`
- **Evaluated Value**: `10`
- **Common Trap Tag**: `whole-triangle-inradius-confusion`
- **Tag Description**: Calculates inradius of the parent right triangle instead of the specified sub-triangle.

### Template: `trapezoid-similar-triangles` | Form: `direct`

#### Seed 42
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 10$ and $CD = 24$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of triangle $ABE$.
- **Answer**: `600/17`
- **trapValue**: `60`
- **trapDerivation**: `(10 * sqrt(25**2 - ((24 - 10)/2)**2)) / 4`
- **Evaluated Value**: `60`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

#### Seed 43
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 10$ and $CD = 24$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of triangle $ABE$.
- **Answer**: `600/17`
- **trapValue**: `60`
- **trapDerivation**: `(10 * sqrt(25**2 - ((24 - 10)/2)**2)) / 4`
- **Evaluated Value**: `60`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

#### Seed 44
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 4$ and $CD = 18$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of triangle $ABE$.
- **Answer**: `96/11`
- **trapValue**: `24`
- **trapDerivation**: `(4 * sqrt(25**2 - ((18 - 4)/2)**2)) / 4`
- **Evaluated Value**: `24`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

### Template: `trapezoid-similar-triangles` | Form: `bottom-triangle`

#### Seed 42
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 10$ and $CD = 24$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of lower triangle $CDE$.
- **Answer**: `3456/17`
- **trapValue**: `144`
- **trapDerivation**: `(24 * sqrt(25**2 - ((24 - 10)/2)**2)) / 4`
- **Evaluated Value**: `144`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

#### Seed 43
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 10$ and $CD = 24$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of lower triangle $CDE$.
- **Answer**: `3456/17`
- **trapValue**: `144`
- **trapDerivation**: `(24 * sqrt(25**2 - ((24 - 10)/2)**2)) / 4`
- **Evaluated Value**: `144`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

#### Seed 44
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 4$ and $CD = 18$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of lower triangle $CDE$.
- **Answer**: `1944/11`
- **trapValue**: `108`
- **trapDerivation**: `(18 * sqrt(25**2 - ((18 - 4)/2)**2)) / 4`
- **Evaluated Value**: `108`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

### Template: `trapezoid-similar-triangles` | Form: `side-triangle`

#### Seed 42
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 10$ and $CD = 24$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of flank triangle $ADE$.
- **Answer**: `1440/17`
- **trapValue**: `102`
- **trapDerivation**: `((10 + 24) * sqrt(25**2 - ((24 - 10)/2)**2)) / 8`
- **Evaluated Value**: `102`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

#### Seed 43
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 10$ and $CD = 24$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of flank triangle $ADE$.
- **Answer**: `1440/17`
- **trapValue**: `102`
- **trapDerivation**: `((10 + 24) * sqrt(25**2 - ((24 - 10)/2)**2)) / 8`
- **Evaluated Value**: `102`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

#### Seed 44
- **Prompt**: In an isosceles trapezoid $ABCD$, the parallel bases are $AB = 4$ and $CD = 18$, and the non-parallel legs are $AD = BC = 25$. Diagonals $AC$ and $BD$ intersect at point $E$. Find the exact area of flank triangle $ADE$.
- **Answer**: `432/11`
- **trapValue**: `66`
- **trapDerivation**: `((4 + 18) * sqrt(25**2 - ((18 - 4)/2)**2)) / 8`
- **Evaluated Value**: `66`
- **Common Trap Tag**: `trapezoid-diagonal-bisect-trap`
- **Tag Description**: Assumes trapezoid diagonals bisect height equally instead of partitioning via similar triangle ratio.

### Template: `lunes-hippocrates` | Form: `direct`

#### Seed 42
- **Prompt**: A square of side length $s = 8$ is inscribed inside a circle. A set of $4$ semicircles are drawn externally on the $4$ sides of the square as diameters. The region outside the circumscribed circle but inside the $4$ semicircles forms $4$ crescent-shaped regions known as the Lunes of Hippocrates. Find the exact total area of all $4$ lunes.
- **Answer**: `64`
- **trapValue**: `32`
- **trapDerivation**: `(8**2 * 2) // 4`
- **Evaluated Value**: `32`
- **Common Trap Tag**: `lunes-half-area-trap`
- **Tag Description**: Computes area for only half of the lunes (2 instead of 4) in Lunes of Hippocrates.

#### Seed 43
- **Prompt**: A square of side length $s = 6$ is inscribed inside a circle. A set of $4$ semicircles are drawn externally on the $4$ sides of the square as diameters. The region outside the circumscribed circle but inside the $4$ semicircles forms $4$ crescent-shaped regions known as the Lunes of Hippocrates. Find the exact total area of all $4$ lunes.
- **Answer**: `36`
- **trapValue**: `18`
- **trapDerivation**: `(6**2 * 2) // 4`
- **Evaluated Value**: `18`
- **Common Trap Tag**: `lunes-half-area-trap`
- **Tag Description**: Computes area for only half of the lunes (2 instead of 4) in Lunes of Hippocrates.

#### Seed 44
- **Prompt**: A square of side length $s = 18$ is inscribed inside a circle. A set of $4$ semicircles are drawn externally on the $4$ sides of the square as diameters. The region outside the circumscribed circle but inside the $4$ semicircles forms $4$ crescent-shaped regions known as the Lunes of Hippocrates. Find the exact total area of all $4$ lunes.
- **Answer**: `324`
- **trapValue**: `162`
- **trapDerivation**: `(18**2 * 2) // 4`
- **Evaluated Value**: `162`
- **Common Trap Tag**: `lunes-half-area-trap`
- **Tag Description**: Computes area for only half of the lunes (2 instead of 4) in Lunes of Hippocrates.

### Template: `lunes-hippocrates` | Form: `single-lune`

#### Seed 42
- **Prompt**: A square of side length $s = 8$ is inscribed inside a circle. A set of $4$ congruent semicircles are drawn externally on the $4$ sides of the square as diameters, forming $4$ congruent crescent-shaped Lunes of Hippocrates outside the circumscribed circle. Find the exact area of ONE such lune.
- **Answer**: `16`
- **trapValue**: `64`
- **trapDerivation**: `(8**2 // 4) * 4`
- **Evaluated Value**: `64`
- **Common Trap Tag**: `lunes-total-instead-of-single-trap`
- **Tag Description**: Computes the total combined area of all four lunes instead of dividing by four for a single lune.

#### Seed 43
- **Prompt**: A square of side length $s = 6$ is inscribed inside a circle. A set of $4$ congruent semicircles are drawn externally on the $4$ sides of the square as diameters, forming $4$ congruent crescent-shaped Lunes of Hippocrates outside the circumscribed circle. Find the exact area of ONE such lune.
- **Answer**: `9`
- **trapValue**: `36`
- **trapDerivation**: `(6**2 // 4) * 4`
- **Evaluated Value**: `36`
- **Common Trap Tag**: `lunes-total-instead-of-single-trap`
- **Tag Description**: Computes the total combined area of all four lunes instead of dividing by four for a single lune.

#### Seed 44
- **Prompt**: A square of side length $s = 18$ is inscribed inside a circle. A set of $4$ congruent semicircles are drawn externally on the $4$ sides of the square as diameters, forming $4$ congruent crescent-shaped Lunes of Hippocrates outside the circumscribed circle. Find the exact area of ONE such lune.
- **Answer**: `81`
- **trapValue**: `324`
- **trapDerivation**: `(18**2 // 4) * 4`
- **Evaluated Value**: `324`
- **Common Trap Tag**: `lunes-total-instead-of-single-trap`
- **Tag Description**: Computes the total combined area of all four lunes instead of dividing by four for a single lune.

### Template: `cone-frustum-volume` | Form: `direct`

#### Seed 42
- **Prompt**: A right circular cone has base radius $R = 9$ and total height $H = 12$. The cone is truncated by a plane parallel to the base at a distance of $h = 4$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\pi$.
- **Answer**: `228 pi`
- **trapValue**: `225*pi`
- **trapDerivation**: `pi * ((9 + (9 * (12 - 4)) // 12) / 2)**2 * 4`
- **Evaluated Value**: `225*pi`
- **Common Trap Tag**: `frustum-cylinder-average-trap`
- **Tag Description**: Averages conical frustum base radii and computes as cylinder instead of frustum volume.

#### Seed 43
- **Prompt**: A right circular cone has base radius $R = 9$ and total height $H = 12$. The cone is truncated by a plane parallel to the base at a distance of $h = 4$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\pi$.
- **Answer**: `228 pi`
- **trapValue**: `225*pi`
- **trapDerivation**: `pi * ((9 + (9 * (12 - 4)) // 12) / 2)**2 * 4`
- **Evaluated Value**: `225*pi`
- **Common Trap Tag**: `frustum-cylinder-average-trap`
- **Tag Description**: Averages conical frustum base radii and computes as cylinder instead of frustum volume.

#### Seed 44
- **Prompt**: A right circular cone has base radius $R = 15$ and total height $H = 20$. The cone is truncated by a plane parallel to the base at a distance of $h = 8$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\pi$.
- **Answer**: `1176 pi`
- **trapValue**: `1152*pi`
- **trapDerivation**: `pi * ((15 + (15 * (20 - 8)) // 20) / 2)**2 * 8`
- **Evaluated Value**: `1152*pi`
- **Common Trap Tag**: `frustum-cylinder-average-trap`
- **Tag Description**: Averages conical frustum base radii and computes as cylinder instead of frustum volume.

### Template: `cone-frustum-volume` | Form: `from-diameter`

#### Seed 42
- **Prompt**: A right circular cone has base diameter $D = 18$ and total height $H = 12$. The cone is truncated by a plane parallel to the base at a distance of $h = 4$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\pi$.
- **Answer**: `228 pi`
- **trapValue**: `225*pi`
- **trapDerivation**: `pi * (((18 // 2) + ((18 // 2) * (12 - 4)) // 12) / 2)**2 * 4`
- **Evaluated Value**: `225*pi`
- **Common Trap Tag**: `frustum-cylinder-average-trap`
- **Tag Description**: Averages conical frustum base radii and computes as cylinder instead of frustum volume.

#### Seed 43
- **Prompt**: A right circular cone has base diameter $D = 18$ and total height $H = 12$. The cone is truncated by a plane parallel to the base at a distance of $h = 4$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\pi$.
- **Answer**: `228 pi`
- **trapValue**: `225*pi`
- **trapDerivation**: `pi * (((18 // 2) + ((18 // 2) * (12 - 4)) // 12) / 2)**2 * 4`
- **Evaluated Value**: `225*pi`
- **Common Trap Tag**: `frustum-cylinder-average-trap`
- **Tag Description**: Averages conical frustum base radii and computes as cylinder instead of frustum volume.

#### Seed 44
- **Prompt**: A right circular cone has base diameter $D = 30$ and total height $H = 20$. The cone is truncated by a plane parallel to the base at a distance of $h = 8$ above the base, forming a conical frustum. Find the exact volume of this frustum in terms of $\pi$.
- **Answer**: `1176 pi`
- **trapValue**: `1152*pi`
- **trapDerivation**: `pi * (((30 // 2) + ((30 // 2) * (20 - 8)) // 20) / 2)**2 * 8`
- **Evaluated Value**: `1152*pi`
- **Common Trap Tag**: `frustum-cylinder-average-trap`
- **Tag Description**: Averages conical frustum base radii and computes as cylinder instead of frustum volume.

### Template: `find-flaw-composite-surface-area` | Form: `flaw-line-2`

#### Seed 42
- **Prompt**: A composite solid consists of a right circular cylinder with radius $r = 3$ and height $h = 5$, capped at one end with a hemispherical dome of the same radius $r = 3$. A student calculates the total exterior surface area as shown. Which line contains the FIRST error?
- **Answer**: `2`
- **trapValue**: `3`
- **trapDerivation**: `3`
- **Evaluated Value**: `3`
- **Common Trap Tag**: `internal-boundary-double-count-trap`
- **Tag Description**: Erroneously counts the internal junction face between joined solids in composite surface area.

#### Seed 43
- **Prompt**: A composite solid consists of a right circular cylinder with radius $r = 3$ and height $h = 5$, capped at one end with a hemispherical dome of the same radius $r = 3$. A student calculates the total exterior surface area as shown. Which line contains the FIRST error?
- **Answer**: `2`
- **trapValue**: `3`
- **trapDerivation**: `3`
- **Evaluated Value**: `3`
- **Common Trap Tag**: `internal-boundary-double-count-trap`
- **Tag Description**: Erroneously counts the internal junction face between joined solids in composite surface area.

#### Seed 44
- **Prompt**: A composite solid consists of a right circular cylinder with radius $r = 2$ and height $h = 4$, capped at one end with a hemispherical dome of the same radius $r = 2$. A student calculates the total exterior surface area as shown. Which line contains the FIRST error?
- **Answer**: `2`
- **trapValue**: `3`
- **trapDerivation**: `3`
- **Evaluated Value**: `3`
- **Common Trap Tag**: `internal-boundary-double-count-trap`
- **Tag Description**: Erroneously counts the internal junction face between joined solids in composite surface area.

### Template: `find-flaw-composite-surface-area` | Form: `flaw-line-3`

#### Seed 42
- **Prompt**: A composite solid consists of a right circular cylinder with radius $r = 3$ and height $h = 5$, capped at one end with a hemispherical dome of the same radius $r = 3$. A student calculates the total exterior surface area as shown. Which line contains the FIRST error?
- **Answer**: `3`
- **trapValue**: `1`
- **trapDerivation**: `1`
- **Evaluated Value**: `1`
- **Common Trap Tag**: `internal-boundary-double-count-trap`
- **Tag Description**: Erroneously counts the internal junction face between joined solids in composite surface area.

#### Seed 43
- **Prompt**: A composite solid consists of a right circular cylinder with radius $r = 3$ and height $h = 5$, capped at one end with a hemispherical dome of the same radius $r = 3$. A student calculates the total exterior surface area as shown. Which line contains the FIRST error?
- **Answer**: `3`
- **trapValue**: `1`
- **trapDerivation**: `1`
- **Evaluated Value**: `1`
- **Common Trap Tag**: `internal-boundary-double-count-trap`
- **Tag Description**: Erroneously counts the internal junction face between joined solids in composite surface area.

#### Seed 44
- **Prompt**: A composite solid consists of a right circular cylinder with radius $r = 2$ and height $h = 4$, capped at one end with a hemispherical dome of the same radius $r = 2$. A student calculates the total exterior surface area as shown. Which line contains the FIRST error?
- **Answer**: `3`
- **trapValue**: `1`
- **trapDerivation**: `1`
- **Evaluated Value**: `1`
- **Common Trap Tag**: `internal-boundary-double-count-trap`
- **Tag Description**: Erroneously counts the internal junction face between joined solids in composite surface area.

