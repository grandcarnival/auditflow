# Technical Risks

## Risk Register

| Risk | Severity | Why It Matters | Mitigation |
| --- | --- | --- | --- |
| PowerPoint formatting preservation is harder than high-level libraries allow | Critical | This is the core product promise | Run first spike on real decks; use Open XML hybrid strategy if needed |
| PPTX output becomes image-based instead of editable | Critical | Users require editable exports | Set editable object preservation as an acceptance criterion |
| AI creates uncited or unsupported audit claims | High | Audit materials are high-trust documents | Require citations, confidence scores, structured validation, and review gates |
| Tenant data leaks through retrieval or storage paths | Critical | Enterprise confidentiality failure | Organization/project metadata filters, RLS, storage policies, and tests |
| Supabase Edge Functions are insufficient for large file processing | High | PPTX/PDF parsing can be CPU or memory heavy | Abstract processing behind job interface; add dedicated worker if spike requires |
| Next.js 15 security/patch line uncertainty | High | App Router has had critical security patches | Pin latest patched Next.js 15 or approve upgrade to current stable |
| Supabase SSR auth misconfiguration | High | Cookie/session mistakes can expose data | Follow `@supabase/ssr`, use `getUser()` server-side, test protected flows |
| Stripe webhook drift causes entitlement errors | Medium | Customers may get wrong access | Verify signatures, make webhook idempotent, store event ids |
| Sentry/Mixpanel accidentally capture confidential text | High | Audit content is sensitive | Scrub payloads, log metadata not document content |
| Large decks cause slow exports | Medium | User experience and server limits | Queue jobs, preview progress, optimize renderer, set plan limits |
| PDF table extraction quality varies | Medium | Findings may be incomplete | Prefer Excel as source of truth, cite confidence, allow user corrections |
| Chart regeneration changes meaning | High | Committee reporting accuracy | Use source-bound chart specs and validation against input ranges |

## Immediate Technical Spikes

1. PPTX round-trip preservation.
2. Editable chart/table generation.
3. PDF extraction quality.
4. Excel findings normalization.
5. Retrieval isolation model.
6. Processing runtime limits.

