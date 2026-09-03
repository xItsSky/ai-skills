# Next.js

Modern Next.js (v16+, App Router): Server Components by default, Server Functions, streaming, and the Cache Components model with `"use cache"`. The patterns below assume that baseline. Where a rule depends on a version, the version is called out. Always check the project's Next version and caching model before assuming a default.

## Mental model

The App Router renders on the server first. Server Components run on the server, produce an RSC payload plus HTML, and the client hydrates only the Client Components inside that tree.

- `page.tsx` and `layout.tsx` are Server Components until you open a client boundary.
- A `"use client"` directive marks the boundary. Everything imported below it ships to the browser.
- Server output is HTML and serialized data. The client fills in interactivity on top.

## Server vs Client Components

Default to Server Components. Reach for a Client Component only when the UI needs the browser.

| Server Component (default) | Client Component (`"use client"`) |
|---|---|
| Data fetching, DB access, backend calls | `useState`, `useEffect`, other hooks |
| Secrets and server-only code | Event handlers (`onClick`, `onChange`) |
| SEO content and HTML generation | Browser APIs (`window`, `localStorage`) |
| Less JavaScript shipped to the client | Anything interactive or stateful |

```tsx
// Server Component: async, awaits the data source directly
export default async function Page() {
  const users = await db.user.findMany();
  return <UserList users={users} />;
}
```

## Push `"use client"` as low as possible

- Mark the smallest leaf that needs interactivity, not the page or layout.
- A `"use client"` high in the tree pulls that branch and all its imports into the client bundle.
- Prefer a Server Component page that renders a small Client Component leaf (a dropdown, a form, a toggle).

## Dynamic params

- `params` and `searchParams` are async and must be awaited (Next 15+). On Next 14 and earlier they are plain objects you read directly.

```tsx
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  // ...
}
```

## The server/client boundary

- Props passed from a Server Component to a Client Component must be serializable.
- You cannot pass arbitrary functions across the boundary. Pass a Server Action reference or plain data instead.
- Fetch and shape data on the server, then hand the Client Component only what it renders.

## Data fetching

Fetch inside Server Components. Call the data source directly.

- `await getUser(id)` or hit the database or service straight from the component.
- Do not call your own Route Handler from a Server Component. That adds a pointless HTTP hop to a server that is already on the server.
- The path is Server Component to service or repository to database. Skip the internal `fetch` to `/api/...`.

Fetch independent data in parallel. Sequential `await`s create waterfalls.

```tsx
// Waterfall: each await blocks the next
const user = await getUser(id);
const posts = await getPosts(id);

// Parallel: both start at once
const [user, posts] = await Promise.all([getUser(id), getPosts(id)]);
```

## Streaming and Suspense

- Wrap slow subtrees in `<Suspense fallback={...}>` so the shell streams immediately.
- Stream the slow parts. Do not block the whole page on the slowest query.
- `loading.tsx` is Suspense for a route segment; use it for the initial route load, and explicit `<Suspense>` for finer control inside a page.

## File conventions

| File | Role |
|---|---|
| `layout.tsx` | Persistent layout wrapping child routes |
| `page.tsx` | The route's rendered UI |
| `loading.tsx` | Suspense fallback for the segment |
| `error.tsx` | Error boundary for the segment (Client Component) |
| `not-found.tsx` | 404 UI for the segment |
| `[id]/` | Dynamic route segment |
| `route.ts` | HTTP endpoint (Route Handler) |

## Route Handlers

- Live in `route.ts`, export `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`.
- They replace the old `pages/api` routes in the App Router.
- They are public HTTP endpoints. Enforce authentication, authorization, and validation on every one.
- Do not create a Route Handler just to fetch data for your own Server Components. Call the service directly instead.

## Server Functions and Server Actions

- Mark with `"use server"`. Use them for mutations: form submissions, DB writes, cache invalidation.
- A Server Action is a backend entry point. Treat it like a public API, because it is one.
- Every action runs, in order: authentication, authorization, input validation (Zod or equivalent), then the work.
- Never trust the arguments. The client can call an action with any payload.

```tsx
"use server";

export async function updateProfile(input: unknown) {
  const session = await requireSession();          // authn
  const data = profileSchema.parse(input);         // validation
  assertCanEdit(session.user, data.id);            // authz
  await db.profile.update({ where: { id: data.id }, data });
  revalidateTag("profile");
}
```

## Rendering strategies

| Strategy | When it renders | Use for |
|---|---|---|
| Static / SSG | At build, HTML reused | Stable content, marketing, docs |
| SSR / dynamic | Per request on the server | Per-user or per-request content |
| ISR | Static plus revalidation | Mostly stable content that refreshes on a schedule or tag |

## Caching (the 2026 model)

The old claim that "Next caches all `fetch` by default" is obsolete. It described Next 13-14. Do not repeat it on a current project.

- On Next 15+, `fetch` is not cached by default; you opt in per call.
- Cache Components with `"use cache"`, `cacheLife()`, and `cacheTag()` (Next 16+) let you opt into caching explicitly at the function or component level.
- Confirm the project's Next version and whether Cache Components is on before reasoning about what is cached.

```tsx
async function getUsers() {
  "use cache";
  cacheLife("hours");
  cacheTag("users");
  return db.user.findMany();
}
```

## Cache invalidation

- After a mutation, call `revalidateTag("users")` or `revalidatePath("/users")`.
- `revalidateTag` targets business data wherever it was cached. `revalidatePath` targets a specific route.
- Prefer tag invalidation when a tag maps cleanly to the data that changed. Reach for path invalidation when you want to refresh a whole route.

## Next as a BFF

Next can sit between the browser and your backend APIs and act as a backend-for-frontend.

- Handle auth server-side, keep secrets off the client, set HTTP-only cookies.
- Aggregate several backend calls and transform their responses before they reach the browser.
- This is a boundary layer, not a replacement for your business backend. Do not migrate core domain logic into Next by default.

## Security

- The client is never trusted. Anything sent from the browser can be forged.
- Validate every input server-side (Zod or equivalent) in Route Handlers and Server Actions.
- Authentication answers "who are you". Authorization answers "are you allowed". Enforce both on the server.
- Hiding a button on the client is not security. The endpoint behind it must still check authorization.

## SEO and metadata

- Server rendering gives crawlers real HTML. Lean on it.
- Export a static `metadata` object or a dynamic `generateMetadata` per route.
- Provide OpenGraph tags, `sitemap.ts`, `robots.ts`, and use `<Image>` for image optimization.

## Performance order

Work through these in order of impact:

1. Keep components as Server Components. Less client JS means less hydration.
2. Small, low Client Component leaves rather than large client subtrees.
3. Parallel data fetching with `Promise.all`, no waterfalls.
4. Streaming and Suspense for slow subtrees.
5. `<Image>`, optimized fonts, `<Link>` with prefetch.
6. Caching matched to the data (`"use cache"`, tags).
7. Dynamic imports for heavy client-only code.

## Quick reference

| Do | Instead of |
|---|---|
| Await the data source in a Server Component | `fetch` your own `/api/...` route |
| `Promise.all([...])` for independent data | Sequential `await`s (waterfall) |
| `"use client"` on the smallest leaf | `"use client"` on the page or layout |
| Pass serializable props across the boundary | Pass functions or class instances |
| Authn + authz + Zod in every Server Action | Trust the client's arguments |
| Enforce auth in Route Handlers | Assume the endpoint is private |
| `"use cache"` + `cacheTag`, check the version | "Next caches all fetch by default" |
| `revalidateTag` for business data | `revalidatePath` for everything |
| Server-side authorization | Hiding the button on the client |
