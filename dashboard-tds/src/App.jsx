import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Send, 
  MessageSquare, 
  Settings, 
  ShieldCheck, 
  BarChart3, 
  LogOut,
  PlusCircle,
  AlertTriangle,
  Zap,
  Play,
  BookOpen,
  BrainCircuit,
  GraduationCap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mock Auth
const ADMIN_PASSWORD = "admin-tds-2026";

import GroupManager from './components/GroupManager';
import BroadcastCenter from './components/BroadcastCenter';
import AIInsight from './components/AIInsight';
import MetricsView from './components/MetricsView';
import TutorsManager from './components/TutorsManager';
import KnowledgeBase from './components/KnowledgeBase';
import StudentPortal from './components/StudentPortal';
import ValidateCert from './pages/ValidateCert';

export default function App() {
  // Public route: certificate validation (computed before hooks, returned after)
  const urlHash = window.location.pathname.match(/^\/validate\/([a-f0-9]+)$/)?.[1];

  const [viewMode, setViewMode] = useState("admin"); // "admin" or "student"
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem('tds_auth') === 'true';
  });
  const [password, setPassword] = useState("");
  const [activeTab, setActiveTab] = useState("groups");
  const [simulationMode, setSimulationMode] = useState(false);
  const [error, setError] = useState("");

  if (urlHash) return <ValidateCert hash={urlHash} />;

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === ADMIN_PASSWORD) {
      setIsLoggedIn(true);
      localStorage.setItem('tds_auth', 'true');
      setError("");
    } else {
      setError("Senha incorreta. Tente novamente.");
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem('tds_auth');
  };

  // Student portal has its own auth, so we bypass admin login if in student mode
  if (viewMode === "student") {
    return (
      <div className="min-h-screen bg-deep p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-xl font-bold">TDS Portal</h1>
            <button 
              onClick={() => setViewMode("admin")}
              className="btn btn-outline py-1 px-3 text-xs"
            >
              Voltar ao Admin
            </button>
          </div>
          <StudentPortal />
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-deep">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-8 w-full max-w-md text-center"
        >
          <div className="w-16 h-16 bg-primary-glow rounded-2xl flex items-center justify-center mx-auto mb-6">
            <ShieldCheck className="text-primary w-10 h-10" />
          </div>
          <h1 className="text-2xl font-bold mb-2">TDS Dashboard</h1>
          <p className="text-text-dim mb-8">Acesso restrito a administradores</p>
          
          <form onSubmit={handleLogin} className="space-y-4 text-left">
            <div className="input-group">
              <label className="input-label">Senha Administrativa</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
            {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
            <button type="submit" className="btn btn-primary w-full">
              Entrar no Sistema
            </button>
          </form>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-deep font-body">
      {/* Sidebar - Tonal Layering (surface_container_low look) */}
      <aside className="w-72 bg-bg-surface border-r border-border p-8 flex flex-col gap-10">
        <div className="flex items-center gap-4 px-2">
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center shadow-lg shadow-secondary/20">
            <Zap className="text-white w-7 h-7" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-2xl tracking-tighter text-text-main font-heading">TDS Ops</span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-secondary font-bold">Premium LMS</span>
          </div>
        </div>

        <nav className="flex-1 flex flex-col gap-3">
          <NavItem 
            icon={<Users size={22} />} 
            label="Grupos" 
            active={activeTab === "groups"} 
            onClick={() => setActiveTab("groups")}
          />
          <NavItem 
            icon={<Send size={22} />} 
            label="Transmissão" 
            active={activeTab === "broadcast"} 
            onClick={() => setActiveTab("broadcast")}
          />
          <NavItem 
            icon={<BrainCircuit size={22} />} 
            label="IA Insight" 
            active={activeTab === "ai"} 
            onClick={() => setActiveTab("ai")}
          />
          <NavItem 
            icon={<ShieldCheck size={22} />} 
            label="Tutores" 
            active={activeTab === "tutors"} 
            onClick={() => setActiveTab("tutors")}
          />
          <NavItem 
            icon={<BookOpen size={22} />} 
            label="Conhecimento" 
            active={activeTab === "knowledge"} 
            onClick={() => setActiveTab("knowledge")}
          />
          <NavItem 
            icon={<BarChart3 size={22} />} 
            label="Métricas" 
            active={activeTab === "metrics"} 
            onClick={() => setActiveTab("metrics")}
          />
        </nav>

        <div className="pt-8 border-t border-border flex flex-col gap-6">
          <div className="glass-card p-4 flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-text-muted uppercase">Visão</span>
              <span className="text-xs font-semibold">{viewMode === "admin" ? "Administrador" : "Aluno"}</span>
            </div>
            <button 
              onClick={() => setViewMode("student")}
              className="p-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-all"
              title="Mudar para Visão Aluno"
            >
              <GraduationCap size={18} />
            </button>
          </div>

          <div className="glass-card p-4 flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-[10px] font-bold text-text-muted uppercase">Ambiente</span>
              <span className="text-xs font-semibold">{simulationMode ? 'Simulação' : 'Produção'}</span>
            </div>
            <button 
              onClick={() => setSimulationMode(!simulationMode)}
              className={`w-12 h-6 rounded-full transition-all relative ${simulationMode ? 'bg-secondary' : 'bg-slate-800'}`}
            >
              <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${simulationMode ? 'translate-x-6' : ''} shadow-sm`} />
            </button>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 px-2 text-red-400 hover:text-red-300 transition-colors text-sm font-bold"
          >
            <LogOut size={18} /> Sair do Sistema
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-12 overflow-y-auto bg-gradient-to-tr from-bg-deep to-bg-surface/30">
        <header className="flex justify-between items-start mb-12">
          <div className="animate-fade">
            <h2 className="text-4xl font-bold mb-2">
              {activeTab === "groups" && "Gestão de Grupos"}
              {activeTab === "broadcast" && "Listas de Transmissão"}
              {activeTab === "ai" && "Inteligência Coletiva"}
              {activeTab === "tutors" && "Gestão de Tutores"}
              {activeTab === "knowledge" && "Base de Conhecimento RAG"}
              {activeTab === "metrics" && "Métricas Operacionais"}
            </h2>
            <div className="flex items-center gap-2">
              <div className="w-8 h-1 bg-secondary rounded-full" />
              <p className="text-text-dim font-medium">
                {activeTab === "groups" && "Organize seus alunos com base no contexto SISEC."}
                {activeTab === "broadcast" && "Comunicação em massa com segurança e marcação premium."}
                {activeTab === "ai" && "Insights automáticos e suporte via RAG AnythingLLM."}
                {activeTab === "tutors" && "Gerencie instâncias e agentes de atendimento."}
                {activeTab === "knowledge" && "Alimente o cérebro da IA com manuais e regras do curso."}
                {activeTab === "metrics" && "Visão analítica da performance educacional."}
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <button className="btn btn-outline" onClick={() => window.open(import.meta.env.VITE_DIGITIZER_URL || 'https://digitalizacao.ipexdesenvolvimento.cloud', '_blank')}>
              <PlusCircle size={18} /> Digitalizar Documentos
            </button>
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            {activeTab === "groups" && <GroupManager simulation={simulationMode} />}
            {activeTab === "broadcast" && <BroadcastCenter />}
            {activeTab === "ai" && <AIInsight />}
            {activeTab === "tutors" && <TutorsManager />}
            {activeTab === "knowledge" && <KnowledgeBase />}
            {activeTab === "metrics" && <MetricsView />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-4 px-5 py-4 rounded-2xl transition-all ${
        active 
          ? 'bg-secondary/10 text-secondary shadow-inner border border-secondary/20 scale-[1.02]' 
          : 'text-text-muted hover:bg-glass hover:text-text-main border border-transparent'
      }`}
    >
      <div className={`transition-colors ${active ? 'text-secondary' : 'text-text-muted'}`}>
        {icon}
      </div>
      <span className="font-bold font-heading text-sm">{label}</span>
      {active && <motion.div layoutId="active-nav" className="ml-auto w-1.5 h-1.5 bg-secondary rounded-full" />}
    </button>
  );
}

