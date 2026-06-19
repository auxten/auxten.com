import type {CSSProperties, ReactNode} from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Series,
  staticFile,
  useCurrentFrame,
  interpolate,
} from "remotion";

export const WIDTH = 1280;
export const HEIGHT = 720;
export const FPS = 30;
export const SLIDE_SECONDS = 75;

const colors = {
  ink: "#161616",
  muted: "#69707d",
  faint: "#eef1f4",
  paper: "#fbfbf8",
  yellow: "#fadb14",
  orange: "#e65100",
  blue: "#1565c0",
  green: "#2e7d32",
  red: "#c62828",
  dark: "#1f2328",
};

type SceneProps = {
  index: number;
};

type SlideDef = {
  kicker: string;
  component: (props: SceneProps) => ReactNode;
};

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const ease = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const pop = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, (start + end) / 2, end], [0.86, 1.04, 1], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const inStyle = (frame: number, delay = 0, distance = 24): CSSProperties => {
  const p = ease(frame, delay * FPS, (delay + 0.75) * FPS);
  return {
    opacity: p,
    transform: `translateY(${(1 - p) * distance}px) scale(${0.98 + p * 0.02})`,
  };
};

const asset = (path: string) => staticFile(`assets/${path}`);

const Card = ({
  children,
  style,
  tone = "white",
}: {
  children: ReactNode;
  style?: CSSProperties;
  tone?: "white" | "yellow" | "blue" | "green" | "red" | "dark";
}) => {
  const palette = {
    white: {bg: "#fff", border: "#e7e9ee", color: colors.ink},
    yellow: {bg: "#fff8d7", border: "#f0d74a", color: colors.ink},
    blue: {bg: "#eef6ff", border: "#86bdf2", color: colors.blue},
    green: {bg: "#eff9ef", border: "#9ad59c", color: colors.green},
    red: {bg: "#fff0f0", border: "#f1a2a2", color: colors.red},
    dark: {bg: colors.dark, border: colors.dark, color: "#fff"},
  }[tone];

  return (
    <div
      style={{
        background: palette.bg,
        border: `2px solid ${palette.border}`,
        color: palette.color,
        borderRadius: 18,
        padding: 26,
        boxShadow: "0 14px 36px rgba(20, 20, 20, 0.08)",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const Label = ({children, tone = "blue"}: {children: ReactNode; tone?: "blue" | "green" | "orange" | "dark"}) => {
  const color = tone === "blue" ? colors.blue : tone === "green" ? colors.green : tone === "orange" ? colors.orange : colors.dark;
  return (
    <span
      style={{
        display: "inline-flex",
        border: `2px solid ${color}`,
        color,
        borderRadius: 999,
        padding: "8px 16px",
        fontSize: 24,
        fontWeight: 800,
        background: "#fff",
      }}
    >
      {children}
    </span>
  );
};

const SlideFrame = ({
  children,
  index,
  kicker,
}: {
  children: ReactNode;
  index: number;
  kicker: string;
}) => {
  const progress = (index + 1) / SLIDES.length;

  return (
    <AbsoluteFill
      style={{
        background: colors.paper,
        color: colors.ink,
        fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(90deg, rgba(22,22,22,0.035) 1px, transparent 1px), linear-gradient(rgba(22,22,22,0.035) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
          opacity: 0.6,
        }}
      />
      <div style={{position: "absolute", left: 54, top: 34, fontSize: 22, fontWeight: 800, color: colors.muted}}>
        {kicker}
      </div>
      <div style={{position: "absolute", right: 54, top: 34, display: "flex", gap: 10, alignItems: "center"}}>
        <div style={{width: 170, height: 6, background: "#e7e9ee", borderRadius: 999, overflow: "hidden"}}>
          <div style={{height: 6, width: `${Math.round(progress * 100)}%`, background: colors.orange}} />
        </div>
        <div style={{fontSize: 20, fontWeight: 800, color: colors.muted}}>
          {String(index + 1).padStart(2, "0")} / {String(SLIDES.length).padStart(2, "0")}
        </div>
      </div>
      <div style={{position: "absolute", inset: "78px 54px 54px"}}>{children}</div>
    </AbsoluteFill>
  );
};

const BigTitle = ({children, style}: {children: ReactNode; style?: CSSProperties}) => (
  <div style={{fontSize: 76, lineHeight: 0.96, letterSpacing: -2, fontWeight: 900, ...style}}>{children}</div>
);

const Mono = ({children, style}: {children: ReactNode; style?: CSSProperties}) => (
  <div
    style={{
      fontFamily: "'JetBrains Mono', 'SFMono-Regular', Menlo, monospace",
      fontSize: 25,
      lineHeight: 1.45,
      background: colors.dark,
      color: "#f7f7f7",
      borderRadius: 18,
      padding: "24px 28px",
      boxShadow: "0 18px 46px rgba(0,0,0,0.18)",
      ...style,
    }}
  >
    {children}
  </div>
);

const Arrow = ({style}: {style?: CSSProperties}) => (
  <div style={{fontSize: 38, color: "#9aa2ad", fontWeight: 900, ...style}}>→</div>
);

const Logo = ({src, style}: {src: string; style?: CSSProperties}) => (
  <Img src={asset(src)} style={{objectFit: "contain", ...style}} />
);

const TitleScene = () => {
  const frame = useCurrentFrame();
  const p = ease(frame, 0, 28);
  const line = ease(frame, 18, 50);
  return (
    <div style={{height: "100%", display: "flex", alignItems: "center", justifyContent: "space-between"}}>
      <div style={{...inStyle(frame, 0.1), width: 760}}>
        <div style={{display: "flex", alignItems: "center", gap: 24, marginBottom: 34}}>
          <Logo src="logos/chdb-light.png" style={{width: 88, height: 88}} />
          <Logo src="logos/clickhouse-logo-black.svg" style={{width: 250, height: 62}} />
        </div>
        <BigTitle>
          Giving Your AI Agent
          <br />
          a Database Brain
        </BigTitle>
        <div style={{fontSize: 34, marginTop: 26, color: colors.muted, fontWeight: 700}}>
          In-Process Analytics with <span style={{color: colors.orange}}>chDB</span>
        </div>
        <div style={{fontSize: 24, marginTop: 32, color: colors.muted}}>
          Auxten Wang · Technical Director @ ClickHouse · PyCon Singapore 2026
        </div>
      </div>
      <div style={{position: "relative", width: 380, height: 380, opacity: p, transform: `scale(${0.92 + p * 0.08})`}}>
        <div
          style={{
            position: "absolute",
            inset: 18,
            borderRadius: 34,
            border: `7px solid ${colors.yellow}`,
            transform: `rotate(${line * 9}deg)`,
            background: "#fff",
            boxShadow: "0 30px 80px rgba(0,0,0,0.15)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 70,
            top: 90,
            width: 240,
            height: 190,
            borderRadius: 24,
            background: colors.dark,
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 92,
            fontWeight: 900,
          }}
        >
          SQL
        </div>
      </div>
    </div>
  );
};

const FailureScene = () => {
  const frame = useCurrentFrame();
  const cards = [
    {title: "Yesterday", body: "Found the right workaround", tone: "green" as const},
    {title: "Today", body: "Similar task, missing context", tone: "yellow" as const},
    {title: "Result", body: "Repeats the failed plan", tone: "red" as const},
  ];
  return (
    <div>
      <BigTitle style={{fontSize: 66, marginBottom: 42}}>A familiar agent failure</BigTitle>
      <div style={{display: "flex", alignItems: "center", gap: 24}}>
        {cards.map((card, i) => (
          <div key={card.title} style={{display: "flex", alignItems: "center", gap: 24, ...inStyle(frame, 0.15 + i * 0.25)}}>
            <Card tone={card.tone} style={{width: 305, height: 190}}>
              <div style={{fontSize: 32, fontWeight: 900}}>{card.title}</div>
              <div style={{fontSize: 28, lineHeight: 1.18, marginTop: 18, color: card.tone === "red" ? colors.red : colors.ink}}>
                {card.body}
              </div>
            </Card>
            {i < cards.length - 1 ? <Arrow /> : null}
          </div>
        ))}
      </div>
      <div style={{...inStyle(frame, 1.35), marginTop: 54}}>
        <Card tone="dark" style={{fontSize: 40, fontWeight: 900, lineHeight: 1.2}}>
          The right context was not queryable at the right time.
        </Card>
      </div>
    </div>
  );
};

const ContextScene = () => {
  const frame = useCurrentFrame();
  const chips = [
    {text: "instructions", x: 78, y: 108, color: colors.blue},
    {text: "working data", x: 790, y: 88, color: colors.green},
    {text: "memory", x: 118, y: 390, color: colors.orange},
    {text: "eval history", x: 760, y: 405, color: colors.red},
  ];
  const pulse = Math.sin(frame / 18) * 5;
  return (
    <div style={{height: "100%", position: "relative"}}>
      <BigTitle style={{fontSize: 64, width: 620}}>Context engineering needs a local database</BigTitle>
      <div
        style={{
          position: "absolute",
          left: 430,
          top: 210,
          width: 330,
          height: 210,
          borderRadius: 34,
          background: colors.dark,
          color: "#fff",
          boxShadow: "0 26px 70px rgba(0,0,0,0.18)",
          transform: `translateY(${pulse}px)`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        <div style={{fontSize: 92, fontWeight: 900}}>SQL</div>
        <div style={{fontSize: 26, color: "#c8ced6", fontWeight: 700}}>local context DB</div>
      </div>
      {chips.map((chip, i) => {
        const p = ease(frame, 12 + i * 8, 40 + i * 8);
        return (
          <div
            key={chip.text}
            style={{
              position: "absolute",
              left: chip.x,
              top: chip.y,
              opacity: p,
              transform: `scale(${pop(frame, 12 + i * 8, 48 + i * 8)})`,
            }}
          >
            <div style={{height: 4, width: 250, background: chip.color, opacity: 0.35, transform: "translate(190px, 72px) rotate(12deg)"}} />
            <Card style={{width: 250, fontSize: 32, fontWeight: 900, textAlign: "center", borderColor: chip.color}}>{chip.text}</Card>
          </div>
        );
      })}
      <div style={{position: "absolute", bottom: 26, left: 0, fontSize: 34, fontWeight: 800, color: colors.muted}}>
        Recall = find the few facts that matter <span style={{color: colors.orange}}>now</span>.
      </div>
    </div>
  );
};

const VectorScene = () => {
  const frame = useCurrentFrame();
  return (
    <div>
      <BigTitle style={{fontSize: 68}}>Why not just a vector DB?</BigTitle>
      <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 34, marginTop: 48}}>
        <Card tone="blue" style={{height: 310, ...inStyle(frame, 0.1)}}>
          <div style={{fontSize: 34, fontWeight: 900}}>Vector search</div>
          <div style={{fontSize: 118, fontWeight: 900, marginTop: 30, color: colors.blue}}>≈</div>
          <div style={{fontSize: 30, color: colors.ink}}>meaning match</div>
        </Card>
        <Card tone="dark" style={{height: 310, ...inStyle(frame, 0.45)}}>
          <div style={{fontSize: 34, fontWeight: 900}}>Agent memory</div>
          <div style={{display: "flex", flexWrap: "wrap", gap: 12, marginTop: 40}}>
            {["scope", "privacy", "status", "tags", "conflicts", "history"].map((t) => (
              <Label key={t} tone={t === "conflicts" ? "orange" : "green"}>{t}</Label>
            ))}
          </div>
        </Card>
      </div>
      <div style={{...inStyle(frame, 1.1), marginTop: 42, fontSize: 38, fontWeight: 900}}>
        Vector search is one operator. The memory system is the database around it.
      </div>
    </div>
  );
};

const trustedLogos = [
  "clickhouse-trusted/anthropic_small_a6ab486d34.svg",
  "clickhouse-trusted/cursor_136f34ab68.svg",
  "clickhouse-trusted/character_3a9027ce90_4085d9ac89.svg",
  "clickhouse-trusted/sierra_321b705206.svg",
  "clickhouse-trusted/vercel_fa4c139b66.svg",
  "clickhouse-trusted/trusted_by_gitlab_2c2904bdb2.svg",
  "clickhouse-trusted/trusted_by_cloudflare_74f4bc587e.svg",
  "clickhouse-trusted/shopee_logo_1_f68ba1df69.svg",
];

const ClickHouseScene = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{height: "100%", display: "grid", gridTemplateColumns: "440px 1fr", gap: 42, alignItems: "center"}}>
      <div style={inStyle(frame, 0.1)}>
        <Logo src="logos/clickhouse-logo-black.svg" style={{width: 360, height: 92, marginBottom: 40}} />
        <BigTitle style={{fontSize: 58}}>ClickHouse in 60 seconds</BigTitle>
        <div style={{fontSize: 30, lineHeight: 1.28, marginTop: 28, color: colors.muted, fontWeight: 700}}>
          An open-source analytical database for fast SQL over large tables.
        </div>
      </div>
      <div>
        <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18}}>
          {trustedLogos.map((logo, i) => (
            <Card key={logo} style={{height: 76, padding: 18, display: "flex", alignItems: "center", justifyContent: "center", ...inStyle(frame, 0.15 + i * 0.05)}}>
              <Logo src={logo} style={{maxWidth: 150, maxHeight: 40}} />
            </Card>
          ))}
        </div>
        <div style={{...inStyle(frame, 0.85), marginTop: 26}}>
          <Card tone="yellow" style={{fontSize: 30, lineHeight: 1.2, fontWeight: 900}}>
            Use it when asking questions over lots of data is on the hot path.
          </Card>
        </div>
      </div>
    </div>
  );
};

