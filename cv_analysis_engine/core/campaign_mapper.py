def get_campaigns(price_range: str):
    if price_range == "LOW_TICKET":
        return ["Small gadgets", "Books", "Accessories"]
    elif price_range == "MID_TICKET":
        return ["Electronics", "Fashion items", "Home appliances"]
    else:  # HIGH_TICKET
        return ["Cars", "Real Estate", "Luxury products"]
