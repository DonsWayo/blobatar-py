// Reference vectors for the render pipeline, produced by running the ORIGINAL
// TypeScript implementation. This file must never be replaced by Python output:
// a reference generated from the port proves only that the port equals itself.

import { blobatar } from "../../blobatar-src/packages/blobatar/src/blobatar";
import type { BlobatarOptions } from "../../blobatar-src/packages/blobatar/src/render";

const SEEDS = [
  "alain",
  "claude",
  "test",
  "hello world",
  "blobatar",
  "example@example.com",
  "1",
  "a",
  "very long seed string that goes on and on",
  "123456789",
  "special!@#$%",
  "mixed.CASE.string",
];

interface TestVector {
  seed: string;
  opts: BlobatarOptions;
  svg: string;
}

const out: TestVector[] = [];

// Basic rendering
for (const seed of SEEDS) {
  out.push({
    seed,
    opts: {},
    svg: blobatar(seed),
  });
}

// With size
for (const seed of SEEDS.slice(0, 4)) {
  out.push({
    seed,
    opts: { size: 256 },
    svg: blobatar(seed, { size: 256 }),
  });
}

// With background
for (const seed of SEEDS.slice(0, 4)) {
  out.push({
    seed,
    opts: { background: "square" },
    svg: blobatar(seed, { background: "square" }),
  });
  out.push({
    seed,
    opts: { background: "circle" },
    svg: blobatar(seed, { background: "circle" }),
  });
  out.push({
    seed,
    opts: { background: false },
    svg: blobatar(seed, { background: false }),
  });
}

// With hue
for (const seed of SEEDS.slice(0, 3)) {
  out.push({
    seed,
    opts: { hue: 120 },
    svg: blobatar(seed, { hue: 120 }),
  });
}

// With tone
for (const seed of SEEDS.slice(0, 3)) {
  out.push({
    seed,
    opts: { tone: 0.5 },
    svg: blobatar(seed, { tone: 0.5 }),
  });
}

// With title
for (const seed of SEEDS.slice(0, 3)) {
  out.push({
    seed,
    opts: { title: "Test Blobatar" },
    svg: blobatar(seed, { title: "Test Blobatar" }),
  });
}

// With normalize disabled
out.push({
  seed: "  MIXED  Case  ",
  opts: { normalize: false },
  svg: blobatar("  MIXED  Case  ", { normalize: false }),
});

console.log(JSON.stringify(out, null, 1));
