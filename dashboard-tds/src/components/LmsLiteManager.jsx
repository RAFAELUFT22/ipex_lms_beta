import React, { useState, useEffect } from 'react';
import { BookOpen, Users, CheckCircle, Award, ExternalLink, RefreshCw, Volume2 } from 'lucide-react';
import { lmsLiteApi } from '../api/lms_lite';
import { speechService } from '../utils/SpeechService';
import CertificatePreview from './CertificatePreview';

export default function LmsLiteManager() {
  const [students, setStudents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedStudentForCert, setSelectedStudentForCert] = useState(null);

  useEffect(() => {
    speechService.init();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await lmsLiteApi.getStudents();
      setStudents(Object.values(data));
    } catch (e) {
      console.error("Erro ao carregar alunos LMS Lite:", e);
    }
    setIsLoading(false);
  };

  const speakStatus = (student) => {
    const text = `O aluno ${student.name} está no curso ${student.current_course || 'de Introdução'} e já concluiu ${student.progress} por cento das atividades.`;
    speechService.speak(text);
  };

  const handleGenerateCert = (student) => {
    // Simulando o Hash recebido do servidor para o prototype (SHA-256 Mockado)
    const mockHash = "TDS-8A9F" + Date.now().toString(16).toUpperCase() + "C2B";
    setSelectedStudentForCert({
      ...student,
      certHash: mockHash
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold flex items-center gap-2">
          <BookOpen size={20} className="text-primary" />
          Gestão de Alunos (LMS Lite)
        </h3>
        <button onClick={loadData} className="btn btn-outline p-2">
          <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {students.length === 0 && (
          <div className="glass-card p-12 text-center text-text-dim">
            Nenhum aluno cadastrado no sistema Lite.
          </div>
        )}
        {students.map((student) => (
          <div key={student.whatsapp} className="glass-card p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold shadow-inner">
                {student.name[0]}
              </div>
              <div>
                <h4 className="font-bold text-lg">{student.name}</h4>
                <p className="text-sm text-text-dim">{student.whatsapp} • {student.sisec_data?.localidade || 'Local não informado'}</p>
              </div>
            </div>

            <div className="flex-1 max-w-xs w-full">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-text-dim">Progresso: {student.current_course || 'Nenhum curso'}</span>
                <span className="font-bold text-primary">{student.progress}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                <div 
                  className="h-full bg-primary transition-all duration-1000" 
                  style={{ width: `${student.progress}%` }}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button 
                onClick={() => speakStatus(student)}
                className="btn btn-outline p-2 text-primary border-primary/20 hover:bg-primary/10"
                title="Ouvir Status"
              >
                <Volume2 size={16} />
              </button>
              {student.progress >= 100 ? (
                <>
                  <div className="flex items-center gap-1 text-emerald-500 text-sm font-bold bg-emerald-500/10 px-3 py-1 rounded-full">
                    <CheckCircle size={16} /> Concluído
                  </div>
                  <button 
                    onClick={() => handleGenerateCert(student)}
                    className="btn bg-gradient-to-r from-[#F9C300] to-yellow-600 text-[#003366] hover:brightness-110 font-bold px-3 py-1 text-xs flex items-center gap-1 shadow-md hover:scale-105 transition-transform"
                    title="Emitir Certificado Premium"
                  >
                    <Award size={14} /> Certificado Premium
                  </button>
                </>
              ) : (
                <button className="btn btn-outline text-xs py-1 px-3">Ver Perfil SISEC</button>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedStudentForCert && (
        <CertificatePreview 
          student={selectedStudentForCert}
          courseName={selectedStudentForCert.current_course === 'audiovisual-e-produ-o-de-conte-do-digital-2' ? 'Produção Audiovisual e Conteúdo Digital' : 'Curso de Formação Continuada TDS'}
          hash={selectedStudentForCert.certHash}
          onClose={() => setSelectedStudentForCert(null)}
        />
      )}
    </div>
  );
}
