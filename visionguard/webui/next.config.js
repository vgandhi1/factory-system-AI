/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_INFERENCE_URL:
      process.env.NEXT_PUBLIC_INFERENCE_URL || "http://localhost:8001",
  },
};
