# Beta 11 P7 — website launch preview (NOT DEPLOYED)

**Repository:** `sharvuncle/tapioca-app`, branch `feature/beta11-website` from website `main`. P7 patches `index.html` only and adds this runbook plus `test_beta11_website.py`. It does not change Cloudflare release routing, binaries, download manifests, backend checkout settings, Stripe records, customer subscriptions, GitHub or the live website.

## Website behavior at launch

- The top navigation, hero, interactive demo and free-account section present Teleport and Route as free with a Tapioca account.
- New users sign in **inside the desktop app** using an email code. Users starting genuinely offline may create a local account, then must verify on reconnecting before new Teleports/Routes. Offline road routing still needs cached geometry or an installed regional routing pack.
- The previous weekly/monthly/annual price cards and website checkout overlay/JavaScript are removed, not merely hidden. This does **not** alone secure the backend against old websites/apps. P6 `TAPIOCA_PAID_CHECKOUT_ENABLED=false` must be deployed at the coordinated launch.
- Existing Stripe Billing Portal links remain in desktop navigation, mobile navigation, free-account section and footer. Legacy checkout-return pages are left intact for historic redirects.
- The current `/download/windows` and `/download/mac` URLs and interactive download guide remain untouched. **Those URLs still serve existing releases until new, tested Beta 11 binaries and signed update manifests are published.** Do not publish this site before updating the release paths.
- This package does not remove obsolete checkout CSS rules; they are inert and retained to minimize risk to other layout sections. The old active payment markup and JS are removed.

## Preparing / testing

1. Clone the website repository or use an existing clean copy. On website `main`, `git pull --ff-only origin main`, then `git switch -c feature/beta11-website`.
2. Extract the P7 ZIP; `py -3 <extracted>\apply_step7_website.py --repo . --check`. It refuses a dirty tree, wrong branch or changed `index.html` base blob.
3. Only after `CHECK OK`, run the same tool with `--apply`.
4. Run `run_step7_tests.ps1 -Repo .`. For JavaScript syntax validation, Node.js must be installed; the regression test reports a skip if unavailable.
5. Preview locally using `py -3 -m http.server 8765` and browse `http://localhost:8765`. Inspect desktop and mobile widths, FAQ, OS-specific downloads **without clicking to install an old Beta 10 release**, billing portal link visibility, and confirmation that no paid plan purchase UI appears.
6. Stage exactly `index.html test_beta11_website.py BETA11_WEBSITE_RUNBOOK.md`. Commit and push the feature branch **only after user-reviewed tests**. Do not merge or publish.

## Release gate — requires explicit approval

- The backend P6 launch switch remains ON for legacy paid checkout by default. Before publishing Beta 11 pricing, test checkout shutdown on local/staging and plan to activate `TAPIOCA_PAID_CHECKOUT_ENABLED=false` in production at coordinated launch.
- Validate and publish the new Windows and **Mac** release binaries, signatures/notarization, SHA-256 hashes, updater manifests and Cloudflare download paths. Mac Beta 11 testing has not yet been completed; do not assume equivalence solely from Windows testing.
- Review older Beta 10 installed-app behavior, onboarding/migration and support plan. The backend switch blocks future paid checkout but does not make old Beta 10 clients free.
- Audit live Stripe subscriptions and all old price IDs. After explicit launch approval, schedule eligible subscriptions to cancel at current period end (not immediate cancellation) with the separate P6 transition tool. No automatic prorated refunds. Resolve open invoices, pending charges, retries, subscription schedules and already-created Stripe Checkout Sessions separately; verify Stripe Dashboard and webhook results.
- Prepare customer-facing notice and support channel. Coordinate the backend flag, subscription actions, signed releases and website publication. Verify live site copy **only after** release URLs lead to Beta 11 and checkout is blocked.
- Keep historic checkout-success/cancelled routes until old payment redirects cannot reach them. Keep Stripe billing management accessible for past subscribers.
