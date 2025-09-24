/*
 * Share image generator (Phase 1)
 * - Renders poem on story/post templates via Canvas 2D
 * - Uses Web Share API with files when available; falls back to download
 */

import { sanitizeInput } from './utils.js';

const FORMATS = {
  story: { w: 1080, h: 1920, safe: { l: 120, r: 120, t: 320, b: 280 } },
  // Instagram Post (portrait 4:5): 1080 x 1350
  post:  { w: 1080, h: 1350, safe: { l: 96,  r: 96,  t: 160, b: 160 } },
};

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

async function ensureFonts(fontFamilies = []) {
  try {
    if (document.fonts && document.fonts.ready) {
      await document.fonts.ready;
    }
  } catch (_) { /* no-op */ }
}

// Wrap a single logical line into multiple canvas-fit lines
function wrapWords(ctx, text, maxWidth) {
  if (text === '') return [''];
  const words = text.split(/\s+/);
  const out = [];
  let line = '';
  for (let i = 0; i < words.length; i++) {
    const test = line ? line + ' ' + words[i] : words[i];
    if (ctx.measureText(test).width > maxWidth && line) {
      out.push(line);
      line = words[i];
    } else {
      line = test;
    }
  }
  if (line) out.push(line);
  return out;
}

// Respect explicit newlines (\n) as hard breaks while still wrapping long lines
function wrapTextWithBreaks(ctx, text, maxWidth, maxLines) {
  const rawLines = String(text).split(/\n/);
  const lines = [];
  for (let idx = 0; idx < rawLines.length; idx++) {
    const seg = rawLines[idx]; // keep empty to allow blank lines
    const pieces = wrapWords(ctx, seg, maxWidth);
    for (const p of pieces) {
      if (lines.length < maxLines) lines.push(p);
      else break;
    }
    if (lines.length >= maxLines) break;
  }
  // Ellipsize if truncated
  if (rawLines.length && lines.length >= maxLines) {
    let last = lines[lines.length - 1];
    const ell = '…';
    while (last && ctx.measureText(last + ell).width > maxWidth) {
      last = last.slice(0, -1);
      if (last.length === 0) break;
    }
    lines[lines.length - 1] = (last || '').trimEnd() + ell;
  }
  return lines;
}

function drawRoundedRect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w/2, h/2);
  ctx.beginPath();
  ctx.moveTo(x+rr, y);
  ctx.arcTo(x+w, y,   x+w, y+h, rr);
  ctx.arcTo(x+w, y+h, x,   y+h, rr);
  ctx.arcTo(x,   y+h, x,   y,   rr);
  ctx.arcTo(x,   y,   x+w, y,   rr);
  ctx.closePath();
}

