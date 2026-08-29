"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Radio,
  FileText,
  LifeBuoy,
  Bell,
  UserCheck,
  Activity,
  MapPin,
  ExternalLink,
  Shield,
  LocateFixed,
} from "lucide-react";
import { useField } from "./FieldContext";

export default function FieldNavbar() {
  const pathname = usePathname();
  const {
    callsign,
    setCallsign,
    data,
    geoStatus,
    coords,
    updateTeamStatus,
    requestGPSLocation,
  } = useField();

  const unackCount = data?.recent_messages?.filter((m) => !m.acknowledged_at).length || 0;

  const navItems = [
    {
      href: "/field",
      label: "Overview",
      icon: Activity,
      exact: true,
    },
    {
      href: "/field/reports",
      label: "Reports",
      icon: FileText,
      badge: data?.recent_reports?.length || null,
    },
    {
      href: "/field/assistance",
      label: "Assistance",
      icon: LifeBuoy,
      alert: data?.team?.status === "NEED_ASSISTANCE",
    },
    {
      href: "/field/messages",
      label: "Directives",
      icon: Bell,
      badge: unackCount > 0 ? unackCount : null,
      badgeAlert: unackCount > 0,
    },
    {
      href: "/field/profile",
      label: "Profile",
      icon: UserCheck,
    },
  ];

  const isActive = (item: typeof navItems[0]) => {
    if (item.exact) {
      return pathname === item.href;
    }
    return pathname.startsWith(item.href);
  };

  return (
    <>
      {/* 1. TOP STICKY TACTICAL HEADER */}
      <header className="bg-slate-900 border-b border-slate-800 px-3.5 py-2.5 sticky top-0 z-40 shadow-lg select-none">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-red-600/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
              <Radio className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-[10px] font-mono tracking-wider uppercase text-red-400 font-bold flex items-center gap-1.5 truncate">
                <span>FIELD RESCUE OP</span>
                <span>•</span>
                <span className="text-slate-400 truncate">{callsign}</span>
              </div>
              <div className="flex items-center gap-1 text-slate-300 text-xs font-bold truncate">
                <span>{data?.team?.team_name || "Assigned Unit"}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => requestGPSLocation()}
              title="Refresh GPS Coordinates"
              className="flex items-center gap-1 text-[10px] font-mono text-indigo-300 bg-slate-950 hover:bg-slate-800 border border-slate-800 px-2 py-1 rounded transition"
            >
              <LocateFixed className="w-3 h-3 text-indigo-400" />
              <span className="hidden sm:inline">GPS</span>
              {coords?.accuracy ? `±${coords.accuracy}m` : "Fix"}
            </button>

            <Link
              href="/"
              className="text-[10px] font-mono text-slate-400 hover:text-slate-200 px-2 py-1 bg-slate-950 hover:bg-slate-800 rounded border border-slate-800 transition flex items-center gap-1"
            >
              <span className="hidden sm:inline">HQ Command</span>
              <span className="sm:hidden">HQ</span>
              <ExternalLink className="w-2.5 h-2.5 text-slate-500" />
            </Link>
          </div>
        </div>

        {/* Status Mode Switcher Bar */}
        <div className="mt-2.5 grid grid-cols-4 gap-1 text-[10px] sm:text-[11px] font-mono">
          {(["AVAILABLE", "DEPLOYED", "ON_SCENE", "NEED_ASSISTANCE"] as const).map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => updateTeamStatus(st)}
              className={`py-1.5 rounded font-bold uppercase transition text-center truncate px-1 ${
                data?.team?.status === st
                  ? st === "NEED_ASSISTANCE"
                    ? "bg-red-600 text-white shadow-md shadow-red-950 ring-1 ring-red-400"
                    : st === "ON_SCENE"
                    ? "bg-amber-600 text-white shadow-md shadow-amber-950 ring-1 ring-amber-400"
                    : "bg-indigo-600 text-white shadow-md shadow-indigo-950 ring-1 ring-indigo-400"
                  : "bg-slate-950/90 text-slate-400 hover:text-slate-200 border border-slate-800/80"
              }`}
            >
              {st === "NEED_ASSISTANCE" ? "SOS / NEED HELP" : st.replace("_", " ")}
            </button>
          ))}
        </div>

        {/* Desktop / Tablet Sub-Navbar Tabs */}
        <nav className="mt-2.5 hidden sm:flex items-center gap-1 border-t border-slate-800/70 pt-2 text-xs font-mono">
          {navItems.map((item) => {
            const active = isActive(item);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg transition font-medium ${
                  active
                    ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/40"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-950/60"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
                {item.badge !== null && item.badge !== undefined && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                      item.badgeAlert ? "bg-red-600 text-white" : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* 2. BOTTOM MOBILE NAVIGATION BAR (Sticky/Fixed, High Z-Index, Touch-Optimized) */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-slate-950/95 border-t border-slate-800 backdrop-blur-md pb-safe">
        <div className="max-w-md mx-auto grid grid-cols-5 py-1.5 px-1">
          {navItems.map((item) => {
            const active = isActive(item);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center py-1 px-1 rounded-lg transition relative ${
                  active
                    ? "text-indigo-400 font-bold bg-indigo-950/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <div className="relative">
                  <Icon className={`w-4 h-4 ${active ? "text-indigo-400" : "text-slate-400"}`} />
                  {item.badge !== null && item.badge !== undefined && (
                    <span
                      className={`absolute -top-1.5 -right-2 text-[9px] min-w-[14px] h-[14px] flex items-center justify-center rounded-full px-1 font-bold ${
                        item.badgeAlert ? "bg-red-600 text-white" : "bg-slate-700 text-slate-200"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
                <span className="text-[10px] mt-0.5 tracking-tight font-mono truncate max-w-[55px]">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </>
  );
}
