/**
 * 冒烟测试：零依赖，`node packages/core/test/smoke.ts` 直接跑。
 * 目的不是覆盖率，而是确保“改一条规则不会悄悄改坏另一条”。
 */
import assert from "node:assert/strict";
import { decodeText, isSuspicious, runPipeline, tableFromJson } from "../src/index.ts";
import type { Dataset, Rule } from "../src/index.ts";

const messy: Dataset = {
  columns: ["order_id", "date", "amount", "customer", "status", "note"],
  rows: [
    {
      order_id: " A-1001 ",
      date: "2026/11/04",
      amount: "$1,234.50",
      customer: "  Acme  Inc ",
      status: "PAID",
      note: "vip",
    },
    {
      order_id: "A-1002",
      date: "11/05/2026",
      amount: "(89.00)",
      customer: "Beta LLC",
      status: "paid",
      note: null,
    },
    {
      order_id: "A-1001",
      date: "2026/11/04",
      amount: "$1,234.50",
      customer: "Acme Inc",
      status: "PAID",
      note: "",
    },
    {
      order_id: "A-1003",
      date: "04.11.2026",
      amount: "N/A",
      customer: "Gamma",
      status: "refunded",
      note: "  ",
    },
    { order_id: "", date: "", amount: "", customer: "", status: "", note: "" },
  ],
};

const rules: Rule[] = [
  { id: "r-trim", type: "trim", column: "order_id" },
  { id: "r-trim2", type: "trim", column: "customer" },
  { id: "r-drop-empty", type: "dropEmptyRows" },
  { id: "r-dates", type: "normalizeDates", column: "date" },
  { id: "r-num", type: "coerceNumbers", column: "amount" },
  { id: "r-case", type: "normalizeCase", column: "status", options: { case: "upper" } },
  { id: "r-map", type: "mapEnum", column: "status", options: { mapping: { PAID: "paid", REFUNDED: "refunded" } } },
  { id: "r-split", type: "splitColumn", column: "customer", options: { delimiter: " ", into: ["customer_name", "customer_suffix"] } },
  { id: "r-dedupe", type: "dedupe", options: { keys: ["order_id"] } },
  { id: "r-range", type: "rangeCheck", column: "amount", options: { min: 0, max: 100000 } },
  { id: "r-req", type: "requireFields", options: { columns: ["order_id", "date"] } },
];

const result = runPipeline(messy, rules);
const { dataset, stats, warnings } = result;

/* 1. 空行被删掉，重复的 A-1001 被去重 */
assert.equal(stats.rowsIn, 5, "输入应有 5 行");
assert.equal(stats.rowsOut, 3, "删空行 + 去重后应剩 3 行");

/* 2. 去重保留的是第一条（带空格的），trim 已把它修好 */
assert.equal(dataset.rows[0].order_id, "A-1001");
assert.equal(dataset.rows[0].customer, "Acme Inc");

/* 3. 日期统一成 ISO */
assert.deepEqual(
  dataset.rows.map((r) => r.date),
  ["2026-11-04", "2026-11-05", "2026-11-04"],
  "三种日期写法都要归一",
);

/* 4. 金额：$1,234.50 → 1234.5；(89.00) → -89；N/A 保持原样并告警 */
assert.equal(dataset.rows[0].amount, 1234.5);
assert.equal(dataset.rows[1].amount, -89);
assert.equal(dataset.rows[2].amount, "N/A");
assert.ok(warnings.some((w) => w.includes("无法转成数字")), "应提示无法转数字的值");

/* 5. 大小写 + 枚举映射 */
assert.equal(dataset.rows[1].status, "paid");
assert.equal(dataset.rows[2].status, "refunded");

/* 6. 拆列把新列插在原列后面，不丢原列 */
assert.ok(dataset.columns.includes("customer_name"));
assert.equal(dataset.rows[0].customer_name, "Acme");
assert.equal(dataset.rows[0].customer_suffix, "Inc");

