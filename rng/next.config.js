const webpack = require("webpack");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // suppress hard-fail on lint warnings during prod build
  eslint: { ignoreDuringBuilds: true },
  // (we still get build-time type-checks; this just lets eslint warnings pass)

  // wallet-adapter packages ship ESM that needs transpiling
  transpilePackages: [
    "@solana/wallet-adapter-base",
    "@solana/wallet-adapter-react",
    "@solana/wallet-adapter-react-ui",
    "@solana/wallet-adapter-wallets",
  ],

  webpack: (config, { isServer }) => {
    // node-only modules referenced by transitive deps; stub on the client
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };

    // pino (transitive from walletconnect) optionally pulls pino-pretty.
    // We don't use pretty logging — IgnorePlugin makes the import resolve to
    // an empty module so it doesn't fail or warn.
    config.plugins = config.plugins || [];
    config.plugins.push(
      new webpack.IgnorePlugin({ resourceRegExp: /^pino-pretty$/ }),
    );

    return config;
  },
};

module.exports = nextConfig;
