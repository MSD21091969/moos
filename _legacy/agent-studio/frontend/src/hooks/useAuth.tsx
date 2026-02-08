import {
  useState,
  useEffect,
  createContext,
  useContext,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";

interface AuthContextType {
  token: string | null;
  email: string | null;
  userId: string | null;
  login: (token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Helper to decode JWT payload safely
function decodeToken(token: string): { email?: string; sub?: string } | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join(""),
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error("Failed to decode token", error);
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check localStorage on mount
    const storedToken = localStorage.getItem("agent_studio_token");
    if (storedToken) {
      setToken(storedToken);
      const payload = decodeToken(storedToken);
      if (payload?.email) setEmail(payload.email);
      if (payload?.sub) setUserId(payload.sub);
    }
    setIsLoading(false);
  }, []);

  const login = (newToken: string) => {
    localStorage.setItem("agent_studio_token", newToken);
    setToken(newToken);
    const payload = decodeToken(newToken);
    if (payload?.email) setEmail(payload.email);
    if (payload?.sub) setUserId(payload.sub);
    router.push("/");
  };

  const logout = () => {
    // Cache persists as scratchpad - no warning needed
    localStorage.removeItem("agent_studio_token");
    setToken(null);
    setEmail(null);
    setUserId(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        email,
        userId,
        login,
        logout,
        isAuthenticated: !!token,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
