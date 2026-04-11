// RecognitionService.js - Utilitário de Reconhecimento de Voz (STT)
// Usa a Web Speech API nativa (Gratuito e Rápido)

class RecognitionService {
  constructor() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false; // Para quando o usuário para de falar
      this.recognition.lang = 'pt-BR';
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 1;
    } else {
      console.warn("Reconhecimento de voz não suportado neste navegador.");
      this.recognition = null;
    }
  }

  start(onResult, onEnd) {
    if (!this.recognition) return;

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };

    this.recognition.onend = () => {
      if (onEnd) onEnd();
    };

    this.recognition.onerror = (event) => {
      console.error("Erro no reconhecimento:", event.error);
      if (onEnd) onEnd();
    };

    try {
      this.recognition.start();
    } catch (e) {
      console.error("Falha ao iniciar microfone:", e);
    }
  }

  stop() {
    if (this.recognition) {
      this.recognition.stop();
    }
  }
}

export const recognitionService = new RecognitionService();
