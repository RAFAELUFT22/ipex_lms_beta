import { useEffect, useMemo, useState } from 'react';
import { Megaphone, PlusCircle, Users, Send } from 'lucide-react';
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
    <section className="space-y-4">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Megaphone className="h-5 w-5 text-teal-400" />
          <h2 className="text-xl font-semibold text-white">Gerenciar Comunidades</h2>
        </div>

        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 rounded-full border border-teal-500/40 bg-teal-500/20 px-4 py-2 text-sm text-teal-100"
        >
          <PlusCircle className="h-4 w-4" />
          Nova Comunidade
        </button>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sortedCommunities.map((community) => (
          <article
            key={community.slug}
            className="glass-card rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
          >
            <div className="mb-2 flex items-start justify-between">
              <div>
                <h3 className="text-base font-semibold text-white">{community.title}</h3>
                <p className="text-xs text-slate-400">{community.whatsapp_group_id}</p>
              </div>

              <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">
                <Users className="h-3 w-3" />
                {community.member_count || 0}
              </span>
            </div>

            <p className="mb-4 text-sm text-slate-300">{community.description || 'Sem descrição.'}</p>

            <button
              type="button"
              onClick={() => handleBroadcast(community.slug)}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-amber-400/20 px-3 py-2 text-sm text-amber-200"
            >
              <Send className="h-4 w-4" />
              Enviar Aviso
            </button>
          </article>
        ))}
      </div>

      {!loading && communities.length === 0 && (
        <p className="rounded-xl border border-dashed border-white/20 p-6 text-center text-sm text-slate-400">
          Nenhuma comunidade cadastrada.
        </p>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4">
          <form onSubmit={handleCreateCommunity} className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold text-white">Nova Comunidade</h3>
            {/* TODO: replace with reusable form fields */}
            <div className="space-y-3">
              {['title', 'slug', 'whatsapp_group_id', 'description'].map((field) => (
                <input
                  key={field}
                  value={form[field]}
                  onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
                  placeholder={field}
                  className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white"
                />
              ))}
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="rounded-lg px-3 py-2 text-sm text-slate-300">Cancelar</button>
              <button type="submit" className="rounded-lg bg-teal-600 px-3 py-2 text-sm text-white">Criar</button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
