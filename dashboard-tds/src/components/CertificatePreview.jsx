import React, { useRef, useState } from 'react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import { Download, Send, X } from 'lucide-react';
import { chatwootApi } from '../api/chatwoot';

export default function CertificatePreview({ student, courseName, hash, onClose }) {
  const certRef = useRef(null);
  const [isSending, setIsSending] = useState(false);
  const [status, setStatus] = useState("");

  const downloadPDF = async () => {
    const element = certRef.current;
    if (!element) return;
    
    // Configura html2canvas com alta escala para melhor resolução
    const canvas = await html2canvas(element, { scale: 3, useCORS: true });
    const imgData = canvas.toDataURL('image/jpeg', 1.0);
    
    // PDF em modo paisagem (A4: 297mm x 210mm)
    const pdf = new jsPDF('landscape', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    
    pdf.addImage(imgData, 'JPEG', 0, 0, pdfWidth, pdfHeight);
    pdf.save(`Certificado_TDS_${student.name.replace(/\s+/g, '_')}.pdf`);
  };

  const sendViaChatwoot = async () => {
    setIsSending(true);
    setStatus("Buscando aluno no Chatwoot e enviando...");
    try {
      // Adiciona o código DDI se não existir
      const cleanPhone = student.whatsapp.startsWith("55") ? `+${student.whatsapp}` : `+55${student.whatsapp}`;
      await chatwootApi.sendCertificateToStudent(cleanPhone, courseName, hash);
      setStatus("✅ Gerenciado via Chatwoot! O aluno recebeu a mensagem com o certificado no WhatsApp.");
    } catch (e) {
      setStatus(`❌ Erro no Chatwoot: ${e.message}`);
    }
    setIsSending(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-5xl overflow-hidden shadow-2xl">
        <div className="flex justify-between items-center p-4 border-b bg-slate-50">
          <h2 className="text-xl font-bold text-[#003366]">Visualização Premium (TDS Navy & Gold)</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full text-slate-500">
            <X size={24} />
          </button>
        </div>
        
        <div className="p-8 bg-gray-200 flex justify-center overflow-auto max-h-[65vh]">
          {/* A div abaixo representa uma folha A4 em paisagem para a captura exata */}
          <div 
            ref={certRef}
            className="bg-white relative shadow-lg overflow-hidden font-serif" 
            style={{ width: '297mm', height: '210mm', padding: '40px', boxSizing: 'border-box', border: '15px solid #003366' }}
          >
            {/* Moldura Interna Dourada */}
            <div style={{ position: 'absolute', top: '15px', left: '15px', width: 'calc(100% - 30px)', height: 'calc(100% - 30px)', border: '2px solid #F9C300', boxSizing: 'border-box', pointerEvents: 'none', zIndex: 1 }}></div>
            
            {/* Watermark Logo (Sutil ao Fundo) */}
            <div className="absolute inset-0 flex items-center justify-center opacity-5 z-0 pointer-events-none">
              <div className="w-96 h-96 rounded-full border-8 border-[#003366]"></div>
            </div>

            <div className="flex justify-between items-start mb-12 relative z-10 pt-4 px-4">
              <div className="text-[#003366] font-bold">
                <p className="text-3xl tracking-tight">PROJETO TDS</p>
                <p className="text-sm tracking-[0.3em] text-[#F9C300]">EXCELÊNCIA EM INCLUSÃO</p>
              </div>
              <div className="text-right">
                <div className="w-24 h-24 bg-gradient-to-br from-yellow-300 to-yellow-600 rounded-full flex flex-col items-center justify-center text-white text-center p-2 font-bold shadow-xl border-4 border-white">
                  <span className="text-[10px]">SELO OFICIAL</span>
                  <span className="text-xl">TDS</span>
                </div>
              </div>
            </div>

            <div className="text-center relative z-10 mt-6">
              <h1 className="text-[70px] font-extrabold text-[#003366] uppercase tracking-widest mb-4">Certificado</h1>
              <p className="text-3xl text-gray-500 mb-10 italic">Certificamos com honra e orgulho que</p>
              
              <h2 className="text-6xl font-bold text-[#008080] border-b-4 border-[#F9C300] inline-block pb-3 px-16 mb-10">
                {student.name}
              </h2>
              
              <p className="text-2xl text-gray-700 max-w-4xl mx-auto leading-relaxed">
                concluiu com êxito todas as etapas de aprendizado, capacitação e desenvolvimento humano no curso de formação:
              </p>
              <strong className="text-[#003366] block mt-4 text-4xl">{courseName}</strong>
            </div>

            <div className="absolute bottom-20 w-full left-0 px-24 flex justify-between items-end z-10">
              <div className="text-center">
                <div className="w-56 border-b-2 border-[#003366] mb-2"></div>
                <p className="text-[#003366] font-bold text-lg">Coordenação Pedagógica</p>
                <p className="text-sm text-gray-500">Projeto TDS - Tocantins</p>
              </div>

              <div className="text-right">
                <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Chave de Autenticação (SHA-256)</p>
                <p className="font-mono text-sm font-bold text-[#003366] bg-slate-50 px-3 py-1 rounded border border-slate-300 shadow-sm inline-block">
                  {hash}
                </p>
                <p className="text-sm text-[#008080] mt-2 font-semibold tracking-wide">🔗 tds.edu.br/v/{hash.substring(0,8)}</p>
              </div>
            </div>
            
            {/* Faixa Dourada/Navy na base */}
            <div className="absolute bottom-0 left-0 w-full h-5 bg-gradient-to-r from-[#003366] via-[#008080] to-[#F9C300] z-10"></div>
          </div>
        </div>

        <div className="p-4 bg-white border-t flex justify-between items-center">
          <p className={`text-sm font-medium max-w-md ${status.includes('Erro') ? 'text-red-500' : 'text-emerald-600'}`}>{status}</p>
          <div className="flex gap-3">
            <button onClick={downloadPDF} className="btn bg-slate-800 text-white hover:bg-slate-700 flex items-center gap-2">
              <Download size={18} /> Baixar PDF HD
            </button>
            <button onClick={sendViaChatwoot} disabled={isSending} className="btn btn-primary flex items-center gap-2 shadow-lg hover:shadow-xl hover:scale-105 transition-all">
              <Send size={18} className={isSending ? "animate-pulse translate-x-1" : ""} /> 
              {isSending ? "Validando Chatwoot..." : "Entregar via Chatwoot"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