const ChdbScene = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{height: "100%", position: "relative"}}>
      <BigTitle style={{fontSize: 66}}>chDB: ClickHouse inside Python</BigTitle>
      <div style={{display: "flex", alignItems: "center", gap: 34, marginTop: 48}}>
        <Card tone="blue" style={{width: 340, height: 260, ...inStyle(frame, 0.1)}}>
          <div style={{fontSize: 98, fontWeight: 900}}>.py</div>
          <div style={{fontSize: 30, fontWeight: 900}}>Python process</div>
        </Card>
        <Arrow />
        <Card tone="yellow" style={{width: 360, height: 260, ...inStyle(frame, 0.45)}}>
          <Logo src="logos/chdb-light.png" style={{width: 120, height: 120}} />
          <div style={{fontSize: 32, fontWeight: 900, marginTop: 18}}>embedded OLAP engine</div>
        </Card>
        <Arrow />
        <Card tone="green" style={{width: 340, height: 260, ...inStyle(frame, 0.8)}}>
          <div style={{fontSize: 54, fontWeight: 900}}>no server</div>
          <div style={{fontSize: 30, marginTop: 26}}>no daemon</div>
          <div style={{fontSize: 30}}>no setup</div>
        </Card>
      </div>
      <Mono style={{position: "absolute", left: 0, bottom: 10, width: 630, fontSize: 27, ...inStyle(frame, 1.1)}}>
        <span style={{color: colors.yellow}}>pip install</span> chdb
        <br />
        sess = chs.Session(<span style={{color: "#9be28f"}}>"./agent_context"</span>)
      </Mono>
    </div>
  );
};