/* 7. diff 能指回输入行号，且每一条都带 rule id */
const first = result.diffs[0];
assert.ok(first.row >= 1 && first.row <= 5, "diff 的行号必须是输入行号");
assert.ok(first.rule.startsWith("r-"), "diff 必须能溯源到规则");

/* 8. 歧义日期告警 */
assert.ok(
  warnings.some((w) => w.includes("MM/DD")),
  "11/05/2026 与 04.11.2026 混用时必须提示歧义",
);

/* 9. 行数异常检测：昨天的 200 行变成今天的 3 行，必须判为可疑 */
assert.equal(isSuspicious(3, 200), true);
assert.equal(isSuspicious(200, 200), false);
assert.equal(isSuspicious(0, 200), true);

/* 10. API 响应 → 表：嵌套对象铺平、标量数组合并、列取并集 */
const api = tableFromJson(
  {
    data: {
      items: [
        { id: 1, customer: { name: "Acme", country: "US" }, tags: ["vip", "new"], total: 120 },
        { id: 2, customer: { name: "Beta", address: { city: "Berlin" } }, total: 80 },
      ],
    },
  },
  "data.items",
);
assert.equal(api.rows.length, 2);
assert.deepEqual(api.columns.slice(0, 4), ["id", "customer.name", "customer.country", "tags"]);
assert.equal(api.rows[0]["customer.name"], "Acme");
assert.equal(api.rows[0].tags, "vip,new");
assert.equal(api.rows[1]["tags"], null, "缺失字段要补 null，不能 undefined");
assert.ok(api.columns.includes("customer.address.city"), "深层字段要展开");

/* 11. 编码识别：中文 CSV 最常见的三种情况 + 两种“这根本不是 CSV” */
const gbkBytes = new Uint8Array([0xb6, 0xa9, 0xb5, 0xa5, 0xba, 0xc5]); // "订单号" in GBK
const gbk = decodeText(gbkBytes);
assert.equal(gbk.ok, true, "GBK 字节必须能被识别");
if (gbk.ok) {
  assert.equal(gbk.encoding, "gb18030");
  assert.equal(gbk.text, "订单号");
}

const utf8Bom = decodeText(
  new Uint8Array([0xef, 0xbb, 0xbf, ...new TextEncoder().encode("订单号")]),
);
assert.equal(utf8Bom.ok, true);
if (utf8Bom.ok) {
  assert.equal(utf8Bom.encoding, "utf-8");
  assert.equal(utf8Bom.text, "订单号", "BOM 必须被剥掉，否则第一列名会带 \\uFEFF");
}

const utf16 = decodeText(new Uint8Array([0xff, 0xfe, 0xa2, 0x8b, 0x55, 0x53])); // "订单"
assert.equal(utf16.ok, true);
if (utf16.ok) {
  assert.equal(utf16.encoding, "utf-16le");
  assert.equal(utf16.text, "订单");
}

const ascii = decodeText(new TextEncoder().encode("id,name\n1,a"));
assert.equal(ascii.ok, true);
if (ascii.ok) {
  assert.equal(ascii.warnings.length, 0, "纯 ASCII 不该产生告警");
}

/* 12. .xlsx 是 ZIP，绝不能被当成文本读出 "PK..." 垃圾 */
const zip = decodeText(new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0x14, 0x00]));
assert.equal(zip.ok, false);
if (!zip.ok) {
  assert.equal(zip.reason, "zip");
  assert.ok(zip.message.includes("xlsx"));
}

const ole = decodeText(new Uint8Array([0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1]));
assert.equal(ole.ok, false);
if (!ole.ok) assert.equal(ole.reason, "ole");

console.log("✅ core smoke test passed");
console.log("   rows:", stats.rowsIn, "→", stats.rowsOut, "｜cells changed:", stats.cellsChanged, "｜diffs:", result.diffs.length);
console.log("   warnings:");
for (const w of warnings) console.log("   -", w);
