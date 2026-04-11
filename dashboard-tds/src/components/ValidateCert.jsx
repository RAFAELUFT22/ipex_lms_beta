import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import { lmsLiteApi } from '../api/lms_lite';

export default function ValidateCert({ hash }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hash) { setLoading(false); return; }
    lmsLiteApi.validateCert(hash)
      .then(data => setResult(data))
      .catch(() => setResult({ valid: false }))
      .finally(() => setLoading(false));
  }, [hash]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-deep">
      <Loader className="animate-spin text-primary" size={40} />
    </div>
  );

  return (
    <div className="flex items-center justify-center min-h-screen bg-deep p-4">
      <div className="glass-card p-8 max-w-md w-full text-center">
        {result?.valid ? (
          <>
            <CheckCircle size={56} className="text-emerald-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-emerald-500 mb-2">Certificado Válido</h1>
            <p className="text-text-dim text-sm mb-6">Este certificado é autêntico e foi emitido pelo TDS.</p>
            <div className="bg-white/5 rounded-xl p-4 text-left space-y-2 text-sm">
              <div><span className="text-text-muted">Aluno:</span> <span className="font-bold">{result.student_name}</span></div>
              <div><span className="text-text-muted">Curso:</span> <span className="font-bold">{result.course_title || result.course}</span></div>
              <div><span className="text-text-muted">Emitido em:</span> <span className="font-bold">{result.issue_date}</span></div>
              <div><span className="text-text-muted">Hash:</span> <span className="font-mono text-xs text-text-muted">{hash}</span></div>
            </div>
          </>
        ) : (
          <>
            <XCircle size={56} className="text-red-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-red-500 mb-2">Certificado Inválido</h1>
            <p className="text-text-dim text-sm">Este hash não corresponde a nenhum certificado emitido pelo TDS.</p>
          </>
        )}
      </div>
    </div>
  );
}
