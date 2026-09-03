"use client";

import React from "react";
import dynamic from "next/dynamic";
import { LocationMapItem } from "@/components/dashboard/types";
import { Loader2 } from "lucide-react";

const DynamicRiskMapInner = dynamic(
  () => import("@/components/dashboard/RiskMapInner"),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[460px] lg:h-[540px] rounded bg-black border border-zinc-800 flex flex-col items-center justify-center text-zinc-400 gap-2 font-mono">
        <Loader2 className="w-6 h-6 animate-spin text-white" />
        <span className="text-xs">Initializing GIS Tactical Risk Map...</span>
      </div>
    ),
  }
);

interface RiskMapProps {
  locations: LocationMapItem[];
  selectedLocationId: string | null;
  onSelectLocation: (locationId: string) => void;
  onOpenInvestigate: (locationId: string) => void;
}

export default function RiskMap(props: RiskMapProps) {
  return <DynamicRiskMapInner {...props} />;
}
