import { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import { debounce, throttle, PerformanceTracker } from '@/utils/performance';

// Hook for performance monitoring
export const usePerformanceMonitor = (componentName: string) => {
  const renderCount = useRef(0);
  const mountTime = useRef(Date.now());
  
  useEffect(() => {
    renderCount.current++;
    
    return () => {
      const lifeTime = Date.now() - mountTime.current;
      console.log(`${componentName} stats:`, {
        renderCount: renderCount.current,
        lifeTime: `${lifeTime}ms`,
      });
    };
  });
  
  const trackOperation = useCallback((operationName: string, operation: () => void) => {
    PerformanceTracker.startMeasurement(`${componentName}-${operationName}`);
    operation();
    const duration = PerformanceTracker.endMeasurement(`${componentName}-${operationName}`);
    
    if (duration > 100) {
      console.warn(`Slow operation detected: ${componentName}-${operationName} took ${duration}ms`);
    }
  }, [componentName]);
  
  return {
    renderCount: renderCount.current,
    trackOperation,
  };
};

// Hook for debounced values
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const handler = debounce(() => {
      setDebouncedValue(value);
    }, delay);
    
    handler();
    
    return () => {
      // Cleanup if needed
    };
  }, [value, delay]);
  
  return debouncedValue;
};

// Hook for throttled callbacks
export const useThrottledCallback = <T extends (...args: any[]) => void>(
  callback: T,
  delay: number
): T => {
  const throttledCallback = useMemo(
    () => throttle(callback, delay),
    [callback, delay]
  );
  
  return throttledCallback;
};

// Hook for memoized expensive computations
export const useMemoizedComputation = <T>(
  computation: () => T,
  dependencies: any[]
): T => {
  return useMemo(() => {
    const start = performance.now();
    const result = computation();
    const end = performance.now();
    
    if (end - start > 50) {
      console.warn(`Expensive computation detected: ${end - start}ms`);
    }
    
    return result;
  }, dependencies);
};

// Hook for virtual scrolling
export const useVirtualScroll = (
  itemCount: number,
  itemHeight: number,
  containerHeight: number
) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [startIndex, setStartIndex] = useState(0);
  const [endIndex, setEndIndex] = useState(0);
  
  useEffect(() => {
    const overscan = 5;
    const visibleStart = Math.floor(scrollTop / itemHeight);
    const visibleEnd = Math.min(
      visibleStart + Math.ceil(containerHeight / itemHeight),
      itemCount
    );
    
    setStartIndex(Math.max(0, visibleStart - overscan));
    setEndIndex(Math.min(itemCount, visibleEnd + overscan));
  }, [scrollTop, itemHeight, containerHeight, itemCount]);
  
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);
  
  return {
    startIndex,
    endIndex,
    offsetY: startIndex * itemHeight,
    totalHeight: itemCount * itemHeight,
    handleScroll,
  };
};

// Hook for intersection observer (lazy loading)
export const useIntersectionObserver = (
  options?: IntersectionObserverInit
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const ref = useRef<HTMLElement>(null);
  
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true);
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options,
      }
    );
    
    observer.observe(element);
    
    return () => observer.disconnect();
  }, [hasIntersected, options]);
  
  return { ref, isIntersecting, hasIntersected };
};

// Hook for image lazy loading
export const useImageLazyLoading = (src: string) => {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { ref, hasIntersected } = useIntersectionObserver();
  
  useEffect(() => {
    if (!hasIntersected) return;
    
    setIsLoading(true);
    setError(null);
    
    const img = new Image();
    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
    };
    img.onerror = () => {
      setError('Failed to load image');
      setIsLoading(false);
    };
    img.src = src;
  }, [src, hasIntersected]);
  
  return { ref, imageSrc, isLoading, error };
};

// Hook for component render optimization
export const useRenderOptimization = (deps: any[]) => {
  const renderCount = useRef(0);
  const prevDeps = useRef<any[]>([]);
  
  const shouldRender = useMemo(() => {
    const hasChanged = deps.some((dep, index) => {
      const prevDep = prevDeps.current[index];
      
      if (typeof dep === 'object' && dep !== null) {
        return JSON.stringify(dep) !== JSON.stringify(prevDep);
      }
      
      return dep !== prevDep;
    });
    
    if (hasChanged) {
      renderCount.current++;
      prevDeps.current = deps;
    }
    
    return hasChanged;
  }, deps);
  
  return {
    shouldRender,
    renderCount: renderCount.current,
  };
};

// Hook for memory usage monitoring
export const useMemoryMonitor = () => {
  const [memoryUsage, setMemoryUsage] = useState(0);
  
  useEffect(() => {
    if (!('memory' in performance)) return;
    
    const updateMemoryUsage = () => {
      const memory = (performance as any).memory;
      const usage = memory.usedJSHeapSize / memory.totalJSHeapSize;
      setMemoryUsage(usage);
    };
    
    updateMemoryUsage();
    const interval = setInterval(updateMemoryUsage, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  return memoryUsage;
};

// Hook for idle callback
export const useIdleCallback = (
  callback: () => void,
  dependencies: any[]
) => {
  useEffect(() => {
    const idleCallback = () => {
      if ('requestIdleCallback' in window) {
        (window as any).requestIdleCallback(callback);
      } else {
        setTimeout(callback, 1);
      }
    };
    
    idleCallback();
  }, dependencies);
};

// Hook for component size monitoring
export const useComponentSize = () => {
  const ref = useRef<HTMLElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    
    const resizeObserver = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ width, height });
    });
    
    resizeObserver.observe(element);
    
    return () => resizeObserver.disconnect();
  }, []);
  
  return { ref, size };
};

