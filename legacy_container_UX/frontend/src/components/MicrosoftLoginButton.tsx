import { useState, useEffect } from 'react';
import { login, logout, getCurrentUser, initializeMsal } from '../lib/microsoft-auth';

export function MicrosoftLoginButton() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    initializeMsal().then(() => {
      setUser(getCurrentUser());
      setLoading(false);
    });
  }, []);

  const handleLogin = async () => {
    setLoading(true);
    try {
      const account = await login();
      setUser(account);
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    setUser(null);
  };

  if (loading) return <div className="text-sm text-gray-400">Loading...</div>;

  return (
    <div className="flex items-center gap-2">
      {user ? (
        <>
          <div className="flex items-center gap-2">
            <img
              src={`https://ui-avatars.com/api/?name=${user.name}&background=0D8ABC&color=fff`}
              alt={user.name}
              className="w-8 h-8 rounded-full border border-gray-600"
            />
            <span className="text-sm hidden sm:inline">{user.name}</span>
          </div>
          <button
            onClick={handleLogout}
            className="px-3 py-1 text-xs bg-red-500/20 text-red-300 border border-red-500/50 rounded hover:bg-red-500/30 transition-colors"
          >
            Logout
          </button>
        </>
      ) : (
        <button
          onClick={handleLogin}
          className="px-4 py-2 bg-[#0078D4] text-white rounded hover:bg-[#006cbd] flex items-center gap-2 transition-colors font-medium text-sm"
        >
          <svg className="w-4 h-4" viewBox="0 0 23 23">
            <path fill="#f3f3f3" d="M0 0h23v23H0z"/>
            <path fill="#f35325" d="M1 1h10v10H1z"/>
            <path fill="#81bc06" d="M12 1h10v10H12z"/>
            <path fill="#05a6f0" d="M1 12h10v10H1z"/>
            <path fill="#ffba08" d="M12 12h10v10H12z"/>
          </svg>
          Sign in with Microsoft
        </button>
      )}
    </div>
  );
}
