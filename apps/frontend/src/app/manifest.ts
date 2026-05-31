import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Źródło – System Parafialny",
    short_name: "Źródło",
    description: "Cyfrowa kancelaria parafialna z asystentem AI dla duszpasterzy",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#ffffff",
    theme_color: "#2563eb",
    lang: "pl",
    categories: ["productivity", "utilities"],
    icons: [
      {
        src: "/icons/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
      },
      {
        src: "/icons/icon-maskable.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "Intencje mszalne",
        short_name: "Intencje",
        url: "/dashboard/intencje",
        description: "Zarządzaj intencjami mszalnymi",
      },
      {
        name: "Dziennik kancleryjny",
        short_name: "Dziennik",
        url: "/dashboard/dziennik",
        description: "Rejestr korespondencji parafii",
      },
      {
        name: "Asystent AI",
        short_name: "Asystent",
        url: "/dashboard/asystent",
        description: "Asystent AI dla duszpasterzy",
      },
    ],
  };
}
