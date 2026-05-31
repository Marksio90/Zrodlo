// Źródło – Service Worker
// Strategia: Cache-First dla statycznych assetów, Network-First dla nawigacji
const CACHE = 'zrodlo-v1';
const OFFLINE_URL = '/offline.html';

const STATIC_SHELL = [OFFLINE_URL];

// ── Install ─────────────────────────────────────────────────────────────────

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(STATIC_SHELL))
  );
  self.skipWaiting();
});

// ── Activate ─────────────────────────────────────────────────────────────────

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch ────────────────────────────────────────────────────────────────────

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Tylko requesty do własnego originu
  if (url.origin !== location.origin) return;

  // API – zawsze sieć (nigdy cache)
  if (url.pathname.startsWith('/api/')) return;

  // Next.js HMR / dev – pomijamy
  if (url.pathname.startsWith('/_next/webpack-hmr')) return;

  // Statyczne assety Next.js (immutable) – Cache First
  if (url.pathname.startsWith('/_next/static/')) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ??
          fetch(request).then((res) => {
            if (res.ok) {
              const clone = res.clone();
              caches.open(CACHE).then((c) => c.put(request, clone));
            }
            return res;
          })
      )
    );
    return;
  }

  // Nawigacja (HTML) – Network First, fallback do offline.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match(OFFLINE_URL).then(
          (r) => r ?? new Response('Brak połączenia', { status: 503 })
        )
      )
    );
    return;
  }

  // Pozostałe zasoby (obrazy, fonty) – Stale While Revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request).then((res) => {
        if (res.ok && res.type !== 'opaque') {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(request, clone));
        }
        return res;
      });
      return cached ?? fetchPromise;
    })
  );
});

// ── Push notifications ────────────────────────────────────────────────────────

self.addEventListener('push', (event) => {
  if (!event.data) return;
  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: 'Źródło', body: event.data.text() };
  }
  event.waitUntil(
    self.registration.showNotification(payload.title ?? 'Źródło', {
      body: payload.body ?? '',
      icon: '/icons/icon.svg',
      badge: '/icons/icon.svg',
      tag: payload.tag ?? 'zrodlo',
      data: { url: payload.url ?? '/dashboard' },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url ?? '/dashboard';
  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clients) => {
        const existing = clients.find((c) => c.url.includes(targetUrl));
        if (existing) return existing.focus();
        return self.clients.openWindow(targetUrl);
      })
  );
});
