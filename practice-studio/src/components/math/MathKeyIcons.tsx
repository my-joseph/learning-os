import React from "react";

export type MathKeyIconId =
  | "frac"
  | "square"
  | "power"
  | "sqrt"
  | "cbrt"
  | "nroot"
  | "abs"
  | "pi"
  | "e"
  | "exp"
  | "pm"
  | "le"
  | "ge"
  | "ne"
  | "parens"
  | "brackets"
  | "comma"
  | "inf"
  | "ninf"
  | "ln"
  | "log"
  | "logb"
  | "sin"
  | "cos"
  | "tan"
  | "arcsin"
  | "arccos"
  | "arctan"
  | "i"
  | "theta"
  | "alpha"
  | "beta"
  | "Delta"
  | "cup"
  | "cap"
  | "emptyset";

export interface KeyIconProps {
  className?: string;
}

const STROKE_WIDTH = 1.35;
const GLYPH_FONT = "var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif";

interface KeyIconFrameProps {
  width?: number;
  className?: string;
  children: React.ReactNode;
}

/** Shared SVG frame preserving uniform scale and stroke weight across all palette keys. */
const KeyIconFrame: React.FC<KeyIconFrameProps> = ({
  width = 24,
  className,
  children,
}) => (
  <svg
    viewBox={`0 0 ${width} 24`}
    width={width}
    height={24}
    fill="none"
    aria-hidden="true"
    focusable="false"
    className={className}
  >
    {children}
  </svg>
);

export interface PlaceholderProps {
  x: number;
  y: number;
  size?: number;
  rx?: number;
  strokeWidth?: number;
}

/** Shared dashed rounded-square placeholder used inside all template key icons. */
export const Placeholder: React.FC<PlaceholderProps> = ({
  x,
  y,
  size = 7.5,
  rx = 1.5,
  strokeWidth = 1.4,
}) => (
  <rect
    x={x}
    y={y}
    width={size}
    height={size}
    rx={rx}
    fill="none"
    stroke="currentColor"
    strokeOpacity={0.85}
    strokeWidth={strokeWidth}
    strokeDasharray="1.5 1.5"
  />
);

interface StrokePathProps {
  d: string;
  strokeWidth?: number;
}

const StrokePath: React.FC<StrokePathProps> = ({
  d,
  strokeWidth = STROKE_WIDTH,
}) => (
  <path
    d={d}
    fill="none"
    stroke="currentColor"
    strokeWidth={strokeWidth}
    strokeLinecap="round"
    strokeLinejoin="round"
  />
);

interface GlyphTextProps {
  x: number;
  y: number;
  fontSize?: number;
  fontStyle?: "normal" | "italic";
  textAnchor?: "start" | "middle" | "end";
  letterSpacing?: string;
  children: React.ReactNode;
}

const GlyphText: React.FC<GlyphTextProps> = ({
  x,
  y,
  fontSize = 13,
  fontStyle = "normal",
  textAnchor = "start",
  letterSpacing,
  children,
}) => (
  <text
    x={x}
    y={y}
    fill="currentColor"
    fontFamily={GLYPH_FONT}
    fontSize={fontSize}
    fontWeight={500}
    fontStyle={fontStyle}
    textAnchor={textAnchor}
    letterSpacing={letterSpacing}
  >
    {children}
  </text>
);

export const FracKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <Placeholder x={8.75} y={2} size={6.5} rx={1.3} />
    <StrokePath d="M 5.5 12 H 18.5" />
    <Placeholder x={8.75} y={15.5} size={6.5} rx={1.3} />
  </KeyIconFrame>
);

export const SquareKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <Placeholder x={4.5} y={9.25} size={8} rx={1.5} />
    <GlyphText x={15.75} y={10} fontSize={8} textAnchor="middle">
      2
    </GlyphText>
  </KeyIconFrame>
);

export const PowerKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <Placeholder x={4.25} y={9.5} size={8} rx={1.5} />
    <Placeholder x={13.75} y={4.5} size={5.5} rx={1.2} />
  </KeyIconFrame>
);

