import { useEffect, useMemo, useState } from 'react';
import { lmsLiteApiV2 } from '../api/lms_lite_v2';

export default function CommunityManager() {
  const [communities, setCommunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const [form, setForm] = useState({
    title: '',
    slug: '',
    whatsapp_group_id: '',
    description: '',
  });

  const sortedCommunities = useMemo(
    () => [...communities].sort((a, b) => (b.member_count || 0) - (a.member_count || 0)),
    [communities],
  );

  useEffect(() => {
    void loadCommunities();
  }, []);

  async function loadCommunities() {
    setLoading(true);
    try {
      const data = await lmsLiteApiV2.getCommunities();
      setCommunities(Array.isArray(data) ? data : []);
    } catch (error) {
      // TODO: add toast error handling
      console.error('Failed to load communities', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateCommunity(event) {
    event.preventDefault();
    try {
      // TODO: validate form and show inline errors
      await lmsLiteApiV2.createCommunity(form);
      setShowModal(false);
      setForm({ title: '', slug: '', whatsapp_group_id: '', description: '' });
      await loadCommunities();
    } catch (error) {
      // TODO: add toast error handling
      console.error('Failed to create community', error);
    }
  }

  async function handleBroadcast(slug) {
    const message = window.prompt('Digite a mensagem para a comunidade:');
    if (!message) return;

    try {
      await lmsLiteApiV2.broadcastToCommunity(slug, message);
      // TODO: show success toast
    } catch (error) {
      // TODO: add toast error handling
      console.error('Failed to broadcast message', error);
    }
  }

  return (
    <section className="space-y-8 bg-surface text-on-surface">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <p className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold mb-1">
            Comunidades WhatsApp
          </p>
          <h2 className="text-on-surface font-headline font-bold text-3xl tracking-tight">
            Dashboard de Comunidades
          </h2>
        </div>

        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 bg-secondary-container text-on-secondary-container rounded-xl font-bold px-4 py-2 text-sm"
        >
          <span className="material-symbols-outlined text-base">add_circle</span>
          Nova Comunidade
        </button>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-surface-container-low p-6 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <span className="material-symbols-outlined text-primary text-2xl">campaign</span>
            <span className="text-on-surface-variant text-sm font-label font-bold uppercase tracking-wider">
              Comunidades Ativas
            </span>
          </div>
          <p className="text-3xl font-bold text-on-surface">{communities.length}</p>
        </div>

        <div className="bg-surface-container-highest p-6 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <span className="material-symbols-outlined text-primary text-2xl">groups</span>
            <span className="text-on-surface-variant text-sm font-label font-bold uppercase tracking-wider">
              Total de Membros
            </span>
          </div>
          <p className="text-3xl font-bold text-on-surface">
            {communities.reduce((sum, c) => sum + (c.member_count || 0), 0)}
          </p>
        </div>

        <div className="bg-secondary-fixed p-6 rounded-xl">
          <div className="flex items-center gap-3 mb-2">
            <span className="material-symbols-outlined text-on-secondary-fixed text-2xl">trending_up</span>
            <span className="text-on-secondary-fixed text-sm font-label font-bold uppercase tracking-wider">
              Mensagens Enviadas
            </span>
          </div>
          <p className="text-3xl font-bold text-on-secondary-fixed">—</p>
        </div>
      </div>

      {/* Community cards grid */}
      {!loading && communities.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedCommunities.map((community) => (
            <article key={community.slug} className="cerrado-card p-6 space-y-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="text-on-surface font-bold text-base leading-tight truncate">
                    {community.title}
                  </h3>
                  <p className="text-on-surface-variant text-xs mt-0.5 truncate">
                    {community.whatsapp_group_id}
                  </p>
                </div>

                <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-secondary-fixed text-on-secondary-fixed px-3 py-1 text-xs font-bold">
                  <span className="material-symbols-outlined text-sm">groups</span>
                  {community.member_count || 0}
                </span>
              </div>

              <p className="text-on-surface-variant text-sm">
                {community.description || 'Sem descrição.'}
              </p>

              <button
                type="button"
                onClick={() => handleBroadcast(community.slug)}
                className="inline-flex w-full items-center justify-center gap-2 bg-cerrado-gradient text-white rounded-xl font-bold px-4 py-2 text-sm"
              >
                <span className="material-symbols-outlined text-base">send</span>
                Enviar Aviso
              </button>
            </article>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && communities.length === 0 && (
        <div className="bg-surface-container-low rounded-xl p-12 text-center space-y-4">
          <span className="material-symbols-outlined text-on-surface-variant text-6xl block">campaign</span>
          <p className="text-on-surface-variant text-sm font-bold">
            Nenhuma comunidade cadastrada.
          </p>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 bg-secondary-container text-on-secondary-container rounded-xl font-bold px-4 py-2 text-sm"
          >
            <span className="material-symbols-outlined text-base">add_circle</span>
            Criar primeira comunidade
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="bg-surface-container-low rounded-xl p-12 text-center">
          <span className="material-symbols-outlined text-primary text-4xl block animate-spin">refresh</span>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <form
            onSubmit={handleCreateCommunity}
            className="w-full max-w-md bg-surface-container-low rounded-xl p-6 space-y-5 shadow-xl"
          >
            <div>
              <p className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold mb-1">
                Nova comunidade
              </p>
              <h3 className="text-on-surface font-headline font-bold text-xl">
                Criar Comunidade
              </h3>
            </div>

            {/* TODO: replace with reusable form fields */}
            <div className="space-y-3">
              {[
                { key: 'title', placeholder: 'Nome da comunidade' },
                { key: 'slug', placeholder: 'Slug (identificador único)' },
                { key: 'whatsapp_group_id', placeholder: 'ID do grupo WhatsApp' },
                { key: 'description', placeholder: 'Descrição (opcional)' },
              ].map(({ key, placeholder }) => (
                <input
                  key={key}
                  value={form[key]}
                  onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="w-full bg-surface-container-high border-none rounded-lg px-3 py-2 text-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-secondary/50 placeholder:text-on-surface-variant"
                />
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="rounded-xl px-4 py-2 text-sm font-bold text-on-surface-variant hover:bg-surface-container-high transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="bg-cerrado-gradient text-white rounded-xl font-bold px-4 py-2 text-sm"
              >
                Criar
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
