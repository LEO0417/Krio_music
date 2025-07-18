// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {}
  
  observe(target: Element): void {}
  unobserve(target: Element): void {}
  disconnect(): void {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(callback: ResizeObserverCallback) {}
  
  observe(target: Element): void {}
  unobserve(target: Element): void {}
  disconnect(): void {}
};

// Mock requestIdleCallback
global.requestIdleCallback = (callback: IdleRequestCallback, options?: IdleRequestOptions) => {
  return setTimeout(callback, 1);
};

global.cancelIdleCallback = (id: number) => {
  clearTimeout(id);
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock HTMLMediaElement methods
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  writable: true,
  value: jest.fn().mockImplementation(() => Promise.resolve()),
});

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(HTMLMediaElement.prototype, 'load', {
  writable: true,
  value: jest.fn(),
});

// Mock URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: jest.fn(() => 'mock-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: jest.fn(),
});

// Mock performance.mark and performance.measure
Object.defineProperty(performance, 'mark', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(performance, 'measure', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(performance, 'getEntriesByName', {
  writable: true,
  value: jest.fn(() => [{ duration: 100 }]),
});

Object.defineProperty(performance, 'clearMarks', {
  writable: true,
  value: jest.fn(),
});

Object.defineProperty(performance, 'clearMeasures', {
  writable: true,
  value: jest.fn(),
});

// Mock console methods in test environment
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
  
  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('componentWillReceiveProps has been renamed')
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// Custom matcher for testing styled-components
expect.extend({
  toHaveStyleRule(received, property, value) {
    const pass = received.style[property] === value;
    
    return {
      pass,
      message: () =>
        pass
          ? `Expected element not to have style property ${property} with value ${value}`
          : `Expected element to have style property ${property} with value ${value}`,
    };
  },
});

// Global test utilities
global.testUtils = {
  // Helper to create mock events
  createMockEvent: (type: string, properties = {}) => ({
    type,
    preventDefault: jest.fn(),
    stopPropagation: jest.fn(),
    target: {
      value: '',
      ...properties,
    },
    currentTarget: {
      value: '',
      ...properties,
    },
  }),
  
  // Helper to create mock file
  createMockFile: (name: string, size: number, type: string) => ({
    name,
    size,
    type,
    lastModified: Date.now(),
  }),
  
  // Helper to wait for async operations
  waitFor: async (condition: () => boolean, timeout = 1000) => {
    const startTime = Date.now();
    
    while (!condition() && Date.now() - startTime < timeout) {
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    if (!condition()) {
      throw new Error(`Condition not met within ${timeout}ms`);
    }
  },
};

// Type declarations for custom matchers
declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveStyleRule(property: string, value: string): R;
    }
  }
  
  interface Window {
    testUtils: {
      createMockEvent: (type: string, properties?: any) => any;
      createMockFile: (name: string, size: number, type: string) => any;
      waitFor: (condition: () => boolean, timeout?: number) => Promise<void>;
    };
  }
  
  var testUtils: {
    createMockEvent: (type: string, properties?: any) => any;
    createMockFile: (name: string, size: number, type: string) => any;
    waitFor: (condition: () => boolean, timeout?: number) => Promise<void>;
  };
}