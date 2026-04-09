document.addEventListener('DOMContentLoaded', () => {
    console.log('Kreativ LMS JS Loaded');
    
    const injectLayout = () => {
        if (document.getElementById('kreativ-sidebar')) return;

        // Create Sidebar
        const sidebar = document.createElement('div');
        sidebar.id = 'kreativ-sidebar';
        sidebar.innerHTML = \`
            <div class="brand">
                <img src="/files/logo_tds_oficial.png" style="width: 40px;">
            </div>
            <div class="nav-icon-box active"><svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg></div>
            <div class="nav-icon-box"><svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg></div>
        \`;
        
        document.body.appendChild(sidebar);
        document.body.classList.add('kreativ-layout-active');
        
        // Wrap #app
        const app = document.getElementById('app');
        if (app) {
            const container = document.createElement('div');
            container.id = 'app-container';
            app.parentNode.insertBefore(container, app);
            container.appendChild(app);
        }
    };

    // Run injection and retry if SPA re-renders
    injectLayout();
    const observer = new MutationObserver(injectLayout);
    observer.observe(document.body, { childList: true });
});
