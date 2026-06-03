# Billing Architecture

## Billing Model

AuditFlow AI should use organization-level billing. Individual users belong to organizations, and subscription entitlements apply to the organization.

## Stripe Components

- Stripe Customers map one-to-one with organizations.
- Stripe Subscriptions map to plans.
- Stripe Checkout handles initial subscription purchase.
- Stripe Customer Portal handles plan changes, payment methods, and cancellation.
- Stripe webhooks sync subscription state and entitlement changes.

## Initial Plans

Plan examples for implementation planning:

- Starter: limited projects, limited monthly deck generations, small file limits.
- Team: more seats, higher usage, standard support.
- Enterprise: SSO-ready, custom limits, retention controls, priority support.

Plan names and prices should be finalized later.

## Entitlements

Initial entitlement dimensions:

- Seat limit.
- Active project limit.
- Monthly deck generation limit.
- Maximum upload size.
- Maximum retained projects.
- Advanced template reuse.
- Enterprise retention controls.

## Stripe Webhook Events

Handle at minimum:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

Webhook processing must:

- Verify Stripe signature from raw request body.
- Be idempotent by Stripe event id.
- Update subscription status in Postgres.
- Record audit and usage-related events where relevant.

## Access Enforcement

Entitlements are enforced in:

- Project creation.
- Upload size validation.
- Processing job creation.
- Deck export generation.
- Member invitation.

Billing state should not delete customer data automatically. It should restrict new value-generating actions while preserving read/export behavior according to policy.

## Implementation Notes

The Vercel payments guidance recommends Stripe as a native Vercel Marketplace integration, with server-side SDK usage, Checkout Sessions or embedded checkout, and raw-body webhook signature verification. The implementation should use server-only Stripe clients and never expose secret keys to the browser.

Sources:

- Stripe Checkout: https://docs.stripe.com/payments/checkout
- Stripe Webhooks: https://docs.stripe.com/webhooks
- Stripe Node SDK: https://docs.stripe.com/sdks
- Vercel Stripe Marketplace: https://vercel.com/marketplace/stripe

