/*
 * Share image generator (Phase 1)
 * - Renders poem on story/post templates via Canvas 2D
 * - Uses Web Share API with files when available; falls back to download
 */

import { sanitizeInput } from './utils.js';

const FORMATS = {
  story: { w: 1080, h: 1920, safe: { l: 120, r: 120, t: 320, b: 280 } },
  post:  { w: 1080, h: 1080, safe: { l: 96,  r: 96,  t: 140, b: 140 } },
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

function wrapText(ctx, text, maxWidth, lineHeight, maxLines) {
  const words = text.split(/\s+/);
  const lines = [];
  let line = '';
  for (let i = 0; i < words.length; i++) {
    const test = line ? line + ' ' + words[i] : words[i];
    const m = ctx.measureText(test);
    if (m.width > maxWidth && line) {
      lines.push(line);
      line = words[i];
      if (lines.length >= maxLines) break;
    } else {
      line = test;
    }
  }
  if (line && lines.length < maxLines) lines.push(line);
  if (lines.length === maxLines && i < words.length) {
    // ellipsize last line
    let last = lines[lines.length - 1];
    while (ctx.measureText(last + '…').width > maxWidth && last.length > 0) {
      last = last.slice(0, -1);
    }
    lines[lines.length - 1] = last + '…';
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
    const bg = await loadImage(backgroundUrl);
    ctx.drawImage(bg, 0, 0, cfg.w, cfg.h);
  } else {
    const grad = ctx.createLinearGradient(0, 0, cfg.w, cfg.h);
    grad.addColorStop(0, '#ffd6c0');
    grad.addColorStop(1, '#ffeef2');
    ctx.fillStyle = grad; ctx.fillRect(0, 0, cfg.w, cfg.h);
  }

  // Soft panel for text area (like your template)
  const panel = {
    x: cfg.safe.l,
    y: cfg.safe.t,
    w: cfg.w - cfg.safe.l - cfg.safe.r,
    h: cfg.h - cfg.safe.t - cfg.safe.b,
    r: 40,
  };
  ctx.save();
  ctx.globalAlpha = 0.85;
  drawRoundedRect(ctx, panel.x, panel.y, panel.w, panel.h, panel.r);
  ctx.fillStyle = theme === 'dark' ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.65)';
  ctx.fill();
  ctx.restore();

  // Typography
  const titleSize = format === 'story' ? 54 : 40;
  const authorSize = format === 'story' ? 36 : 28;
  const bodySize = format === 'story' ? 40 : 32;
  const lineHeight = Math.round(bodySize * 1.35);
  const maxWidth = panel.w - 64; // inner padding 32px each side
  let cursorY = panel.y + 56; // top padding

  // Title
  if (safeTitle) {
    ctx.font = `700 ${titleSize}px Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
    ctx.fillStyle = '#d76f43';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    const lines = wrapText(ctx, safeTitle, maxWidth, lineHeight, 2);
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
    ctx.fillText(`— ${safeAuthor}`, panel.x + 32, cursorY);
    cursorY += authorSize + 24;
  }

  // Body
  ctx.font = `400 ${bodySize}px Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif`;
  ctx.fillStyle = '#5e5e5e';
  const maxLines = Math.floor((panel.y + panel.h - cursorY - 32) / lineHeight);
  const bodyLines = wrapText(ctx, safeText, maxWidth, lineHeight, Math.max(6, maxLines));
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
