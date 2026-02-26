import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable Turbopack to use Webpack (better compatibility with react-map-gl)
  // Remove when Turbopack has better support
  experimental: {
    // turbo: false, // Uncomment if needed
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'spot-sf-res.cloudinary.com',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;
