import { useEffect, useState } from 'react';
import { lmsLiteApiV2 } from '../../api/lms_lite_v2';

function CertCard({ cert }) {
  const issuedDate = cert.issued_at || cert.created_at || null;
  const formattedDate = issuedDate
    ? new Date(issuedDate).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
      })
    : '';

  function handleDownload() {
    // TODO: trigger download by cert hash or URL
    console.log('Download cert:', cert.hash);
  }

  function handleShare() {
    if (navigator.share) {
      navigator.share({
        title: cert.course_title || 'Certificado TDS',
        text: `Concluí o curso "${cert.course_title}" na plataforma TDS!`,
        url: cert.verify_url || window.location.href,
      }).catch(() => {});
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard?.writeText(cert.verify_url || window.location.href).catch(() => {});
    }
  }

  return (
    <article className="bg-surface-container-low rounded-xl overflow-hidden">
      {/* Top section with gradient */}
      <div className="bg-cerrado-gradient p-6">
        <h3 className="font-bold text-white text-base leading-tight">
          {cert.course_title || 'Certificado'}
        </h3>
        {formattedDate && (
          <p className="text-white/80 text-sm mt-1">{formattedDate}</p>
        )}
      </div>

      {/* Bottom section */}
      <div className="p-4 flex justify-between items-center gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="material-symbols-outlined text-primary text-base shrink-0">verified</span>
          <span className="text-xs text-on-surface-variant font-mono truncate max-w-[120px]">
            {cert.hash || '---'}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handleDownload}
            aria-label="Baixar certificado"
            className="bg-secondary-container text-on-secondary-container rounded-lg p-2 transition-opacity hover:opacity-80"
          >
            <span className="material-symbols-outlined text-base">download</span>
          </button>
          <button
            type="button"
            onClick={handleShare}
            aria-label="Compartilhar certificado"
            className="bg-surface-container-high rounded-lg p-2 text-on-surface transition-opacity hover:opacity-80"
          >
            <span className="material-symbols-outlined text-base">share</span>
          </button>
        </div>
      </div>
    </article>
  );
}

export default function CertificateList({ phone }) {
  const [certs, setCerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadCertificates();
  }, [phone]);

  async function loadCertificates() {
    try {
      if (!phone) {
        setLoading(false);
        return;
      }
      const result = await lmsLiteApiV2.validateCert(phone);
      setCerts(result ? [result] : []);
    } catch (error) {
      console.error('Failed to validate certificate', error);
      setCerts([]);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface p-6 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-on-surface-variant">
          <span className="material-symbols-outlined text-5xl text-primary animate-pulse">
            workspace_premium
          </span>
          <p className="font-bold text-on-surface">Carregando diplomas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface p-6 space-y-8">
      {/* Header */}
      <header className="space-y-1">
        <span className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold">
          Suas Conquistas
        </span>
        <h2 className="text-3xl font-bold font-headline text-on-surface">Meus Diplomas</h2>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-surface-container-highest rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-primary font-headline">{certs.length}</p>
          <p className="text-xs text-on-surface-variant mt-1 font-bold uppercase tracking-wide">
            Diplomas Emitidos
          </p>
        </div>
        <div className="bg-surface-container-highest rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-primary font-headline">{certs.length}</p>
          <p className="text-xs text-on-surface-variant mt-1 font-bold uppercase tracking-wide">
            Cursos Concluídos
          </p>
        </div>
      </div>

      {/* Certificates grid or empty state */}
      {certs.length === 0 ? (
        <div className="bg-surface-container-low rounded-xl p-16 text-center space-y-4">
          <span className="material-symbols-outlined text-7xl text-outline opacity-40 block">
            workspace_premium
          </span>
          <div>
            <p className="text-on-surface font-bold text-base">Nenhum diploma ainda</p>
            <p className="text-on-surface-variant text-sm mt-2">
              Complete sua primeira trilha para receber seu certificado.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {certs.map((cert, idx) => (
            <CertCard key={cert.hash || idx} cert={cert} />
          ))}
        </div>
      )}
    </div>
  );
}
