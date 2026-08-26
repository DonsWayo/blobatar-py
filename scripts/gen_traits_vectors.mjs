// Hash functions (copied from hash.ts)
const SEP = 0xff;

function feed(h, bytes) {
  for (let i = 0; i < bytes.length; i++) {
    h = Math.imul(h ^ bytes[i], 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return h;
}

function finalize(h) {
  h = Math.imul(h ^ (h >>> 16), 2246822507);
  h = Math.imul(h ^ (h >>> 13), 3266489909);
  return (h ^ (h >>> 16)) >>> 0;
}

const utf8 = new TextEncoder();

function _i32(n) {
  return n | 0;
}

function _utf16_length(s) {
  let count = 0;
  for (let i = 0; i < s.length; i++) {
    const code = s.charCodeAt(i);
    count += code > 0xffff ? 2 : 1;
  }
  return count;
}

const _JS_WS = "\t\n\v\f\r                 　﻿";

function normalizeSeed(seed) {
  return seed.normalize("NFC").trim().toLowerCase();
}

function seedState(seed, normalize = true) {
  const s = normalize ? normalizeSeed(seed) : seed;
  return feed(_i32(1779033703 ^ _utf16_length(s)), utf8.encode(s));
}

function stream(state, key) {
  return (
    finalize(feed(feed(state, Uint8Array.of(SEP)), utf8.encode(key))) /
    4294967296
  );
}

// Traits function (copied from traits.ts)
function traits(seed, normalize = true, overrides = undefined) {
  const state = seedState(seed, normalize);

  const t = (key) => {
    const v = overrides?.[key];
    const o = Array.isArray(v)
      ? v[Math.floor(stream(state, key) * v.length)]
      : v;
    return o === undefined
      ? stream(state, key)
      : o > 0
        ? o < 1
          ? o
          : 0.999999
        : 0;
  };

  t.num = (key, min, max) => min + t(key) * (max - min);
  t.int = (key, min, max) => min + Math.floor(t(key) * (max - min + 1));
  t.pick = (key, options) =>
    options[Math.floor(t(key) * options.length)];
  t.bool = (key, p = 0.5) => t(key) < p;
  t.jitter = (key, amount) => (t(key) * 2 - 1) * amount;

  return t;
}

// Test vectors
const seeds = [
  "alain",
  "alaim",
  "",
  "a",
  "ALAIN",
  "  alain  ",
  "José",
  "日本語",
  "🎮",
  "x".repeat(200),
  "lab-cormoran",
  "donswayo@example.com",
];

const keys = ["hue", "shape", "eyes", "mouth", "expression", "tilt"];
const options = ["round", "square", "triangle", "star"];

const out = seeds.map((seed) => {
  const t = traits(seed);
  return {
    seed,
    base: Object.fromEntries(keys.map((k) => [k, t(k)])),
    num: Object.fromEntries(
      keys.map((k) => [k, t.num(k, 0.1, 0.9)])
    ),
    int: Object.fromEntries(
      keys.map((k) => [k, t.int(k, 1, 10)])
    ),
    pick: Object.fromEntries(
      keys.map((k) => [k, t.pick(k, options)])
    ),
    bool: Object.fromEntries(
      keys.map((k) => [k, t.bool(k, 0.5)])
    ),
    jitter: Object.fromEntries(
      keys.map((k) => [k, t.jitter(k, 0.5)])
    ),
  };
});

console.log(JSON.stringify(out, null, 1));
