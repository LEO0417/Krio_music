export const downloadAudioFile = async (url: string, filename: string) => {
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    throw new Error('Failed to download audio file');
  }
};

export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getAudioFormat = (url: string): string => {
  const extension = url.split('.').pop()?.toLowerCase();
  switch (extension) {
    case 'mp3':
      return 'MP3';
    case 'wav':
      return 'WAV';
    case 'flac':
      return 'FLAC';
    case 'ogg':
      return 'OGG';
    case 'm4a':
      return 'M4A';
    default:
      return 'Unknown';
  }
};

export const generateFileName = (prompt: string, format: string = 'mp3'): string => {
  const sanitizedPrompt = prompt
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .substring(0, 50);
  
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  
  return `music_${sanitizedPrompt}_${timestamp}.${format}`;
};

export const validateAudioUrl = (url: string): boolean => {
  const audioExtensions = ['mp3', 'wav', 'flac', 'ogg', 'm4a'];
  const extension = url.split('.').pop()?.toLowerCase();
  return audioExtensions.includes(extension || '');
};

export const calculateWaveformData = (audioBuffer: ArrayBuffer): number[] => {
  // This is a simplified waveform calculation
  // In a real implementation, you would use Web Audio API
  const data = new Uint8Array(audioBuffer);
  const waveform: number[] = [];
  const sampleSize = Math.floor(data.length / 100); // 100 points for waveform
  
  for (let i = 0; i < 100; i++) {
    const start = i * sampleSize;
    const end = start + sampleSize;
    let sum = 0;
    
    for (let j = start; j < end && j < data.length; j++) {
      sum += Math.abs(data[j] - 128);
    }
    
    waveform.push(sum / sampleSize);
  }
  
  return waveform;
};

export const preloadAudio = (url: string): Promise<HTMLAudioElement> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    audio.addEventListener('canplaythrough', () => resolve(audio));
    audio.addEventListener('error', reject);
    audio.src = url;
  });
};