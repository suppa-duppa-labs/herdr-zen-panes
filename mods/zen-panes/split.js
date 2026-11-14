const EPSILON = 1e-6;

export function boxes(node, out = {}, x = 0, y = 0, w = 1, h = 1) {
  if (node.type === "block") {
    out[node.id] = { x, y, w, h };
    return out;
  }
  const children = node.children ?? [];
  const weight = (child) => child.size?.weight ?? 1;
  const total = children.reduce((sum, child) => sum + weight(child), 0) || 1;
  let start = 0;
  for (const child of children) {
    const share = weight(child) / total;
    if (node.type === "row") boxes(child, out, x + start * w, y, share * w, h);
    else boxes(child, out, x, y + start * h, w, share * h);
    start += share;
  }
  return out;
}

const overlap = (a0, a1, b0, b1) => Math.min(a1, b1) - Math.max(a0, b0);

export function neighbour(all, from, direction, history = []) {
  const a = all[from];
  if (!a) return null;
  let best = null;
  for (const [id, b] of Object.entries(all)) {
    if (id === from) continue;
    const gap = {
      left: a.x - (b.x + b.w),
      right: b.x - (a.x + a.w),
      up: a.y - (b.y + b.h),
      down: b.y - (a.y + a.h),
    }[direction];
    const shared = direction === "left" || direction === "right"
      ? overlap(a.y, a.y + a.h, b.y, b.y + b.h)
      : overlap(a.x, a.x + a.w, b.x, b.x + b.w);
    if (gap < -EPSILON || shared <= EPSILON) continue;
    const next = { id, gap, recent: history.indexOf(id), shared };
    if (!best || closer(next, best)) best = next;
  }
  return best?.id ?? null;
}

function closer(next, best) {
  if (Math.abs(next.gap - best.gap) > EPSILON) return next.gap < best.gap;
  if (next.recent !== best.recent) return next.recent > best.recent;
  return next.shared - best.shared > EPSILON;
}

