// Performance optimization utilities for the frontend

// Debounce function to limit rapid function calls
export function debounce<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return function(this: any, ...args: Parameters<T>) {
    const context = this;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(context, args), delay);
  };
}

// Throttle function to limit function calls to once per interval
export function throttle<T extends (...args: any[]) => void>(
  func: T,
  interval: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;
  
  return function(this: any, ...args: Parameters<T>) {
    const now = Date.now();
    if (now - lastCall >= interval) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}

// Memoization utility for expensive computations
export function memoize<T extends (...args: any[]) => any>(
  fn: T,
  getKey?: (...args: Parameters<T>) => string
): T {
  const cache = new Map<string, ReturnType<T>>();
  
  return ((...args: Parameters<T>) => {
    const key = getKey ? getKey(...args) : JSON.stringify(args);
    
    if (cache.has(key)) {
      return cache.get(key);
    }
    
    const result = fn(...args);
    cache.set(key, result);
    return result;
  }) as T;
}

// Lazy loading utility
export function lazy<T>(factory: () => T): () => T {
  let cached: T | null = null;
  let isInitialized = false;
  
  return () => {
    if (!isInitialized) {
      cached = factory();
      isInitialized = true;
    }
    return cached!;
  };
}

// Virtual scrolling utility for large lists
export interface VirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export function calculateVirtualScrollRange(
  scrollTop: number,
  totalItems: number,
  options: VirtualScrollOptions
): { start: number; end: number; offsetY: number } {
  const { itemHeight, containerHeight, overscan = 5 } = options;
  
  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight),
    totalItems
  );
  
  const start = Math.max(0, visibleStart - overscan);
  const end = Math.min(totalItems, visibleEnd + overscan);
  
  return {
    start,
    end,
    offsetY: start * itemHeight,
  };
}

// Image lazy loading utility
export function createImageObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options?: IntersectionObserverInit
): IntersectionObserver {
  const defaultOptions: IntersectionObserverInit = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    ...options,
  };
  
  return new IntersectionObserver(callback, defaultOptions);
}

// Bundle splitting utility
export function loadChunk<T>(
  importFn: () => Promise<{ default: T }>
): Promise<T> {
  return importFn().then(module => module.default);
}

// Memory management utilities
export class MemoryMonitor {
  private static instance: MemoryMonitor;
  private observers: Set<(usage: number) => void> = new Set();
  private intervalId: NodeJS.Timeout | null = null;
  
  static getInstance(): MemoryMonitor {
    if (!MemoryMonitor.instance) {
      MemoryMonitor.instance = new MemoryMonitor();
    }
    return MemoryMonitor.instance;
  }
  
  startMonitoring(intervalMs: number = 5000): void {
    if (this.intervalId) return;
    
    this.intervalId = setInterval(() => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usage = memory.usedJSHeapSize / memory.totalJSHeapSize;
        this.observers.forEach(observer => observer(usage));
      }
    }, intervalMs);
  }
  
  stopMonitoring(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
  
  addObserver(observer: (usage: number) => void): void {
    this.observers.add(observer);
  }
  
  removeObserver(observer: (usage: number) => void): void {
    this.observers.delete(observer);
  }
}

// Performance measurement utilities
export class PerformanceTracker {
  private static measurements: Map<string, number[]> = new Map();
  
  static startMeasurement(name: string): void {
    performance.mark(`${name}-start`);
  }
  
  static endMeasurement(name: string): number {
    const startMark = `${name}-start`;
    const endMark = `${name}-end`;
    
    performance.mark(endMark);
    performance.measure(name, startMark, endMark);
    
    const measure = performance.getEntriesByName(name, 'measure')[0];
    const duration = measure.duration;
    
    // Store measurement
    if (!this.measurements.has(name)) {
      this.measurements.set(name, []);
    }
    this.measurements.get(name)!.push(duration);
    
    // Clean up marks and measures
    performance.clearMarks(startMark);
    performance.clearMarks(endMark);
    performance.clearMeasures(name);
    
    return duration;
  }
  
  static getAverageDuration(name: string): number {
    const measurements = this.measurements.get(name) || [];
    if (measurements.length === 0) return 0;
    
    const sum = measurements.reduce((a, b) => a + b, 0);
    return sum / measurements.length;
  }
  
  static getStatistics(name: string): {
    count: number;
    average: number;
    min: number;
    max: number;
  } {
    const measurements = this.measurements.get(name) || [];
    
    if (measurements.length === 0) {
      return { count: 0, average: 0, min: 0, max: 0 };
    }
    
    const sum = measurements.reduce((a, b) => a + b, 0);
    const average = sum / measurements.length;
    const min = Math.min(...measurements);
    const max = Math.max(...measurements);
    
    return { count: measurements.length, average, min, max };
  }
  
  static clearMeasurements(name?: string): void {
    if (name) {
      this.measurements.delete(name);
    } else {
      this.measurements.clear();
    }
  }
}

// Component optimization utilities
export function shouldComponentUpdate<T extends Record<string, any>>(
  prevProps: T,
  nextProps: T,
  keys?: (keyof T)[]
): boolean {
  const propsToCheck = keys || Object.keys(nextProps);
  
  return propsToCheck.some(key => {
    const prevValue = prevProps[key];
    const nextValue = nextProps[key];
    
    // Handle primitive values
    if (typeof prevValue !== 'object' || typeof nextValue !== 'object') {
      return prevValue !== nextValue;
    }
    
    // Handle null values
    if (prevValue === null || nextValue === null) {
      return prevValue !== nextValue;
    }
    
    // Handle arrays
    if (Array.isArray(prevValue) && Array.isArray(nextValue)) {
      if (prevValue.length !== nextValue.length) return true;
      return prevValue.some((item, index) => item !== nextValue[index]);
    }
    
    // Handle objects (shallow comparison)
    const prevKeys = Object.keys(prevValue);
    const nextKeys = Object.keys(nextValue);
    
    if (prevKeys.length !== nextKeys.length) return true;
    
    return prevKeys.some(k => prevValue[k] !== nextValue[k]);
  });
}

// Animation performance utilities
export function requestIdleCallback(
  callback: () => void,
  options?: { timeout?: number }
): number {
  if ('requestIdleCallback' in window) {
    return (window as any).requestIdleCallback(callback, options);
  }
  
  // Fallback for browsers without requestIdleCallback
  return setTimeout(callback, 1);
}

export function cancelIdleCallback(id: number): void {
  if ('cancelIdleCallback' in window) {
    (window as any).cancelIdleCallback(id);
  } else {
    clearTimeout(id);
  }
}

// Resource preloading utilities
export function preloadImage(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = src;
  });
}

export function preloadAudio(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    audio.oncanplaythrough = () => resolve();
    audio.onerror = reject;
    audio.src = src;
  });
}

export function preloadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.onload = () => resolve();
    script.onerror = reject;
    script.src = src;
    document.head.appendChild(script);
  });
}