export const SqrtKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 3 13.5 L 5.5 18 L 9.5 6.5 H 20.5" />
    <Placeholder x={11.5} y={9.75} size={7.5} rx={1.5} />
  </KeyIconFrame>
);

export const CbrtKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={4.75} y={10.5} fontSize={7} textAnchor="middle">
      3
    </GlyphText>
    <StrokePath d="M 4 14.5 L 6.5 18.25 L 10 6.75 H 20.5" />
    <Placeholder x={12} y={10.25} size={7} rx={1.4} />
  </KeyIconFrame>
);

export const NrootKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <Placeholder x={2} y={4.75} size={5} rx={1.1} />
    <StrokePath d="M 4.5 15 L 7 18.25 L 10.5 6.75 H 21" />
    <Placeholder x={12.5} y={10.25} size={7} rx={1.4} />
  </KeyIconFrame>
);

export const AbsKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 5.5 5 V 19" />
    <Placeholder x={8.25} y={8.25} size={7.5} rx={1.5} />
    <StrokePath d="M 18.5 5 V 19" />
  </KeyIconFrame>
);

export const PiKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 6.5 8.5 H 17.5" />
    <StrokePath d="M 9.5 8.5 L 8.5 17" />
    <StrokePath d="M 14.5 8.5 V 15.2 C 14.5 16.5 15.6 17.1 17 16.5" />
  </KeyIconFrame>
);

export const EulerKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={12} y={16.5} fontSize={12} fontStyle="italic" textAnchor="middle">
      e
    </GlyphText>
  </KeyIconFrame>
);

export const ExpKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={8.25} y={17} fontSize={11.5} fontStyle="italic" textAnchor="middle">
      e
    </GlyphText>
    <Placeholder x={13.25} y={4.75} size={5.5} rx={1.2} />
  </KeyIconFrame>
);

export const PmKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 7.5 9.5 H 16.5" />
    <StrokePath d="M 12 5 V 14" />
    <StrokePath d="M 7.5 17.5 H 16.5" />
  </KeyIconFrame>
);

export const LeKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame width={28} className={className}>
    <Placeholder x={2} y={8.75} size={6.5} rx={1.3} />
    <StrokePath d="M 16.2 7.75 L 11.8 10.3 L 16.2 12.85" />
    <StrokePath d="M 11.8 15.5 H 16.2" />
    <Placeholder x={19.5} y={8.75} size={6.5} rx={1.3} />
  </KeyIconFrame>
);

export const GeKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame width={28} className={className}>
    <Placeholder x={2} y={8.75} size={6.5} rx={1.3} />
    <StrokePath d="M 11.8 7.75 L 16.2 10.3 L 11.8 12.85" />
    <StrokePath d="M 11.8 15.5 H 16.2" />
    <Placeholder x={19.5} y={8.75} size={6.5} rx={1.3} />
  </KeyIconFrame>
);

export const NeKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame width={28} className={className}>
    <Placeholder x={2} y={8.75} size={6.5} rx={1.3} />
    <StrokePath d="M 11.5 10.3 H 16.5" />
    <StrokePath d="M 11.5 13.7 H 16.5" />
    <StrokePath d="M 15.4 7.5 L 12.6 16.5" />
    <Placeholder x={19.5} y={8.75} size={6.5} rx={1.3} />
  </KeyIconFrame>
);

export const ParensKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 6.5 5.5 C 4 8.5 4 15.5 6.5 18.5" />
    <Placeholder x={8.25} y={8.25} size={7.5} rx={1.5} />
    <StrokePath d="M 17.5 5.5 C 20 8.5 20 15.5 17.5 18.5" />
  </KeyIconFrame>
);

export const BracketsKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 6.5 5.5 H 4.5 V 18.5 H 6.5" />
    <Placeholder x={8.25} y={8.25} size={7.5} rx={1.5} />
    <StrokePath d="M 17.5 5.5 H 19.5 V 18.5 H 17.5" />
  </KeyIconFrame>
);

