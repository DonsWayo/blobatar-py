// Generate test vectors for shape functions.
// This script uses the original TypeScript implementations to produce byte-exact reference output.

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
const normalizeSeed = (s) => s.normalize("NFC").trim().toLowerCase();

function seedState(seed, normalize = true) {
  const s = normalize ? normalizeSeed(seed) : seed;
  return feed(1779033703 ^ s.length, utf8.encode(s));
}

function stream(state, key) {
  return finalize(feed(feed(state, Uint8Array.of(SEP)), utf8.encode(key))) / 4294967296;
}

// Original shape.ts implementations
const r2 = (v) => {
  const s = Math.round(v * 100) / 100;
  return Object.is(s, -0) ? "0" : String(s);
};

function superellipse({ cx, cy, rx, ry, n = 4, rot = 0 }) {
  const k = Math.min(1, (8 * Math.pow(2, -1 / n) - 4) / 3);
  const a = rx;
  const b = ry;
  const ak = a * k;
  const bk = b * k;

  const pts = [
    [a, 0],
    [a, bk], [ak, b], [0, b],
    [-ak, b], [-a, bk], [-a, 0],
    [-a, -bk], [-ak, -b], [0, -b],
    [ak, -b], [a, -bk], [a, 0],
  ];

  const t = (rot * Math.PI) / 180;
  const cos = Math.cos(t);
  const sin = Math.sin(t);
  const at = (i) => {
    const [x, y] = pts[i];
    return `${r2(cx + x * cos - y * sin)} ${r2(cy + x * sin + y * cos)}`;
  };

  let d = `M${at(0)}`;
  for (let i = 1; i < 13; i += 3) d += `C${at(i)} ${at(i + 1)} ${at(i + 2)}`;
  return d + "Z";
}

function arc(cx, cy, w, depth) {
  return `M${r2(cx - w)} ${r2(cy)}Q${r2(cx)} ${r2(cy + depth)} ${r2(cx + w)} ${r2(cy)}`;
}

function blobPath(cx, cy, rx, ry, radii, rot = 0) {
  const n = radii.length;
  const t0 = (rot * Math.PI) / 180;
  const p = radii.map((m, i) => {
    const a = t0 + (2 * Math.PI * i) / n;
    return [cx + rx * m * Math.cos(a), cy + ry * m * Math.sin(a)];
  });

  const at = (i) => p[((i % n) + n) % n];
  let d = `M${r2(at(0)[0])} ${r2(at(0)[1])}`;

  for (let i = 0; i < n; i++) {
    const [x0, y0] = at(i - 1);
    const [x1, y1] = at(i);
    const [x2, y2] = at(i + 1);
    const [x3, y3] = at(i + 2);
    d +=
      `C${r2(x1 + (x2 - x0) / 6)} ${r2(y1 + (y2 - y0) / 6)}` +
      ` ${r2(x2 - (x3 - x1) / 6)} ${r2(y2 - (y3 - y1) / 6)}` +
      ` ${r2(x2)} ${r2(y2)}`;
  }

  return d + "Z";
}

function polygon({ cx, cy, rx, ry, sides, round = 0.3, rot = 0 }) {
  const k = round > 0 ? (round < 1 ? round / 2 : 0.5) : 0;
  const t0 = (rot * Math.PI) / 180 - Math.PI / 2;
  const v = Array.from({ length: sides }, (_, i) => {
    const a = t0 + (2 * Math.PI * i) / sides;
    return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  });

  const at = (i) => v[((i % sides) + sides) % sides];
  const cut = (i, j) => {
    const [x0, y0] = at(i);
    const [x1, y1] = at(j);
    return `${r2(x0 + (x1 - x0) * k)} ${r2(y0 + (y1 - y0) * k)}`;
  };

  let d = `M${cut(0, -1)}`;
  for (let i = 0; i < sides; i++) {
    const [x, y] = at(i);
    d += `Q${r2(x)} ${r2(y)} ${cut(i, i + 1)}`;
    if (k < 0.5) d += `L${cut(i + 1, i)}`;
  }
  return d + "Z";
}

function box(cx, cy, rx, ry) {
  const l = r2(cx - rx);
  const r = r2(cx + rx);
  return `M${l} ${r2(cy - ry)}H${r}V${r2(cy + ry)}H${l}Z`;
}

function taper(cx, cy, rx, ry, tip) {
  const t = Math.max(1.05, tip);
  const tx = rx * Math.sqrt(1 - 1 / (t * t));
  const ty = cy - ry / t;
  const apex = cy - t * ry;
  const px = tx * 0.14;
  const py = ty + 0.86 * (apex - ty);
  return (
    `M${r2(cx - tx)} ${r2(ty)}` +
    `L${r2(cx - px)} ${r2(py)}` +
    `Q${r2(cx)} ${r2(apex)} ${r2(cx + px)} ${r2(py)}` +
    `L${r2(cx + tx)} ${r2(ty)}Z`
  );
}

// Generate test vectors
const seeds = ["alain", "alaim", "", "a", "ALAIN", "  alain  ", "José", "José", "日本語", "🎮🎲", "﻿alain", "ß", "İstanbul", "ΣΟΦΟΣ", "x".repeat(200), "lab-cormoran", "donswayo@example.com"];

const vectors = seeds.map((seed) => {
  const state = seedState(seed);
  const t = (key) => stream(state, key);

  return {
    seed,
    superellipse: superellipse({
      cx: t("cx"),
      cy: t("cy"),
      rx: 100 * t("rx"),
      ry: 100 * t("ry"),
      n: 2 + 6 * t("n"),
      rot: 360 * t("rot"),
    }),
    arc: arc(50 * t("cx"), 50 * t("cy"), 30 * t("w"), 20 * t("d")),
    blobPath: blobPath(
      50 * t("cx"),
      50 * t("cy"),
      100 * t("rx"),
      100 * t("ry"),
      [t("r0"), t("r1"), t("r2"), t("r3"), t("r4"), t("r5")],
      360 * t("rot"),
    ),
    polygon: polygon({
      cx: 50 * t("cx"),
      cy: 50 * t("cy"),
      rx: 100 * t("rx"),
      ry: 100 * t("ry"),
      sides: 3 + Math.floor(7 * t("sides")),
      round: t("round"),
      rot: 360 * t("rot"),
    }),
    box: box(50 * t("cx"), 50 * t("cy"), 40 * t("rx"), 60 * t("ry")),
    taper: taper(50 * t("cx"), 50 * t("cy"), 50 * t("rx"), 80 * t("ry"), 1.4 + 0.3 * t("tip")),
  };
});

console.log(JSON.stringify(vectors, null, 1));
