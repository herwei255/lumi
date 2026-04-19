"use client";

import { useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { SignOutButton } from "../components/SignInButton";

export default function Onboarding() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <OnboardingInner />
    </Suspense>
  );
}

function OnboardingInner() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [telegramLinked, setTelegramLinked] = useState(false);
  const [linkCode, setLinkCode] = useState<string | null>(null);
  const [calendarConnected, setCalendarConnected] = useState(
    searchParams.get("calendar") === "connected"
  );
  const [gmailConnected, setGmailConnected] = useState(
    searchParams.get("gmail") === "connected"
  );

  // Redirect to home if not signed in
  useEffect(() => {
    if (status === "unauthenticated") router.push("/");
  }, [status, router]);

  // Check existing connection status on load
  useEffect(() => {
    if (status !== "authenticated" || !session?.user?.id) return;
    const id = session.user.id;

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/telegram-status?google_id=${id}`)
      .then((r) => r.json())
      .then((d) => { if (d.linked) setTelegramLinked(true); })
      .catch(() => {});

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google-calendar/status?google_id=${id}`)
      .then((r) => r.json())
      .then((d) => { if (d.connected) setCalendarConnected(true); })
      .catch(() => {});

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/gmail/status?google_id=${id}`)
      .then((r) => r.json())
      .then((d) => { if (d.connected) setGmailConnected(true); })
      .catch(() => {});
  }, [status, session?.user?.id]);

  const handleLinkTelegram = async () => {
    // Generate a link code from the backend
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/telegram-link`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ google_id: session?.user?.id }),
    });
    const data = await res.json();
    setLinkCode(data.code);

    // Open Telegram deep link in new tab
    window.open(`https://t.me/lumi_butlerbot?start=link_${data.code}`, "_blank");

    // Poll for confirmation (simple approach)
    const interval = setInterval(async () => {
      const check = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/telegram-link/${data.code}`);
      const result = await check.json();
      if (result.linked) {
        setTelegramLinked(true);
        clearInterval(interval);
      }
    }, 2000);

    // Stop polling after 2 minutes
    setTimeout(() => clearInterval(interval), 120000);
  };

  if (status === "loading") return <LoadingScreen />;

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#080810", color: "#f0f0f8", fontFamily: "var(--font-geist-sans)" }}>
      {/* Nav */}
      <nav style={{
        borderBottom: "1px solid rgba(167,139,250,0.1)",
        padding: "0 24px", height: 56,
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <span style={{ fontWeight: 600, fontSize: 18, color: "#a78bfa" }}>lumi</span>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {session?.user?.image && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={session.user.image} alt="avatar" style={{ width: 28, height: 28, borderRadius: "50%" }} />
          )}
          <span style={{ fontSize: 14, color: "#6b6b8a" }}>{session?.user?.email}</span>
          <SignOutButton />
        </div>
      </nav>

      {/* Content */}
      <div style={{ maxWidth: 560, margin: "80px auto", padding: "0 24px" }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, letterSpacing: "-0.03em", marginBottom: 8 }}>
          Set up Lumi
        </h1>
        <p style={{ color: "#6b6b8a", fontSize: 16, marginBottom: 48 }}>
          Connect your accounts and you&apos;re good to go.
        </p>

        {/* Step 1 — Telegram */}
        <Step
          number={1}
          title="Link your Telegram"
          description="Connect your Telegram account so Lumi knows who you are when you text it."
          done={telegramLinked}
        >
          {!telegramLinked ? (
            <button
              onClick={handleLinkTelegram}
              style={{
                background: "#a78bfa", color: "#080810", fontWeight: 600,
                padding: "12px 24px", borderRadius: 999, fontSize: 15,
                border: "none", cursor: "pointer", marginTop: 20,
              }}
            >
              Open Telegram →
            </button>
          ) : (
            <p style={{ color: "#a78bfa", fontSize: 14, marginTop: 16 }}>✓ Telegram linked</p>
          )}
          {linkCode && !telegramLinked && (
            <p style={{ color: "#6b6b8a", fontSize: 13, marginTop: 12 }}>
              Waiting for you to send <code style={{ color: "#a78bfa", background: "rgba(167,139,250,0.1)", padding: "2px 6px", borderRadius: 4 }}>/start</code> in Telegram...
            </p>
          )}
        </Step>

        {/* Step 2 — Calendar (locked until Telegram linked) */}
        <Step
          number={2}
          title="Connect Google Calendar"
          description="Let Lumi see your calendar so it can help you stay on top of your schedule."
          done={calendarConnected}
          locked={!telegramLinked}
        >
          {!calendarConnected ? (
            <button
              disabled={!telegramLinked}
              onClick={() => {
                window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/google-calendar?google_id=${session?.user?.id}`;
              }}
              style={{
                background: telegramLinked ? "#a78bfa" : "rgba(167,139,250,0.2)",
                color: telegramLinked ? "#080810" : "#6b6b8a",
                fontWeight: 600,
                padding: "12px 24px", borderRadius: 999, fontSize: 15,
                border: "none", cursor: telegramLinked ? "pointer" : "not-allowed",
                marginTop: 20,
              }}
            >
              Connect Calendar →
            </button>
          ) : (
            <p style={{ color: "#a78bfa", fontSize: 14, marginTop: 16 }}>✓ Google Calendar connected</p>
          )}
        </Step>

        {/* Step 3 — Gmail (locked until Telegram linked) */}
        <Step
          number={3}
          title="Connect Gmail"
          description="Let Lumi read your emails so it can summarize, search, and keep you in the loop."
          done={gmailConnected}
          locked={!telegramLinked}
        >
          {!gmailConnected ? (
            <button
              disabled={!telegramLinked}
              onClick={() => {
                window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/gmail?google_id=${session?.user?.id}`;
              }}
              style={{
                background: telegramLinked ? "#a78bfa" : "rgba(167,139,250,0.2)",
                color: telegramLinked ? "#080810" : "#6b6b8a",
                fontWeight: 600,
                padding: "12px 24px", borderRadius: 999, fontSize: 15,
                border: "none", cursor: telegramLinked ? "pointer" : "not-allowed",
                marginTop: 20,
              }}
            >
              Connect Gmail →
            </button>
          ) : (
            <p style={{ color: "#a78bfa", fontSize: 14, marginTop: 16 }}>✓ Gmail connected</p>
          )}
        </Step>
      </div>
    </div>
  );
}  // end OnboardingInner

function Step({
  number, title, description, done, locked, children,
}: {
  number: number;
  title: string;
  description: string;
  done: boolean;
  locked?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div style={{
      borderRadius: 16, padding: 28, marginBottom: 16,
      background: locked ? "rgba(167,139,250,0.02)" : "rgba(167,139,250,0.05)",
      border: `1px solid ${done ? "rgba(167,139,250,0.4)" : locked ? "rgba(167,139,250,0.06)" : "rgba(167,139,250,0.12)"}`,
      opacity: locked ? 0.5 : 1,
      transition: "all 0.2s",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          background: done ? "#a78bfa" : "rgba(167,139,250,0.1)",
          border: `1px solid ${done ? "#a78bfa" : "rgba(167,139,250,0.2)"}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, fontWeight: 700,
          color: done ? "#080810" : "#a78bfa",
          flexShrink: 0,
        }}>
          {done ? "✓" : number}
        </div>
        <h3 style={{ fontWeight: 600, fontSize: 17 }}>{title}</h3>
      </div>
      <p style={{ color: "#6b6b8a", fontSize: 14, lineHeight: 1.6, marginLeft: 40 }}>{description}</p>
      <div style={{ marginLeft: 40 }}>{children}</div>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#080810", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ color: "#6b6b8a", fontSize: 14 }}>Loading...</div>
    </div>
  );
}
