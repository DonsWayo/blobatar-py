// Reference vectors for the colour pipeline, produced by running the ORIGINAL
// TypeScript implementation. This file must never be replaced by Python output:
// a reference generated from the port proves only that the port equals itself.
import { toHex, fromHex, contrast, mixHex, fadeHex, mix, ramp, palette } from
  "../../blobatar-src/packages/blobatar/src/color.ts";

const HEXES = ["#ffffff", "#000000", "#6e5b77", "#ff0000", "#00ff00", "#0000ff",
  "#7f7f7f", "#123456", "#fedcba", "#010101", "#fefefe", "#4a90d9", "#8c937b",
  "#c0ffee", "#deadbe", "#0a0a0b", "#333333", "#f5f5f5"];
const WHITE = fromHex("#ffffff");

const out = HEXES.map((hex) => {
  const o = fromHex(hex);
  return {
    hex,
    from_hex: { l: o.l, c: o.c, h: o.h },
    to_hex: toHex(o),
    contrast_white: contrast(o, WHITE),
    mix_hex_05: mixHex(hex, "#8c937b", 0.5),
    mix_hex_025: mixHex(hex, "#4a90d9", 0.25),
    fade_hex_05: fadeHex(hex, "#8c937b", 0.5),
  };
});

const ramps = [0, 37, 120, 210, 359].flatMap((h) =>
  [0, 0.25, 0.5, 0.75, 0.99].map((tone) => ({
    hue: h, tone, palette: palette(h, true, tone),
  }))
);

console.log(JSON.stringify({ from_hex: out, ramps }, null, 1));