export const CommaKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <circle cx={12} cy={13.5} r={1.15} fill="currentColor" />
    <StrokePath d="M 12.6 14.2 C 12.6 15.9 11.7 17.2 10.6 17.9" strokeWidth={1.3} />
  </KeyIconFrame>
);

export const InfKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 12 12 C 10.2 9.1 7.5 8.5 5.8 9.8 C 4.2 11 4.2 13 5.8 14.2 C 7.5 15.5 10.2 14.9 12 12 C 13.8 9.1 16.5 8.5 18.2 9.8 C 19.8 11 19.8 13 18.2 14.2 C 16.5 15.5 13.8 14.9 12 12 Z" />
  </KeyIconFrame>
);

export const NinfKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 3 12 H 6.75" />
    <StrokePath d="M 14.75 12 C 13.4 9.7 11.4 9 10 10 C 8.6 11 8.6 13 10 14 C 11.4 15 13.4 14.3 14.75 12 C 16.1 9.7 18.1 9 19.5 10 C 20.9 11 20.9 13 19.5 14 C 18.1 15 16.1 14.3 14.75 12 Z" />
  </KeyIconFrame>
);

export const LnKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame width={27} className={className}>
    <GlyphText x={1.75} y={15.25} fontSize={9.5} letterSpacing="-0.02em">
      ln
    </GlyphText>
    <StrokePath d="M 13.5 7.5 C 11.9 9.8 11.9 14.2 13.5 16.5" strokeWidth={1.25} />
    <Placeholder x={15} y={8.75} size={6.5} rx={1.3} />
    <StrokePath d="M 23.25 7.5 C 24.85 9.8 24.85 14.2 23.25 16.5" strokeWidth={1.25} />
  </KeyIconFrame>
);

export const LogKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame width={27} className={className}>
    <GlyphText x={0.5} y={15.25} fontSize={9.5} letterSpacing="-0.04em">
      log
    </GlyphText>
    <StrokePath d="M 15 7.5 C 13.5 9.8 13.5 14.2 15 16.5" strokeWidth={1.25} />
    <Placeholder x={16.25} y={8.75} size={5.5} rx={1.2} />
    <StrokePath d="M 26 7.5 C 27.5 9.8 27.5 14.2 26 16.5" strokeWidth={1.25} />
  </KeyIconFrame>
);

export const LogBaseKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame width={28} className={className}>
    <GlyphText x={0.5} y={15.25} fontSize={9.5} letterSpacing="-0.04em">
      log
    </GlyphText>
    <Placeholder x={12.75} y={12.5} size={4.5} rx={1} />
    <StrokePath d="M 19 7.5 C 17.5 9.8 17.5 14.2 19 16.5" strokeWidth={1.25} />
    <Placeholder x={19.75} y={8.75} size={5.25} rx={1.15} />
    <StrokePath d="M 26.25 7.5 C 27.75 9.8 27.75 14.2 26.25 16.5" strokeWidth={1.25} />
  </KeyIconFrame>
);

function createTrigIcon(name: string): React.FC<KeyIconProps> {
  const TrigIcon: React.FC<KeyIconProps> = ({ className }) => (
    <KeyIconFrame width={29} className={className}>
      <GlyphText x={1.75} y={15.25} fontSize={9.5} letterSpacing="-0.02em">
        {name}
      </GlyphText>
      <Placeholder x={19} y={8.5} size={7} rx={1.4} />
    </KeyIconFrame>
  );
  TrigIcon.displayName = `${name}KeyIcon`;
  return TrigIcon;
}

function createInverseTrigIcon(name: string): React.FC<KeyIconProps> {
  const InverseTrigIcon: React.FC<KeyIconProps> = ({ className }) => (
    <KeyIconFrame width={34} className={className}>
      <GlyphText x={1} y={15.75} fontSize={9} letterSpacing="-0.03em">
        {name}
      </GlyphText>
      <GlyphText x={15.75} y={10.25} fontSize={6.25} letterSpacing="-0.04em">
        −1
      </GlyphText>
      <Placeholder x={24.5} y={9} size={6.5} rx={1.3} />
    </KeyIconFrame>
  );
  InverseTrigIcon.displayName = `Arc${name}KeyIcon`;
  return InverseTrigIcon;
}

