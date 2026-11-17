import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

# Catalog of enterprise equipment & goods with semantic features
PRODUCT_CATALOG = [
    {
        "id": 1,
        "title": "Heavy Duty Automatic Milking Claw Unit",
        "category": "Dairy",
        "price": 18500.0,
        "tags": "dairy cattle cow buffalo milk extraction automation hygienic stainless steel",
        "margin_fit": 50000.0,
        "sales_count": 142,
        "rating": 4.9,
        "velocity_score": 9.4
    },
    {
        "id": 2,
        "title": "Micro Bulk Milk Cooler (100L Chiller)",
        "category": "Dairy",
        "price": 65000.0,
        "tags": "dairy milk cooling refrigeration storage spoilage prevention cooperative chilling",
        "margin_fit": 100000.0,
        "sales_count": 88,
        "rating": 4.8,
        "velocity_score": 8.7
    },
    {
        "id": 3,
        "title": "Enriched High-Protein Cattle Feed (50kg Bag)",
        "category": "Dairy",
        "price": 1450.0,
        "tags": "dairy cattle food nutrition protein bypass fat lactating feed mineral",
        "margin_fit": 20000.0,
        "sales_count": 520,
        "rating": 4.9,
        "velocity_score": 9.9
    },
    {
        "id": 4,
        "title": "Ultrasonic Digital Milk Fat & SNF Analyzer",
        "category": "Dairy",
        "price": 24000.0,
        "tags": "dairy testing quality milk fat snf density lab cooperative payment",
        "margin_fit": 50000.0,
        "sales_count": 65,
        "rating": 4.7,
        "velocity_score": 7.8
    },
    {
        "id": 5,
        "title": "Industrial Direct-Drive High-Speed Sewing Machine",
        "category": "Textiles",
        "price": 19200.0,
        "tags": "textiles tailoring garment uniform stitch apparel cloth dress electric",
        "margin_fit": 50000.0,
        "sales_count": 190,
        "rating": 4.9,
        "velocity_score": 9.2
    },
    {
        "id": 6,
        "title": "5-Thread Interlock Overedging Machine",
        "category": "Textiles",
        "price": 28000.0,
        "tags": "textiles hemming overlock stitching garment manufacturing apparel school uniform",
        "margin_fit": 80000.0,
        "sales_count": 74,
        "rating": 4.6,
        "velocity_score": 7.9
    },
    {
        "id": 7,
        "title": "Compact Commercial Cold-Press Oil Expeller",
        "category": "Agro-processing",
        "price": 45000.0,
        "tags": "agro-processing oil mustard groundnut extraction edible healthy pure",
        "margin_fit": 100000.0,
        "sales_count": 43,
        "rating": 4.8,
        "velocity_score": 7.5
    },
    {
        "id": 8,
        "title": "Continuous Band Nitrogen Bag Sealer",
        "category": "Retail",
        "price": 14800.0,
        "tags": "retail packaging sealing plastic pouch chips spices pulses fmcg kirana",
        "margin_fit": 30000.0,
        "sales_count": 110,
        "rating": 4.7,
        "velocity_score": 8.5
    },
    {
        "id": 9,
        "title": "Automatic 500-Egg Poultry Incubator with Hatcher",
        "category": "Poultry",
        "price": 32000.0,
        "tags": "poultry chicken eggs incubator hatching birds broiler desi farm",
        "margin_fit": 60000.0,
        "sales_count": 52,
        "rating": 4.6,
        "velocity_score": 7.6
    },
    {
        "id": 10,
        "title": "3HP Solar Water Pump System for Rural Enterprises",
        "category": "Agro-machinery",
        "price": 85000.0,
        "tags": "solar pump water irrigation green electricity borewell horticulture dairy",
        "margin_fit": 120000.0,
        "sales_count": 98,
        "rating": 4.9,
        "velocity_score": 9.1
    }
]

