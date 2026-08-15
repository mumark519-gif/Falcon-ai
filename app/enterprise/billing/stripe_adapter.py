from __future__ import annotations
class StripeAdapter:
    def __init__(self,secret_key=None):self.secret_key=secret_key
    def available(self):return bool(self.secret_key)
    def create_checkout(self,*args,**kwargs):
        if not self.secret_key: raise RuntimeError("Stripe is not configured")
        import stripe
        stripe.api_key=self.secret_key
        return stripe.checkout.Session.create(*args,**kwargs)