const InterfaceScene = () => {
  const frame = useCurrentFrame();
  const sources = [
    {label: "HTTP API", expr: "url(...)", color: colors.blue},
    {label: "Local CSV", expr: "file(...)", color: colors.green},
    {label: "DataFrame", expr: "Python(...)", color: colors.orange},
  ];
  return (
    <div style={{display: "grid", gridTemplateColumns: "0.58fr 1.42fr", gap: 28, alignItems: "center", height: "100%"}}>
      <div>
        <BigTitle style={{fontSize: 58}}>Join anything with SQL</BigTitle>
        <div style={{display: "grid", gap: 14, marginTop: 38}}>
          {sources.map((source, i) => (
            <Card key={source.label} style={{padding: 18, borderColor: source.color, ...inStyle(frame, 0.16 + i * 0.16)}}>
              <div style={{fontSize: 28, fontWeight: 900, color: source.color}}>{source.label}</div>
              <div style={{fontFamily: "JetBrains Mono, monospace", fontSize: 23, marginTop: 8, fontWeight: 800}}>{source.expr}</div>
            </Card>
          ))}
        </div>
        <div style={{fontSize: 28, lineHeight: 1.25, color: colors.muted, fontWeight: 800, marginTop: 34}}>
          Three data sources. One query. No ETL.
        </div>
      </div>
      <div style={inStyle(frame, 0.3)}>
        <Mono style={{fontSize: 20, lineHeight: 1.32}}>
          <span style={{color: "#7cc7ff"}}>chdb.query</span>(<span style={{color: "#9be28f"}}>"""</span>
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>SELECT</span> name, age, purchase_total
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>FROM</span> url(<span style={{color: "#9be28f"}}>'https://api.example.com/users.parquet'</span>) users
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>LEFT JOIN</span> file(<span style={{color: "#9be28f"}}>'local_orders.csv'</span>) orders
          <br />
          &nbsp;&nbsp;&nbsp;&nbsp;<span style={{color: colors.yellow}}>ON</span> users.uid = orders.uid
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>LEFT JOIN</span> Python(processed_df) enriched
          <br />
          &nbsp;&nbsp;&nbsp;&nbsp;<span style={{color: colors.yellow}}>ON</span> enriched.uid = users.uid
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>WHERE</span> age &gt; 25
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>ORDER BY</span> purchase_total <span style={{color: colors.yellow}}>DESC</span>
          <br />
          &nbsp;&nbsp;<span style={{color: colors.yellow}}>LIMIT</span> 1000
          <br />
          <span style={{color: "#9be28f"}}>"""</span>)
        </Mono>
      </div>
    </div>
  );
};

