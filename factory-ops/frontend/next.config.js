/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  // Allow `docker compose` to pass the API URL at build/run time.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};
