/** @type {import('next').NextConfig} */

// On Vercel, /api/* never reaches Next.js: vercel.json routes it to the
// Python service on the same domain. Anywhere else (`next dev`, `next start`),
// Next.js proxies /api/* to the backend at BACKEND_URL.
const backend = (process.env.BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");

const nextConfig = {
  async rewrites() {
    if (process.env.VERCEL) return [];
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

module.exports = nextConfig;
