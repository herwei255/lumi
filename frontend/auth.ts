import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Credentials({
      id: "telegram",
      name: "Telegram",
      credentials: { telegramData: { type: "text" } },
      async authorize(credentials) {
        if (!credentials?.telegramData) return null;
        const resp = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/telegram-verify`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: credentials.telegramData as string,
          }
        );
        if (!resp.ok) return null;
        return await resp.json(); // { id, name, email, image }
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      if (token.sub) session.user.id = token.sub;
      return session;
    },
  },
  pages: {
    signIn: "/",
  },
});
