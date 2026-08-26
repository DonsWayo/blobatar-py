/**
 * Generate test vectors for color.py parity verification.
 *
 * Covers the full hue circle, extremes of lightness and chroma, and gamut-clamping edges.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

// Inline the TypeScript color functions for testing
const Math_cbrt = (x) => Math.sign(x) * Math.pow(Math.abs(x), 1 / 3);

function toLinear({ l, c, h }) {
  const r = (h * Math.PI) / 180;
  const a = c * Math.cos(r);
  const b = c * Math.sin(r);

  const l_ = l + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = l - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = l - 0.0894841775 * a - 1.291485548 * b;

  const L = l_ * l_ * l_;
  const M = m_ * m_ * m_;
  const S = s_ * s_ * s_;

  return [
    4.0767416621 * L - 3.3077115913 * M + 0.2309699292 * S,
    -1.2684380046 * L + 2.6097574011 * M - 0.3413193965 * S,
    -0.0041960863 * L - 0.7034186147 * M + 1.707614701 * S,
  ];
}

const inGamut = (rgb) =>
  rgb.every((v) => v >= -1e-4 && v <= 1 + 1e-4);

function resolve(color) {
  let rgb = toLinear(color);
  if (!inGamut(rgb)) {
    let lo = 0;
    let hi = color.c;
    for (let i = 0; i < 12; i++) {
      const mid = (lo + hi) / 2;
      if (inGamut(toLinear({ ...color, c: mid }))) lo = mid;
      else hi = mid;
    }
    rgb = toLinear({ ...color, c: lo });
  }
  return rgb.map((v) => Math.min(1, Math.max(0, v)));
}

function luminance(color) {
  const [r, g, b] = resolve(color);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const x = luminance(a);
  const y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

function toHex(color) {
  return (
    "#" +
    resolve(color)
      .map((v) => {
        const s =
          v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055;
        return Math.round(s * 255)
          .toString(16)
          .padStart(2, "0");
      })
      .join("")
  );
}

function fromHex(hex) {
  const n = parseInt(hex.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const s = v / 255;
    return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });

  const l = Math_cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math_cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math_cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);

  const A = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s;
  const B = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s;

  return {
    l: 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    c: Math.hypot(A, B),
    h: (Math.atan2(B, A) * 180) / Math.PI,
  };
}

function mix(a, b, t) {
  const rad = (v) => (v * Math.PI) / 180;
  const ax = a.c * Math.cos(rad(a.h));
  const ay = a.c * Math.sin(rad(a.h));
  const bx = b.c * Math.cos(rad(b.h));
  const by = b.c * Math.sin(rad(b.h));
  const x = ax + (bx - ax) * t;
  const y = ay + (by - ay) * t;
  return {
    l: a.l + (b.l - a.l) * t,
    c: Math.hypot(x, y),
    h: (Math.atan2(y, x) * 180) / Math.PI,
  };
}

function mixHex(a, b, t) {
  return toHex(mix(fromHex(a), fromHex(b), t));
}

function fadeHex(a, b, t) {
  let out = "#";
  for (let i = 1; i < 7; i += 2) {
    const from = parseInt(a.slice(i, i + 2), 16);
    const to = parseInt(b.slice(i, i + 2), 16);
    const v = Math.round(from + (to - from) * t);
    out += (v < 16 ? "0" : "") + v.toString(16);
  }
  return out;
}

// Test colors: hues from 0 to 360, various L and C
const testColors = [];

// Full hue circle with mid L and C
for (let h = 0; h < 360; h += 30) {
  testColors.push({ l: 0.7, c: 0.15, h });
}

// Extremes of lightness
for (let h of [0, 45, 90, 180, 270, 315]) {
  testColors.push({ l: 0.95, c: 0.1, h }); // very light
  testColors.push({ l: 0.05, c: 0.1, h }); // very dark
  testColors.push({ l: 0.5, c: 0.05, h }); // low chroma
  testColors.push({ l: 0.5, c: 0.3, h }); // high chroma
}

// Edge cases
testColors.push({ l: 1, c: 0, h: 0 }); // pure white
testColors.push({ l: 0, c: 0, h: 0 }); // pure black
testColors.push({ l: 0.5, c: 0, h: 180 }); // gray
testColors.push({ l: 0.145, c: 0, h: 0 }); // DARK_SURFACE from color.ts

const vectors = testColors.map((color) => {
  const hex = toHex(color);
  const backToColor = fromHex(hex);

  // Test mix with another color
  const other = { l: 0.3, c: 0.2, h: (color.h + 120) % 360 };
  const otherHex = toHex(other);
  const mixedHex = mixHex(hex, otherHex, 0.5);
  const fadedHex = fadeHex(hex, otherHex, 0.5);

  // Test contrast
  const contrastVal = contrast(color, other);

  return {
    oklch: color,
    hex: hex,
    from_hex: {
      l: backToColor.l,
      c: backToColor.c,
      h: backToColor.h,
    },
    contrast: contrastVal,
    mix_hex_0_5: mixedHex,
    fade_hex_0_5: fadedHex,
  };
});

console.log(JSON.stringify(vectors, null, 1));
