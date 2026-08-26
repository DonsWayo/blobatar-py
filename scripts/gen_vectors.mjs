const SEP=0xff;
function feed(h,bytes){for(let i=0;i<bytes.length;i++){h=Math.imul(h^bytes[i],3432918353);h=(h<<13)|(h>>>19);}return h;}
function finalize(h){h=Math.imul(h^(h>>>16),2246822507);h=Math.imul(h^(h>>>13),3266489909);return (h^(h>>>16))>>>0;}
const utf8=new TextEncoder();
const normalizeSeed=s=>s.normalize("NFC").trim().toLowerCase();
function seedState(seed,normalize=true){const s=normalize?normalizeSeed(seed):seed;return feed(1779033703^s.length,utf8.encode(s));}
function stream(state,key){return finalize(feed(feed(state,Uint8Array.of(SEP)),utf8.encode(key)))/4294967296;}
const seeds=["alain","alaim","","a","ALAIN","  alain  ","José","Jos\u00e9","日本語","🎮🎲","\ufeffalain","ß","İstanbul","ΣΟΦΟΣ","x".repeat(200),"lab-cormoran","donswayo@example.com"];
const keys=["hue","shape","eyes","mouth","expression","tilt"];
const out=seeds.map(s=>({seed:s,norm:normalizeSeed(s),jsLength:normalizeSeed(s).length,state:seedState(s)|0,
  streams:Object.fromEntries(keys.map(k=>[k,stream(seedState(s),k)]))}));
console.log(JSON.stringify(out,null,1));
