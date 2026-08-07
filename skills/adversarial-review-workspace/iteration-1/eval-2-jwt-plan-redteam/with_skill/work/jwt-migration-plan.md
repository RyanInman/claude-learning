# Plan: Migrate Auth from Server Sessions to JWTs

## Goal

Replace our Redis-backed session auth with stateless JWTs so the API tier scales horizontally
without a shared session store, and so our upcoming mobile app can use the same auth as the web
app.

## Current state

- Monolith Flask API, ~40k daily active users.
- Session cookie (`sid`) → Redis lookup on every request.
- Redis cluster is our only stateful infra besides Postgres; ops wants to retire it.
- Web SPA (React) is the only client today; mobile app ships next quarter.

## Design decisions

1. **Access tokens:** RS256-signed JWTs, 24-hour expiry, issued by the existing `/login` endpoint.
   Claims: `sub`, `role`, `exp`, `iat`.
2. **Storage:** The SPA stores the JWT in `localStorage` so it survives page reloads and is easy
   to attach as a `Bearer` header from our fetch wrapper.
3. **No refresh tokens for v1.** 24-hour expiry means users log in at most once a day, which
   matches our current session TTL. Refresh-token rotation adds server state, which defeats the
   purpose of going stateless.
4. **Logout:** Client-side only — delete the token from `localStorage`. Since tokens are
   stateless, server-side logout would require a denylist, which reintroduces Redis.
5. **Cutover:** Single release. The `/login` endpoint starts issuing JWTs, the session middleware
   is removed in the same deploy, and all logged-in users re-authenticate once.
6. **Key management:** One RS256 keypair, generated at deploy time, stored in the deployment
   environment variables. Rotation deferred to v2.

## Timeline

Two sprints: sprint 1 for the token issuance + middleware, sprint 2 for SPA changes and cutover.
