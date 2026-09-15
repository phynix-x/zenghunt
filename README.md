# ZenGhunt — Supabase-connected website

## Current status
- GitHub Pages-compatible frontend
- Supabase REST read layer using the publishable browser key
- Products, store listings, current prices and recorded price history are loaded from Supabase
- Product page calculates lowest/average/previous recorded price from actual history rows
- Store comparison uses actual listing URLs from Supabase
- No synthetic price-history graph or hard-coded product catalog is used by the live pages
- Responsive layout includes safe image containment, chart overflow protection and horizontal offer-table scrolling on small screens

## Important
The site will show no products until approved/legitimate data sources populate the Supabase tables. Do not put service-role keys or database passwords in this frontend.

## Deploy
Upload the contents of this folder to the GitHub Pages repository root.
