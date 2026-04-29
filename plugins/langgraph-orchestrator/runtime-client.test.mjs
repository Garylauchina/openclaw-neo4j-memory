import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { once } from 'node:events';
import { LangGraphRuntimeClient } from './runtime-client.js';

async function startMockServer(routes) {
  const requests = [];
  const server = http.createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const rawBody = Buffer.concat(chunks).toString('utf8');
    const body = rawBody ? JSON.parse(rawBody) : undefined;
    requests.push({ method: req.method, url: req.url, body });

    const handler = routes[`${req.method} ${req.url}`];
    if (!handler) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'not found' }));
      return;
    }

    const { status = 200, payload = {} } = await handler({ req, body, requests });
    res.writeHead(status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(payload));
  });

  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const address = server.address();
  return {
    server,
    requests,
    port: address.port,
    async close() {
      server.close();
      await once(server, 'close');
    },
  };
}

test('runtime client performs before-agent-start request against mock LangGraph runtime', async () => {
  const mock = await startMockServer({
    'POST /runtime/before-agent-start': async ({ body }) => ({
      payload: {
        prepend_context: `context for ${body.query}`,
        planning_hints: ['hint-a', 'hint-b'],
      },
    }),
  });

  try {
    const client = new LangGraphRuntimeClient('127.0.0.1', mock.port);
    const result = await client.request('/runtime/before-agent-start', 'POST', {
      graph_id: 'default',
      session_id: 's1',
      channel: 'telegram',
      user_id: 'u1',
      query: 'hello',
    });

    assert.equal(result.prepend_context, 'context for hello');
    assert.deepEqual(result.planning_hints, ['hint-a', 'hint-b']);
    assert.equal(mock.requests.length, 1);
    assert.equal(mock.requests[0].body.query, 'hello');
  } finally {
    await mock.close();
  }
});

test('runtime client fireAndForget logs success for async reflection endpoint', async () => {
  const mock = await startMockServer({
    'POST /runtime/agent-end': async ({ body }) => ({
      payload: {
        event_written: true,
        summary_written: true,
        reflection_scheduled: body.success === true,
      },
    }),
  });

  const infos = [];
  const warns = [];
  const logger = { info: (msg) => infos.push(msg), warn: (msg) => warns.push(msg) };

  try {
    const client = new LangGraphRuntimeClient('127.0.0.1', mock.port);
    client.fireAndForget('/runtime/agent-end', { success: true }, 2000, logger, 'agent_end');
    await new Promise((resolve) => setTimeout(resolve, 50));

    assert.equal(mock.requests.length, 1);
    assert.equal(warns.length, 0);
    assert.equal(infos.length, 1);
    assert.match(infos[0], /agent_end/);
    assert.match(infos[0], /reflection_scheduled/);
  } finally {
    await mock.close();
  }
});

test('runtime client surfaces non-2xx responses from mock LangGraph runtime', async () => {
  const mock = await startMockServer({
    'GET /health': async () => ({ status: 503, payload: { error: 'unavailable' } }),
  });

  try {
    const client = new LangGraphRuntimeClient('127.0.0.1', mock.port);
    await assert.rejects(() => client.request('/health', 'GET'), /HTTP 503/);
  } finally {
    await mock.close();
  }
});
