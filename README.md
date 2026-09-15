# ZenGhunt — Smart price intelligence

ZenGhunt is a GitHub Pages frontend backed by Supabase, with a server-side collection pipeline designed for real multi-store price comparison.

## Architecture

`Store/API feeds → connector manager → normalized offers → product matcher → Supabase → price history → ZenGhunt frontend`

The collector supports the store adapter layer for Amazon, Flipkart, Myntra, AJIO, Meesho, Tata CLiQ, Croma and Reliance Digital. A store is activated only when a legitimate/approved JSON API or feed is configured. ZenGhunt never fabricates prices, links or price-history points.

## Current website

- GitHub Pages-compatible frontend
- Supabase REST read layer using the publishable browser key
- Product cards use actual Supabase listings and prices
- Store comparison uses the real listing URL stored for each offer
- Product pages calculate current, previous recorded, lowest and average prices from recorded history
- Price-history charts use only collected history
- Responsive image containment and mobile offer-table scrolling

## Collector

Run locally with:

```bash
SUPABASE_URL="..." SUPABASE_SERVICE_ROLE_KEY="..." python -m collector.main
```

GitHub Actions runs the collector every 6 hours and can also be started manually. The workflow reads the Supabase service-role key and store feed credentials from GitHub Actions secrets; these credentials must never be placed in `assets/config.js` or any browser code.

### Feed contract

Each configured JSON feed should return either an array or `{ "products": [...] }`. Each product should provide:

- `id` or `store_product_id`
- `title` or `name`
- `price` or `current_price`
- `url` or `product_url`
- optional `mrp`, `image_url`, `brand`, `category`, `model_number`, `global_product_id`, `currency`, `availability`, offer/coupon fields

### GitHub Actions secrets

Required:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Optional per store:
- `ZENGHUNT_FEED_AMAZON_URL` / `_TOKEN`
- `ZENGHUNT_FEED_FLIPKART_URL` / `_TOKEN`
- `ZENGHUNT_FEED_MYNTRA_URL` / `_TOKEN`
- `ZENGHUNT_FEED_AJIO_URL` / `_TOKEN`
- `ZENGHUNT_FEED_MEESHO_URL` / `_TOKEN`
- `ZENGHUNT_FEED_TATACLIQ_URL` / `_TOKEN`
- `ZENGHUNT_FEED_CROMA_URL` / `_TOKEN`
- `ZENGHUNT_FEED_RELIANCEDIGITAL_URL` / `_TOKEN`

If no approved feed is configured, the collector exits without inserting data. This is intentional: empty real data is better than fake data.

## Security

The browser uses only the Supabase publishable key. Never commit a Supabase service-role key, database password, private API token or other secret.

## Deploy

The site is designed for GitHub Pages from the repository root. Enable Pages for the `main` branch and `/ (root)` if it is not already enabled.
