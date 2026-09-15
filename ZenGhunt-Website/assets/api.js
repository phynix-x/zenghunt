/* ZenGhunt API Manager — browser-side read layer for GitHub Pages. */
(function () {
  const cfg = window.ZENGHUNT_CONFIG || {};
  const REST = `${cfg.supabaseUrl}/rest/v1`;
  const headers = {
    apikey: cfg.supabasePublishableKey,
    Authorization: `Bearer ${cfg.supabasePublishableKey}`,
    'Content-Type': 'application/json'
  };

  async function request(path, params = {}) {
    const url = new URL(`${REST}/${path}`);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) url.searchParams.set(key, value);
    });
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  }

  async function getProducts() {
    return request('products', {
      select: 'id,name,brand,category,image_url,description,model_number,global_product_id,product_listings(id,store_id,product_url,title,image_url,availability,stores(id,name,slug,website_url,logo_url),prices(id,price,mrp,discount_percent,currency,checked_at))',
      order: 'updated_at.desc'
    });
  }

  async function getProduct(id) {
    const rows = await request('products', {
      id: `eq.${encodeURIComponent(id)}`,
      select: 'id,name,brand,category,image_url,description,model_number,global_product_id,product_listings(id,store_id,product_url,title,image_url,availability,stores(id,name,slug,website_url,logo_url),prices(id,price,mrp,discount_percent,currency,checked_at))'
    });
    return rows[0] || null;
  }

  async function getHistory(listingId) {
    return request('price_history', {
      listing_id: `eq.${encodeURIComponent(listingId)}`,
      select: 'id,price,mrp,recorded_at',
      order: 'recorded_at.asc'
    });
  }

  window.ZenGhuntAPI = { getProducts, getProduct, getHistory };
})();
