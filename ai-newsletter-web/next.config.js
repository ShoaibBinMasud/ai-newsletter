/** @type {import('next').NextConfig} */
const nextConfig = {
  // better-sqlite3 is a native module — tell webpack not to bundle it
  webpack: (config) => {
    config.externals = [...(config.externals || []), "better-sqlite3"];
    return config;
  },
};

module.exports = nextConfig;
