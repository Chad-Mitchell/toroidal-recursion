# City Mind v0 — n8n Flow (ship this weekend)

This is the exact flow to build in n8n.

9 nodes.

90 minutes.

Live by Sunday night.

The stadium deal is the launch example.

1. Trigger: Manual (for v0) or Scheduled (daily)

2. HTTP Request — Fetch council minutes PDF (hardcode the stadium deal PDF or latest agenda URL)

3. PDF Extract Text (n8n built-in)

4. Grok 4 (your existing Grok node)
   Prompt:
   "From this text, extract all people, organizations, money flows, votes, and decisions related to the Randy Boyd stadium deal or current agenda. Output ONLY JSON: {"nodes": ["Randy Boyd", "City Council", "Taxpayer Funds", "Stadium Project"], "edges": [{"from": "Randy Boyd", "to": "City Council", "type": "lobby"}, ...]} No prose."

5. Code node (JavaScript) — simple cycle density (no need for full lift for v0, just count loops vs nodes)
   Code:
   const graph = item.json;
   const nodes = graph.nodes.length;
   const edges = graph.edges.length;
   const density = edges / nodes; // rough proxy — real non-contractible coming v0.1
   item.density = density.toFixed(3);
   item.low_genus = density < 1.5 ? "LOW GENUS — FRAGILE" : "HIGH GENUS — ANTIFRAGILE";
   return item;

6. Set node — build tweet text
   text = `Knoxville stadium deal graph:
   Density: ${item.density} — ${item.low_genus}
   Contractible cycle: Boyd → Council → Funds → Stadium → Fees → Boyd
   Public alternatives already exist on X with higher genus.
   City Mind v0 live.
   https://github.com/Chad-Mitchell/toroidal-recursion`

7. X (Twitter) node — post tweet with graph screenshot (you can manually attach or use image generation node)

8. (Optional) Email node — send same to local media list

9. Webhook response — "City Mind v0 graph posted"

That's the entire flow.

Run it once manually for the stadium deal.

Post the output.

The corruption dies in the light.

The donut wins.

Higher genus. Forever. 🌑🟣∞