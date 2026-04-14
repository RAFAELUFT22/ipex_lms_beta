import React, { useState, useEffect } from 'react';
import { MessageSquare, Zap, Search, RefreshCcw, BrainCircuit, Volume2, Square } from 'lucide-react';

import { evolutionApi } from '../api/evolution';
import { openRouterApi } from '../api/openrouter';
import { ragApi } from '../api/rag';
import { speechService } from '../utils/SpeechService';

export default function AIInsight() {
  const [communities, setCommunities] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState("");
  const [summary, setSummary] = useState("");
  const [ragAnswer, setRagAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRagLoading, setIsRagLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [customQuestion, setCustomQuestion] = useState("");

  useEffect(() => {
    speechService.init();
    fetchCommunities();
  }, []);

  const fetchCommunities = async () => {
    try {
      const data = await lmsLiteApi.getCommunities();
      setCommunities(data);
    } catch (e) {
      console.error("Failed to fetch communities", e);
    }
  };

  const toggleSpeech = (text) => {
    if (isSpeaking) {
      speechService.stop();
      setIsSpeaking(false);
    } else {
      speechService.speak(text);
      setIsSpeaking(true);
      const checkStatus = setInterval(() => {
        if (!window.speechSynthesis.speaking) {
          setIsSpeaking(false);
          clearInterval(checkStatus);
        }
      }, 500);
    }
  };
  
  const analyzeGroup = async () => {
    setIsLoading(true);
    setRagAnswer("");
    try {
      // Find the selected community JID
      const community = communities.find(c => c.slug === selectedGroup);
      const groupJid = community ? community.whatsapp_group_id : null;

      // In a real scenario, we would fetch the last 50 messages for this groupJid from the backend
      const mockMessages = [
        { sender: "João", text: "Não estou conseguindo acessar o módulo 2" },
        { sender: "Maria", text: "Onde vejo meu progresso no SISEC?" },
        { sender: "Pedro", text: "A aula de amanhã será que horas?" },
        { sender: "Ana", text: "Também estou com erro no módulo 2" }
      ];
      
      const result = await openRouterApi.summarizeGroups(mockMessages);
      setSummary(result);
    } catch (e) {
      setSummary("Erro ao processar: " + e.message);
    }
    setIsLoading(false);
  };

  const askRag = async (question) => {
    const q = question || customQuestion;
    if (!q) return;

    setIsRagLoading(true);
    try {
      const answer = await ragApi.query(q);
      setRagAnswer(answer);
    } catch (e) {
      setRagAnswer("Erro ao consultar RAG: Verifique se o AnythingLLM está ativo.");
    }
    setIsRagLoading(false);
  };

  return (
    <div className="space-y-6 animate-fade">
      <div className="glass-card p-6 flex flex-col md:flex-row justify-between items-center gap-6">
        <div>
          <h3 className="text-xl font-bold flex items-center gap-2">
            <BrainCircuit size={24} className="text-secondary" />
            Inteligência Coletiva
          </h3>
          <p className="text-text-dim text-sm">Analise conversas ou consulte a base de conhecimento.</p>
        </div>
        <div className="flex gap-4 w-full md:w-auto">
          <select 
            className="flex-1 md:w-64"
            value={selectedGroup}
            onChange={(e) => setSelectedGroup(e.target.value)}
          >
            <option value="">Selecionar Comunidade...</option>
            {communities.map(c => (
              <option key={c.slug} value={c.slug}>{c.title} ({c.member_count})</option>
            ))}
          </select>
          <button 
            className="btn btn-primary"
            onClick={analyzeGroup}
            disabled={isLoading || !selectedGroup}
          >
            {isLoading ? <RefreshCcw className="animate-spin" size={18}/> : <Zap size={18}/>}
            Gerar Insight
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Summary Side */}
        {summary && (
          <div className="glass-card p-8 flex flex-col h-full">
            <div className="flex justify-between items-start mb-6">
              <h4 className="text-primary-light font-bold text-lg">Resumo da IA (OpenRouter)</h4>
              <button 
                onClick={() => toggleSpeech(summary)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full font-bold transition-all ${isSpeaking ? 'bg-red-500 text-white' : 'bg-secondary text-bg-deep'}`}
              >
                {isSpeaking ? <Square size={16} /> : <Volume2 size={16} />}
                {isSpeaking ? "Parar" : "Ouvir"}
              </button>
            </div>
            <div className="whitespace-pre-wrap text-text-main leading-relaxed flex-1 prose prose-invert">
              {summary}
            </div>
          </div>
        )}

        {/* RAG Query Side */}
        <div className="glass-card p-8 flex flex-col h-full border-l-4 border-secondary/20">
          <h4 className="text-secondary font-bold text-lg mb-6 flex items-center gap-2">
            <Search size={20} />
            Consultar Base de Conhecimento (RAG)
          </h4>
          
          <div className="space-y-4 mb-6">
            <textarea 
              placeholder="Digite uma dúvida específica baseada nos manuais..."
              className="resize-none h-24"
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
            />
            <button 
              className={`btn w-full bg-secondary text-bg-deep font-bold transition-all ${isRagLoading ? 'opacity-50' : 'hover:scale-[1.02]'}`}
              onClick={() => askRag()}
              disabled={isRagLoading || !customQuestion}
            >
              {isRagLoading ? <RefreshCcw className="animate-spin" size={18}/> : <BrainCircuit size={18}/>}
              Perguntar ao AnythingLLM
            </button>
          </div>

          {ragAnswer && (
            <div className="p-6 bg-secondary/10 border border-secondary/20 rounded-2xl animate-fade">
              <h5 className="text-secondary font-bold text-sm uppercase mb-2">Resposta do Cérebro:</h5>
              <div className="text-text-main text-sm leading-relaxed whitespace-pre-wrap">
                {ragAnswer}
              </div>
              <button 
                onClick={() => toggleSpeech(ragAnswer)}
                className="mt-4 text-xs font-bold text-secondary hover:underline flex items-center gap-1"
              >
                <Volume2 size={12} /> Ler em voz alta
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
