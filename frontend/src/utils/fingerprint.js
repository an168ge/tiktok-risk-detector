/**
 * 浏览器指纹采集工具
 */

export class FingerprintCollector {
  /**
   * 收集所有指纹信息
   */
  static async collect() {
    const fingerprint = {
      // 基础信息
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language || navigator.userLanguage,
      languages: navigator.languages || [navigator.language],
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timezoneOffset: new Date().getTimezoneOffset(),
      
      // 屏幕信息
      screenResolution: `${screen.width}x${screen.height}`,
      availableResolution: `${screen.availWidth}x${screen.availHeight}`,
      colorDepth: screen.colorDepth,
      pixelRatio: window.devicePixelRatio || 1,
      
      // 浏览器特性
      cookiesEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack || window.doNotTrack || null,
      
      // 硬件信息
      hardwareConcurrency: navigator.hardwareConcurrency || null,
      deviceMemory: navigator.deviceMemory || null,
      maxTouchPoints: navigator.maxTouchPoints || 0,
      
      // 高级指纹
      canvasFingerprint: await this.getCanvasFingerprint(),
      webglFingerprint: this.getWebGLFingerprint(),
      audioFingerprint: await this.getAudioFingerprint(),
      fonts: await this.detectFonts(),
      plugins: this.getPlugins(),
      
      // WebRTC信息
      webrtcIps: await this.getWebRTCIPs(),
      
      // DNS信息（尝试检测）
      dnsServers: await this.getDNSServers(),
      
      // WebDriver检测
      hasWebdriver: this.detectWebDriver(),
      
      // 移动设备标志
      isMobile: /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent),
    };
    
