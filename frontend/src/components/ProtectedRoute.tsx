/**
 * Protected Route Component (Phase 30 + Phase A-Pro Verification)
 * Role-based route guard for RBAC enforcement
 * Verification status check for hospital users
 */
import React from "react";
import { Navigate } from "react-router-dom";

interface ProtectedRouteProps {
  role?: "ADMIN" | "HOSPITAL";
  children: React.ReactNode;
}

const VERIFICATION_RESTRICTED_ROUTES = [
  "/dashboard",
  "/training",
  "/datasets",
  "/aggregation",
  "/governance",
  "/monitoring",
  "/prediction",
  "/global-model",
];

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ role, children }) => {
  const token = localStorage.getItem("access_token");

  const isTokenExpired = (rawToken: string) => {
    try {
      const payload = JSON.parse(atob(rawToken.split(".")[1]));
      if (!payload.exp) {
        return false;
      }
      return Date.now() >= payload.exp * 1000;
    } catch (error) {
      return true;
    }
  };

  // Check if user is authenticated
  if (!token) {
    // Check if this is an admin route - redirect to admin login
    if (role === "ADMIN") {
      return <Navigate to="/admin-login" replace />;
    }
    return <Navigate to="/login" replace />;
  }

  if (isTokenExpired(token)) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("verification_status");
    if (role === "ADMIN") {
      return <Navigate to="/admin-login" replace />;
    }
    return <Navigate to="/login" replace />;
  }

  // If specific role is required, verify user has that role
  if (role) {
    try {
      // Decode JWT to extract role (simple base64 decode of payload)
      const payload = JSON.parse(atob(token.split(".")[1]));
      const userRole = payload.role === "ADMIN" ? "ADMIN" : "HOSPITAL";
      const verificationStatus = payload.verification_status || "VERIFIED";

      if (userRole !== role) {
        // Redirect to appropriate page based on actual role
        if (userRole === "ADMIN") {
          return <Navigate to="/admin-dashboard" replace />;
        }
        return <Navigate to="/dashboard" replace />;
      }

      // Additional check for HOSPITAL users: enforce verification for restricted routes
      if (
        userRole === "HOSPITAL" &&
        verificationStatus !== "VERIFIED" &&
        VERIFICATION_RESTRICTED_ROUTES.some(route => window.location.pathname.includes(route))
      ) {
        return <Navigate to="/verification-status" replace />;
      }
    } catch (error) {
      console.error("Error decoding token:", error);
      return <Navigate to="/login" replace />;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
