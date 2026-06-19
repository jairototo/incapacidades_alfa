/**
 * Tests for src/lib/api.ts
 *
 * Strategy:
 * - The module keeps module-level mutable state (`isRefreshing`, `queue`).
 *   We reset it between tests with `vi.resetModules()` + dynamic `import()`.
 * - Transport is controlled by overriding `api.defaults.adapter` so we don't
 *   need a real HTTP server.
 * - The refresh call goes through the bare `axios.post`, which we spy on.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a minimal AxiosResponse shape for the adapter mock. */
function makeAxiosResponse(
  data: unknown,
  status: number,
  config: InternalAxiosRequestConfig,
): AxiosResponse {
  return {
    data,
    status,
    statusText: status === 200 ? 'OK' : 'Unauthorized',
    headers: {},
    config,
  };
}

/** Build a minimal AxiosError for 401 responses. */
function make401Error(config: InternalAxiosRequestConfig) {
  const err = Object.assign(new Error('401'), {
    isAxiosError: true,
    response: {
      data: { detail: 'Unauthorized' },
      status: 401,
      statusText: 'Unauthorized',
      headers: {},
      config,
    },
    config,
    code: 'ERR_BAD_RESPONSE',
  });
  return err;
}

// ---------------------------------------------------------------------------
// (a) Request interceptor attaches / omits Authorization header
// ---------------------------------------------------------------------------

describe('(a) request interceptor', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('attaches Bearer token when access_token is in localStorage', async () => {
    vi.resetModules();
    const { default: api } = await import('@/lib/api');

    localStorage.setItem('access_token', 'MY_TOKEN');

    let capturedAuth: string | undefined;

    // Override adapter to capture the header and return success
    api.defaults.adapter = vi.fn(async (config: InternalAxiosRequestConfig) => {
      capturedAuth = config.headers?.Authorization as string | undefined;
      return makeAxiosResponse({ ok: true }, 200, config);
    });

    await api.get('/some-endpoint');

    expect(capturedAuth).toBe('Bearer MY_TOKEN');
  });

  it('omits Authorization header when access_token is absent', async () => {
    vi.resetModules();
    const { default: api } = await import('@/lib/api');

    // Ensure no token in storage
    localStorage.removeItem('access_token');

    let capturedAuth: string | null | undefined = 'SENTINEL';

    api.defaults.adapter = vi.fn(async (config: InternalAxiosRequestConfig) => {
      capturedAuth = (config.headers?.Authorization as string | undefined) ?? null;
      return makeAxiosResponse({ ok: true }, 200, config);
    });

    await api.get('/some-endpoint');

    expect(capturedAuth).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// (b) 401 → silent refresh → retry with new token
// ---------------------------------------------------------------------------

describe('(b) 401 triggers refresh and retries original request', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('calls refresh endpoint and retries with new Bearer token', async () => {
    vi.resetModules();
    const { default: api } = await import('@/lib/api');

    localStorage.setItem('access_token', 'OLD_TOKEN');
    localStorage.setItem('refresh_token', 'MY_REFRESH');

    // Spy on bare axios.post (used for the refresh call)
    const refreshSpy = vi.spyOn(axios, 'post').mockResolvedValueOnce({
      data: {
        access_token: 'NEW_TOKEN',
        token_type: 'bearer',
        expires_in: 900,
      },
    });

    let callCount = 0;
    let retryAuth: string | undefined;

    // First call returns 401; second call (retry) returns 200
    api.defaults.adapter = vi.fn(async (config: InternalAxiosRequestConfig) => {
      callCount += 1;
      if (callCount === 1) {
        // Simulate 401
        throw make401Error(config);
      }
      // Retry: capture auth header and succeed
      retryAuth = config.headers?.Authorization as string | undefined;
      return makeAxiosResponse({ ok: true }, 200, config);
    });

    const result = await api.get('/protected');

    expect(refreshSpy).toHaveBeenCalledTimes(1);
    expect(refreshSpy).toHaveBeenCalledWith(
      expect.stringContaining('/auth/refresh'),
      { refresh_token: 'MY_REFRESH' },
    );
    expect(retryAuth).toBe('Bearer NEW_TOKEN');
    expect(result.data).toEqual({ ok: true });
    expect(localStorage.getItem('access_token')).toBe('NEW_TOKEN');
  });
});

// ---------------------------------------------------------------------------
// (c) Two concurrent 401s trigger only ONE refresh call
// ---------------------------------------------------------------------------

describe('(c) concurrent 401s trigger only one refresh call', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('deduplicates the refresh call and resolves both original requests', async () => {
    vi.resetModules();
    const { default: api } = await import('@/lib/api');

    localStorage.setItem('access_token', 'OLD_TOKEN');
    localStorage.setItem('refresh_token', 'MY_REFRESH');

    // Refresh resolves after a micro-tick so the second 401 can queue up
    const refreshSpy = vi.spyOn(axios, 'post').mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                data: {
                  access_token: 'NEW_TOKEN',
                  token_type: 'bearer',
                  expires_in: 900,
                },
              }),
            0,
          ),
        ),
    );

    // Track call counts per logical "request" (identified by a header we set)
    const callCounts: Record<string, number> = { req1: 0, req2: 0 };

    api.defaults.adapter = vi.fn(async (config: InternalAxiosRequestConfig) => {
      // Identify which logical request this is by the URL path
      const key = (config.url ?? '').includes('req1') ? 'req1' : 'req2';
      callCounts[key] = (callCounts[key] ?? 0) + 1;

      // First call of each always returns 401
      if (callCounts[key] === 1) {
        throw make401Error(config);
      }

      // Retry call returns 200
      return makeAxiosResponse({ key }, 200, config);
    });

    // Fire both requests concurrently
    const [r1, r2] = await Promise.all([
      api.get('/protected/req1'),
      api.get('/protected/req2'),
    ]);

    expect(refreshSpy).toHaveBeenCalledTimes(1);
    expect(r1.data).toEqual({ key: 'req1' });
    expect(r2.data).toEqual({ key: 'req2' });
  });
});