const DataCheckScene = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "grid", gridTemplateColumns: "1.08fr 0.92fr", gap: 34, alignItems: "center", height: "100%"}}>
      <div>
        <BigTitle style={{fontSize: 58}}>Check local and remote data with one query</BigTitle>
        <div style={{display: "flex", gap: 18, marginTop: 46}}>
          {["count", "revenue", "checksum"].map((item, i) => (
            <Card key={item} tone="green" style={{width: 190, textAlign: "center", ...inStyle(frame, 0.25 + i * 0.2)}}>
              <div style={{fontSize: 50, fontWeight: 900}}>✓</div>
              <div style={{fontSize: 26, fontWeight: 900}}>{item}</div>
            </Card>
          ))}
        </div>
        <div style={{fontSize: 28, color: colors.muted, marginTop: 44, lineHeight: 1.3, fontWeight: 700}}>
          The agent gets an auditable answer before trusting the data.
        </div>
      </div>
      <Mono style={{fontSize: 21, lineHeight: 1.32, ...inStyle(frame, 0.35)}}>
        <span style={{color: "#7cc7ff"}}>chdb.query</span>(<span style={{color: "#9be28f"}}>"""</span>
        <br />
        WITH local AS (
        <br />
        &nbsp;&nbsp;SELECT count() rows, sum(amount) revenue
        <br />
        &nbsp;&nbsp;FROM file(<span style={{color: "#9be28f"}}>'orders.parquet'</span>, Parquet)
        <br />
        ), cloud AS (
        <br />
        &nbsp;&nbsp;SELECT count() rows, sum(amount) revenue
        <br />
        &nbsp;&nbsp;FROM remoteSecure(<span style={{color: "#9be28f"}}>'cloud:9440'</span>, ...)
        <br />
        )
        <br />
        SELECT local.rows = cloud.rows AS same_count,
        <br />
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;local.revenue = cloud.revenue AS same_revenue
        <br />
        FROM local, cloud
        <br />
        <span style={{color: "#9be28f"}}>"""</span>)
      </Mono>
    </div>
  );
};

