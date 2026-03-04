"use client";

import { useEffect, useState } from "react";

export function ClientTime({ className }: { className?: string }) {
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    setTime(new Date().toLocaleTimeString());
    const id = setInterval(() => setTime(new Date().toLocaleTimeString()), 30_000);
    return () => clearInterval(id);
  }, []);

  return <span className={className}>{time ?? "—"}</span>;
}

export function ClientDate({ className }: { className?: string }) {
  const [date, setDate] = useState<string | null>(null);

  useEffect(() => {
    setDate(
      new Date().toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
      })
    );
  }, []);

  return <span className={className}>{date ?? "—"}</span>;
}
