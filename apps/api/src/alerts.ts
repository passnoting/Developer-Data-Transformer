import type { Env } from "./types.ts";

/**
 * 邮件告警。v0.1 只接 Resend；没配 key 就打到日志，保证本地开发不阻塞。
 * 注意：告警是产品的核心承诺（“坏了你知道”），上线前必须做失败重试与去重。
 */
export async function sendEmail(
  env: Env,
  to: string,
  subject: string,
  body: string,
): Promise<boolean> {
  if (!env.RESEND_API_KEY) {
    console.log(`[alert:no-key] ${to} | ${subject}\n${body}`);
    return false;
  }

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: env.ALERT_FROM,
      to: [to],
      subject,
      text: body,
    }),
  });

  if (!res.ok) {
    console.error(`[alert:failed] ${res.status} ${await res.text()}`);
    return false;
  }
  return true;
}

/** 给管道所属 workspace 的邮箱发告警；收件人为空时只记日志。 */
export async function sendAlert(
  env: Env,
  to: string | null,
  msg: { subject: string; body: string },
): Promise<void> {
  if (!to) {
    console.log(`[alert:no-recipient] ${msg.subject}\n${msg.body}`);
    return;
  }
  await sendEmail(env, to, msg.subject, msg.body);
}
