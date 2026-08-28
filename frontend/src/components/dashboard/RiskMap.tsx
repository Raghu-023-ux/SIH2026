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
      <div className="w-full h-[460px] lg:h-[540px] rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center text-slate-400 gap-2">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
        <span className="text-xs font-mono">Initializing GIS Tactical Risk Map...</span>
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
