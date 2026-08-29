"use client";

import React from "react";
import { FieldProvider } from "@/components/field/FieldContext";
import FieldNavbar from "@/components/field/FieldNavbar";

export default function FieldLayout({ children }: { children: React.ReactNode }) {
  return (
    <FieldProvider>
      <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md sm:max-w-3xl mx-auto shadow-2xl border-x border-zinc-800 pb-16 sm:pb-4 relative">
        <FieldNavbar />
        <div className="flex-1 flex flex-col">{children}</div>
      </div>
    </FieldProvider>
  );
}
