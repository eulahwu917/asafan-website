(function () {
  'use strict';

  var STORAGE_KEY = 'asafan-consent-v1';
  var GA_ID = 'G-FJ24086P54';
  var GTM_ID = 'GTM-TLD85DRR';
  var META_ID = '1381605680078293';
  var current = readConsent();
  var preferencesTrigger = null;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

  // Default to no optional storage before any Google code can load.
  window.gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500
  });
  window.gtag('set', 'ads_data_redaction', true);

  function readConsent() {
    try {
      var parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY));
      if (!parsed || parsed.version !== 1) return null;
      return {
        version: 1,
        analytics: parsed.analytics === true,
        marketing: parsed.marketing === true,
        updatedAt: parsed.updatedAt || null
      };
    } catch (_) {
      return null;
    }
  }

  function saveConsent(preferences) {
    current = {
      version: 1,
      analytics: preferences.analytics === true,
      marketing: preferences.marketing === true,
      updatedAt: new Date().toISOString()
    };
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
    } catch (_) {}
    applyConsent(current);
    hideBanner();
    closePreferences();
    document.dispatchEvent(new CustomEvent('asafan:consent-updated', { detail: current }));
  }

  function loadScript(id, src) {
    if (document.getElementById(id)) return;
    var script = document.createElement('script');
    script.id = id;
    script.async = true;
    script.src = src;
    document.head.appendChild(script);
  }

  function loadAnalytics() {
    if (window.__asafanAnalyticsLoaded) return;
    window.__asafanAnalyticsLoaded = true;
    loadScript('asafan-gtag', 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID));
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { anonymize_ip: true });
  }

  function loadTagManager() {
    if (window.__asafanTagManagerLoaded) return;
    window.__asafanTagManagerLoaded = true;
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    loadScript('asafan-gtm', 'https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(GTM_ID));
  }

  function loadMetaPixel() {
    if (window.__asafanMetaLoaded) return;
    window.__asafanMetaLoaded = true;
    !function(f,b,e,v,n,t,s) {
      if (f.fbq) return;
      n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};
      if(!f._fbq)f._fbq=n;
      n.push=n;n.loaded=true;n.version='2.0';n.queue=[];
      t=b.createElement(e);t.async=true;t.src=v;
      s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', META_ID);
    window.fbq('track', 'PageView');
  }

  function applyConsent(preferences) {
    var analytics = preferences && preferences.analytics === true;
    var marketing = preferences && preferences.marketing === true;
    window.gtag('consent', 'update', {
      analytics_storage: analytics ? 'granted' : 'denied',
      ad_storage: marketing ? 'granted' : 'denied',
      ad_user_data: marketing ? 'granted' : 'denied',
      ad_personalization: marketing ? 'granted' : 'denied'
    });
    if (analytics) loadAnalytics();
    // GTM is kept behind marketing consent because its container may include
    // non-Google marketing tags that do not understand Google Consent Mode.
    if (marketing) {
      loadTagManager();
      loadMetaPixel();
    }
  }

  function renderControls() {
    if (document.getElementById('cookieConsent')) return;
    var wrapper = document.createElement('div');
    wrapper.innerHTML = [
      '<section class="cookie-consent" id="cookieConsent" aria-labelledby="cookieConsentTitle" hidden>',
      '  <div class="cookie-consent__content">',
      '    <h2 id="cookieConsentTitle">Sua privacidade importa</h2>',
      '    <p>Usamos cookies opcionais para medir o uso do site e, com sua autorização, para marketing. Cookies necessários permanecem ativos. Saiba mais na <a href="/privacidade.html">Política de Privacidade</a>.</p>',
      '  </div>',
      '  <div class="cookie-consent__actions">',
      '    <button type="button" class="btn btn--outline cookie-consent__customize" data-consent-action="customize">Personalizar</button>',
      '    <button type="button" class="btn btn--outline" data-consent-action="reject">Recusar opcionais</button>',
      '    <button type="button" class="btn btn--red" data-consent-action="accept">Aceitar todos</button>',
      '  </div>',
      '</section>',
      '<div class="cookie-preferences" id="cookiePreferences" role="dialog" aria-modal="true" aria-labelledby="cookiePreferencesTitle" hidden>',
      '  <div class="cookie-preferences__panel">',
      '    <button type="button" class="cookie-preferences__close" data-consent-action="close" aria-label="Fechar preferências">&times;</button>',
      '    <h2 id="cookiePreferencesTitle">Preferências de privacidade</h2>',
      '    <p>Você pode alterar estas escolhas a qualquer momento.</p>',
      '    <div class="cookie-preferences__option">',
      '      <div><strong>Necessários</strong><span>Segurança, preferências e funcionamento básico.</span></div>',
      '      <input type="checkbox" checked disabled aria-label="Cookies necessários sempre ativos">',
      '    </div>',
      '    <label class="cookie-preferences__option">',
      '      <div><strong>Analytics</strong><span>Google Analytics para entender visitas e melhorar o site.</span></div>',
      '      <input type="checkbox" id="consentAnalytics">',
      '    </label>',
      '    <label class="cookie-preferences__option">',
      '      <div><strong>Marketing</strong><span>Google Tag Manager e Meta Pixel para campanhas e conversões.</span></div>',
      '      <input type="checkbox" id="consentMarketing">',
      '    </label>',
      '    <button type="button" class="btn btn--red cookie-preferences__save" data-consent-action="save">Salvar preferências</button>',
      '  </div>',
      '</div>'
    ].join('');
    while (wrapper.firstChild) document.body.appendChild(wrapper.firstChild);

    document.addEventListener('click', function (event) {
      var actionTarget = event.target.closest('[data-consent-action]');
      var settingsTarget = event.target.closest('.js-cookie-settings');
      if (settingsTarget) {
        event.preventDefault();
        openPreferences();
        return;
      }
      if (!actionTarget) return;
      var action = actionTarget.getAttribute('data-consent-action');
      if (action === 'accept') saveConsent({ analytics: true, marketing: true });
      if (action === 'reject') saveConsent({ analytics: false, marketing: false });
      if (action === 'customize') openPreferences();
      if (action === 'close') closePreferences();
      if (action === 'save') saveConsent({
        analytics: document.getElementById('consentAnalytics').checked,
        marketing: document.getElementById('consentMarketing').checked
      });
    });

    document.addEventListener('keydown', function (event) {
      var modal = document.getElementById('cookiePreferences');
      if (!modal || modal.hidden) return;
      if (event.key === 'Escape') {
        closePreferences();
        return;
      }
      if (event.key !== 'Tab') return;
      var focusable = modal.querySelectorAll('button:not([disabled]), input:not([disabled]), a[href]');
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    if (!current) showBanner();
  }

  function showBanner() {
    var banner = document.getElementById('cookieConsent');
    if (banner) banner.hidden = false;
  }

  function hideBanner() {
    var banner = document.getElementById('cookieConsent');
    if (banner) banner.hidden = true;
  }

  function openPreferences() {
    var modal = document.getElementById('cookiePreferences');
    if (!modal) return;
    preferencesTrigger = document.activeElement;
    document.getElementById('consentAnalytics').checked = !!(current && current.analytics);
    document.getElementById('consentMarketing').checked = !!(current && current.marketing);
    modal.hidden = false;
    document.body.classList.add('has-cookie-modal');
    var close = modal.querySelector('.cookie-preferences__close');
    if (close) close.focus();
  }

  function closePreferences() {
    var modal = document.getElementById('cookiePreferences');
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.classList.remove('has-cookie-modal');
    if (preferencesTrigger && typeof preferencesTrigger.focus === 'function') {
      preferencesTrigger.focus();
    }
    preferencesTrigger = null;
  }

  if (current) applyConsent(current);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderControls);
  } else {
    renderControls();
  }

  window.AsaConsent = {
    get: function () { return current; },
    open: openPreferences
  };
}());
