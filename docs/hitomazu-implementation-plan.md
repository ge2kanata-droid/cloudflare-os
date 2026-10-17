# Hitomazu Tools: agent operations implementation plan

Status: design and verification only. No production deployment or LLM subscription integration is claimed.

## Objective
Build an iPhone-accessible, cost-guarded AI work environment to continue revenue-related work while Manus credits are exhausted. Keep existing assignments and Notion as the source of truth. Exclude personal activities and Worldline Archive.

## Constraints
- No new subscription, API pay-as-you-go, or paid Cloudflare resources without explicit authorization.
- No automatic purchasing, contracts, paid ads, irreversible publication or overwriting existing products.
- Respect platform terms and model usage limits; never use ChatGPT session cookies as unofficial API credentials.
- Distinguish unavailable metrics from zero and drafts from published changes.

## Verification before coding
1. Trace the existing model-provider interface and settings UI.
2. Verify whether an officially supported ChatGPT subscription sign-in flow can serve this runtime, including refresh and unattended operation; if unsupported, do not claim it works.
3. Identify Cloudflare Workers, Durable Objects, and other service costs and free-tier constraints.
4. Define deployment, rollback, authentication, and secret storage suitable for iPhone-only administration.

## Implementation phases
1. Add a model-provider selection UI for verified, supported providers only, retaining existing API-key behavior.
2. Add a persistent task queue with owner, priority, schedule, status, deduplication, audit logs, and bounded retries.
3. Add approval gates for side-effecting external actions; allow unattended drafting, research, and non-destructive validation.
4. Integrate existing Notion records and existing product links without duplicate work.
5. Run one end-to-end no-cost, non-destructive revenue-funnel improvement task and verify the outcome.

## Success criteria
- No surprise costs, credential exposure, or unauthorized publications.
- At least one scheduled task runs successfully within documented limits.
- Work can resume safely after interruptions without duplicate execution.
- Actual revenue is measured, not assumed.
