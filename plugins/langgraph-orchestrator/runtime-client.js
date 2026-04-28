export class LangGraphRuntimeClient {
  constructor(host, port) {
    this.baseUrl = `http://${host}:${port}`;
  }

  async request(path, method = 'GET', body, timeoutMs = 8000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  fireAndForget(path, body, timeoutMs, log, label) {
    this.request(path, 'POST', body, timeoutMs)
      .then((result) => {
        log.info(`langgraph-orchestrator [${label}]: OK ${JSON.stringify(result)}`);
      })
      .catch((error) => {
        log.warn?.(`langgraph-orchestrator [${label}]: ${String(error)}`);
      });
  }
}
