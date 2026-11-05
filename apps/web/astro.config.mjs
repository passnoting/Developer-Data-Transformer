import { defineConfig } from "astro/config";

// 纯静态输出：工具页要极致首屏，且 Cloudflare Pages 免费托管静态资源。
// 需要服务端能力时，调用 apps/api（Worker）而不是开 SSR。
// 绑自定义域名后用 SITE_URL 覆盖，否则 canonical / sitemap 会一直指向 pages.dev。
export default defineConfig({
  site: process.env.SITE_URL ?? "https://flowtable.pages.dev",
  output: "static",
  build: { inlineStylesheets: "auto" },
  devToolbar: { enabled: false },
});
