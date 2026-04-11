// SpeechService.js - Utilitário de Voz para o Dashboard TDS
// Usa a Web Speech API nativa (Custo Zero)

class SpeechService {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voice = null;
  }

  // Inicializa e busca uma voz em Português do Brasil
  init() {
    return new Promise((resolve) => {
      let voices = this.synth.getVoices();
      if (voices.length > 0) {
        this.voice = voices.find(v => v.lang.includes('pt-BR')) || voices[0];
        resolve();
      } else {
        this.synth.onvoiceschanged = () => {
          voices = this.synth.getVoices();
          this.voice = voices.find(v => v.lang.includes('pt-BR')) || voices[0];
          resolve();
        };
      }
    });
  }

  speak(text) {
    if (this.synth.speaking) {
      this.synth.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = this.voice;
    utterance.pitch = 1.0;
    utterance.rate = 1.0; // Velocidade natural
    
    this.synth.speak(utterance);
  }

  stop() {
    this.synth.cancel();
  }
}

export const speechService = new SpeechService();
