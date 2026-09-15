from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NormalizedOffer:
    store: str
    store_product_id: str
    product_url: str
    title: str
    price: float
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    model_number: Optional[str] = None
    global_product_id: Optional[str] = None
    currency: str = "INR"
    availability: bool = True
    offer_title: Optional[str] = None
    offer_description: Optional[str] = None
    coupon_code: Optional[str] = None
    discount_text: Optional[str] = None
    valid_until: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def discount_percent(self) -> Optional[float]:
        if self.mrp and self.mrp > 0 and self.price >= 0:
            return round((self.mrp - self.price) * 100 / self.mrp, 2)
        return None
