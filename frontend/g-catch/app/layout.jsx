import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import Navigation from "@/components/Navigation";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "G-Catch | Forensic Receipt Verification",
  description: "AI-powered forensic pixel analysis for digital receipt verification. Protect your business from fraud with deep-scan technology.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "G-Catch",
    startupImage: [],
  },
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport = {
  themeColor: "#0066ff",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#030712] text-[#f0f6ff] relative overflow-x-hidden">
        {/* Animated background orbs */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
          <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-[#0066ff]/10 rounded-full blur-[120px] animate-float" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-[#00d4ff]/8 rounded-full blur-[100px] animate-float" style={{ animationDelay: '-3s' }} />
          <div className="absolute top-[40%] left-[60%] w-[300px] h-[300px] bg-[#0052cc]/10 rounded-full blur-[80px] animate-pulse-glow" />
          {/* Subtle grid overlay */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: `linear-gradient(rgba(0, 102, 255, 0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 102, 255, 0.5) 1px, transparent 1px)`,
              backgroundSize: '60px 60px'
            }}
          />
        </div>

        <AuthProvider>
          <div className="relative z-10 flex flex-col min-h-full">
            <Navigation />
            {children}
          </div>
        </AuthProvider>

        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', () => {
                  navigator.serviceWorker.register('/sw.js').then(
                    () => console.log('SW registered'),
                    (err) => console.log('SW registration failed:', err)
                  );
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
