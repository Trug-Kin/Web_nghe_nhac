// SPA Router - Xử lý navigation không reload trang
(function() {
    'use strict';

    // Lưu trữ content ban đầu
    const mainContent = document.getElementById('main-content');
    if (!mainContent) return;

    // Intercept tất cả link clicks
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (!link) return;
        
        const href = link.getAttribute('href');
        if (!href) return;
        
        // Bỏ qua các link đặc biệt
        if (
            href.startsWith('#') ||           // Anchor links
            href.startsWith('javascript:') || // JS links
            href.includes('logout') ||        // Logout
            link.target === '_blank' ||       // New tab
            link.hasAttribute('download') ||  // Downloads
            href.startsWith('http://') ||     // External links
            href.startsWith('https://') ||    // External links
            link.classList.contains('no-spa') // Explicitly disabled
        ) {
            return;
        }
        
        // Prevent default navigation
        e.preventDefault();
        
        // Navigate using SPA
        navigateTo(href);
    });

    // Handle browser back/forward buttons
    window.addEventListener('popstate', function(e) {
        if (e.state && e.state.path) {
            loadPage(e.state.path, false); // false = don't push to history again
        }
    });

    // Navigate to a new page
    function navigateTo(path) {
        // Don't navigate if already on this page
        if (window.location.pathname === path) {
            console.log('Already on page:', path);
            return;
        }
        
        // Pages we still force full reload (need fresh environment / security context)
        const fullReloadPaths = ['/auth/login-page','/auth/register-page'];
        if (path && (path.startsWith('/playlist/') || fullReloadPaths.includes(path))) {
            window.location.href = path;
            return;
        }
        // Fade out current content for smoother UX
        try {
            mainContent.style.transition = 'opacity .28s ease';
            mainContent.style.opacity = '0';
        } catch(_) {}
        // Update URL without reload
        history.pushState({ path: path }, '', path);
        // Load new content via AJAX (homepage now SPA-enabled so audio continues playing)
        loadPage(path, true);
    }

    // Load page content via AJAX
    function loadPage(path, pushState) {
        // Keep opacity at 0 if we triggered fade-out; else show subtle loading state
        if (parseFloat(getComputedStyle(mainContent).opacity) > 0.1) {
            mainContent.style.opacity = '0.4';
        }
        
        // Get JWT token from cookies (same as user.js)
        function getJwtTokenFromCookie() {
            const token = document.cookie
                .split("; ")
                .find((row) => row.startsWith("access_token="));
            return token ? token.split("=")[1] : null;
        }
        
        const token = getJwtTokenFromCookie();
        const headers = {
            'X-Requested-With': 'XMLHttpRequest' // Đánh dấu là AJAX request
        };
        
        // Add Authorization header if token exists
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        fetch(path, {
            headers: headers,
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Page not found');
            }
            return response.text();
        })
        .then(html => {
            // Parse HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
                // Copy body classes from fetched page so page-specific CSS applies (e.g., body.login-page)
                try {
                    document.body.className = doc.body.className || document.body.className;
                } catch (err) { /* ignore */ }

                // Extract new content
            const newContent = doc.getElementById('main-content');
            if (newContent) {
                // Replace content
                mainContent.innerHTML = newContent.innerHTML;
                // Fade-in
                requestAnimationFrame(()=>{
                    mainContent.style.opacity = '0'; // ensure starting point
                    requestAnimationFrame(()=>{ mainContent.style.opacity = '1'; });
                });
                
                // Update page title
                const newTitle = doc.querySelector('title');
                if (newTitle) {
                    document.title = newTitle.textContent;
                }

                // Copy stylesheet <link> and inline <style> tags from fetched head to current head
                try {
                    const fetchedHead = doc.querySelector('head');
                    if (fetchedHead) {
                        // Copy link[rel=stylesheet]
                        const links = Array.from(fetchedHead.querySelectorAll('link[rel="stylesheet"]'));
                        links.forEach(l => {
                            const href = l.getAttribute('href');
                            if (!href) return;
                            // Avoid duplicating same href
                            if (!document.querySelector('head link[rel="stylesheet"][href="' + href + '"]')) {
                                const newLink = document.createElement('link');
                                newLink.rel = 'stylesheet';
                                newLink.href = href;
                                document.head.appendChild(newLink);
                            }
                        });

                        // Copy inline <style> tags
                        const styles = Array.from(fetchedHead.querySelectorAll('style'));
                        styles.forEach(s => {
                            const text = s.textContent || '';
                            if (!text.trim()) return;
                            const existingStyle = Array.from(document.head.querySelectorAll('style')).find(st => st.textContent === text);
                            if (!existingStyle) {
                                const ns = document.createElement('style');
                                ns.textContent = text;
                                document.head.appendChild(ns);
                            }
                        });
                    }
                } catch (err) {
                    console.warn('Failed to copy fetched page head styles', err);
                }
                
                // Scroll to top
                window.scrollTo(0, 0);
                
                // Re-check login status after SPA navigation
                if (typeof checkLoginStatus === 'function') {
                    console.log('[SPA] Re-checking login status after navigation');
                    checkLoginStatus();
                }
                
                // Execute any <script> tags present in the fetched document (not just inside #main-content).
                // This ensures page-specific scripts injected via `scripts_extra` (which are placed after
                // #main-content in the template) also run on SPA navigation.
                try {
                    const allScriptNodes = Array.from(doc.querySelectorAll('script'));
                    allScriptNodes.forEach(s => {
                        try {
                            // If script has src, normalize to absolute URL for dedupe check
                            if (s.src) {
                                const srcAbs = new URL(s.getAttribute('src'), location.origin).href;
                                // Skip if already present in current document
                                if (document.querySelector(`script[src="${srcAbs}"]`)) return;
                                const newScript = document.createElement('script');
                                newScript.src = srcAbs;
                                newScript.async = false; // preserve execution order
                                document.body.appendChild(newScript);
                            } else {
                                const text = (s.textContent || '').trim();
                                if (!text) return;
                                // Skip if an identical inline script already exists
                                const exists = Array.from(document.querySelectorAll('script:not([src])')).some(st => (st.textContent || '').trim() === text);
                                if (exists) return;
                                const newInline = document.createElement('script');
                                newInline.textContent = text;
                                document.body.appendChild(newInline);
                            }
                        } catch (innerErr) {
                            // Continue with other scripts even if one fails
                            console.warn('Error while injecting fetched script', innerErr);
                        }
                    });
                } catch (err) {
                    console.warn('Failed to execute page scripts after SPA load', err);
                }

                // Re-trigger any scripts that need to run
                // (app.js sẽ tự động bind events do event delegation)
                
                // Trigger custom event for other scripts
                window.dispatchEvent(new CustomEvent('spa-navigated', { detail: { path } }));
            } else {
                // Fallback: full page reload
                window.location.href = path;
            }
        })
        .catch(error => {
            console.error('Navigation error:', error);
            // Fallback: full page reload
            window.location.href = path;
        });
    }

    // Export for external use
    window.SPA = {
        navigateTo: navigateTo
    };
})();
