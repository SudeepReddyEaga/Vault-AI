from typing import Dict, Any, List

# Local sector knowledge repository for Indian rural & semi-urban blocks
SECTOR_KNOWLEDGE = {
    "dairy": {
        "unit_name": "Dairy Farm & Milk Collection Unit",
        "primary_goods": ["A2 Cow/Buffalo Milk", "Fresh Curd/Dahi", "Paneer", "Ghee"],
        "unit_price_range": "₹42 - ₹54 per liter",
        "margin_range": "22% - 32%",
        "niches": [
            "Value-added Paneer & Khoa production for local weekly sweet shops",
            "Doorstep direct morning delivery to nearby semi-urban housing colonies",
            "Organic fodder cultivation & silage supply to neighboring dairy farmers"
        ],
        "threats": [
            "Fodder cost volatility and green forage deficit during summer months",
            "Single-dairy cooperative pricing monopoly or delayed payment cycles",
            "Perishable spoilage risk during unannounced rural power outages without chilling equipment",
            "Bovine disease outbreaks (Lumpy Skin, Mastitis) without prompt veterinary access"
        ],
        "swot": {
            "strengths": [
                "Continuous daily cash-flow with high recurring liquid demand",
                "High cultural acceptance and government subsidized veterinary support",
                "Organic manure (cow dung) acts as secondary revenue stream"
            ],
            "weaknesses": [
                "Labor intensive 365-day schedule requiring early morning milking",
                "High initial capital tied up in cattle acquisition",
                "Susceptible to feed cost inflation"
            ],
            "opportunities": [
                "Direct tie-up with local tea stalls, sweet vendors, and residential apartments",
                "Availing SCA interest subvention to install small bulk milk cooler (BMC)",
                "Producing high-margin indigenous ghee sold at ₹900-₹1200/kg"
            ],
            "threats": [
                "Seasonal summer drop in lactation yields",
                "Unorganized local milk middlemen taking excessive commission cuts"
            ]
        },
        "distribution_channels": [
            "Village Milk Cooperative Society (Primary collection point)",
            "Direct-to-consumer doorstep delivery within 6 km radius",
            "Local sweet makers and dhabas along the block highway",
            "Weekly Gram Panchayat Haat (bazaar)"
        ]
    },
    "textiles": {
        "unit_name": "Garment Manufacturing & Apparel Tailoring",
        "primary_goods": ["School Uniforms", "Ethnic Wear & Blouses", "Readymade Shirts", "Workwear"],
        "unit_price_range": "₹280 - ₹850 per piece",
        "margin_range": "30% - 42%",
        "niches": [
            "Bulk institutional contracts for local government schools and private nurseries",
            "Festive wedding ethnic stitching with local embroidery embellishments",
            "Low-cost cotton nightwear and kids daily-wear for weekly haats"
        ],
        "threats": [
            "Competition from ultra-cheap polyester machine garments imported from Surat/Tirupur",
            "Seasonal demand troughs during exam and non-wedding months",
            "Fabric supply bottlenecks from district headquarters"
        ],
        "swot": {
            "strengths": [
                "High profit margins per custom garment (up to 45%)",
                "Low machinery depreciation with modern multi-needle electric stitchers",
                "Scalable home-based workforce"
            ],
            "weaknesses": [
                "Requires skilled tailoring labor which may require initial training",
                "Working capital tied up in seasonal inventory"
            ],
            "opportunities": [
                "Exclusive uniform contracts for 4-5 village schools in the block",
                "Online aggregation via WhatsApp commerce for nearby township customers"
            ],
            "threats": [
                "Customer payment defaults on credit stitching books",
                "Erratic electricity supply slowing down motorized sewing machines"
            ]
        },
        "distribution_channels": [
            "Direct village tailoring boutique",
            "Weekly Friday/Sunday village haat stalls",
            "Tie-up with block-level uniform retailers"
        ]
    },
    "retail": {
        "unit_name": "Rural FMCG & Kirana Enterprise",
        "primary_goods": ["Daily Provisions", "Packaged Food", "Personal Hygiene", "Agro-Inputs"],
        "unit_price_range": "MRP based with 12% - 20% aggregate retail margin",
        "margin_range": "15% - 22%",
        "niches": [
            "Small sachet & micro-pack curation tailored to daily-wage purchasing power",
            "Digital micro-services counter (UPI cash out, mobile recharge, utility bill pay)",
            "Farm-fresh local pulses and spice packaging at lower price than branded MNCs"
        ],
        "threats": [
            "Local informal credit ('Khata') leading to working capital lockup",
            "High competitor density in village main chowk",
            "Wholesaler minimum order quantity (MOQ) friction from district mandi"
        ],
        "swot": {
            "strengths": [
                "Essential inelastic everyday demand from every household",
                "High customer retention through personal relationships",
                "Fast inventory turnover"
            ],
            "weaknesses": [
                "Thin product margins on branded packaged items (8-12%)",
                "Requires continuous working capital replenishment"
            ],
            "opportunities": [
                "Offering home delivery to elderly villagers and remote hamlets",
                "Bundling local farm produce with store groceries"
            ],
            "threats": [
                "Bad debt from uncollected customer credit books",
                "Quick-commerce expansion reaching peri-urban block boundaries"
            ]
        },
        "distribution_channels": [
            "Main Village Chowk storefront",
            "Mobile van delivery to smaller satellite hamlets (wadis/tolas)",
            "Weekly agricultural market stalls"
        ]
    },
    "poultry": {
        "unit_name": "Broiler & Desi Poultry Farm",
        "primary_goods": ["Desi Eggs", "Broiler Live Birds", "Poultry Manure"],
        "unit_price_range": "₹8 - ₹14 per egg; ₹140 - ₹210 per kg bird",
        "margin_range": "24% - 35%",
        "niches": [
            "Free-range Desi / Kadaknath eggs fetching premium health-conscious prices",
            "Direct supply to block dhabas and hotel corridors on state highway",
            "Organic poultry litter pelleting for horticulture orchards"
        ],
        "threats": [
            "Bird flu (Avian influenza) rumor outbreaks causing sudden market demand collapse",
            "Commercial feed price surges (soya & maize market volatility)",
            "Predator attacks and extreme heatwave mortality in peak summer"
        ],
        "swot": {
            "strengths": [
                "Short 35-42 day production cycle for rapid capital turnover",
                "High consumer protein demand in semi-urban belts",
                "Predictable growth metrics under controlled feeding"
            ],
            "weaknesses": [
                "Strict biosecurity hygiene protocols required daily",
                "Vulnerable to weather extremes without shed insulation"
            ],
            "opportunities": [
                "Contract farming tie-ups with regional poultry integrators",
                "Establishing direct retail dressing counter to capture consumer margin"
            ],
            "threats": [
                "Sudden disease epidemics wiping out flocks",
                "Seasonal consumption drops during religious fasting periods (Shravan, Navratri)"
            ]
        },
        "distribution_channels": [
            "Direct farm-gate wholesale buyers",
            "Local meat vendors in a 10 km radius",
            "Highway dhabas and catering contractors"
        ]
    }
}