export const SinKeyIcon = createTrigIcon("sin");
export const CosKeyIcon = createTrigIcon("cos");
export const TanKeyIcon = createTrigIcon("tan");
export const ArcsinKeyIcon = createInverseTrigIcon("sin");
export const ArccosKeyIcon = createInverseTrigIcon("cos");
export const ArctanKeyIcon = createInverseTrigIcon("tan");

export const ImaginaryUnitKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={12} y={17} fontSize={12} fontStyle="italic" textAnchor="middle">
      i
    </GlyphText>
  </KeyIconFrame>
);

export const ThetaKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={12} y={16.5} fontSize={12} fontStyle="italic" textAnchor="middle">
      θ
    </GlyphText>
  </KeyIconFrame>
);

export const AlphaKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={12} y={16} fontSize={12} fontStyle="italic" textAnchor="middle">
      α
    </GlyphText>
  </KeyIconFrame>
);

export const BetaKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <GlyphText x={12} y={16.5} fontSize={12} fontStyle="italic" textAnchor="middle">
      β
    </GlyphText>
  </KeyIconFrame>
);

export const DeltaKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 12 6.5 L 18 17.5 H 6 Z" />
  </KeyIconFrame>
);

export const CupKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 7.5 7 V 13 C 7.5 15.8 9.5 17.5 12 17.5 C 14.5 17.5 16.5 15.8 16.5 13 V 7" />
  </KeyIconFrame>
);

export const CapKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <StrokePath d="M 7.5 17 V 11 C 7.5 8.2 9.5 6.5 12 6.5 C 14.5 6.5 16.5 8.2 16.5 11 V 17" />
  </KeyIconFrame>
);

export const EmptysetKeyIcon: React.FC<KeyIconProps> = ({ className }) => (
  <KeyIconFrame className={className}>
    <circle
      cx={12}
      cy={12}
      r={5}
      fill="none"
      stroke="currentColor"
      strokeWidth={STROKE_WIDTH}
    />
    <StrokePath d="M 7.5 17 L 16.5 7" />
  </KeyIconFrame>
);

export const MATH_KEY_ICONS: Record<MathKeyIconId, React.ComponentType<KeyIconProps>> = {
  frac: FracKeyIcon,
  square: SquareKeyIcon,
  power: PowerKeyIcon,
  sqrt: SqrtKeyIcon,
  cbrt: CbrtKeyIcon,
  nroot: NrootKeyIcon,
  abs: AbsKeyIcon,
  pi: PiKeyIcon,
  e: EulerKeyIcon,
  exp: ExpKeyIcon,
  pm: PmKeyIcon,
  le: LeKeyIcon,
  ge: GeKeyIcon,
  ne: NeKeyIcon,
  parens: ParensKeyIcon,
  brackets: BracketsKeyIcon,
  comma: CommaKeyIcon,
  inf: InfKeyIcon,
  ninf: NinfKeyIcon,
  ln: LnKeyIcon,
  log: LogKeyIcon,
  logb: LogBaseKeyIcon,
  sin: SinKeyIcon,
  cos: CosKeyIcon,
  tan: TanKeyIcon,
  arcsin: ArcsinKeyIcon,
  arccos: ArccosKeyIcon,
  arctan: ArctanKeyIcon,
  i: ImaginaryUnitKeyIcon,
  theta: ThetaKeyIcon,
  alpha: AlphaKeyIcon,
  beta: BetaKeyIcon,
  Delta: DeltaKeyIcon,
  cup: CupKeyIcon,
  cap: CapKeyIcon,
  emptyset: EmptysetKeyIcon,
};

export const MathKeyIcon: React.FC<{ iconId: MathKeyIconId; className?: string }> = ({
  iconId,
  className,
}) => {
  const Icon = MATH_KEY_ICONS[iconId];
  return <Icon className={className} />;
};
