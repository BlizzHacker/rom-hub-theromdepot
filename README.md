# The ROM Depot provider for ROM Hub / ROMarr

**Status: not installable. This repository is documentation and a catalogue
entry, not a working provider.**

| Capability | Status |
|---|---|
| `search` | **Unavailable** — the API requires a logged-in session, which an RPP v1 plugin cannot hold |
| `importer` | **Unavailable** — same reason |
| `stream` | **Unavailable** — the site hosts no player |

This is the most frustrating result of the seven-site survey, because The ROM
Depot is technically the *easiest* of them all — and it is still blocked, by
the plugin runtime rather than by the site.

## What the site offers

`theromdepot.com` is a Vite/React single-page app. It has no `robots.txt` —
requesting one returns the SPA shell, because the server serves `index.html`
for every unmatched route. Its JavaScript bundle
(`/assets/index-DVaFPJRP.js`, 989 KB) names a small, clean API:

```
/api/getContents        /api/download/          /api/login
/api/checkLoginStatus   /api/profile            /api/download-history
/api/register           /api/forgot-password    /api/change-password
```

`GET /api/getContents` is a **single, unpaginated call that returns the entire
directory tree as JSON** — `name`, `size`, `mtime`, `path`, and a child count
per node. No pagination to walk, no HTML to parse, no rate limiting to
respect, no anti-bot challenge anywhere on the site.

That would have made this the easiest provider of the seven by a wide margin.

## Why it cannot be built anyway

`GET /api/getContents` returns:

```
HTTP/1.1 401 Unauthorized
{"message":"Unauthorized"}
```

Browsing requires an account. That alone would be workable if a plugin could
log in — but it cannot, and this is worth being precise about, because it is a
property of ROM Hub rather than a difficulty to be overcome.

From the site's own bundle, the session is established by:

```js
fetch("/api/login", {method: "POST", headers: {"Content-Type": "application/json"},
                     body: JSON.stringify({username, password})})
```

…and carried by a **cookie** — credentials are `same-origin`, and no
`Authorization` header appears anywhere in the bundle.

Now the runtime, from `rom_hub_sdk/context.py` and `rom_hub/broker/fetcher.py`:

* **`ctx.http` exposes `get()` and nothing else.** There is no POST, so the
  login call cannot be made.
* **The cookie jar is cleared before every single request** —
  `fetcher.get()` calls `self._client.cookies.clear()` deliberately, so that
  one plugin's `Set-Cookie` cannot ride along on another plugin's request to
  the same host. So even if a session existed, it could not be carried into
  the next call.
* A plugin has no socket of its own either: the subprocess installs a seccomp
  filter before any plugin module is imported, so `import socket` raises
  `PermissionError`.

**So an RPP v1 plugin cannot authenticate to this site.** Not "not yet", and
not "unless you try harder" — there is no code that could be written inside a
plugin that would do it.

## What was deliberately not done

* **No login was attempted.** The owner has an account here; it was not used,
  and no credential of any kind was entered anywhere.
* **The JSON schema of `getContents` was not verified**, because seeing it
  requires being logged in. The field names above are read off the site's own
  JavaScript, not off a response.

  That is the reason this repository ships no parser. Writing one against a
  schema nobody has seen would produce exactly the thing this project refuses
  elsewhere: something that looks like it works.

* **No `password` config key is declared.** This is a deliberate departure
  worth flagging: a config field that accepts a credential the plugin can
  never transmit is a place for a password to sit for no reason. When a
  working path exists (below), the credential belongs to whichever component
  actually performs the login — and in both candidate designs, that component
  is the operator's own browser, which already has it.

## The two paths that would actually work

Either of these is a real project, and both keep the credential with the
operator rather than in the plugin:

1. **Operator-supplied export.** Because `getContents` is one GET returning
   the whole tree, an operator who is already logged in can save that JSON
   from their browser and point the plugin at the file. The provider then
   reads and validates it and never touches the network for the catalogue at
   all. This is the smaller of the two and is the natural fit here.

2. **Companion capture extension**, exactly as the Vimm.net provider does: a
   Manifest V3 extension builds the catalogue from pages the operator's own
   browser is already authorised to see, and the provider revalidates every
   URL before using it.

Both need the JSON schema confirmed first, which needs one logged-in look at
`/api/getContents` — an operator's action, not this survey's.

## Terms

Nothing here fetches, indexes or redistributes anything. This repository
records a finding.

## License

MIT — see `LICENSE`.
