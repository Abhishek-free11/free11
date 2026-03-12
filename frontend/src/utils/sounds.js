// Sound effects for FREE11
// Sound is OFF by default (opt-in only)

// Check if sounds are enabled
export const isSoundEnabled = () => {
  return localStorage.getItem('free11_sounds_enabled') === 'true';
};

export const setSoundEnabled = (enabled) => {
  localStorage.setItem('free11_sounds_enabled', enabled ? 'true' : 'false');
};

export const playCoinSound = () => {
  if (!isSoundEnabled()) return;
  
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (e) {
    console.log('Sound playback not available');
  }
};

export const playCelebrationSound = () => {
  if (!isSoundEnabled()) return;
  
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Create a cheerful ascending tone
    [400, 500, 600, 800].forEach((freq, i) => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = freq;
      oscillator.type = 'sine';

      const startTime = audioContext.currentTime + (i * 0.1);
      gainNode.gain.setValueAtTime(0.2, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.3);

      oscillator.start(startTime);
      oscillator.stop(startTime + 0.3);
    });
  } catch (e) {
    console.log('Sound playback not available');
  }
};

export const playWinSound = () => {
  if (!isSoundEnabled()) return;
  
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Victory fanfare
    const notes = [523, 659, 784, 1047]; // C, E, G, high C
    notes.forEach((freq, i) => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = freq;
      oscillator.type = 'triangle';

      const startTime = audioContext.currentTime + (i * 0.15);
      gainNode.gain.setValueAtTime(0.3, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.4);

      oscillator.start(startTime);
      oscillator.stop(startTime + 0.4);
    });
  } catch (e) {
    console.log('Sound playback not available');
  }
};

// Soft celebration ding for correct predictions
export const playCorrectPredictionSound = () => {
  if (!isSoundEnabled()) return;
  
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 880; // A5 - pleasant ding
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.3);
  } catch (e) {
    console.log('Sound playback not available');
  }
};
