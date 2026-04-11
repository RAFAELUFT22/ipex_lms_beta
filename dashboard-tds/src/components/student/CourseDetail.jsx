import { useMemo, useState } from 'react';
import { ProgressBar } from '../shared/ProgressBar';

export default function CourseDetail({ courseSlug }) {
  const [expandedModule, setExpandedModule] = useState(null);

  const course = useMemo(
    () => ({
      title: courseSlug
        ? courseSlug
            .split('-')
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ')
        : 'Detalhes do Curso',
      instructor: 'Equipe TDS',
      progress: 42,
      quizAvailable: true,
    }),
    [courseSlug],
  );

  const modules = useMemo(
    () => [
      {
        id: 1,
        title: 'Introdução',
        status: 'done',
        duration: '10 min',
        type: 'video',
        lessons: [
          { id: 'l1', title: 'Bem-vindo ao curso', status: 'done', duration: '5 min' },
          { id: 'l2', title: 'Como aproveitar o conteúdo', status: 'done', duration: '5 min' },
        ],
      },
      {
        id: 2,
        title: 'Módulo Principal',
        status: 'available',
        duration: '25 min',
        type: 'lesson',
        lessons: [
          { id: 'l3', title: 'Conceitos fundamentais', status: 'available', duration: '15 min' },
          { id: 'l4', title: 'Aplicação prática', status: 'available', duration: '10 min' },
        ],
      },
      {
        id: 3,
        title: 'Projeto Final',
        status: 'locked',
        duration: '40 min',
        type: 'project',
        lessons: [
          { id: 'l5', title: 'Instruções do projeto', status: 'locked', duration: '10 min' },
          { id: 'l6', title: 'Entrega e avaliação', status: 'locked', duration: '30 min' },
        ],
      },
    ],
    [],
  );

  function toggleModule(id) {
    setExpandedModule((prev) => (prev === id ? null : id));
  }

  function getLessonIcon(status) {
    if (status === 'done') return { icon: 'check_circle', colorClass: 'text-secondary' };
    if (status === 'locked') return { icon: 'lock', colorClass: 'text-outline' };
    return { icon: 'play_circle', colorClass: 'text-primary' };
  }

  function getModuleIcon(status) {
    if (status === 'done') return { icon: 'check_circle', colorClass: 'text-secondary' };
    if (status === 'locked') return { icon: 'lock', colorClass: 'text-outline' };
    return { icon: 'play_circle', colorClass: 'text-primary' };
  }

  return (
    <div className="min-h-screen bg-surface">
      {/* Hero section */}
      <div className="bg-surface-container-low p-8 rounded-b-[2rem]">
        <span className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold">Curso</span>
        <h1 className="text-3xl font-bold font-headline text-on-surface mt-1">{course.title}</h1>
        <p className="text-on-surface-variant text-sm flex items-center gap-2 mt-2">
          <span className="material-symbols-outlined text-base">school</span>
          {course.instructor}
        </p>
        <div className="mt-6">
          <ProgressBar value={course.progress} label="Progresso geral" showPercent />
          <p className="text-xs text-on-surface-variant mt-1">{course.progress}% concluído</p>
        </div>
      </div>

      <main className="px-4 pt-6 pb-24 space-y-4 max-w-2xl mx-auto">
        {/* Modules accordion */}
        <section className="space-y-3">
          <h2 className="text-on-surface font-bold text-base px-2">Módulos</h2>
          {modules.map((module) => {
            const { icon, colorClass } = getModuleIcon(module.status);
            const isOpen = expandedModule === module.id;
            return (
              <div key={module.id} className="bg-surface-container-low rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleModule(module.id)}
                  className="w-full p-4 flex items-center justify-between gap-3 cursor-pointer text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className={`material-symbols-outlined text-xl ${colorClass}`}>{icon}</span>
                    <span className="font-bold text-on-surface text-sm">{module.title}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">schedule</span>
                      {module.duration}
                    </span>
                    <span className={`material-symbols-outlined text-on-surface-variant transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
                      expand_more
                    </span>
                  </div>
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 space-y-2">
                    {module.lessons.map((lesson) => {
                      const lessonIcon = getLessonIcon(lesson.status);
                      return (
                        <div
                          key={lesson.id}
                          className="flex items-center gap-3 py-2 px-3 rounded-lg bg-surface-container-high"
                        >
                          <span className={`material-symbols-outlined text-base ${lessonIcon.colorClass}`}>
                            {lessonIcon.icon}
                          </span>
                          <span className="text-sm text-on-surface flex-1">{lesson.title}</span>
                          <span className="text-xs text-on-surface-variant flex items-center gap-1">
                            <span className="material-symbols-outlined text-sm">schedule</span>
                            {lesson.duration}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </section>

        {/* Quiz available card */}
        {course.quizAvailable && (
          <div className="bg-secondary-fixed rounded-xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="material-symbols-outlined text-on-secondary-fixed text-2xl">quiz</span>
              <h3 className="font-bold text-on-secondary-fixed text-base">Quiz disponível!</h3>
            </div>
            <p className="text-sm text-on-secondary-fixed/80 mb-4">
              Teste seus conhecimentos sobre {course.title} e desbloqueie sua conquista.
            </p>
            <button
              type="button"
              className="bg-cerrado-gradient text-white rounded-xl py-3 px-6 font-bold text-sm w-full"
            >
              Iniciar Quiz
            </button>
          </div>
        )}

        {/* Certificate card */}
        {course.progress < 100 ? (
          <div className="bg-surface-container-high rounded-xl p-6 flex items-center gap-4">
            <span className="material-symbols-outlined text-4xl text-outline">lock</span>
            <div>
              <h3 className="font-bold text-on-surface text-base">Certificado</h3>
              <p className="text-sm text-on-surface-variant mt-1">
                Complete 100% para desbloquear seu certificado.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-cerrado-gradient rounded-xl p-6 flex items-center gap-4">
            <span className="material-symbols-outlined text-4xl text-white">workspace_premium</span>
            <div>
              <h3 className="font-bold text-white text-base">Certificado disponível!</h3>
              <p className="text-sm text-white/80 mt-1">
                Parabéns! Você concluiu o curso com sucesso.
              </p>
              <button
                type="button"
                className="mt-3 bg-white/20 text-white rounded-xl py-2 px-4 font-bold text-sm"
              >
                Ver Certificado
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
