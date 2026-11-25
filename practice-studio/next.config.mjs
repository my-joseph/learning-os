/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "motion",
      "motion/react",
      "@radix-ui/react-alert-dialog",
      "@radix-ui/react-collapsible",
      "@radix-ui/react-dialog",
      "@radix-ui/react-hover-card",
      "@radix-ui/react-popover",
      "@radix-ui/react-slot",
      "@radix-ui/react-tabs",
      "@radix-ui/react-tooltip",
    ],
  },
  webpack: (config, { dev, isServer }) => {
    if (isServer) {
      // Client-only dynamic({ ssr: false }) dependencies (Interactive3DCylinder, MathLiveInput)
      // never execute on the server; skip bundling them into SSR/API server compilations.
      config.resolve.alias = {
        ...config.resolve.alias,
        three: false,
        "@react-three/fiber": false,
        "@react-three/drei": false,
        mathlive: false,
      };
    }
    if (dev && !isServer) {
      // Defer compiling heavy dynamic() client chunks (MathLive, 3D Cylinder, Review & Sync)
      // until the learner actually opens those views.
      config.experiments = {
        ...config.experiments,
        lazyCompilation: {
          entries: false,
          imports: true,
          backend: {
            listen: {
              host: "127.0.0.1",
            },
          },
        },
      };
    }
    return config;
  },
};

export default nextConfig;
