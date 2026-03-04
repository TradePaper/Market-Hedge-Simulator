/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: "tmp/nextbuild",
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "no-store, must-revalidate",
          },
        ],
      },
    ];
  },
  webpack: (config) => {
    config.output = {
      ...config.output,
      hashFunction: "sha256",
    };
    config.cache = false;
    return config;
  },
};

module.exports = nextConfig;
