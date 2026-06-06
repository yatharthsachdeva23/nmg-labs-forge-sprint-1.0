# PROMPTS.md — my key prompts log

Keep the handful of prompts that actually moved the build. Not every message — the ones that
mattered: the system/sub-agent prompts, the ones you iterated on, the "this finally worked"
moment. This shows how you direct an AI, which is graded (challenge brief section 08).

Format per entry:
- **Prompt** (paste it)
- **For:** what you were trying to do
- **Revised?** did you have to change it, and why

---

## Example (replace with your own)

- **Prompt:** "Extend seo/detector.py to detect redirect chains: build a map of {Address ->
  Redirect URL} for all 3xx rows, then a chain exists when a Redirect URL is itself a key in
  that map. Add a redirect_chain issue (High). Run python seo/detector.py and show counts."
- **For:** adding the redirect-chain detector
- **Revised?** Yes — first version flagged single redirects as chains; added the "target is
  also a redirecting URL" condition.

---

## My prompts
- **Prompt:** "Prompted to resolve empty dashboard data streams by running the server under the explicitly mapped 'py -3.12' environment pipeline."
- **For:** Environment calibration to ensure stable data streaming to the live dashboard.
- **Revised?** N/A
- **Prompt:** "Please execute our complete multi-agent pipeline by sequentially invoking all 4 system sub-agents: 1. Ingest Agent: Read and normalize the Screaming Frog dataset. 2. Auditor Agent: Scan the rows using the 17 deterministic SEO rules in 'seo/detector.py'. 3. Fixer Agent: Trigger our length-guarded local model title rewrites and redirect mapper. 4. Reporter Agent: Compile everything into our machine-readable outputs/report.json and client deliverables."
- **For:** Multi-agent delegation sequence to cleanly separate data ingestion, policy checks, LLM metadata rewriting, and artifact generation.
- **Revised?** N/A
