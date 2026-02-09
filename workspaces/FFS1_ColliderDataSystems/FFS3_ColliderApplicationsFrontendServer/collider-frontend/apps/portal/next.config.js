/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    "@collider/api-client",
    "@collider/node-container",
    "@collider/shared-ui",
  ],
};

module.exports = nextConfig;
