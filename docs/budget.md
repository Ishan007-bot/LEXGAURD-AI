# Budget discipline ($5 cap)

LexGuard is being built against a hard ~$5 GCP credit cap. This doc captures the
decisions that come from that constraint, so future changes don't accidentally
re-introduce a budget-killer.

## What we cut

| Component | Reason | Replacement |
| --- | --- | --- |
| **Memorystore (Redis)** | $35/month minimum — single biggest fixed cost | In-process `cachetools.TTLCache` + Firestore for durability |
| **Cloud Trace / Profiler agents** | Per-span cost adds up at scale; not visible to bot checker | Plain structured logs in Cloud Logging (free tier) |
| **Multi-region Cloud Run** | Egress costs and duplicate cold-starts | Single region (`asia-south1`), min-instances=0 |
| **Live deploy from day 1** | Each Cloud Build run + Artifact Registry storage costs cents | Local dev primary; deploy in the final 24h, redeploy only on key milestones |

## Model routing (the part that actually moves the needle)

Vertex AI token costs dominate everything else. Routing:

| Agent | Model | Why |
| --- | --- | --- |
| Extractor | `gemini-2.5-flash` | Mechanical segmentation; Flash is plenty |
| Prosecutor | `gemini-2.5-flash` | Many short reasoning calls; Flash keeps cost flat |
| Defender | `gemini-2.5-flash` | Same |
| Judge | `gemini-2.5-pro` **only for top-3 risky clauses** | Pro reasoning matters most here; capped to 3 calls per document |
| Negotiator | `gemini-2.5-flash` | Redline generation is templated |

Estimated cost per 5-page contract analysis with this routing:

- ~12k input tokens × Flash = $0.004
- ~8k output tokens × Flash = $0.020
- ~3k input tokens × Pro (Judge, 3 calls) = $0.011
- ~1.5k output tokens × Pro = $0.021
- **Total: ~$0.06 per analysis**

Budget = $5 ÷ $0.06 ≈ **80 analyses** for the whole hackathon. Plenty for dev +
a 30-clause demo, but no margin for accidental loops.

## Phase 5 add-ons

| Feature | Per-use cost | Notes |
| --- | --- | --- |
| **What-If simulator** | ~$0.005 / scenario | One Gemini Flash call. Capped at 500-char user input |
| **Voice walkthrough** | ~$0.0004 / play | Cloud TTS at $4 per 1M chars · script is ≤ 1 kB |

These are bounded per-user-action costs (no background loops), so they're safe
to leave enabled.

## Hard rules

1. **Never** call Gemini Pro from inside a loop. Only the Judge step, only on top-3 clauses.
2. **Always** apply prompt caching to system prompts (cuts repeat-call cost ~90%).
3. **Always** check the in-process cache, then Firestore, then call Vertex.
4. **Cap max document size** at 25 MiB / ~40 pages. Refuse larger uploads in the UI.
5. **No background polling jobs.** Every Vertex call is user-initiated.
6. **Set Cloud Run `min-instances=0`** so we pay $0 when idle.
7. **Set Cloud Build trigger to manual** for non-main branches, so PR pushes don't burn build minutes.

## What to monitor

```powershell
# Show current month spend
gcloud billing accounts list
gcloud beta billing budgets list --billing-account=<ID>
```

Set a budget alert at $3 (60% of cap) in the GCP console:
**Billing → Budgets & alerts → Create budget**.
