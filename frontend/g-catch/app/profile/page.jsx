'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { motion } from 'framer-motion';
import { User, Mail, LogOut, Shield, Fingerprint, Key, Copy, Check } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function Profile() {
  const { user, logout, loading } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await logout();
  };

  const copyUid = () => {
    if (user?.uid) {
      navigator.clipboard.writeText(user.uid);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center pt-24">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-[#0066ff] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#8899b8]">Loading profile...</p>
        </div>
      </main>
    );
  }

  return (
    <ProtectedRoute>
      <ProfileContent user={user} isLoggingOut={isLoggingOut} handleLogout={handleLogout} copyUid={copyUid} copied={copied} />
    </ProtectedRoute>
  );
}

function ProfileContent({ user, isLoggingOut, handleLogout, copyUid, copied }) {
  return (
    <main className="min-h-screen pt-24 pb-12 px-4">
      {/* Background Glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#0066ff]/10 rounded-full blur-3xl opacity-30 animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#00d4ff]/8 rounded-full blur-3xl opacity-30 animate-pulse-glow" style={{ animationDelay: '1.5s' }} />
      </div>

      <div className="max-w-2xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass rounded-3xl p-8 md:p-10 glow-blue relative overflow-hidden"
        >
          {/* Corner accents */}
          <div className="absolute top-0 left-0 w-12 h-12 border-l-2 border-t-2 border-[rgba(0,102,255,0.2)] rounded-tl-3xl" />
          <div className="absolute top-0 right-0 w-12 h-12 border-r-2 border-t-2 border-[rgba(0,102,255,0.2)] rounded-tr-3xl" />
          <div className="absolute bottom-0 left-0 w-12 h-12 border-l-2 border-b-2 border-[rgba(0,102,255,0.2)] rounded-bl-3xl" />
          <div className="absolute bottom-0 right-0 w-12 h-12 border-r-2 border-b-2 border-[rgba(0,102,255,0.2)] rounded-br-3xl" />

          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <div className="relative">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0066ff] to-[#00a8ff] flex items-center justify-center shadow-lg shadow-[#0066ff]/25">
                {user.photoURL ? (
                  <img src={user.photoURL} alt="Profile" className="w-16 h-16 rounded-2xl object-cover" />
                ) : (
                  <User className="w-8 h-8 text-white" />
                )}
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-[#00c853] rounded-full border-2 border-[#0a1020] flex items-center justify-center">
                <div className="w-2 h-2 bg-white rounded-full" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[#f0f6ff]">
                {user.displayName || 'User'}
              </h1>
              <p className="text-[#8899b8] text-sm">Account Profile</p>
            </div>
          </div>

          {/* Profile Details */}
          <div className="space-y-4 mb-8">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="flex items-start gap-4 p-4 bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] hover:border-[rgba(0,102,255,0.2)] rounded-xl transition-colors"
            >
              <div className="w-9 h-9 rounded-lg bg-[rgba(0,102,255,0.08)] flex items-center justify-center flex-shrink-0">
                <Mail className="w-4 h-4 text-[#0066ff]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#8899b8] uppercase tracking-wider mb-0.5">Email Address</p>
                <p className="text-[#f0f6ff] font-medium truncate">{user.email}</p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="flex items-start gap-4 p-4 bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] hover:border-[rgba(0,102,255,0.2)] rounded-xl transition-colors"
            >
              <div className="w-9 h-9 rounded-lg bg-[rgba(0,200,83,0.08)] flex items-center justify-center flex-shrink-0">
                <Shield className="w-4 h-4 text-[#00c853]" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-[#8899b8] uppercase tracking-wider mb-0.5">Account Status</p>
                <p className="text-[#f0f6ff] font-medium">
                  {user.emailVerified ? (
                    <span className="text-[#00c853]">✓ Email Verified</span>
                  ) : (
                    <span className="text-[#ffb800]">⚠ Email Not Verified</span>
                  )}
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="flex items-start gap-4 p-4 bg-[rgba(0,102,255,0.04)] border border-[rgba(0,102,255,0.1)] hover:border-[rgba(0,102,255,0.2)] rounded-xl transition-colors"
            >
              <div className="w-9 h-9 rounded-lg bg-[rgba(147,51,234,0.08)] flex items-center justify-center flex-shrink-0">
                <Key className="w-4 h-4 text-purple-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#8899b8] uppercase tracking-wider mb-0.5">User ID</p>
                <div className="flex items-center gap-2">
                  <p className="text-[#f0f6ff] font-mono text-xs break-all">{user.uid}</p>
                  <button
                    onClick={copyUid}
                    className="flex-shrink-0 p-1.5 rounded-lg bg-[rgba(0,102,255,0.08)] hover:bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.1)] hover:border-[rgba(0,102,255,0.2)] transition-all"
                    title="Copy User ID"
                  >
                    {copied ? <Check className="w-3 h-3 text-[#00c853]" /> : <Copy className="w-3 h-3 text-[#8899b8]" />}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Divider */}
          <div className="h-px bg-[rgba(0,102,255,0.1)] mb-8" />

          {/* Sign Out Button */}
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="w-full flex items-center justify-center gap-2 bg-[rgba(255,61,113,0.06)] hover:bg-[rgba(255,61,113,0.1)] border border-[rgba(255,61,113,0.15)] hover:border-[rgba(255,61,113,0.3)] text-[#ff3d71] font-semibold py-3 px-4 rounded-xl transition-all duration-200 disabled:opacity-50 cursor-pointer"
          >
            {isLoggingOut ? (
              <>
                <div className="w-5 h-5 border-2 border-[#ff3d71] border-t-transparent rounded-full animate-spin" />
                Signing out...
              </>
            ) : (
              <>
                <LogOut className="w-5 h-5" />
                Sign Out
              </>
            )}
          </motion.button>

          {/* Additional Info */}
          <div className="mt-6 p-4 bg-[rgba(0,102,255,0.03)] border border-[rgba(0,102,255,0.08)] rounded-xl">
            <div className="flex items-start gap-3">
              <Fingerprint className="w-4 h-4 text-[#0066ff] mt-0.5 flex-shrink-0" />
              <p className="text-xs text-[#8899b8] leading-relaxed">
                Your account is secured with Firebase Authentication. All verification scans are processed locally and no receipt data is stored on our servers.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
