/** @type {import('next').NextConfig} */
const nextConfig = {
  // Do not statically export — app uses browser-only Supabase auth
  output: "standalone",
};
module.exports = nextConfig;