const MemoryRowScene = () => {
  const frame = useCurrentFrame();
  const cells = [
    ["content", "Use chDB file() for local Parquet checks."],
    ["project", "auxten/chdb"],
    ["tags", "parquet, fidelity"],
    ["status", "active"],
    ["embedding", "[0.02, -0.11, ...]"],
  ];
  return (
    <div>
      <BigTitle style={{fontSize: 64}}>Good agent memory must be a row</BigTitle>
      <div style={{display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginTop: 58}}>
        {cells.map(([head, value], i) => (
          <Card key={head} style={{height: 230, padding: 20, ...inStyle(frame, 0.12 + i * 0.12)}}>
            <div style={{fontSize: 24, color: colors.orange, fontWeight: 900, textTransform: "uppercase"}}>{head}</div>
            <div style={{fontSize: 25, lineHeight: 1.22, marginTop: 24, fontWeight: 800}}>{value}</div>
          </Card>
        ))}
      </div>
      <div style={{...inStyle(frame, 1.0), marginTop: 50}}>
        <Card tone="dark" style={{fontSize: 36, fontWeight: 900}}>
          Once memory is a row, recall can use filters, joins, vectors, and history.
        </Card>
      </div>
    </div>
  );
};

const LifecycleScene = () => {
  const frame = useCurrentFrame();
  const steps = [
    ["remember", "explicit decision", "green"],
    ["recall", "project + vector", "blue"],
    ["conflict?", "similar but different", "red"],
    ["revise", "better belief wins", "green"],
  ] as const;
  return (
    <div>
      <BigTitle style={{fontSize: 66}}>ClickMem lifecycle</BigTitle>
      <div style={{display: "flex", alignItems: "center", gap: 16, marginTop: 58}}>
        {steps.map(([title, sub, tone], i) => (
          <div key={title} style={{display: "flex", alignItems: "center", gap: 16, ...inStyle(frame, 0.15 + i * 0.2)}}>
            <Card tone={tone === "red" ? "red" : tone === "blue" ? "blue" : "green"} style={{width: 225, height: 160}}>
              <div style={{fontSize: 34, fontWeight: 900}}>{title}</div>
              <div style={{fontSize: 22, marginTop: 18, color: colors.muted, fontWeight: 700}}>{sub}</div>
            </Card>
            {i < steps.length - 1 ? <Arrow /> : null}
          </div>
        ))}
      </div>
      <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 26, marginTop: 54}}>
        <Card tone="red" style={inStyle(frame, 1.1)}>
          <div style={{fontSize: 28, fontWeight: 900}}>Old memory</div>
          <div style={{fontSize: 34, marginTop: 16}}>"Use Poetry for this repo."</div>
        </Card>
        <Card tone="green" style={inStyle(frame, 1.3)}>
          <div style={{fontSize: 28, fontWeight: 900}}>Revised memory</div>
          <div style={{fontSize: 34, marginTop: 16}}>"This repo now standardizes on uv."</div>
        </Card>
      </div>
    </div>
  );
};

