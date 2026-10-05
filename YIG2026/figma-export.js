"use strict";

// Turns a rendered card into SVG markup that Figma turns into editable layers when pasted.
//
//   const { svg, warnings } = await cardToSvg(document.querySelector("#card .card"));
//
// It reads the card as the browser laid it out (box positions and computed styles), so the SVG matches
// the screen. Text becomes <text>, boxes become <rect>, game icons become nested vector art. Each line
// of the card is a <g id="<style>">, so the layers in Figma are named after the card styles.
// Nothing here knows about the configurator page; it works on any .card element.

// Font families as Figma knows them (the YIG Prototype file uses the same names as the CSS).
const FIGMA_FONTS = {
  NYTKarnak: "NYTKarnak",
  NYTFranklin: "NYTFranklin",
};

// CSS weight -> Figma style name.
const FIGMA_STYLES = { 300: "Light", 400: "Book", 500: "Medium", 600: "Semibold", 700: "Bold" };

// ---------- small helpers ----------

function escapeXml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
}

function round(n) {
  return Math.round(n * 100) / 100;
}

// "rgba(97, 97, 97, 0.05)" -> { color: "rgb(97, 97, 97)", opacity: 0.05 }, or null when fully clear.
function parseColor(css) {
  const m = css.match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const [r, g, b, a = 1] = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
  if (a === 0) return null;
  return { color: `rgb(${r}, ${g}, ${b})`, opacity: a };
}

function paint(attr, parsed) {
  return `${attr}="${parsed.color}"${parsed.opacity < 1 ? ` ${attr}-opacity="${parsed.opacity}"` : ""}`;
}

// ---------- boxes ----------

function boxSvg(cs, rect, origin) {
  const fill = parseColor(cs.backgroundColor);
  const borderWidth = parseFloat(cs.borderTopWidth) || 0;
  const stroke = cs.borderTopStyle !== "none" && borderWidth > 0 ? parseColor(cs.borderTopColor) : null;
  if (!fill && !stroke) return "";
  // An SVG stroke is centered on the edge; a CSS border sits inside it. Pull the rect in by half.
  const inset = stroke ? borderWidth / 2 : 0;
  const radius = Math.max(0, (parseFloat(cs.borderTopLeftRadius) || 0) - inset);
  const attrs = [
    `x="${round(rect.left - origin.left + inset)}"`,
    `y="${round(rect.top - origin.top + inset)}"`,
    `width="${round(rect.width - inset * 2)}"`,
    `height="${round(rect.height - inset * 2)}"`,
  ];
  if (radius) attrs.push(`rx="${round(radius)}"`);
  attrs.push(fill ? paint("fill", fill) : 'fill="none"');
  if (stroke) {
    attrs.push(paint("stroke", stroke), `stroke-width="${borderWidth}"`);
    if (cs.borderTopStyle === "dashed") attrs.push('stroke-dasharray="4 3"');
  }
  return `<rect ${attrs.join(" ")}/>`;
}

// ---------- text ----------

let measureContext;
// Distance from the top of a text box to its baseline, which is where SVG wants y.
function ascent(cs) {
  measureContext = measureContext || document.createElement("canvas").getContext("2d");
  measureContext.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  const measured = measureContext.measureText("Hg").fontBoundingBoxAscent;
  return measured || parseFloat(cs.fontSize) * 0.8;
}

