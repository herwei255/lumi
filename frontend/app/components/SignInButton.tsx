"use client";

import { signIn, signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

// ─── Feature flag ────────────────────────────────────────────────────────────
// Set NEXT_PUBLIC_TELEGRAM_AUTH_ENABLED=true in .env.local once you have a
// real domain set in BotFather. Until then, the Telegram button shows as
// "coming soon".
const TELEGRAM_AUTH_ENABLED = process.env.NEXT_PUBLIC_TELEGRAM_AUTH_ENABLED === "true";

const btnBase: React.CSSProperties = {
  width: "100%",
  maxWidth: 320,
  padding: "13px 24px",
  borderRadius: 999,
  fontSize: 15,
  fontWeight: 600,
  border: "none",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 10,
  transition: "opacity 0.2s",
};

export function AuthButtons() {
  const { data: session } = useSession();
  const router = useRouter();

  if (session) {
    return (
      <button
        onClick={() => router.push("/onboarding")}
        style={{ ...btnBase, background: "#a78bfa", color: "#080810" }}
      >
        Go to dashboard →
      </button>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
      {/* Telegram — enabled once domain is configured */}
      <button
        onClick={() => TELEGRAM_AUTH_ENABLED
          ? undefined /* TODO: trigger Telegram Login Widget */
          : null}
        disabled={!TELEGRAM_AUTH_ENABLED}
        title={TELEGRAM_AUTH_ENABLED ? undefined : "Coming soon — available after launch"}
        style={{
          ...btnBase,
          background: TELEGRAM_AUTH_ENABLED ? "#229ED9" : "rgba(34,158,217,0.15)",
          color: TELEGRAM_AUTH_ENABLED ? "#fff" : "#4a8aaa",
          cursor: TELEGRAM_AUTH_ENABLED ? "pointer" : "not-allowed",
          position: "relative",
        }}
      >
        <TelegramIcon />
        Continue with Telegram
        {!TELEGRAM_AUTH_ENABLED && (
          <span style={{
            position: "absolute", right: 16,
            fontSize: 11, fontWeight: 500,
            background: "rgba(34,158,217,0.2)",
            padding: "2px 8px", borderRadius: 999,
            color: "#4a8aaa",
          }}>
            soon
          </span>
        )}
      </button>

      {/* Google */}
      <button
        onClick={() => signIn("google", { callbackUrl: "/onboarding" })}
        style={{
          ...btnBase,
          background: "rgba(255,255,255,0.06)",
          color: "#c4c4d4",
          border: "1px solid rgba(255,255,255,0.1)",
        }}
      >
        <GoogleIcon />
        Continue with Google
      </button>
    </div>
  );
}

// Keep the simple one for nav bar
export function SignInButton({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const { data: session } = useSession();
  const router = useRouter();

  const padding = size === "sm" ? "8px 20px" : size === "lg" ? "16px 40px" : "14px 32px";
  const fontSize = size === "sm" ? 14 : size === "lg" ? 17 : 16;

  if (session) {
    return (
      <button
        onClick={() => router.push("/onboarding")}
        style={{ ...btnBase, width: "auto", background: "#a78bfa", color: "#080810", padding, fontSize }}
      >
        Dashboard →
      </button>
    );
  }

  return (
    <button
      onClick={() => signIn("google", { callbackUrl: "/onboarding" })}
      style={{ ...btnBase, width: "auto", background: "#a78bfa", color: "#080810", padding, fontSize }}
    >
      Get started
    </button>
  );
}

export function SignOutButton() {
  return (
    <button
      onClick={() => signOut({ callbackUrl: "/" })}
      style={{ color: "#6b6b8a", background: "none", border: "none", cursor: "pointer", fontSize: 14 }}
    >
      Sign out
    </button>
  );
}

function TelegramIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L7.19 13.981 4.23 13.07c-.65-.203-.664-.65.136-.961l11.28-4.35c.537-.194 1.009.131.838.952l-.59.51z"/>
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  );
}
