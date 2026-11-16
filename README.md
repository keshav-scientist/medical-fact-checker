# Medical fact-checking AI (starter project)

A small pipeline that checks medical claims against real PubMed
evidence instead of letting a model answer from memory. Built around
four rules: understand the problem before coding, never trust a
single unverified source, put safety checks before the AI runs, and
always disclose limits.

## How it works

1. **Safety filter** (`safety_filter.py`) - blocks emergencies, personal
   diagnosis requests, and dosage questions before anything else runs.
2. **Retrieval** - pulls evidence from two independent NIH sources,
   so a verdict never rests on a single source:
   - `pubmed_retrieval.py` - research abstracts from PubMed
   - `medlineplus_retrieval.py` - plain-language consumer health
     summaries from MedlinePlus
   - `evidence.py` - the shared `Evidence` shape both sources return,
     so `fact_checker.py` doesn't need to know which source a given
     piece of evidence came from.
3. **Fact-check** (`fact_checker.py`) - sends the claim plus all
   retrieved evidence to Claude, which must ground its verdict in
   that evidence and return a structured, cited answer. If one
   source fails (rate limit, network hiccup), the pipeline keeps
   going on whatever the other source returned.
4. **CLI** (`main.py`) - talk to the pipeline.
5. **Stress test** (`test_claims.py`) - run known true/false claims
   through it and check the results.

This mirrors the pipeline diagram from earlier: question -> safety
check -> retrieve evidence -> generate verdict -> show result. Adding
a source was just: write a module that returns a list of `Evidence`
objects, then pull from it in `fact_checker.py` - that's the pattern
to follow for WHO, CDC, or Cochrane later (see Limitations below).

## Setup

1. Install Python 3.9+.
2. `pip install -r requirements.txt`
3. Get an API key from https://console.anthropic.com and set it as
   an environment variable:
   - macOS/Linux: `export ANTHROPIC_API_KEY=sk-ant-...`
   - Windows (PowerShell): `$env:ANTHROPIC_API_KEY="sk-ant-..."`
4. Run it: `python main.py`
5. Try the stress test: `python test_claims.py`

## Known limitations (read before showing this to anyone else)

- The PubMed abstract parser in `pubmed_retrieval.py` is a simple
  text splitter, not a real XML parser - it's good enough for a
  prototype but will occasionally mis-split a record. For production,
  switch `retmode` to `"xml"` and parse it properly.
- The safety filter is keyword-based. It will miss creatively-phrased
  emergencies and can false-positive on unrelated text. It's a first
  line of defense, not a substitute for a real triage system.
- This tool does not replace a doctor. It's designed to help someone
  sanity-check a claim or spot obvious misinformation, not to make an
  actual health decision. Keep that framing anywhere you deploy it.
- No rate limiting or caching is implemented - add both before letting
  more than one person use this at once (NCBI limits unauthenticated
  traffic to roughly 3 requests/second).

## Extending it

- Swap the keyword safety filter for a small classifier if you outgrow it.
- Add a confidence threshold that routes low-confidence results to a
  human reviewer instead of showing them directly.
- Cache retrieval results so repeat claims don't re-fetch every time
  (both NCBI and NLM explicitly ask API users to cache).
- More sources: MedlinePlus and PubMed both have free, documented,
  no-key-required APIs, which is why they're first. WHO and CDC don't
  currently offer an equivalent full-text search API for their
  guidance pages - the realistic options there are a small hand-curated
  local reference file of specific facts you trust, or their
  structured statistics APIs (WHO's GHO OData API, CDC's data.cdc.gov)
  if you need numbers rather than prose. Cochrane reviews are behind
  access restrictions, so treat those as a manual addition, not an
  automated one.
