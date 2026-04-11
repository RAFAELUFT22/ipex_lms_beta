import { useEffect, useState } from 'react';
import { lmsLiteApiV2 } from '../../api/lms_lite_v2';

function CertCard({ cert }) {
  return (
    <article className="rounded-xl border border-white/10 bg-white/5 p-4">
      <h3 className="text-sm font-semibold text-white">{cert.course_title || 'Certificado'}</h3>
      <p className="text-xs text-slate-400">Hash: {cert.hash || '---'}</p>
      {/* TODO: add preview/download actions */}
    </article>
  );
}

export default function CertificateList({ phone }) {
  const [certs, setCerts] = useState([]);

  useEffect(() => {
    // TODO: replace with list endpoint when available
    void loadCertificates();
  }, [phone]);

  async function loadCertificates() {
    try {
      if (!phone) return;
      const result = await lmsLiteApiV2.validateCert(phone);
      setCerts(result ? [result] : []);
    } catch (error) {
      console.error('Failed to validate certificate', error);
      setCerts([]);
    }
  }

  if (certs.length === 0) {
    return (
      <section className="grid place-items-center rounded-2xl border border-dashed border-white/20 p-8 text-center">
        <div className="mb-3 h-20 w-20 rounded-full bg-white/5" aria-hidden />
        <p className="text-sm text-slate-300">Você ainda não possui certificados disponíveis.</p>
      </section>
    );
  }

  return (
    <section className="grid gap-3 sm:grid-cols-2">
      {certs.map((cert, idx) => (
        <CertCard key={cert.hash || idx} cert={cert} />
      ))}
    </section>
  );
}
