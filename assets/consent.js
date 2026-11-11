/* Cookie choices for dotnetmadeeasy.com.
 *
 * The consent defaults are set in each page's <head> (src/partials/consent-head.html)
 * before any Google tag runs: advertising cookies start off in the EEA, the UK and
 * Switzerland, a stored choice is re-applied on every page, and a Global Privacy
 * Control signal counts as "Reject all". This file shows the banner on a first
 * visit, stores the visitor's choice in localStorage and passes it to Google
 * Consent Mode. Any element with data-cookie-settings (the "Privacy choices" footer
 * link) reopens it. When Google's own consent message (the AdSense Privacy &
 * messaging CMP) appears, it takes precedence and this banner steps aside.
 */
(function () {
    var KEY = 'dme-cookie-consent';

    function apply(choice) {
        var v = choice === 'accepted' ? 'granted' : 'denied';
        try {
            if (typeof window.gtag === 'function') {
                window.gtag('consent', 'update', { ad_storage: v, ad_user_data: v, ad_personalization: v, analytics_storage: v });
            }
        } catch (e) {}
    }

    function addStyles() {
        if (document.getElementById('dme-consent-css')) return;
        var s = document.createElement('style');
        s.id = 'dme-consent-css';
        s.textContent =
            '.dme-consent{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:10050;width:min(720px,calc(100% - 32px));box-sizing:border-box;' +
            'display:flex;flex-wrap:wrap;align-items:center;gap:14px 20px;padding:16px 20px;border-radius:14px;' +
            'background:#161A23;color:#E2E8F0;border:1px solid #2A3042;box-shadow:0 12px 40px rgba(0,0,0,.45);' +
            "font:400 14px/1.55 'Space Grotesk',system-ui,-apple-system,'Segoe UI',sans-serif}" +
            '.dme-consent p{margin:0;flex:1 1 320px}' +
            '.dme-consent a{color:#C4B5FD;text-decoration:underline;text-underline-offset:2px}' +
            '.dme-consent-actions{display:flex;gap:10px;flex:0 0 auto}' +
            '.dme-consent button{font-family:inherit;font-weight:600;font-size:14px;line-height:1;padding:10px 18px;border-radius:999px;cursor:pointer;' +
            'background:rgba(139,92,246,.14);color:#EDE9FE;border:1px solid rgba(139,92,246,.55)}' +
            '.dme-consent button:hover{background:rgba(139,92,246,.26)}' +
            '.dme-consent button:focus-visible,.dme-consent a:focus-visible{outline:2px solid #C4B5FD;outline-offset:2px}' +
            '[data-theme="light"] .dme-consent{background:#FFFFFF;color:#1E293B;border-color:#E2E8F0;box-shadow:0 12px 40px rgba(15,23,42,.18)}' +
            '[data-theme="light"] .dme-consent a{color:#6D3FE0}' +
            '[data-theme="light"] .dme-consent button{background:rgba(109,63,224,.08);color:#4C1D95;border-color:rgba(109,63,224,.45)}' +
            '@media (max-width:520px){.dme-consent{bottom:10px;padding:14px 16px}.dme-consent-actions{width:100%}.dme-consent button{flex:1}}';
        document.head.appendChild(s);
    }

    function googleMessageShown() {
        return !!document.querySelector('.fc-consent-root, .fc-dialog-container');
    }

    function show(force) {
        var stored = null;
        try { stored = localStorage.getItem(KEY); } catch (e) { if (!force) return; }
        if (!force && (stored === 'accepted' || stored === 'rejected')) return;
        // A Global Privacy Control signal is already a choice ("Reject all"); don't ask again.
        if (!force && navigator.globalPrivacyControl === true) return;
        if (document.querySelector('.dme-consent')) return;

        addStyles();
        var banner = document.createElement('div');
        banner.className = 'dme-consent';
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-live', 'polite');
        banner.setAttribute('aria-label', 'Cookie choices');
        banner.innerHTML =
            '<p>We use cookies to show ads (Google AdSense), which fund the course. Your lesson progress stays in your browser either way. ' +
            'Choose whether to allow advertising cookies; you can change this any time from &ldquo;Privacy choices&rdquo; in the footer. ' +
            '<a href="/privacy.html#cookies">Privacy policy</a></p>' +
            '<div class="dme-consent-actions">' +
            '<button type="button" data-choice="rejected">Reject all</button>' +
            '<button type="button" data-choice="accepted">Accept all</button>' +
            '</div>';
        document.body.appendChild(banner);
        banner.addEventListener('click', function (e) {
            var b = e.target.closest && e.target.closest('button[data-choice]');
            if (!b) return;
            var choice = b.getAttribute('data-choice');
            try { localStorage.setItem(KEY, choice); } catch (err) {}
            apply(choice);
            banner.remove();
        });

        // Google's certified consent message (EEA, UK, Switzerland) takes precedence.
        if (!force) {
            var checks = 0;
            var timer = setInterval(function () {
                checks++;
                if (googleMessageShown()) { banner.remove(); clearInterval(timer); }
                if (checks > 20) clearInterval(timer);
            }, 300);
        }
    }

    document.addEventListener('click', function (e) {
        var link = e.target.closest && e.target.closest('[data-cookie-settings]');
        if (!link) return;
        e.preventDefault();
        if (window.googlefc && typeof window.googlefc.showRevocationMessage === 'function' && googleMessageShown()) {
            window.googlefc.showRevocationMessage();
            return;
        }
        show(true);
    });

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { show(false); });
    else show(false);
})();
