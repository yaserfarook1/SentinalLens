"use client";

import React from "react";
import Link from "next/link";
import { useMsal } from "@azure/msal-react";
import { Button } from "@/components/ui/button";
import { loginRequest } from "@/lib/auth";

export function NavigationBar() {
  const { accounts, instance } = useMsal();
  const [isLoading, setIsLoading] = React.useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      await instance.loginPopup(loginRequest);
    } catch (error) {
      console.error("Login failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    instance.logoutPopup();
  };

  const userName = accounts?.[0]?.name || null;

  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">SL</span>
            </div>
            <span className="font-bold text-lg text-gray-900">SentinelLens</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex gap-8">
            <Link
              href="/dashboard"
              className="text-gray-700 hover:text-gray-900 font-medium"
            >
              Dashboard
            </Link>
            <Link
              href="/audit/new"
              className="text-gray-700 hover:text-gray-900 font-medium"
            >
              New Audit
            </Link>
            <Link
              href="/history"
              className="text-gray-700 hover:text-gray-900 font-medium"
            >
              History
            </Link>
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-4">
            {accounts && accounts.length > 0 ? (
              <>
                <span className="text-sm text-gray-600">
                  {userName}
                </span>
                <Link href="/setup">
                  <Button variant="ghost" size="sm" className="text-xs">
                    ⚙️ Setup
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                >
                  Sign out
                </Button>
              </>
            ) : (
              <Button
                size="sm"
                onClick={handleLogin}
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
