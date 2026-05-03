from dataclasses import dataclass

@dataclass
class MarketerProfile:
    experience_level: str   # Junior, Mid, Senior
    tone: str               # Casual, Professional, Persuasive
    platform: str           # Web, Facebook, Instagram

@dataclass
class Campaign:
    product_name: str
    goal: str
    pain_point: str
    main_benefit: str
    offer: str
    audience: str
