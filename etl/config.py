# ---------------- CONFIG ----------------
PAGE_KEYWORDS = {
    "sales_specials": ["offer", "special", "lease", "rebate", "save"],
    "service_specials": ["service", "maintenance", "coupon", "brake", "oil change"],
    "ev_incentives": ["electric", "ev", "incentive", "rebate", "battery"],
    "financing_deals": ["financing", "apr", "loan", "payment", "credit", "rate"],
}

EXCLUDE_TERMS = ["home", "privacy", "contact", "terms", "cookie", "menu", "navigation", "footer"]

URLS = {
   "sales_specials": [
       "https://www.stevenscreekchevy.com/newspecials.html",
   ],
   "service_specials": [
       "https://www.stevenscreekchevy.com/service-parts-specials.html",
       "https://www.stevenscreekchevy.com/service",
       "https://www.stevenscreekchevy.com/serviceapptform",
       "https://www.stevenscreekchevy.com/service-department-san-jose-ca",
       "https://www.stevenscreekchevy.com/onstar.html",
       "https://www.stevenscreekchevy.com/brake-service-san-jose-ca",
       "https://www.stevenscreekchevy.com/tire-rotation-san-jose-ca",
       "https://www.stevenscreekchevy.com/new-tires",
       "https://www.stevenscreekchevy.com/mobile-service-plus",
   ],
   "ev_incentives": [
       "https://www.stevenscreekchevy.com/ev-incentives",
       "https://www.stevenscreekchevy.com/electric-vehicles",
   ],
   "financing_deals": [
       "https://www.stevenscreekchevy.com/finance.aspx",
   ],
}

# Vehicle API
BASE_URL = "https://www.stevenscreekchevy.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/16823/3165452"
HEADERS = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
    "referer": "https://www.stevenscreekchevy.com/searchall.aspx",
}