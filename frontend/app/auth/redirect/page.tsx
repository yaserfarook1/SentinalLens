'use client';

import { useEffect, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { useRouter } from 'next/navigation';

export default function AuthRedirectPage() {
  const { instance } = useMsal();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const handleRedirect = async () => {
      try {
        // MSAL will automatically handle the redirect and complete the auth flow
        console.log('[AUTH] Handling redirect callback...');

        // Check if auth was successful by looking for an account
        const accounts = instance.getAllAccounts();
        if (accounts.length > 0) {
          console.log('[AUTH] Successfully authenticated');
          // Redirect to dashboard
          router.push('/dashboard');
        } else {
          console.log('[AUTH] No accounts found after redirect');
          // Could be in process of loading - wait a bit
          setTimeout(() => {
            const retryAccounts = instance.getAllAccounts();
            if (retryAccounts.length > 0) {
              router.push('/dashboard');
            } else {
              setError('Authentication failed. Please try signing in again.');
            }
          }, 1000);
        }
      } catch (err) {
        console.error('[AUTH] Redirect error:', err);
        setError(`Authentication error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };

    handleRedirect();
  }, [instance, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Completing authentication...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <h1 className="text-xl font-bold text-red-800 mb-2">Authentication Error</h1>
            <p className="text-red-700 mb-4">{error}</p>
            <a
              href="/dashboard"
              className="inline-block bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Return to Dashboard
            </a>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
