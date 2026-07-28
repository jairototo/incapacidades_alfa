import '@testing-library/jest-dom/vitest';

// jsdom does not implement ResizeObserver, which recharts' ResponsiveContainer
// relies on to compute chart dimensions. Without this, ResponsiveContainer never
// receives a positive width/height and refuses to render its children in tests.
class ResizeObserverMock implements ResizeObserver {
  private readonly callback: ResizeObserverCallback;

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  observe(target: Element) {
    this.callback(
      [{ target, contentRect: { width: 800, height: 300 } } as ResizeObserverEntry],
      this,
    );
  }

  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;
