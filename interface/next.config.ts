const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://13.220.128.77:8000/:path*",
      },
    ];
  },
};
export default nextConfig;