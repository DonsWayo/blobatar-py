// Renders seeds through the ORIGINAL TypeScript implementation and writes the
// SVG to stdout as JSON, for scripts/compare_upstream.py to diff against this
// port. It never imports anything from src/blobatar: a reference produced by
// the port proves only that the port equals itself.
//
//   BLOBATAR_SRC=/path/to/blobatar bun scripts/upstream_parity.ts > up.json
//   python scripts/compare_upstream.py up.json
//
// BLOBATAR_SRC must be a checkout of https://github.com/Alain00/blobatar. The
// pinned revision CI uses is recorded in .github/workflows/ci.yml.

import { pathToFileURL } from "url";
import path from "path";

const src = process.env.BLOBATAR_SRC ?? path.join(import.meta.dirname, "..", "..", "blobatar-src");
const mod = await import(
  pathToFileURL(path.join(src, "packages/blobatar/src/blobatar.ts")).href
);
const blobatar = mod.blobatar;

// The seeds a naive port gets wrong: UTF-16 length, trim() versus strip(), NFC,
// case folding, and a seed long enough to exercise the 32-bit overflow.
const SEEDS = [
  "alain",
  "alaim",
  "",
  "a",
  "ALAIN",
  "  alain  ",
  "José",
  "José",
  "日本語",
  "🎮🎲",
  "﻿alain",
  "ß",
  "İstanbul",
  "ΣΟΦΟΣ",
  "x".repeat(200),
  "lab-cormoran",
  "donswayo@example.com",
  "María",
  "🦊 fox",
];

// Every option the renderer exposes that changes observable output.
const OPTIONS: Array<[string, Record<string, unknown>]> = [
  ["bare", {}],
  ["size", { size: 64 }],
  ["title", { title: "avatar" }],
  ["background-false", { background: false }],
  ["hue", { hue: 210 }],
  ["tone", { tone: 0.35 }],
  ["no-normalize", { normalize: false }],
  ["no-contrast", { contrast: false }],
  ["palette", { palette: { 0: "#112233", 3: "#ff0000" } }],
  ["traits", { traits: { eyes: [0.1, 0.9], tilt: 0.2 } }],
];

const out = SEEDS.flatMap((seed) =>
  OPTIONS.map(([label, opts]) => ({
    seed,
    label,
    opts,
    svg: blobatar(seed, opts as never),
  })),
);

console.log(JSON.stringify(out));