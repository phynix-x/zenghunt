const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

type Product = {
  name: string | null;
  image: string | null;
  price: number | null;
  currency: string;
  store: string;
  url: string;
};

function storeFromUrl(url: URL) {
  const h = url.hostname.toLowerCase().replace(/^www\./, "");
  if (h.includes("amazon.")) return "Amazon";
  if (h.includes("flipkart.")) return "Flipkart";
  if (h.includes("myntra.")) return "Myntra";
  if (h.includes("ajio.")) return "AJIO";
  if (h.includes("meesho.")) return "Meesho";
  if (h.includes("tatacliq.")) return "Tata CLiQ";
  if (h.includes("croma.")) return "Croma";
  if (h.includes("reliancedigital.")) return "Reliance Digital";
  return null;
}

function cleanText(value: string | null) {
  return value?.replace(/\\s+/g, " ").trim() || null;
}

function parsePrice(value: string | null) {
  if (!value) return null;
  const match = value.replace(/,/g, "").match(/(?:₹|INR|Rs\\.?|\\$|€|£)?\\s*(\\d+(?:\\.\\d{1,2})?)/i);
  return match ? Number(match[1]) : null;
}

function meta(doc: string, property: string) {
  const re = new RegExp(`<meta[^>]+(?:property|name)=["']${property.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")}["'][^>]+content=["']([^"']+)["']`, "i");
  const m = doc.match(re);
  return m ? cleanText(m[1]) : null;
}

function jsonLdProducts(html: string) {
  const out: Record<string, unknown>[] = [];
  const re = /<script[^>]+type=["']application\\/ld\\+json["'][^>]*>([\\s\\S]*?)<\\/script>/gi;
  for (const m of html.matchAll(re)) {
    try {
      const parsed = JSON.parse(m[1]);
      const items = Array.isArray(parsed) ? parsed : [parsed];
      for (const item of items) {
        if (item && typeof item === "object") {
          if (item["@type"] === "Product") out.push(item);
          if (Array.isArray(item["@graph"])) out.push(...item["@graph"].filter((x: any) => x?.["@type"] === "Product"));
        }
      }
    } catch (_) {}
  }
  return out;
}

function extract(html: string, pageUrl: URL, store: string): Product {
  const products = jsonLdProducts(html);
  const p: any = products[0] || {};
  const offers: any = Array.isArray(p.offers) ? p.offers[0] : p.offers || {};
  const name = cleanText(p.name) || meta(html, "og:title") || cleanText(html.match(/<title[^>]*>([\\s\\S]*?)<\\/title>/i)?.[1] || null);
  const imageValue = Array.isArray(p.image) ? p.image[0] : p.image;
  const image = imageValue || meta(html, "og:image");
  const price = parsePrice(String(offers.price ?? meta(html, "product:price:amount") ?? ""));
  const currency = String(offers.priceCurrency || meta(html, "product:price:currency") || "INR");
  return { name, image: image ? new URL(String(image), pageUrl).href : null, price, currency, store, url: pageUrl.href };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "POST a product URL" }), { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } });

  try {
    const body = await req.json();
    const raw = String(body?.url || "").trim();
    const pageUrl = new URL(raw);
    if (!/^https?:$/.test(pageUrl.protocol)) throw new Error("Only http/https URLs are supported.");
    const store = storeFromUrl(pageUrl);
    if (!store) throw new Error("This store is not supported yet.");

    const response = await fetch(pageUrl.href, {
      headers: {
        "User-Agent": "ZenGhunt/1.0 product tracker",
        "Accept": "text/html,application/xhtml+xml",
      },
      redirect: "follow",
    });
    if (!response.ok) throw new Error(`Store returned HTTP ${response.status}.`);
    const html = await response.text();
    if (html.length > 8_000_000) throw new Error("Product page is too large to process.");

    const product = extract(html, pageUrl, store);
    return new Response(JSON.stringify({ ok: true, product, note: product.price == null ? "Product page was reachable, but no reliable price was exposed in structured/meta data." : null }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : "Unable to track this URL." }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