const ArchitectureScene = () => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "grid", gridTemplateColumns: "0.7fr 1.3fr", gap: 34, alignItems: "center", height: "100%"}}>
      <div style={inStyle(frame, 0.1)}>
        <BigTitle style={{fontSize: 58}}>Where ClickMem runs</BigTitle>
        <div style={{marginTop: 34, display: "grid", gap: 14}}>
          <Label tone="green">agent adapters</Label>
          <Label tone="blue">local server</Label>
          <Label tone="orange">chDB backend</Label>
          <Label tone="dark">ClickHouse escape hatch</Label>
        </div>
      </div>
      <Card style={{padding: 18, ...inStyle(frame, 0.35)}}>
        <Logo src="logos/clickmem-architecture.png" style={{width: "100%", height: 430, objectFit: "contain"}} />
      </Card>
    </div>
  );
};

const QueryScene = () => {
  const frame = useCurrentFrame();
  const bands = [
    ["WHERE", "project + status + tags", colors.blue],
    ["cosine", "semantic meaning", colors.green],
    ["events", "used before", colors.orange],
  ];
  return (
    <div style={{display: "grid", gridTemplateColumns: "1.04fr 0.96fr", gap: 30, alignItems: "center", height: "100%"}}>
      <div>
        <BigTitle style={{fontSize: 54}}>One query ranks memory by meaning, rules, and past use</BigTitle>
        <div style={{display: "grid", gap: 14, marginTop: 44}}>
          {bands.map(([head, body, color], i) => (
            <Card key={head} style={{padding: 18, borderColor: color, ...inStyle(frame, 0.2 + i * 0.18)}}>
              <div style={{display: "flex", alignItems: "center", justifyContent: "space-between"}}>
                <div style={{fontSize: 34, fontWeight: 900, color}}>{head}</div>
                <div style={{fontSize: 26, fontWeight: 800}}>{body}</div>
              </div>
            </Card>
          ))}
        </div>
      </div>
      <Mono style={{fontSize: 20, lineHeight: 1.32, ...inStyle(frame, 0.35)}}>
        <span style={{color: "#7cc7ff"}}>chdb.query</span>(<span style={{color: "#9be28f"}}>"""</span>
        <br />
        SELECT m.id, m.content,
        <br />
        &nbsp;&nbsp;1 - cosineDistance(...) AS meaning,
        <br />
        &nbsp;&nbsp;count(e.id) AS used_before
        <br />
        FROM memories m
        <br />
        LEFT JOIN events e
        <br />
        WHERE project + status + tags
        <br />
        ORDER BY pinned, meaning, used_before
        <br />
        LIMIT 8
        <br />
        <span style={{color: "#9be28f"}}>"""</span>)
      </Mono>
    </div>
  );
};

