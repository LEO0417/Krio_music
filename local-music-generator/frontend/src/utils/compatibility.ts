// Browser compatibility utilities

export interface BrowserInfo {
  name: string;
  version: string;
  os: string;
  isMobile: boolean;
  isSupported: boolean;
  features: FeatureSupport;
}

export interface FeatureSupport {
  webAudio: boolean;
  mediaRecorder: boolean;
  serviceWorker: boolean;
  indexedDB: boolean;
  localStorage: boolean;
  sessionStorage: boolean;
  fetch: boolean;
  promises: boolean;
  arrow: boolean;
  async: boolean;
  modules: boolean;
  css: {
    grid: boolean;
    flexbox: boolean;
    customProperties: boolean;
    transitions: boolean;
    animations: boolean;
  };
  audio: {
    mp3: boolean;
    wav: boolean;
    ogg: boolean;
    flac: boolean;
    m4a: boolean;
  };
}

// Detect browser information
export function detectBrowser(): BrowserInfo {
  const userAgent = navigator.userAgent;
  const name = getBrowserName(userAgent);
  const version = getBrowserVersion(userAgent, name);
  const os = getOperatingSystem(userAgent);
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
  const features = checkFeatureSupport();
  const isSupported = checkBrowserSupport(name, version, features);

  return {
    name,
    version,
    os,
    isMobile,
    isSupported,
    features,
  };
}

function getBrowserName(userAgent: string): string {
  if (userAgent.includes('Chrome')) return 'Chrome';
  if (userAgent.includes('Firefox')) return 'Firefox';
  if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) return 'Safari';
  if (userAgent.includes('Edge')) return 'Edge';
  if (userAgent.includes('Opera')) return 'Opera';
  if (userAgent.includes('MSIE') || userAgent.includes('Trident')) return 'Internet Explorer';
  return 'Unknown';
}

function getBrowserVersion(userAgent: string, browserName: string): string {
  const patterns: { [key: string]: RegExp } = {
    'Chrome': /Chrome\/(\d+)/,
    'Firefox': /Firefox\/(\d+)/,
    'Safari': /Version\/(\d+)/,
    'Edge': /Edge\/(\d+)/,
    'Opera': /Opera\/(\d+)/,
    'Internet Explorer': /MSIE (\d+)/,
  };

  const pattern = patterns[browserName];
  if (!pattern) return 'Unknown';

  const match = userAgent.match(pattern);
  return match ? match[1] : 'Unknown';
}

function getOperatingSystem(userAgent: string): string {
  if (userAgent.includes('Windows')) return 'Windows';
  if (userAgent.includes('Mac OS')) return 'macOS';
  if (userAgent.includes('Linux')) return 'Linux';
  if (userAgent.includes('Android')) return 'Android';
  if (userAgent.includes('iOS')) return 'iOS';
  return 'Unknown';
}

function checkFeatureSupport(): FeatureSupport {
  return {
    webAudio: 'AudioContext' in window || 'webkitAudioContext' in window,
    mediaRecorder: 'MediaRecorder' in window,
    serviceWorker: 'serviceWorker' in navigator,
    indexedDB: 'indexedDB' in window,
    localStorage: 'localStorage' in window,
    sessionStorage: 'sessionStorage' in window,
    fetch: 'fetch' in window,
    promises: 'Promise' in window,
    arrow: checkArrowFunctionSupport(),
    async: checkAsyncAwaitSupport(),
    modules: 'import' in document.createElement('script'),
    css: {
      grid: CSS.supports('display', 'grid'),
      flexbox: CSS.supports('display', 'flex'),
      customProperties: CSS.supports('--custom', 'property'),
      transitions: CSS.supports('transition', 'all 0.3s ease'),
      animations: CSS.supports('animation', 'slide 1s ease'),
    },
    audio: checkAudioSupport(),
  };
}

function checkArrowFunctionSupport(): boolean {
  try {
    eval('() => {}');
    return true;
  } catch {
    return false;
  }
}

function checkAsyncAwaitSupport(): boolean {
  try {
    eval('async function test() { await Promise.resolve(); }');
    return true;
  } catch {
    return false;
  }
}

function checkAudioSupport(): FeatureSupport['audio'] {
  const audio = document.createElement('audio');
  
  return {
    mp3: audio.canPlayType('audio/mpeg') !== '',
    wav: audio.canPlayType('audio/wav') !== '',
    ogg: audio.canPlayType('audio/ogg') !== '',
    flac: audio.canPlayType('audio/flac') !== '',
    m4a: audio.canPlayType('audio/mp4') !== '',
  };
}

function checkBrowserSupport(name: string, version: string, features: FeatureSupport): boolean {
  const minVersions: { [key: string]: number } = {
    'Chrome': 70,
    'Firefox': 65,
    'Safari': 12,
    'Edge': 79,
    'Opera': 57,
  };

  const versionNumber = parseInt(version, 10);
  const minVersion = minVersions[name];

  if (!minVersion) return false;
  if (versionNumber < minVersion) return false;

  // Check essential features
  const essentialFeatures = [
    features.fetch,
    features.promises,
    features.localStorage,
    features.css.flexbox,
    features.audio.mp3,
  ];

  return essentialFeatures.every(feature => feature);
}