// Figma's SVG import ignores font-weight="600" (it lands on Bold), but it reads "Family-Style" as the
// exact font, so the style goes into the family name: "NYTFranklin-Semibold". Verified against the
// YIG Prototype fonts for all six Karnak / Franklin styles we use.
function fontFamily(cs) {
  const first = cs.fontFamily.split(",")[0].trim().replace(/^["']|["']$/g, "");
  const family = FIGMA_FONTS[first];
  const style = FIGMA_STYLES[cs.fontWeight];
  return family && style ? `${family}-${style}` : first;
}

// One <text> per line the browser actually drew: characters are grouped by where they sit vertically, so
// wrapped text and line breaks come out as separate lines, just as on the card.
function textSvg(node, origin) {
  const cs = getComputedStyle(node.parentElement);
  const upper = cs.textTransform === "uppercase";
  const rows = [];
  const range = document.createRange();
  const text = node.nodeValue;
  for (let i = 0; i < text.length; i++) {
    if (text[i] === "\n") continue;
    range.setStart(node, i);
    range.setEnd(node, i + 1);
    const box = range.getClientRects()[0];
    if (!box || !box.width) continue;
    const top = Math.round(box.top);
    let row = rows.find((r) => r.top === top);
    if (!row) rows.push((row = { top, boxTop: box.top, left: box.left, right: box.right, text: "" }));
    row.text += text[i];
    row.left = Math.min(row.left, box.left);
    row.right = Math.max(row.right, box.right);
  }

  const align = cs.textAlign;
  const anchor = align === "center" ? "middle" : align === "right" || align === "end" ? "end" : "start";
  const base = ascent(cs);
  const tracking = parseFloat(cs.letterSpacing);
  return rows
    .map((row) => {
      const words = (upper ? row.text.toUpperCase() : row.text).trim();
      if (!words) return "";
      const x = anchor === "middle" ? (row.left + row.right) / 2 : anchor === "end" ? row.right : row.left;
      const fill = parseColor(cs.color) || { color: "rgb(0, 0, 0)", opacity: 1 };
      const attrs = [
        `x="${round(x - origin.left)}"`,
        `y="${round(row.boxTop - origin.top + base)}"`,
        `font-family="${escapeXml(fontFamily(cs))}"`,
        `font-size="${parseFloat(cs.fontSize)}"`,
        `font-weight="${cs.fontWeight}"`,
        paint("fill", fill),
        `text-anchor="${anchor}"`,
      ];
      if (tracking) attrs.push(`letter-spacing="${round(tracking)}"`);
      return `<text ${attrs.join(" ")}>${escapeXml(words)}</text>`;
    })
    .join("");
}

// ---------- icons ----------

// Fetches an icon file and returns it nested at the image's position, so it pastes as vector art.
// Returns null when the file can't be read (for example when the page is opened from disk).
async function iconSvg(img, rect, origin) {
  try {
    const response = await fetch(img.currentSrc || img.src);
    if (!response.ok) return null;
    const doc = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
    const root = doc.documentElement;
    if (root.nodeName !== "svg" || doc.querySelector("parsererror")) return null;
    const viewBox = root.getAttribute("viewBox") || `0 0 ${root.getAttribute("width")} ${root.getAttribute("height")}`;
    const inner = new XMLSerializer().serializeToString(root).replace(/^<svg[^>]*>|<\/svg>\s*$/g, "");
    return (
      `<svg x="${round(rect.left - origin.left)}" y="${round(rect.top - origin.top)}" ` +
      `width="${round(rect.width)}" height="${round(rect.height)}" viewBox="${viewBox}" fill="none">${inner}</svg>`
    );
  } catch (error) {
    return null;
  }
}

// ---------- walking the card ----------

async function elementSvg(node, origin, warnings) {
  if (node.nodeType === Node.TEXT_NODE) return node.nodeValue.trim() ? textSvg(node, origin) : "";
  if (node.nodeType !== Node.ELEMENT_NODE) return "";

  const cs = getComputedStyle(node);
  // The spacer is a development aid (a pink block): it draws nothing on a live card. Its space is kept
  // because every other position comes from the page.
  if (cs.display === "none" || node.classList.contains("spacer")) return "";

  const rect = node.getBoundingClientRect();
  let out = "";

  if (node.tagName === "IMG") {
    const icon = await iconSvg(node, rect, origin);
    if (icon) return icon;
    warnings.push(`Could not read ${node.getAttribute("src")}; pasted a gray box in its place.`);
    return `<rect x="${round(rect.left - origin.left)}" y="${round(rect.top - origin.top)}" width="${round(rect.width)}" height="${round(rect.height)}" fill="rgb(235, 235, 235)"/>`;
  }

  if (rect.width && rect.height) out += boxSvg(cs, rect, origin);
  for (const child of node.childNodes) out += await elementSvg(child, origin, warnings);
  return out;
}

// Returns { svg, warnings }. Each line of the card becomes a group named after its style.
async function cardToSvg(card) {
  const warnings = [];
  const box = card.getBoundingClientRect();
  const origin = { left: box.left, top: box.top };

  // No background rectangle: the card's white is a page look, and the export is just the elements, so it
  // pastes onto whatever frame it lands in. The canvas is still the full card width (375px), which leaves
  // the card's 20px padding on each side.
  let body = "";
  const cs = getComputedStyle(card);
  const content = { left: box.left + parseFloat(cs.paddingLeft), right: box.right - parseFloat(cs.paddingRight) };
  for (const node of card.querySelectorAll("[data-style] *, [data-style]")) {
    const r = node.getBoundingClientRect();
    if (r.width && (r.left < content.left - 0.5 || r.right > content.right + 0.5)) {
      warnings.push(`A ${node.closest("[data-style]").dataset.style} line is wider than the ${round(content.right - content.left)}px content area. Adjust its CSS.`);
      break;
    }
  }
  for (const child of card.children) {
    for (const line of child.classList.contains("stack") ? child.children : [child]) {
      const inner = await elementSvg(line, origin, warnings);
      if (!inner) continue;
      const name = line.dataset && line.dataset.style ? line.dataset.style : line.className;
      body += `<g id="${escapeXml(name)}">${inner}</g>`;
    }
  }

  const width = round(box.width);
  const height = round(box.height);
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" fill="none">` +
    body +
    "</svg>";
  return { svg, warnings };
}
