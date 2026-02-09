import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        collider: {
          cloud: "#22c55e",
          filesyst: "#3b82f6",
          admin: "#ef4444",
          dom: "#a855f7",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