// Performance testing utilities
export class PerformanceTest {
  private results: { [key: string]: number } = {};

  async testRenderPerformance(iterations: number = 100): Promise<number> {
    const startTime = performance.now();
    
    for (let i = 0; i < iterations; i++) {
      const div = document.createElement('div');
      div.innerHTML = `<span>Test ${i}</span>`;
      document.body.appendChild(div);
      document.body.removeChild(div);
    }
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    this.results.renderPerformance = duration;
    return duration;
  }

  async testJavaScriptPerformance(): Promise<number> {
    const startTime = performance.now();
    
    // CPU-intensive task
    let result = 0;
    for (let i = 0; i < 1000000; i++) {
      result += Math.sqrt(i);
    }
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    this.results.jsPerformance = duration;
    return duration;
  }

  async testMemoryUsage(): Promise<number> {
    if (!('memory' in performance)) return 0;
    
    const memory = (performance as any).memory;
    const usage = memory.usedJSHeapSize / memory.totalJSHeapSize;
    
    this.results.memoryUsage = usage;
    return usage;
  }

  async testNetworkSpeed(): Promise<number> {
    const startTime = performance.now();
    
    try {
      // Test with a small image
      const response = await fetch('data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7');
      await response.blob();
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      this.results.networkSpeed = duration;
      return duration;
    } catch (error) {
      return -1;
    }
  }

  getResults(): { [key: string]: number } {
    return { ...this.results };
  }

  async runAllTests(): Promise<{ [key: string]: number }> {
    await this.testRenderPerformance();
    await this.testJavaScriptPerformance();
    await this.testMemoryUsage();
    await this.testNetworkSpeed();
    
    return this.getResults();
  }
}

// Device capability detection
export function detectDeviceCapabilities() {
  return {
    screen: {
      width: screen.width,
      height: screen.height,
      pixelRatio: window.devicePixelRatio || 1,
      colorDepth: screen.colorDepth,
    },
    hardware: {
      cores: navigator.hardwareConcurrency || 1,
      memory: (navigator as any).deviceMemory || 'unknown',
      connection: getConnectionInfo(),
    },
    input: {
      touch: 'ontouchstart' in window,
      mouse: window.matchMedia('(pointer: fine)').matches,
      keyboard: !('ontouchstart' in window),
    },
    sensors: {
      accelerometer: 'DeviceMotionEvent' in window,
      gyroscope: 'DeviceOrientationEvent' in window,
      geolocation: 'geolocation' in navigator,
    },
  };
}

function getConnectionInfo() {
  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
  
  if (!connection) return { type: 'unknown', speed: 'unknown' };
  
  return {
    type: connection.effectiveType || connection.type || 'unknown',
    speed: connection.downlink || 'unknown',
    rtt: connection.rtt || 'unknown',
  };
}

// Accessibility testing utilities
export function checkAccessibilitySupport() {
  return {
    screenReader: {
      ariaSupported: 'ariaLabel' in document.createElement('div'),
      roleSupported: 'role' in document.createElement('div'),
    },
    keyboard: {
      tabIndex: 'tabIndex' in document.createElement('div'),
      keyboardEvents: 'onkeydown' in document.createElement('div'),
    },
    colorContrast: {
      highContrastMode: window.matchMedia('(prefers-contrast: high)').matches,
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    },
  };
}

// Generate compatibility report
export async function generateCompatibilityReport() {
  const browser = detectBrowser();
  const device = detectDeviceCapabilities();
  const accessibility = checkAccessibilitySupport();
  const performance = new PerformanceTest();
  const performanceResults = await performance.runAllTests();
  
  return {
    browser,
    device,
    accessibility,
    performance: performanceResults,
    timestamp: new Date().toISOString(),
  };
}

// Polyfill utilities
export function loadPolyfills() {
  const polyfills = [];
  
  // Promise polyfill
  if (!window.Promise) {
    polyfills.push(loadScript('https://cdn.jsdelivr.net/npm/es6-promise@4/dist/es6-promise.auto.min.js'));
  }
  
  // Fetch polyfill
  if (!window.fetch) {
    polyfills.push(loadScript('https://cdn.jsdelivr.net/npm/whatwg-fetch@3.6.2/dist/fetch.umd.js'));
  }
  
  // IntersectionObserver polyfill
  if (!window.IntersectionObserver) {
    polyfills.push(loadScript('https://cdn.jsdelivr.net/npm/intersection-observer@0.12.0/intersection-observer.js'));
  }
  
  // ResizeObserver polyfill
  if (!window.ResizeObserver) {
    polyfills.push(loadScript('https://cdn.jsdelivr.net/npm/resize-observer-polyfill@1.5.1/dist/ResizeObserver.global.js'));
  }
  
  return Promise.all(polyfills);
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve();
    script.onerror = reject;
    document.head.appendChild(script);
  });
}