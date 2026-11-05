/**
 * 编码识别与解码。
 *
 * 为什么必须有这个文件：中国/日本用户从 Excel 导出的 CSV 大多是 GBK（GB2312/GB18030），
 * 巴西/欧洲用户可能是 windows-1252，Excel 的「Unicode 文本」是 UTF-16LE。
 * 一律按 UTF-8 解 = 满屏 ``。这是最常见的第一个 bug。
 *
 * 另外：.xlsx / .xls 不是文本。它们的文件头分别是 ZIP 和 OLE2，
 * 被当文本读就会解出 "PK\x03\x04..." 这种垃圾——必须在解析前拦住。
 */

export interface DecodedText {
  ok: true;
  text: string;
  /** 实际使用的编码，界面上要显示给用户看 */
  encoding: "utf-8" | "utf-16le" | "utf-16be" | "gb18030" | "windows-1252";
  warnings: string[];
}

export interface DecodeFailure {
  ok: false;
  reason: "zip" | "ole" | "binary";
  message: string;
}

export type DecodeResult = DecodedText | DecodeFailure;

const startsWith = (b: Uint8Array, sig: number[]): boolean =>
  sig.every((v, i) => b[i] === v);

/** ZIP（xlsx / docx / 普通 zip）：50 4B 03 04，空包是 50 4B 05 06 */
const ZIP_SIGS = [
  [0x50, 0x4b, 0x03, 0x04],
  [0x50, 0x4b, 0x05, 0x06],
  [0x50, 0x4b, 0x07, 0x08],
];
/** OLE2（老的 .xls / .doc）：D0 CF 11 E0 A1 B1 1A E1 */
const OLE_SIG = [0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1];

/** 严格解码：失败（有非法字节）就返回 null，绝不静默替换成 � */
function strictDecode(bytes: Uint8Array, label: string): string | null {
  try {
    return new TextDecoder(label, { fatal: true }).decode(bytes);
  } catch {
    return null;
  }
}

/** 控制字符占比过高 → 不是文本 */
function looksBinary(text: string): boolean {
  if (text.length === 0) return false;
  let bad = 0;
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    if (c < 0x09 || (c > 0x0d && c < 0x20)) bad++;
  }
  return bad / text.length > 0.02;
}

/**
 * 无 BOM 的 UTF-16 识别：ASCII 文本在 UTF-16 里会出现大量 0x00。
 * 偶数位为 0 → 大概率 UTF-16BE；奇数位为 0 → 大概率 UTF-16LE。
 */
function sniffUtf16(bytes: Uint8Array): "utf-16le" | "utf-16be" | null {
  const n = Math.min(bytes.length, 4000);
  if (n < 8) return null;
  let evenZero = 0;
  let oddZero = 0;
  for (let i = 0; i < n; i += 2) {
    if (bytes[i] === 0) evenZero++;
    if (i + 1 < n && bytes[i + 1] === 0) oddZero++;
  }
  const pairs = n / 2;
  if (oddZero / pairs > 0.3 && evenZero / pairs < 0.1) return "utf-16le";
  if (evenZero / pairs > 0.3 && oddZero / pairs < 0.1) return "utf-16be";
  return null;
}

export function decodeText(bytes: Uint8Array): DecodeResult {
  if (bytes.length === 0) {
    return { ok: true, text: "", encoding: "utf-8", warnings: ["文件是空的"] };
  }

  // 1) 先拦二进制容器，别让它们进入文本流程
  if (ZIP_SIGS.some((sig) => startsWith(bytes, sig))) {
    return {
      ok: false,
      reason: "zip",
      message:
        "这是 .xlsx / .zip 文件，不是 CSV。xlsx 是压缩包，不能当文本读。" +
        "请用 Excel / WPS 打开，另存为「CSV UTF-8（逗号分隔）」，再拖进来。",
    };
  }
  if (startsWith(bytes, OLE_SIG)) {
    return {
      ok: false,
      reason: "ole",
      message:
        "这是老的 .xls / .doc 格式（OLE2），不是 CSV。" +
        "请用 Excel 打开后另存为「CSV UTF-8」，再拖进来。",
    };
  }

  // 2) BOM 优先，最可靠
  let encoding: DecodedText["encoding"] | null = null;
  if (startsWith(bytes, [0xef, 0xbb, 0xbf])) encoding = "utf-8";
  else if (startsWith(bytes, [0xff, 0xfe])) encoding = "utf-16le";
  else if (startsWith(bytes, [0xfe, 0xff])) encoding = "utf-16be";

  // 3) 无 BOM 的 UTF-16 字节规律
  if (!encoding) encoding = sniffUtf16(bytes);

  const warnings: string[] = [];

  // 4) UTF-8 严格；失败再试 GB18030；最后兜底 windows-1252
  if (!encoding || encoding === "utf-8") {
    const text = strictDecode(bytes, "utf-8");
    if (text !== null) {
      return { ok: true, text: stripBom(text), encoding: "utf-8", warnings };
    }
    const gb = strictDecode(bytes, "gb18030");
    if (gb !== null) {
      warnings.push(
        "文件不是 UTF-8 编码，已按 GB18030/GBK 解码（中文 Windows 下 Excel 导出的 CSV 通常是这个编码）",
      );
      return { ok: true, text: stripBom(gb), encoding: "gb18030", warnings };
    }
    const latin = new TextDecoder("windows-1252").decode(bytes);
    if (looksBinary(latin)) {
      return {
        ok: false,
        reason: "binary",
        message: "这个文件看起来是二进制格式，不是 CSV。请确认导出的是文本 CSV。",
      };
    }
    warnings.push("无法识别编码，已按 windows-1252 解码，如果出现乱码请另存为 CSV UTF-8");
    return { ok: true, text: stripBom(latin), encoding: "windows-1252", warnings };
  }

  const text = strictDecode(bytes, encoding) ?? new TextDecoder(encoding).decode(bytes);
  if (encoding !== "utf-8") {
    warnings.push(`文件编码是 ${encoding.toUpperCase()}，已自动转换`);
  }
  return { ok: true, text: stripBom(text), encoding, warnings };
}

function stripBom(s: string): string {
  return s.charCodeAt(0) === 0xfeff ? s.slice(1) : s;
}
