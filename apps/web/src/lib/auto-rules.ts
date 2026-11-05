import type { Dataset, Rule } from "@flowtable/core";

/**
 * 从列名猜规则。
 *
 * 这是"免费工具"和"付费管道"共用的第一步：用户不用懂规则，
 * 我们先把明显该做的事做掉，再把改了什么摊开给他看。
 * 宁可少猜（漏掉只影响体验），也不要猜错（改坏数据 = 信任崩塌）。
 */
export function suggestRules(ds: Dataset): Rule[] {
  const rules: Rule[] = [];
  let n = 0;
  const id = (prefix: string): string => `auto-${prefix}-${++n}`;

  for (const col of ds.columns.slice(0, 30)) {
    rules.push({ id: id("trim"), type: "trim", column: col });
  }

  rules.push({ id: id("empty"), type: "dropEmptyRows" });
  rules.push({ id: id("emptycol"), type: "dropEmptyColumns" });

  for (const col of ds.columns) {
    if (/date|day|_at$|time/i.test(col)) {
      rules.push({ id: id("date"), type: "normalizeDates", column: col });
    }
    if (/amount|total|price|cost|qty|quantity|count|revenue|balance/i.test(col)) {
      rules.push({ id: id("num"), type: "coerceNumbers", column: col });
    }
  }

  rules.push({ id: id("dedupe"), type: "dedupe" });
  return rules;
}

/** 给界面用的一句人话总结 */
export function summarize(ds: Dataset): string {
  return `${ds.columns.length} 列 · ${ds.rows.length} 行`;
}