    return fingerprint;
  }
  
  /**
   * Canvas指纹
   */
  static async getCanvasFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) return null;
      
      // 绘制文本
      const txt = 'TikTok Risk Detector <canvas> 🎨 123';
      ctx.textBaseline = 'top';
      ctx.font = '14px "Arial"';
      ctx.textBaseline = 'alphabetic';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText(txt, 2, 15);
      ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
      ctx.fillText(txt, 4, 17);
      
      // 生成指纹
      const dataURL = canvas.toDataURL();
      const hash = await this.hashString(dataURL);
      
      return hash;
    } catch (error) {
      console.error('Canvas fingerprint error:', error);
      return null;
    }
  }
  
  /**
   * WebGL指纹
   */
  static getWebGLFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      
      if (!gl) return null;
      
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (!debugInfo) return null;
      
      const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
      
      return `${vendor}~${renderer}`;
    } catch (error) {
      console.error('WebGL fingerprint error:', error);
      return null;
    }
  }
  
  /**
   * Audio指纹
   */
  static async getAudioFingerprint() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return null;
      
      const context = new AudioContext();
      const oscillator = context.createOscillator();
      const analyser = context.createAnalyser();
      const gainNode = context.createGain();
      const scriptProcessor = context.createScriptProcessor(4096, 1, 1);
      
      gainNode.gain.value = 0; // 静音
      oscillator.type = 'triangle';
      oscillator.connect(analyser);
      analyser.connect(scriptProcessor);
      scriptProcessor.connect(gainNode);
      gainNode.connect(context.destination);
      
      return new Promise((resolve) => {
        scriptProcessor.onaudioprocess = function(event) {
          const output = event.outputBuffer.getChannelData(0);
          const fingerprint = Array.from(output.slice(0, 30)).join(',');
          
          oscillator.disconnect();
          scriptProcessor.disconnect();
          analyser.disconnect();
          gainNode.disconnect();
          context.close();
          
          resolve(fingerprint);
        };
        
        oscillator.start(0);
        setTimeout(() => {
          oscillator.stop();
          resolve(null);
        }, 100);
      });
    } catch (error) {
      console.error('Audio fingerprint error:', error);
      return null;
    }
  }
  
  /**
   * 检测字体
   */
  static async detectFonts() {
    const baseFonts = ['monospace', 'sans-serif', 'serif'];
    const testFonts = [
      'Arial', 'Verdana', 'Times New Roman', 'Courier New', 'Georgia',
      'Palatino', 'Garamond', 'Bookman', 'Comic Sans MS', 'Trebuchet MS',
      'Impact', 'Arial Black', 'Tahoma', 'Helvetica', 'Century Gothic'
    ];
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return [];
    
    const text = 'mmmmmmmmmmlli';
    const textSize = '72px';
    
    const getWidth = (font) => {
      ctx.font = `${textSize} ${font}`;
      return ctx.measureText(text).width;
    };
    
    const baseWidths = {};
    baseFonts.forEach(font => {
      baseWidths[font] = getWidth(font);
    });
    
    const detectedFonts = [];
    testFonts.forEach(font => {
      let detected = false;
      baseFonts.forEach(baseFont => {
        const width = getWidth(`${font}, ${baseFont}`);
        if (width !== baseWidths[baseFont]) {
          detected = true;
        }
      });
      if (detected) {
        detectedFonts.push(font);
      }
    });
    
    return detectedFonts;
  }
  
  /**
   * 获取插件列表
   */
  static getPlugins() {
    if (!navigator.plugins) return [];
    
    const plugins = [];
    for (let i = 0; i < navigator.plugins.length; i++) {
      const plugin = navigator.plugins[i];
      plugins.push(plugin.name);
    }
    return plugins;
  }
  
  /**
   * 获取WebRTC暴露的IP地址
   */
  static async getWebRTCIPs() {
    return new Promise((resolve) => {
      const ips = [];
      const RTCPeerConnection = window.RTCPeerConnection ||
                                window.mozRTCPeerConnection ||
                                window.webkitRTCPeerConnection;
      
      if (!RTCPeerConnection) {
        resolve([]);
        return;
      }
      
      const pc = new RTCPeerConnection({ iceServers: [] });
      
      pc.createDataChannel('');
      
      pc.createOffer()
        .then(offer => pc.setLocalDescription(offer))
        .catch(() => {});
      
      pc.onicecandidate = (event) => {
        if (!event || !event.candidate || !event.candidate.candidate) {
          setTimeout(() => {
            pc.close();
            resolve([...new Set(ips)]); // 去重
          }, 500);
          return;
        }
        
        const candidate = event.candidate.candidate;
        const ipRegex = /([0-9]{1,3}\.){3}[0-9]{1,3}|([a-f0-9:]+:+)+[a-f0-9]+/g;
        const matches = candidate.match(ipRegex);
        
        if (matches) {
          matches.forEach(ip => {
            // 过滤掉本地回环地址
            if (!ip.startsWith('127.') && ip !== '0.0.0.0' && !ips.includes(ip)) {
              ips.push(ip);
            }
          });
        }
      };
      
      // 超时保护
      setTimeout(() => {
        pc.close();
        resolve([...new Set(ips)]);
      }, 2000);
    });
  }
  
  /**
   * 字符串哈希
   */
  static async hashString(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex.substring(0, 16);
  }
  
  /**
   * 获取DNS服务器（尝试检测，可能失败）
   */
  static async getDNSServers() {
    // 浏览器环境下无法直接获取DNS服务器
    // 这里返回空数组，需要用户手动输入或使用浏览器扩展
    // 实际项目中可以提示用户访问特定页面获取DNS信息
    return [];
  }
  
  /**
   * 检测WebDriver
   */
  static detectWebDriver() {
    return (
      navigator.webdriver === true ||
      window.document.documentElement.getAttribute('webdriver') !== null ||
      window.callPhantom !== undefined ||
      window._phantom !== undefined
    );
  }
  
  /**
   * 检测是否在无头浏览器中
   */
  static isHeadlessBrowser() {
    // 检测常见的无头浏览器特征
    const checks = [
      !navigator.webdriver === false,
      /HeadlessChrome/.test(navigator.userAgent),
      navigator.plugins.length === 0,
      !navigator.languages || navigator.languages.length === 0,
    ];
    
    return checks.some(check => check);
  }
  
  /**
   * 检测是否在自动化环境中
   */
  static isAutomated() {
    return (
      navigator.webdriver === true ||
      window.document.documentElement.getAttribute('webdriver') !== null ||
      window.callPhantom !== undefined ||
      window._phantom !== undefined ||
      window.phantom !== undefined
    );
  }
}

export default FingerprintCollector;
