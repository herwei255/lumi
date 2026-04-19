import { AuthButtons, SignInButton } from "./components/SignInButton";

const FEATURES = [
  {
    icon: "✦",
    title: "Remembers everything",
    description: "Lumi keeps memory of every conversation. Tell it once — it never forgets.",
  },
  {
    icon: "⌘",
    title: "Lives in Telegram",
    description: "No new app to download. Just text it like you would a friend.",
  },
  {
    icon: "→",
    title: "Actually useful",
    description: "Answer questions, think through problems, get things done.",
  },
];

const STEPS = [
  { step: "01", title: "Get access", description: "Create an account in under a minute." },
  { step: "02", title: "Open Telegram", description: "Start a chat with Lumi — it's already waiting." },
  { step: "03", title: "Just talk", description: "Ask anything. Lumi learns as you go." },
];

export default function Home() {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#080810", color: "#f0f0f8" }}>

      {/* Nav */}
      <nav style={{
        position: "fixed", top: 0, width: "100%", zIndex: 50,
        borderBottom: "1px solid rgba(167,139,250,0.1)",
        backdropFilter: "blur(12px)",
        backgroundColor: "rgba(8,8,16,0.7)",
      }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontWeight: 600, fontSize: 18, letterSpacing: "-0.02em", color: "#a78bfa" }}>lumi</span>
          <SignInButton size="sm" />
        </div>
      </nav>

      {/* Hero */}
      <section style={{ position: "relative", overflow: "hidden", paddingTop: 160, paddingBottom: 120, textAlign: "center" }}>
        <div className="bg-grid" style={{ position: "absolute", inset: 0, opacity: 0.6 }} />
        <div className="glow-orb" style={{ position: "absolute", top: -100, left: "50%", transform: "translateX(-50%)", width: 700, height: 700, borderRadius: "50%", pointerEvents: "none" }} />
        <div style={{ position: "absolute", top: 200, left: "15%", width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", top: 150, right: "10%", width: 250, height: 250, borderRadius: "50%", background: "radial-gradient(circle, rgba(167,139,250,0.1) 0%, transparent 70%)", pointerEvents: "none" }} />

        <div style={{ position: "relative", maxWidth: 720, margin: "0 auto", padding: "0 24px" }}>
          <div className="badge" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 14px", borderRadius: 999, fontSize: 13, marginBottom: 32 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#a78bfa", display: "inline-block" }} />
            Now in early access
          </div>

          <h1 style={{ fontSize: "clamp(48px, 7vw, 80px)", fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1.05, marginBottom: 24 }}>
            Say hey to{" "}
            <span className="gradient-text">Lumi.</span>
          </h1>

          <p style={{ fontSize: 20, color: "#6b6b8a", lineHeight: 1.6, marginBottom: 40, maxWidth: 480, margin: "0 auto 40px" }}>
            Ask anything. Get things done.
          </p>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
            <AuthButtons />
            <a href="#how" style={{
              color: "#6b6b8a", fontWeight: 500, fontSize: 14,
              textDecoration: "none",
            }}>
              See how it works →
            </a>
          </div>
        </div>

        {/* Chat preview */}
        <div style={{ position: "relative", maxWidth: 480, margin: "72px auto 0", padding: "0 24px" }}>
          <div style={{ position: "absolute", inset: -20, background: "radial-gradient(ellipse, rgba(124,58,237,0.2) 0%, transparent 70%)", pointerEvents: "none" }} />
          <div style={{
            position: "relative",
            border: "1px solid rgba(167,139,250,0.15)",
            borderRadius: 20,
            backgroundColor: "rgba(15,15,26,0.9)",
            backdropFilter: "blur(12px)",
            padding: 24,
            display: "flex", flexDirection: "column", gap: 12,
            boxShadow: "0 0 60px rgba(124,58,237,0.15), 0 24px 48px rgba(0,0,0,0.5)",
          }}>
            <div style={{ display: "flex", gap: 6, marginBottom: 4 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: "#ff5f57" }} />
              <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: "#febc2e" }} />
              <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: "#28c840" }} />
            </div>
            <ChatBubble role="user" text="hey what do i have going on this week" />
            <ChatBubble role="lumi" text="dentist wednesday, and you wanted to prep for that friday presentation. help with the slides? 👀" />
            <ChatBubble role="user" text="yes pls" />
            <ChatBubble role="lumi" text="on it — what's the topic and who's the audience?" />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" style={{ padding: "100px 24px", borderTop: "1px solid rgba(167,139,250,0.08)" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto" }}>
          <SectionLabel>How it works</SectionLabel>
          <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 700, letterSpacing: "-0.03em", textAlign: "center", marginBottom: 64 }}>
            Up and running in 2 minutes
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
            {STEPS.map((s) => (
              <div key={s.step} className="card-glow" style={{ borderRadius: 16, padding: 28 }}>
                <div style={{ fontFamily: "monospace", fontSize: 13, color: "#a78bfa", marginBottom: 16 }}>{s.step}</div>
                <h3 style={{ fontWeight: 600, fontSize: 18, marginBottom: 8 }}>{s.title}</h3>
                <p style={{ color: "#6b6b8a", fontSize: 14, lineHeight: 1.6 }}>{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: "100px 24px", borderTop: "1px solid rgba(167,139,250,0.08)" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto" }}>
          <SectionLabel>Features</SectionLabel>
          <h2 style={{ fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 700, letterSpacing: "-0.03em", textAlign: "center", marginBottom: 64 }}>
            Built different
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
            {FEATURES.map((f) => (
              <div key={f.title} className="card-glow" style={{ borderRadius: 16, padding: 28 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10, marginBottom: 20,
                  background: "rgba(167,139,250,0.1)",
                  border: "1px solid rgba(167,139,250,0.15)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 16, color: "#a78bfa",
                }}>
                  {f.icon}
                </div>
                <h3 style={{ fontWeight: 600, fontSize: 17, marginBottom: 8 }}>{f.title}</h3>
                <p style={{ color: "#6b6b8a", fontSize: 14, lineHeight: 1.6 }}>{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section style={{ padding: "100px 24px", borderTop: "1px solid rgba(167,139,250,0.08)", textAlign: "center", position: "relative", overflow: "hidden" }}>
        <div className="glow-orb" style={{ position: "absolute", bottom: -100, left: "50%", transform: "translateX(-50%)", width: 600, height: 600, borderRadius: "50%", opacity: 0.5, pointerEvents: "none" }} />
        <div style={{ position: "relative", maxWidth: 560, margin: "0 auto" }}>
          <h2 style={{ fontSize: "clamp(32px, 5vw, 52px)", fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1.1, marginBottom: 20 }}>
            Ready to meet <span className="gradient-text">Lumi?</span>
          </h2>
          <p style={{ color: "#6b6b8a", fontSize: 17, marginBottom: 40 }}>Get access in under a minute.</p>
          <SignInButton size="lg" />
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid rgba(167,139,250,0.08)", padding: "32px 24px", textAlign: "center", color: "#3a3a5c", fontSize: 13 }}>
        © 2026 Lumi
      </footer>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ textAlign: "center", marginBottom: 16 }}>
      <span className="badge" style={{ display: "inline-block", padding: "4px 12px", borderRadius: 999, fontSize: 12, fontWeight: 500, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>
        {children}
      </span>
    </div>
  );
}

function ChatBubble({ role, text }: { role: "user" | "lumi"; text: string }) {
  const isUser = role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div style={{
        maxWidth: "80%",
        padding: "10px 14px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
        fontSize: 14,
        lineHeight: 1.5,
        background: isUser ? "#a78bfa" : "rgba(255,255,255,0.06)",
        color: isUser ? "#080810" : "#c4c4d4",
        border: isUser ? "none" : "1px solid rgba(255,255,255,0.06)",
      }}>
        {text}
      </div>
    </div>
  );
}
