# Market Hedge Simulator

A practical simulator for testing sportsbook hedging strategies against prediction-market style execution risk.

## Live Demo
[market-hedge-simulator.replit.app](https://market-hedge-simulator.replit.app)

## What It Does
This app runs Monte Carlo simulations to estimate outcomes for a hedged position.

You can tune:
- sportsbook odds
- stake size
- true win probability
- hedge fraction
- fill probability
- slippage (bps)
- fees (bps)
- latency penalty (bps)
- number of simulation paths
- random seed (for reproducible runs)

## Outputs
- Expected value (EV)
- P/L distribution (p5, p50, p95)
- Maximum loss
- Break-even win rate
- Distribution chart of simulated outcomes

## Why This Exists
Hedging looks simple in theory but execution quality matters in practice.  
This tool helps visualize how fill risk, slippage, and latency can change expected returns.

## Features
- Deterministic seeded simulation mode
- Strategy presets (conservative / neutral / aggressive)
- Input validation with clear error states
- Shareable run configurations (URL params)

## Tech
- Replit-hosted web app
- TypeScript/JavaScript frontend
- Monte Carlo simulation core

## Local Development
1. Clone this repo
2. Install dependencies
3. Run the dev server

```bash
# example
npm install
npm run dev
npm test
```
