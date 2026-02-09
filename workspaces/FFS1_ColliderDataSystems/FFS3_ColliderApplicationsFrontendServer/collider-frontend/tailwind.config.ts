import type { Config } from "tailwindcss";

export default {
  content: [
    "./apps/portal/src/**/*.{ts,tsx}",
    "./libs/shared-ui/src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        collider: {
          cloud: "#22c55e",
          filesyst: "#3b82f6",
          admin: "#ef4444",
          sidepanel: "#a855f7",
          "agent-seat": "#eab308",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
