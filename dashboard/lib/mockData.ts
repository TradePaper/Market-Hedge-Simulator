export interface SportEvent {
  id: string;
  event: string;
  sport: string;
  league: string;
  kickoff: string;
  americanOdds: number;
  marketProb: number;
}

export interface TimePoint {
  time: string;
  [eventId: string]: number | string;
}

function americanToImplied(odds: number): number {
  if (odds > 0) return 100 / (odds + 100);
  return Math.abs(odds) / (Math.abs(odds) + 100);
}

export const EVENTS: SportEvent[] = [
  { id: "e1", event: "Chiefs vs Eagles",       sport: "American Football", league: "NFL",   kickoff: "Sun 4:25 PM", americanOdds: -165, marketProb: 0.578 },
  { id: "e2", event: "Lakers vs Celtics",      sport: "Basketball",       league: "NBA",   kickoff: "Today 7:30 PM", americanOdds: +120, marketProb: 0.432 },
  { id: "e3", event: "Man City vs Arsenal",    sport: "Soccer",           league: "PL",    kickoff: "Sat 12:30 PM", americanOdds: -140, marketProb: 0.614 },
  { id: "e4", event: "Djokovic vs Alcaraz",   sport: "Tennis",           league: "ATP",   kickoff: "Today 2:00 PM", americanOdds: -200, marketProb: 0.623 },
  { id: "e5", event: "Yankees vs Red Sox",    sport: "Baseball",         league: "MLB",   kickoff: "Tonight 7:10 PM", americanOdds: +105, marketProb: 0.502 },
  { id: "e6", event: "Canelo vs Benavidez",   sport: "Boxing",           league: "WBC",   kickoff: "Sat 9:00 PM", americanOdds: -250, marketProb: 0.711 },
  { id: "e7", event: "Maple Leafs vs Bruins", sport: "Hockey",           league: "NHL",   kickoff: "Tonight 7:00 PM", americanOdds: +180, marketProb: 0.367 },
  { id: "e8", event: "Verstappen to Win",     sport: "Motorsport",       league: "F1",    kickoff: "Sun 2:00 PM", americanOdds: -130, marketProb: 0.548 },
];

export interface EnrichedEvent extends SportEvent {
  sbProb: number;
  diff: number;
  alert: boolean;
}

export function enrichEvents(): EnrichedEvent[] {
  return EVENTS.map((e) => {
    const sbProb = americanToImplied(e.americanOdds);
    const diff = marketProb(e) - sbProb;
    return { ...e, sbProb, diff, alert: Math.abs(diff) > 0.05 };
  });
}

function marketProb(e: SportEvent) {
  return e.marketProb;
}

function generateTimeSeries(): TimePoint[] {
  const points: TimePoint[] = [];
  const now = new Date();
  const enriched = enrichEvents();

  for (let i = 23; i >= 0; i--) {
    const t = new Date(now.getTime() - i * 60 * 60 * 1000);
    const label = t.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
    const point: TimePoint = { time: label };

    enriched.forEach((ev) => {
      const base = ev.diff;
      const noise = (Math.random() - 0.5) * 0.04;
      const drift = (i / 23) * (Math.random() - 0.5) * 0.06;
      point[ev.id] = parseFloat((base + noise + drift).toFixed(4));
    });

    points.push(point);
  }

  return points;
}

export const TIME_SERIES: TimePoint[] = generateTimeSeries();

export const EVENT_COLORS: Record<string, string> = {
  e1: "#58a6ff",
  e2: "#3fb950",
  e3: "#d29922",
  e4: "#bc8cff",
  e5: "#76e3ea",
  e6: "#f85149",
  e7: "#ffa657",
  e8: "#e3b341",
};
