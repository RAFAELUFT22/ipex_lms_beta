import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Upload, 
  Database, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Trash2, 
  RefreshCw,
  Search,
  BrainCircuit
} from 'lucide-react';
import { ragApi } from '../api/rag';

export default function KnowledgeBase() {
  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [status, setStatus] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await ragApi.listDocuments();
      // Transform AnythingLLM docs to local state format
      setFiles(docs.map(doc => ({
        id: doc.id,
        name: doc.title || doc.name,
        path: doc.location || doc.docpath,
        date: new Date().toLocaleDateString('pt-BR') // Mock date if not provided
      })));
    } catch (error) {
      console.error("Fetch docs failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsSyncing(true);
    setStatus({ type: 'info', message: "Enviando arquivo para o cérebro da IA..." });

    try {
      const result = await ragApi.uploadDocument(file);
      if (result.success) {
        setStatus({ type: 'success', message: "Arquivo aprendido com sucesso!" });
        fetchDocuments();
      }
    } catch (error) {
      setStatus({ type: 'error', message: "Falha ao enviar arquivo. Verifique a conexão com o AnythingLLM." });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDelete = async (path) => {
    if (!window.confirm("Tem certeza que deseja remover este conhecimento?")) return;
    
    try {
      await ragApi.deleteDocument(path);
      fetchDocuments();
      setStatus({ type: 'success', message: "Documento removido do vocabulário da IA." });
    } catch (error) {
      setStatus({ type: 'error', message: "Erro ao remover documento." });
    }
  };

  const filteredFiles = files.filter(f => f.name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="space-y-6 animate-fade">
      {/* Top Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-card p-4 md:col-span-3 flex items-center gap-4">
          <Search className="text-text-muted" size={20} />
          <input 
            type="text" 
            placeholder="Pesquisar na base de conhecimento..." 
            className="bg-transparent border-none focus:ring-0 p-0 text-lg w-full"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <label className="btn btn-primary flex-1 h-full cursor-pointer">
          <Upload size={20} />
          Adicionar PDF
          <input type="file" className="hidden" onChange={handleUpload} accept=".pdf,.doc,.docx,.txt" />
        </label>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Repo List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card p-6 min-h-[400px]">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-3">
              <BrainCircuit size={24} className="text-secondary" />
              Cérebro Ativo: TDS Knowledge
            </h3>

            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-64 text-text-muted gap-4">
                <RefreshCw className="animate-spin" size={32} />
                <p>Consultando base de dados...</p>
              </div>
            ) : filteredFiles.length > 0 ? (
              <div className="space-y-3">
                {filteredFiles.map((file, i) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-2xl group hover:border-secondary/30 transition-all hover:bg-secondary/5">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-primary/20 rounded-xl text-primary-light">
                        <FileText size={24} />
                      </div>
                      <div>
                        <h4 className="font-semibold text-text-main">{file.name}</h4>
                        <p className="text-xs text-text-muted">Caminho: {file.path} • {file.date}</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => handleDelete(file.path)}
                      className="p-2 text-text-muted hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-text-muted text-center p-8">
                <Database size={48} className="mb-4 opacity-20" />
                <p className="text-lg font-medium">Nenhum documento encontrado</p>
                <p className="text-sm">Carregue manuais ou PDFs para treinar a IA do curso.</p>
              </div>
            )}
          </div>
        </div>

        {/* Sync & Stats */}
        <div className="space-y-6">
          <div className="glass-card p-6 bg-gradient-to-br from-secondary/10 to-transparent">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Database size={20} className="text-secondary" />
              Status do RAG
            </h3>
            <div className="space-y-4 mb-6">
              <div className="flex justify-between items-center text-sm">
                <span className="text-text-muted">Documentos</span>
                <span className="font-bold">{files.length}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-text-muted">Conectividade</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle size={14} /> Ativa
                </span>
              </div>
            </div>
            <button 
              className={`btn w-full py-4 bg-secondary text-bg-deep font-bold gap-2 ${isSyncing ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 shadow-lg shadow-secondary/20'}`}
              onClick={fetchDocuments}
              disabled={isSyncing}
            >
              <RefreshCw size={20} className={isSyncing ? "animate-spin" : ""} />
              {isSyncing ? "Processando..." : "Sincronizar"}
            </button>
          </div>

          <div className="glass-card p-6 border-l-4 border-accent/50">
            <h4 className="text-sm font-bold text-accent uppercase tracking-wider mb-2">Dica de Performance</h4>
            <p className="text-xs text-text-dim leading-relaxed">
              O RAG do AnythingLLM funciona melhor com documentos curtos e bem estruturados. Divida manuais grandes em capítulos para respostas mais precisas.
            </p>
          </div>
        </div>
      </div>

      {status && (
        <div className={`p-4 rounded-2xl flex items-center gap-3 animate-fade ${
          status.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
          status.type === 'info' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
          'bg-red-500/10 text-red-400 border border-red-500/20'
        }`}>
          {status.type === 'success' ? <CheckCircle size={20}/> : <AlertCircle size={20}/>}
          <p className="font-semibold text-sm">{status.message}</p>
        </div>
      )}
    </div>
  );
}