const LatencyScene = () => {
  const frame = useCurrentFrame();
  const localWidth = interpolate(frame, [10, 50], [0, 145], clamp);
  const remoteWidth = interpolate(frame, [24, 74], [0, 760], clamp);
  return (
    <div>
      <BigTitle style={{fontSize: 66}}>Slow memory calls waste tokens</BigTitle>
      <div style={{marginTop: 70, display: "grid", gap: 48}}>
        <div>
          <div style={{fontSize: 28, fontWeight: 900}}>local in-process recall</div>
          <div style={{height: 42, marginTop: 12, background: "#e5f3e5", borderRadius: 999}}>
            <div style={{height: 42, width: localWidth, background: colors.green, borderRadius: 999}} />
          </div>
          <div style={{fontSize: 26, color: colors.green, marginTop: 10, fontWeight: 900}}>p99: 2.8 ms</div>
        </div>
        <div>
          <div style={{fontSize: 28, fontWeight: 900}}>remote recall with retries</div>
          <div style={{height: 42, marginTop: 12, background: "#ffe4e4", borderRadius: 999}}>
            <div style={{height: 42, width: remoteWidth, background: colors.red, borderRadius: 999}} />
          </div>
          <div style={{fontSize: 26, color: colors.red, marginTop: 10, fontWeight: 900}}>p99: up to 2,000 ms</div>
        </div>
      </div>
      <div style={{...inStyle(frame, 1.4), marginTop: 54, fontSize: 34, fontWeight: 900, color: colors.muted}}>
        In an agent loop, retries resend context. Latency becomes token waste.
      </div>
    </div>
  );
};

const ScaleScene = () => {
  const frame = useCurrentFrame();
  const ribbon = ease(frame, 20, 70);
  return (
    <div style={{height: "100%", position: "relative"}}>
      <BigTitle style={{fontSize: 66}}>Start local, scale to ClickHouse</BigTitle>
      <div style={{display: "flex", alignItems: "center", gap: 44, marginTop: 74}}>
        <Card tone="yellow" style={{width: 360, height: 230, ...inStyle(frame, 0.15)}}>
          <div style={{fontSize: 82, fontWeight: 900}}>Day 1</div>
          <div style={{fontSize: 30, marginTop: 16}}>chDB session on laptop</div>
        </Card>
        <div style={{width: 240, height: 8, background: "#e0e4ea", borderRadius: 999, overflow: "hidden"}}>
          <div style={{height: 8, width: 240 * ribbon, background: colors.orange}} />
        </div>
        <Card tone="blue" style={{width: 360, height: 230, ...inStyle(frame, 0.55)}}>
          <div style={{fontSize: 82, fontWeight: 900}}>Day 100</div>
          <div style={{fontSize: 30, marginTop: 16}}>ClickHouse Cloud or Server</div>
        </Card>
      </div>
      <Mono style={{position: "absolute", left: 80, bottom: 18, width: 900, fontSize: 25, ...inStyle(frame, 1.1)}}>
        <span style={{color: "#7cc7ff"}}>sess.query</span>(<span style={{color: "#9be28f"}}>"""</span>
        SELECT * FROM memories WHERE project_id = <span style={{color: "#9be28f"}}>'checkout'</span>
        <span style={{color: "#9be28f"}}>"""</span>)
      </Mono>
    </div>
  );
};

