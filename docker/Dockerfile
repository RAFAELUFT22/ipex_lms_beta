# =============================================================================
# Territórios de Desenvolvimento Social e Inclusão Produtiva — Frappe LMS Docker Image (V4 - Custom Theme)
# Inclui o kreativ_theme (Custom App) para customização visual oficial
# conforme arquitetura Frappe Framework (hooks.py + web_include_css)
# =============================================================================

FROM frappe/erpnext:version-15

USER root

RUN chown -R frappe:frappe \
    /home/frappe/frappe-bench/env \
    /home/frappe/frappe-bench/apps \
    /home/frappe/frappe-bench/sites

USER frappe
WORKDIR /home/frappe/frappe-bench

# Criar common_site_config.json temporário para satisfazer o build do frontend
RUN echo '{"socketio_port": 9000}' > sites/common_site_config.json

# Baixar apps necessários
RUN bench get-app payments --branch version-15 && \
    bench get-app lms --branch develop

# Pré-instalar dependências do frontend do LMS
RUN cd /home/frappe/frappe-bench/apps/lms/frontend && \
    yarn install --frozen-lockfile 2>/dev/null || yarn install

# ─── KREATIV THEME (Custom App — Estratégia Oficial Frappe) ───────────────────
# Copia o app de tema customizado para dentro do bench
COPY --chown=frappe:frappe kreativ_theme/ /home/frappe/frappe-bench/apps/kreativ_theme/

# Instalar o custom app no ambiente Python do bench
RUN /home/frappe/frappe-bench/env/bin/pip install -e apps/kreativ_theme

# Registrar o app para que o bench o reconheça
RUN echo "kreativ_theme" >> sites/apps.txt

# ─── FIM DO KREATIV THEME ──────────────────────────────────────────────────────

# Garantir que os apps principais estejam listados para instalação
RUN echo "payments" >> sites/apps.txt && \
    echo "lms"      >> sites/apps.txt

# Remover o config temporário para não conflitar com volumes em runtime
RUN rm sites/common_site_config.json
