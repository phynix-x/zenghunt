import os
from urllib.parse import quote
from urllib.request import Request, urlopen
import json


class SupabaseWriter:
    def __init__(self):
        self.url = os.environ["SUPABASE_URL"].rstrip("/")
        self.key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def request(self, method, table, payload=None, params=""):
        url = f"{self.url}/rest/v1/{table}{params}"
        headers = dict(self.headers)
        if method in {"POST", "PATCH"}:
            headers["Prefer"] = "return=representation"
        body = json.dumps(payload).encode() if payload is not None else None
        req = Request(url, data=body, headers=headers, method=method)
        with urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else []

    def find_one(self, table, column, value):
        params = f"?select=*&{quote(column)}=eq.{quote(str(value))}&limit=1"
        rows = self.request("GET", table, params=params)
        return rows[0] if rows else None

    def store(self, offer):
        row = self.find_one("stores", "slug", offer.store)
        data = {"name": offer.store, "slug": offer.store, "is_active": True}
        if row:
            return row["id"]
        return self.request("POST", "stores", data)[0]["id"]

    def product(self, offer):
        if offer.global_product_id:
            row = self.find_one("products", "global_product_id", offer.global_product_id)
            if row:
                return row["id"]
        if offer.model_number:
            row = self.find_one("products", "model_number", offer.model_number)
            if row:
                return row["id"]
        data = {
            "name": offer.title,
            "brand": offer.brand,
            "category": offer.category,
            "image_url": offer.image_url,
            "model_number": offer.model_number,
            "global_product_id": offer.global_product_id,
        }
        return self.request("POST", "products", data)[0]["id"]

    def listing(self, offer, product_id, store_id):
        params = "?on_conflict=product_id,store_id"
        data = {
            "product_id": product_id,
            "store_id": store_id,
            "store_product_id": offer.store_product_id,
            "product_url": offer.product_url,
            "title": offer.title,
            "image_url": offer.image_url,
            "availability": offer.availability,
        }
        return self.request("POST", "product_listings", data, params=params)[0]["id"]

    def record(self, offer):
        store_id = self.store(offer)
        product_id = self.product(offer)
        listing_id = self.listing(offer, product_id, store_id)
        price_row = {
            "listing_id": listing_id,
            "price": offer.price,
            "mrp": offer.mrp,
            "discount_percent": offer.discount_percent,
            "currency": offer.currency,
        }
        self.request("POST", "prices", price_row)
        self.request("POST", "price_history", {
            "listing_id": listing_id,
            "price": offer.price,
            "mrp": offer.mrp,
        })
        if offer.offer_title or offer.coupon_code or offer.discount_text:
            self.request("POST", "offers", {
                "listing_id": listing_id,
                "title": offer.offer_title,
                "description": offer.offer_description,
                "coupon_code": offer.coupon_code,
                "discount_text": offer.discount_text,
                "valid_until": offer.valid_until,
                "is_active": True,
            })
