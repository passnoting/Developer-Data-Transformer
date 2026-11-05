/**
 * Creem webhook 验签。
 *
 * Creem 用 HMAC-SHA256 对「原始请求体」签名，放在 `creem-signature` 头里（hex）。
 * —— 上线前请对照官方文档确认头名与编码；这里只实现最常见的形态，并在
 *    验签失败时不写库（宁可漏记，不可被伪造的 webhook 改订阅状态）。
 */
export async function verifySignature(
  rawBody: string,
  signature: string | null,
  secret: string | undefined,
): Promise<boolean> {
  if (!secret) {
    console.warn("[billing] CREEM_WEBHOOK_SECRET 未配置，拒绝所有 webhook");
    return false;
  }
  if (!signature) return false;

  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(rawBody));
  const expected = [...new Uint8Array(mac)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  // 长度不同直接 false；长度相同再逐字符比较（时间侧信道风险可接受，TODO 用常量时间比较）
  if (expected.length !== signature.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ signature.charCodeAt(i);
  }
  return diff === 0;
}

/** Creem 事件 → 内部订阅状态 */
export function mapEventToStatus(eventType: string): {
  status: "active" | "past_due" | "canceled";
} | null {
  switch (eventType) {
    case "subscription.active":
    case "subscription.paid":
    case "subscription.renewed":
      return { status: "active" };
    case "subscription.past_due":
    case "subscription.payment_failed":
      return { status: "past_due" };
    case "subscription.canceled":
    case "subscription.expired":
      return { status: "canceled" };
    default:
      return null;
  }
}

export interface CreemEvent {
  type: string;
  data?: {
    customer?: { id?: string; email?: string };
    subscription?: { id?: string; status?: string; product_id?: string };
    metadata?: { workspace_id?: string };
    current_period_end?: string;
  };
}

export function workspaceIdFromEvent(event: CreemEvent): string | null {
  return event.data?.metadata?.workspace_id ?? null;
}
