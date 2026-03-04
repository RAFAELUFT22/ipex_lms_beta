# =============================================================================
# Kreativ Education — Frappe LMS Docker Image
#
# Baseado na imagem oficial ERPNext v15 + app LMS (Frappe Learning)
# Pré-instala dependências do frontend para evitar OOM em runtime
# =============================================================================

FROM frappe/erpnext:version-15

LABEL maintainer="Kreativ Educação <admin@extensionista.site>"
LABEL description="Frappe LMS (Learning Management System) for Kreativ Education"
LABEL version="2.44.0"

USER root
RUN chown -R frappe:frappe \
    /home/frappe/frappe-bench/env \
    /home/frappe/frappe-bench/apps \
    /home/frappe/frappe-bench/sites

USER frappe

# Clonar o app LMS e instalar dependências Python
RUN git clone --depth 1 --branch develop \
    https://github.com/frappe/lms.git \
    /home/frappe/frappe-bench/apps/lms && \
    cd /home/frappe/frappe-bench && \
    env/bin/pip install -e apps/lms && \
    echo "frappe"  >  sites/apps.txt && \
    echo "erpnext" >> sites/apps.txt && \
    echo "lms"     >> sites/apps.txt

# Pré-instalar dependências do frontend (evita OOM ao rodar bench build em runtime)
RUN cd /home/frappe/frappe-bench/apps/lms/frontend && \
    yarn install --frozen-lockfile 2>/dev/null || yarn install
