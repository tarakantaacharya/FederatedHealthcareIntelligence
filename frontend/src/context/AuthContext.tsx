/**
 * Authentication Context (Phase 30 + Phase A-Pro)
 * Manages user authentication state, role information, and verification status
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

interface User {
  token: string;
  role: "ADMIN" | "HOSPITAL";
  hospital_id?: string;
  hospital_name?: string;
  admin_name?: string;
  verification_status?: "PENDING" | "VERIFIED" | "REJECTED";
}

interface AuthContextType {
  user: User | null;
  login: (token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
  verificationStatus: "PENDING" | "VERIFIED" | "REJECTED" | null;
  isVerified: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);

  const parseToken = useCallback((token: string) => {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload as {
      exp?: number;
      sub?: string;
      role?: string;
      hospital_name?: string;
      admin_name?: string;
      verification_status?: "PENDING" | "VERIFIED" | "REJECTED";
    };
  }, []);

  const isTokenExpired = useCallback((token: string) => {
    try {
      const payload = parseToken(token);
      if (!payload.exp) {
        return false;
      }
      return Date.now() >= payload.exp * 1000;
    } catch (error) {
      return true;
    }
  }, [parseToken]);

  useEffect(() => {
    // Load user from localStorage on mount
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        if (isTokenExpired(token)) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("verification_status");
          setUser(null);
          return;
        }
        // Decode JWT payload
        const payload = parseToken(token);
        const resolvedRole = payload.role === "ADMIN" ? "ADMIN" : "HOSPITAL";
        const verificationStatus = payload.verification_status || "VERIFIED";

        setUser({
          token,
          role: resolvedRole,
          hospital_id: payload.sub,
          hospital_name: payload.hospital_name,
          admin_name: payload.admin_name,
          verification_status: verificationStatus,
        });

        // Store verification status for route guards
        if (resolvedRole === "HOSPITAL") {
          localStorage.setItem("verification_status", verificationStatus);
        }
      } catch (error) {
        console.error("Error loading user from token:", error);
        localStorage.removeItem("access_token");
        localStorage.removeItem("verification_status");
      }
    }
  }, [isTokenExpired, parseToken]);

  useEffect(() => {
    if (!user?.token) {
      return;
    }

    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    try {
      const payload = parseToken(user.token);
      if (payload.exp) {
        const expiresAtMs = payload.exp * 1000;
        const delayMs = Math.max(expiresAtMs - Date.now(), 0);
        timeoutId = setTimeout(() => {
          setUser(null);
          localStorage.removeItem("access_token");
          localStorage.removeItem("verification_status");
        }, delayMs);
      }
    } catch (error) {
      console.error("Error scheduling token expiry:", error);
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [parseToken, user?.token]);

  const login = (token: string) => {
    try {
      if (isTokenExpired(token)) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("verification_status");
        setUser(null);
        return;
      }
      const payload = parseToken(token);
      const resolvedRole = payload.role === "ADMIN" ? "ADMIN" : "HOSPITAL";
      const verificationStatus = payload.verification_status || "VERIFIED";

      const userData: User = {
        token,
        role: resolvedRole,
        hospital_id: payload.sub,
        hospital_name: payload.hospital_name,
        admin_name: payload.admin_name,
        verification_status: verificationStatus,
      };
      setUser(userData);
      localStorage.setItem("access_token", token);

      // Store verification status for route guards
      if (resolvedRole === "HOSPITAL") {
        localStorage.setItem("verification_status", verificationStatus);
      }
    } catch (error) {
      console.error("Error parsing token:", error);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("verification_status");
  };

  const verificationStatus = user?.verification_status || null;
  const isVerified = verificationStatus === "VERIFIED";

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
        verificationStatus,
        isVerified,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
