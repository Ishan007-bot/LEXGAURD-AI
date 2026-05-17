/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== 'production';

// Google domains Firebase Auth loads / frames / talks to.
const GOOGLE_SCRIPT = 'https://apis.google.com https://*.gstatic.com';
const GOOGLE_FRAME = 'https://*.firebaseapp.com https://accounts.google.com';
const GOOGLE_API =
  'https://*.googleapis.com https://*.firebaseio.com https://*.firebaseapp.com https://identitytoolkit.googleapis.com https://securetoken.googleapis.com';

const cspParts = [
  "default-src 'self'",
  // 'unsafe-eval' is required by Next.js's dev React Refresh runtime.
  isDev
    ? `script-src 'self' 'unsafe-inline' 'unsafe-eval' ${GOOGLE_SCRIPT}`
    : `script-src 'self' 'unsafe-inline' ${GOOGLE_SCRIPT}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  // Firebase Auth popup runs as an iframe at your-project.firebaseapp.com,
  // which in turn frames accounts.google.com.
  `frame-src 'self' ${GOOGLE_FRAME}`,
  `child-src 'self' ${GOOGLE_FRAME}`,
  isDev
    ? `connect-src 'self' ws: wss: http://localhost:* ${GOOGLE_API}`
    : `connect-src 'self' ${GOOGLE_API}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
];

const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'geolocation=(), microphone=(), camera=()' },
  { key: 'Content-Security-Policy', value: cspParts.join('; ') },
];

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: 'standalone',
  experimental: { instrumentationHook: false },
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }];
  },
};

export default nextConfig;