class MLRecommender:
    def __init__(self):
        # Build TF-IDF semantic vector space
        self.descriptions = [f"{p['title']} {p['category']} {p['tags']}" for p in PRODUCT_CATALOG]
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.descriptions)

    def recommend_for_customer(self, category: str, margin_capital: float, location: str = "") -> Dict[str, Any]:
        """
        Customer Recommendation:
        Uses TF-IDF Cosine Similarity matched with category query and budget affordability constraint
        """
        query_text = f"{category} rural micro enterprise equipment machinery {location}"
        query_vec = self.vectorizer.transform([query_text])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        recommendations = []
        feasible_project_cost = margin_capital / 0.10

        for idx, score in enumerate(sim_scores):
            prod = PRODUCT_CATALOG[idx]
            # Score formula: Cosine Semantic Similarity * 0.5 + Budget Compatibility * 0.3 + Product Quality/Rating * 0.2
            budget_ratio = min(1.0, (feasible_project_cost * 0.40) / max(1.0, prod["price"]))
            quality_factor = (prod["rating"] / 5.0)

            composite_score = (score * 0.50) + (budget_ratio * 0.30) + (quality_factor * 0.20)

            reason = f"Essential for your proposed {category} venture. Fits comfortably within your ₹{feasible_project_cost:,.2f} project scope."
            if prod["category"].lower() == category.lower():
                composite_score += 0.25

            recommendations.append({
                "product_id": prod["id"],
                "title": prod["title"],
                "category": prod["category"],
                "price": prod["price"],
                "rating": prod["rating"],
                "match_score": round(min(0.99, float(composite_score)), 2),
                "reason": reason,
                "is_essential": prod["price"] <= (feasible_project_cost * 0.35)
            })

        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        top_recs = recommendations[:5]

        # Strategic business tips
        strategic_opportunities = [
            f"Set up value-added processing (e.g. packaged goods vs raw produce) to boost margins by 20-30%.",
            f"Pool bulk logistics with adjacent beneficiaries in {location or 'your block'} to lower transportation overhead.",
            f"Ensure 100% of machinery invoices are submitted to the SCA for concessional interest subsidy clearance."
        ]

        return {
            "query_category": category,
            "margin_capital": margin_capital,
            "recommended_products": top_recs,
            "strategic_opportunities": strategic_opportunities
        }

    def recommend_for_seller(self, seller_id: int = 2) -> Dict[str, Any]:
        """
        Seller Recommendation:
        Identifies top-selling goods and fast-moving inventory based on sales velocity and demand analysis
        """
        sorted_by_velocity = sorted(PRODUCT_CATALOG, key=lambda x: x["velocity_score"], reverse=True)
        top_selling = [
            {
                "product_id": p["id"],
                "title": p["title"],
                "category": p["category"],
                "price": p["price"],
                "sales_count": p["sales_count"],
                "velocity_score": p["velocity_score"],
                "rating": p["rating"],
                "turnover_status": "Fast Moving (High Margin)" if p["velocity_score"] > 8.5 else "Stable Performer"
            }
            for p in sorted_by_velocity[:5]
        ]

        # High-demand inventory suggestions for seller
        high_demand_inventory_gaps = [
            {
                "item_name": "Solar Powered Milk Chillers (50L/100L)",
                "target_category": "Dairy",
                "estimated_monthly_demand": "18 - 25 units in block",
                "recommended_stock_action": "High Priority: Rural power instability creates urgent buyer demand."
            },
            {
                "item_name": "Multi-Crop Seeders & Battery Sprayers",
                "target_category": "Agro-machinery",
                "estimated_monthly_demand": "40 - 60 units in block",
                "recommended_stock_action": "Stock up before pre-monsoon planting cycle."
            },
            {
                "item_name": "Digital Weighing Scales with Thermal Receipt Printer",
                "target_category": "Retail & Dairy",
                "estimated_monthly_demand": "30 - 35 units in block",
                "recommended_stock_action": "Bundle with retail packaging machinery for 12% higher ticket size."
            }
        ]

        return {
            "seller_id": seller_id,
            "top_selling_goods": top_selling,
            "high_demand_stock_opportunities": high_demand_inventory_gaps,
            "pricing_recommendation": "Current top-selling products have strong price inelasticity. Consider volume discounts for purchases funded by SCA term loans."
        }

recommender = MLRecommender()
