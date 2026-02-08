/**
 * Global Configuration for the Agent Studio Frontend
 */

// Detect the current host to handle network IP access automatically
const getBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // If we're on localhost, force IPv4 (127.0.0.1) to avoid IPv6 resolution issues
    // because backend listens on 0.0.0.0 (IPv4)
    if (hostname === "localhost") {
      return "http://127.0.0.1:8000";
    }
    return `http://${hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
};

const getWsUrl = () => {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === "localhost") {
      return "ws://127.0.0.1:8000";
    }
    return `ws://${hostname}:8000`;
  }
  return "ws://127.0.0.1:8000";
};

export const API_BASE = getBaseUrl();
export const WS_BASE = getWsUrl();
