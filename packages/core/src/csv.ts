import type { CellValue, Dataset, Row } from "./types.ts";

/**
 * 极简 RFC4180 CSV 解析：支持引号、转义引号、字段内换行、CRLF。
 * 不做类型推断 —— 类型转换交给清洗规则，保持“解析”和“改数据”两件事分开。
 * 放在 core 里的原因：浏览器内清洗和 Worker 端定时跑必须用同一份解析逻辑。
 */
export function parseCsv(text: string): Dataset {
  const rows: string[][] = [];
  let field = "";
  let row: string[] = [];
  let inQuotes = false;

  // 去掉 BOM（Excel 导出的 UTF-8 CSV 几乎都带，不去掉第一列名会变成 "\uFEFForder_id"）
  const src = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;

  for (let i = 0; i < src.length; i++) {
    const ch = src[i];

    if (inQuotes) {
      if (ch === '"') {
        if (src[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
      continue;
    }

    if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (ch === "\r") {
      // 交给 \n 处理
    } else {
      field += ch;
    }
  }

  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  if (rows.length === 0) return { columns: [], rows: [] };

  const header = rows[0].map((h, i) => h.trim() || `column_${i + 1}`);
  const data: Row[] = [];

  for (const cells of rows.slice(1)) {
    if (cells.every((c) => c.trim() === "")) continue;
    const obj: Row = {};
    header.forEach((name, i) => {
      obj[name] = (cells[i] ?? null) as CellValue;
    });
    data.push(obj);
  }

  return { columns: header, rows: data };
}

/** 反向：表 → CSV（导出用，带 BOM 让 Excel 正确识别 UTF-8） */
export function toCsv(dataset: Dataset, withBom = true): string {
  const esc = (v: unknown): string => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [dataset.columns.map(esc).join(",")];
  for (const row of dataset.rows) {
    lines.push(dataset.columns.map((c) => esc(row[c])).join(","));
  }
  return (withBom ? "\uFEFF" : "") + lines.join("\r\n");
}
