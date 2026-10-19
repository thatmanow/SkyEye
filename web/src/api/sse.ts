/** POST + SSE 流式请求（识图追问 / 多智能体股票分析） */
export async function ssePost(
  url: string,
  body: any,
  onEvent: (data: any) => void,
  signal?: AbortSignal,
) {
  const token = localStorage.getItem('tyt_access_token')
  const resp = await fetch(`/api/v1${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  })
  if (!resp.ok || !resp.body) {
    let msg = `请求失败（${resp.status}）`
    try {
      const j = await resp.json()
      if (j?.message) msg = j.message
    } catch { /* 非 JSON 错误体 */ }
    throw new Error(msg)
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const parts = buf.split('\n\n')
    buf = parts.pop() ?? ''
    for (const part of parts) {
      const line = part.split('\n').find((l) => l.startsWith('data:'))
      if (!line) continue
      const payload = line.slice(5).trim()
      if (!payload) continue
      try { onEvent(JSON.parse(payload)) } catch { /* 忽略非 JSON 行 */ }
    }
  }
}