DEFAULT_SECTOR = {
    "unit_name": "Rural Micro-Enterprise Unit",
    "primary_goods": ["Locally processed goods", "Customized products", "Essential service delivery"],
    "unit_price_range": "Competitive local market rate",
    "margin_range": "20% - 30%",
    "niches": [
        "Specialized customer service within walking distance of rural households",
        "Value addition to locally sourced raw materials before selling to township buyers",
        "Affordable pricing benchmarked against regional daily-wage income"
    ],
    "threats": [
        "Raw material procurement delays from larger regional cities",
        "Cash liquidity constraints during agricultural sowing season",
        "Informal competitors operating without licensing or standards"
    ],
    "swot": {
        "strengths": ["Zero commute cost and direct local familiarity", "Flexible operating hours"],
        "weaknesses": ["Limited initial marketing reach beyond neighboring hamlets", "Working capital constraints"],
        "opportunities": ["SCA subsidized low-interest credit to scale machinery", "Expanding to adjacent weekly haats"],
        "threats": ["Seasonal cash cycle linked to monsoon harvest", "Power fluctuation"]
    },
    "distribution_channels": [
        "Local village center",
        "Weekly rural haats (5-10 km radius)",
        "Direct peer-to-peer neighborhood word of mouth"
    ]
}

def generate_hyperlocal_feasibility(
    village: str,
    block: str,
    district: str,
    category: str,
    margin_capital: float
) -> Dict[str, Any]:
    """
    Module 1: Hyper-Local Business Feasibility Report
    Generates dynamic analysis across 6 mandatory dimensions:
    1. Market Reach (5-10km radius)
    2. Opportunity Analysis (underserved local niches)
    3. SWOT Analysis (tailored to budget)
    4. Threats Identification
    5. Competitor Mapping & Density
    6. Product Market Value & Pricing Strategy
    """
    cat_key = category.strip().lower()
    sector_info = SECTOR_KNOWLEDGE.get(cat_key, DEFAULT_SECTOR)

    project_cost = margin_capital / 0.10

    # Demographic & Catchment estimation for 5-10 km radius
    # Rural block radius model
    estimated_households_5km = 1850
    estimated_population_5km = estimated_households_5km * 5  # ~9,250 people
    estimated_households_10km = 4200
    estimated_population_10km = estimated_households_10km * 5 # ~21,000 people

    # Competitor mapping proxy based on category in block
    competitor_density_map = {
        "dairy": {"units_in_block": 14, "saturation_level": "Moderate", "index": 58},
        "textiles": {"units_in_block": 8, "saturation_level": "Low-Moderate", "index": 42},
        "retail": {"units_in_block": 26, "saturation_level": "High", "index": 82},
        "poultry": {"units_in_block": 6, "saturation_level": "Low (High Unmet Demand)", "index": 35}
    }
    comp_data = competitor_density_map.get(cat_key, {"units_in_block": 10, "saturation_level": "Moderate", "index": 50})

    # Pricing strategy recommendations
    pricing_strategy = {
        "target_pricing": sector_info["unit_price_range"],
        "gross_margin_guidance": sector_info["margin_range"],
        "recommendation": f"Adopt penetration pricing during the 3-6 month moratorium period. Offer introductory discounts to village institutional buyers, then shift to value-added differentiation.",
        "purchasing_power_fit": f"Benchmarked for semi-rural income tier in {district}. Packaging in smaller micro-units maximizes daily transaction frequency."
    }

    # Feasibility Score (0 to 100)
    # Higher for lower competitor saturation and solid margin
    base_score = 88 - (comp_data["index"] * 0.25)
    if margin_capital >= 50000:
        base_score += 5
    feasibility_score = max(55, min(95, round(base_score)))

    return {
        "location": {
            "village": village,
            "block": block,
            "district": district,
            "catchment_radius_km": "5 - 10 km",
            "consumer_reach_5km": f"{estimated_population_5km:,} citizens (~{estimated_households_5km:,} families)",
            "consumer_reach_10km": f"{estimated_population_10km:,} citizens (~{estimated_households_10km:,} families)"
        },
        "business_category": category,
        "feasible_project_cost": project_cost,
        "feasibility_score": feasibility_score,
        "feasibility_rating": "Highly Viable" if feasibility_score >= 80 else "Viable with Risk Mitigation",
        
        # 1. Market Reach
        "market_reach": {
            "estimated_radius": "5 to 10 km",
            "immediate_consumer_base": f"{estimated_population_5km:,} individuals across 4-6 adjoining Gram Panchayats",
            "distribution_channels": sector_info["distribution_channels"],
            "primary_buyer_personas": [
                "Local village families and agricultural laborers",
                "Highway traveler rest stops and dhabas",
                "Block-level trade aggregators and cooperatives"
            ]
        },

        # 2. Opportunity Analysis (Underserved local niches)
        "opportunity_analysis": {
            "unserved_niches": sector_info["niches"],
            "market_gap": f"Most existing players in {block} sell unbranded commodity items. Upgrading to hygienic processing, consistent packaging, or on-demand delivery captures immediate market share."
        },

        # 3. SWOT Breakdown
        "swot_analysis": {
            "strengths": sector_info["swot"]["strengths"],
            "weaknesses": sector_info["swot"]["weaknesses"],
            "opportunities": sector_info["swot"]["opportunities"],
            "threats": sector_info["swot"]["threats"]
        },

        # 4. Threats Identification
        "threats_identification": {
            "primary_risks": sector_info["threats"],
            "mitigation_strategies": [
                "Create a dedicated 3-month working capital cash buffer before withdrawing profits",
                "Diversify buyer base beyond single middlemen by engaging local weekly markets",
                "Leverage government livestock / property insurance under SCA scheme provisions"
            ]
        },

        # 5. Competitor Mapping
        "competitor_mapping": {
            "block_name": block,
            "estimated_competitor_density": f"{comp_data['units_in_block']} existing micro units in {block} block",
            "saturation_level": comp_data["saturation_level"],
            "saturation_index": comp_data["index"],
            "competitive_advantage": f"New machinery funded via 90% concessional loan lowers production cost by 15-20% compared to obsolete competitor units."
        },

        # 6. Product Market Value & Optimal Pricing
        "product_market_value": pricing_strategy
    }