const BuildScene = () => {
  const frame = useCurrentFrame();
  const steps = ["create table", "insert decisions", "rank with SQL", "evaluate"];
  return (
    <div>
      <BigTitle style={{fontSize: 66}}>Build this afternoon: Mini ClickMem</BigTitle>
      <div style={{display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 18, marginTop: 64}}>
        {steps.map((step, i) => (
          <Card key={step} tone={i === 2 ? "yellow" : "white"} style={{height: 180, ...inStyle(frame, 0.15 + i * 0.2)}}>
            <div style={{fontSize: 56, fontWeight: 900, color: colors.orange}}>0{i + 1}</div>
            <div style={{fontSize: 30, fontWeight: 900, marginTop: 18}}>{step}</div>
          </Card>
        ))}
      </div>
      <Mono style={{marginTop: 50, fontSize: 24, lineHeight: 1.34, ...inStyle(frame, 1.1)}}>
        sess = chs.Session(<span style={{color: "#9be28f"}}>"./agent_context"</span>)
        <br />
        <span style={{color: "#7cc7ff"}}>sess.query</span>(<span style={{color: "#9be28f"}}>"""</span>
        SELECT content FROM memories
        <br />
        &nbsp;&nbsp;ORDER BY cosineDistance(embedding, {"{query_vec}"})
        <br />
        &nbsp;&nbsp;LIMIT 8
        <span style={{color: "#9be28f"}}>"""</span>)
      </Mono>
    </div>
  );
};

const TakeawaysScene = () => {
  const frame = useCurrentFrame();
  const items = [
    ["01", "Context is data.", "Filter it, rank it, join it, evaluate it."],
    ["02", "Recall is a query.", "Structured rules + vector meaning + task history."],
    ["03", "Local first.", "chDB now; ClickHouse when shared or large."],
  ];
  return (
    <div>
      <BigTitle style={{fontSize: 72}}>Three takeaways</BigTitle>
      <div style={{display: "grid", gap: 18, marginTop: 46}}>
        {items.map(([num, title, body], i) => (
          <Card key={num} tone={i === 1 ? "yellow" : "white"} style={{display: "grid", gridTemplateColumns: "90px 1fr", gap: 24, alignItems: "center", ...inStyle(frame, 0.15 + i * 0.24)}}>
            <div style={{fontSize: 46, fontWeight: 900, color: colors.orange}}>{num}</div>
            <div>
              <div style={{fontSize: 36, fontWeight: 900}}>{title}</div>
              <div style={{fontSize: 27, color: colors.muted, marginTop: 4, fontWeight: 700}}>{body}</div>
            </div>
          </Card>
        ))}
      </div>
      <div style={{position: "absolute", right: 70, bottom: 55, display: "flex", alignItems: "center", gap: 18, ...inStyle(frame, 1.3)}}>
        <Logo src="logos/chdb-light.png" style={{width: 74, height: 74}} />
        <div style={{fontSize: 34, fontWeight: 900}}>Q&amp;A</div>
      </div>
    </div>
  );
};

export const SLIDES: SlideDef[] = [
  {kicker: "PyCon Singapore 2026", component: TitleScene},
  {kicker: "The pain", component: FailureScene},
  {kicker: "Context engineering", component: ContextScene},
  {kicker: "Memory architecture", component: VectorScene},
  {kicker: "ClickHouse", component: ClickHouseScene},
  {kicker: "chDB", component: ChdbScene},
  {kicker: "Multi-source SQL", component: InterfaceScene},
  {kicker: "Data fidelity", component: DataCheckScene},
  {kicker: "Memory model", component: MemoryRowScene},
  {kicker: "ClickMem", component: LifecycleScene},
  {kicker: "ClickMem architecture", component: ArchitectureScene},
  {kicker: "Recall SQL", component: QueryScene},
  {kicker: "Local hot path", component: LatencyScene},
  {kicker: "Scale path", component: ScaleScene},
  {kicker: "Hackathon build", component: BuildScene},
  {kicker: "Close", component: TakeawaysScene},
];

export const AgentDatabaseBrain = () => {
  return (
    <Series>
      {SLIDES.map((slide, index) => {
        const Scene = slide.component;
        return (
          <Series.Sequence key={slide.kicker} durationInFrames={SLIDE_SECONDS * FPS}>
            <SlideFrame index={index} kicker={slide.kicker}>
              <Scene index={index} />
            </SlideFrame>
          </Series.Sequence>
        );
      })}
    </Series>
  );
};
