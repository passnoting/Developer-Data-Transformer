import type { APIRoute } from "astro";

/**
 * 构建时生成 sitemap.xml，而不是手写一个 public/sitemap.xml。
 *
 * 原因：URL 必须和页面里的 canonical 完全一致（Astro 默认生成 /xxx/ 带尾斜杠），
 * 而且域名来自 astro.config 的 site（可由 SITE_URL 覆盖），换域名时不用改两处。
 *
 * 新增页面记得往 PAGES 里加一行，否则爬虫不知道它存在。
 */
const PAGES: Array<{ path: string; priority: string }> = [
  { path: "/", priority: "1.0" },
  { path: "/tools/", priority: "0.9" },
  { path: "/tools/clean-csv/", priority: "0.9" },
  { path: "/privacy/", priority: "0.2" },
  { path: "/terms/", priority: "0.2" },
];

export const GET: APIRoute = ({ site }) => {
  const base = site ?? new URL("https://flowtable.pages.dev");

  const urls = PAGES.map((p) => {
    const loc = new URL(p.path, base).href;
    return `  <url>\n    <loc>${loc}</loc>\n    <priority>${p.priority}</priority>\n  </url>`;
  }).join("\n");

  const xml =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    `${urls}\n` +
    `</urlset>\n`;

  return new Response(xml, {
    headers: { "content-type": "application/xml; charset=utf-8" },
  });
};
