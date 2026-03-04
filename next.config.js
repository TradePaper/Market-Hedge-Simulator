/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: "tmp/nextbuild",
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
