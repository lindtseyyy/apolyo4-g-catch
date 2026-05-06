'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { LogOut, LogIn, UserPlus, Menu, X, Shield, Zap } from 'lucide-react';
import { useState } from 'react';

export default function Navigation() {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    setIsOpen(false);
  };

  return (
    <nav className="fixed top-0 w-full z-50">
      {/* Glass nav bar */}
      <div className="glass-strong border-b border-[rgba(0,102,255,0.12)]">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#0066ff] to-[#00a8ff] flex items-center justify-center shadow-lg shadow-[#0066ff]/25 group-hover:shadow-[#0066ff]/40 transition-all duration-300">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-[#00d4ff] rounded-full border-2 border-[#0a1020] animate-pulse" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-xl font-extrabold tracking-tight">
                <span className="gradient-text">G-Catch</span>
              </span>
              <span className="text-[10px] text-[#8899b8] font-medium tracking-[0.2em] uppercase">Forensic Scan</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-3">
            {loading ? (
              <div className="w-8 h-8 bg-[#0f1729] rounded-full animate-pulse border border-[rgba(0,102,255,0.15)]" />
            ) : user ? (
              <>
                <span className="text-[#8899b8] text-sm mr-2">
                  <span className="font-medium text-[#c8d4e8]">{user.displayName || user.email?.split('@')[0]}</span>
                </span>
                <Link href="/profile">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 bg-[rgba(0,102,255,0.08)] hover:bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.2)] text-[#0066ff] px-4 py-2 rounded-xl transition-all duration-200 text-sm font-medium"
                  >
                    <UserPlus className="w-4 h-4" />
                    Profile
                  </motion.button>
                </Link>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleLogout}
                  className="flex items-center gap-2 bg-[rgba(255,61,113,0.08)] hover:bg-[rgba(255,61,113,0.15)] border border-[rgba(255,61,113,0.2)] text-[#ff3d71] px-4 py-2 rounded-xl transition-all duration-200 text-sm font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </motion.button>
              </>
            ) : (
              <>
                {pathname !== '/signin' && (
                  <Link href="/signin">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex items-center gap-2 text-[#8899b8] hover:text-[#f0f6ff] px-4 py-2 rounded-xl transition-all duration-200 text-sm font-medium"
                    >
                      <LogIn className="w-4 h-4" />
                      Sign In
                    </motion.button>
                  </Link>
                )}
                {pathname !== '/signup' && (
                  <Link href="/signup">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex items-center gap-2 bg-gradient-to-r from-[#0066ff] to-[#00a8ff] hover:from-[#0052cc] hover:to-[#0090e0] text-white px-5 py-2 rounded-xl transition-all duration-200 text-sm font-semibold shadow-lg shadow-[#0066ff]/20 hover:shadow-[#0066ff]/35"
                    >
                      <Zap className="w-4 h-4" />
                      Get Started
                    </motion.button>
                  </Link>
                )}
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden text-[#c8d4e8] p-2 hover:bg-[rgba(0,102,255,0.08)] rounded-xl transition-all border border-transparent hover:border-[rgba(0,102,255,0.15)]"
          >
            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -10, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden glass-strong border-b border-[rgba(0,102,255,0.12)] overflow-hidden"
          >
            <div className="p-4 space-y-2">
              {loading ? (
                <div className="w-8 h-8 bg-[#0f1729] rounded-full animate-pulse mx-auto border border-[rgba(0,102,255,0.15)]" />
              ) : user ? (
                <>
                  <div className="px-4 py-2 text-[#8899b8] text-sm text-center">
                    Signed in as <span className="font-semibold text-[#c8d4e8]">{user.displayName || user.email?.split('@')[0]}</span>
                  </div>
                  <Link href="/profile" onClick={() => setIsOpen(false)} className="block">
                    <button className="w-full flex items-center justify-center gap-2 bg-[rgba(0,102,255,0.08)] hover:bg-[rgba(0,102,255,0.15)] border border-[rgba(0,102,255,0.2)] text-[#0066ff] px-4 py-2.5 rounded-xl transition text-sm font-medium">
                      <UserPlus className="w-4 h-4" />
                      Profile
                    </button>
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 bg-[rgba(255,61,113,0.08)] hover:bg-[rgba(255,61,113,0.15)] border border-[rgba(255,61,113,0.2)] text-[#ff3d71] px-4 py-2.5 rounded-xl transition justify-center text-sm font-medium"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  {pathname !== '/signin' && (
                    <Link href="/signin" onClick={() => setIsOpen(false)} className="block">
                      <button className="w-full flex items-center gap-2 bg-[rgba(0,102,255,0.05)] hover:bg-[rgba(0,102,255,0.1)] border border-[rgba(0,102,255,0.12)] text-[#c8d4e8] px-4 py-2.5 rounded-xl transition justify-center text-sm font-medium">
                        <LogIn className="w-4 h-4" />
                        Sign In
                      </button>
                    </Link>
                  )}
                  {pathname !== '/signup' && (
                    <Link href="/signup" onClick={() => setIsOpen(false)} className="block">
                      <button className="w-full flex items-center gap-2 bg-gradient-to-r from-[#0066ff] to-[#00a8ff] hover:from-[#0052cc] hover:to-[#0090e0] text-white px-4 py-2.5 rounded-xl transition text-sm font-semibold justify-center shadow-lg shadow-[#0066ff]/20">
                        <Zap className="w-4 h-4" />
                        Get Started
                      </button>
                    </Link>
                  )}
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