export async function renderShareImage({
  format = 'story',
  backgroundUrl,
  title = '',
  author = '',
  text = '',
  watermark = 'aleshaikus.me',
  theme = 'light'
}) {
  const cfg = FORMATS[format] || FORMATS.story;
  await ensureFonts();

  // Sanitize inputs
  const safeTitle = sanitizeInput(String(title||'')).trim();
  const safeAuthor = sanitizeInput(String(author||'')).trim();
  let safeText = sanitizeInput(String(text||''))
    .replace(/[\t\r]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();

  // Canvas
  const canvas = document.createElement('canvas');
  canvas.width = cfg.w; canvas.height = cfg.h;
  const ctx = canvas.getContext('2d');

  // Background image or gradient fallback
  if (backgroundUrl) {
    try {
      const bg = await loadImage(backgroundUrl);
      ctx.drawImage(bg, 0, 0, cfg.w, cfg.h);
    } catch (err) {
      // Fallback to gradient if image fails to load (CORS or missing asset)
      const grad = ctx.createLinearGradient(0, 0, cfg.w, cfg.h);
      grad.addColorStop(0, '#ffd6c0');
      grad.addColorStop(1, '#ffeef2');
      ctx.fillStyle = grad; ctx.fillRect(0, 0, cfg.w, cfg.h);
    }
  } else {
    const grad = ctx.createLinearGradient(0, 0, cfg.w, cfg.h);
    grad.addColorStop(0, '#ffd6c0');
    grad.addColorStop(1, '#ffeef2');
    ctx.fillStyle = grad; ctx.fillRect(0, 0, cfg.w, cfg.h);
  }

  // Soft panel for text area
  // Story uses safe-area; Post uses a custom panel narrower and much lower
  const panel = (format === 'post')
    ? {
        // ~18% side margins → narrower card
        x: Math.round(cfg.w * 0.18),                     // ≈ 194px on 1080w
        // place the panel much lower (~39% from top)
        y: Math.round(cfg.h * 0.39),                     // ≈ 526px on 1350h
        // ~64% width for a compact feel
        w: Math.round(cfg.w * 0.64),                     // ≈ 691px
        // ~47% height to leave top/bottom breathing room
        h: Math.round(cfg.h * 0.47),                     // ≈ 635px
        r: 40,
      }
    : {
        x: cfg.safe.l,
        y: cfg.safe.t + 150, // slight downward shift per feedback
        w: cfg.w - cfg.safe.l - cfg.safe.r,
        h: cfg.h - cfg.safe.t - cfg.safe.b,
        r: 40,
      };
  ctx.save();
  ctx.globalAlpha = (format === 'post') ? 0.80 : 0.85;
  drawRoundedRect(ctx, panel.x, panel.y, panel.w, panel.h, panel.r);
  ctx.fillStyle = theme === 'dark' ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.65)';
  ctx.fill();
  ctx.restore();

  // Typography
  const titleSize = format === 'story' ? 54 : 38;
  const authorSize = format === 'story' ? 36 : 26;
  const bodySize = format === 'story' ? 40 : 30;
  const lineHeight = Math.round(bodySize * 1.35);
  const maxWidth = panel.w - 64; // inner padding 32px each side
  let cursorY = panel.y + 56; // top padding

  // Title
  if (safeTitle) {
    ctx.font = `700 ${titleSize}px Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
    ctx.fillStyle = '#d76f43';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    const lines = wrapTextWithBreaks(ctx, safeTitle, maxWidth, 2);
    lines.forEach(line => {
      ctx.fillText(line, panel.x + 32, cursorY);
      cursorY += Math.round(titleSize * 1.1);
    });
    cursorY += 12;
  }

  // Author
  if (safeAuthor) {
    ctx.font = `600 ${authorSize}px Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
    ctx.fillStyle = '#5e5e5e';
    ctx.fillText(`- ${safeAuthor}`, panel.x + 32, cursorY);
    cursorY += authorSize + 24;
  }

  // Body
  ctx.font = `400 ${bodySize}px Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
  ctx.fillStyle = '#5e5e5e';
  const maxLines = Math.floor((panel.y + panel.h - cursorY - 32) / lineHeight);
  const bodyLines = wrapTextWithBreaks(ctx, safeText, maxWidth, Math.max(6, maxLines));
  bodyLines.forEach(line => {
    ctx.fillText(line, panel.x + 32, cursorY);
    cursorY += lineHeight;
  });

  // Watermark bottom-right
  if (watermark) {
    ctx.font = `600 ${format === 'story' ? 28 : 22}px Inter, system-ui`;
    ctx.fillStyle = '#b85c2b';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'bottom';
    ctx.fillText(watermark, panel.x + panel.w - 24, panel.y + panel.h - 18);
  }

  return canvas;
}

export async function shareOrDownload(canvas, filename = 'poesia.png') {
  const blob = await new Promise(res => canvas.toBlob(res, 'image/png', 0.95));
  if (!blob) throw new Error('Canvas toBlob failed');

  const file = new File([blob], filename, { type: 'image/png' });

  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    await navigator.share({ files: [file], title: 'Poesia', text: 'Condividi su Instagram' });
    return 'shared';
  }

  // Fallback: download
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
  return 'downloaded';
}
