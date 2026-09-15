# ZenGhunt — Buyhatke-style website foundation

ZenGhunt is now wired for a Supabase-backed product/price workflow instead of the old demo `data/products.json` flow.

## Current architecture

GitHub Pages → browser API manager → Supabase REST API → products/listings/prices/history.

The browser uses the Supabase **publishable** key only. Do not put a service-role/secret key in this repository.

## Database tables

- `products`
- `stores`
- `product_listings`
- `prices`
- `price_history`
- `offers`
- `price_alerts`

## Important

The website now reads live records from Supabase. Because the database starts empty, the home page will show an empty state until real store data is inserted by an approved API/feed connector.

The old `data/products.json` remains in the project only as a reference/demo file; it is no longer used by the live home/product pages.
