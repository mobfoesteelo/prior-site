/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // wallet-adapter ships ESM that needs transpiling
  transpilePackages: [
    "@solana/wallet-adapter-base",
    "@solana/wallet-adapter-react",
    "@solana/wallet-adapter-react-ui",
    "@solana/wallet-adapter-wallets",
  ],
  webpack: (config) => {
    // some wallet-adapter packages reference node-only fs; stub it on the client
    config.resolve.fallback = { ...config.resolve.fallback, fs: false };
    // pino (transitive from walletconnect) optionally requires pino-pretty;
    // suppress the missing-module warning since we don't use pretty logging.
    config.externals = [
      ...(config.externals || []),
      { 'pino-pretty': 'commonjs pino-pretty' },
    ];
    return config;
  },
};

module.exports = nextConfig;
