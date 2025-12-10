"""
Seed script to populate database with sample supplement products
Run: python -m scripts.seed_supplements
"""
import sys
import os
from datetime import date, datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_db_session
from app.models.sqlalchemy import Product, ProductSize, Order, OrderItem, Cart, Cart_Item, Review
from sqlalchemy.orm import Session


def clear_existing_products(db: Session):
    """Clear existing fashion products and related data"""
    print("🗑️  Clearing existing data...")
    
    # Delete in order to respect foreign key constraints
    db.query(Review).delete()
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.query(Cart_Item).delete()
    db.query(Cart).delete()
    db.query(ProductSize).delete()
    db.query(Product).delete()
    
    db.commit()
    print("✓ Existing products and related data cleared")


def create_supplement_products(db: Session):
    """Create sample supplement products"""
    
    # Calculate expiry dates (2 years from now)
    expiry_date = date.today() + timedelta(days=730)
    
    supplements = [
        # Vitamins & Minerals
        {
            "slug": "vitamin-d3-5000iu",
            "product_type": "Vitamins & Minerals",
            "product_name": "Vitamin D3 5000 IU",
            "price": 19.99,
            "sale_price": 15.99,
            "stock": 200,
            "blurb": "High-potency Vitamin D3 for bone and immune health",
            "description": "Premium Vitamin D3 (Cholecalciferol) supplement supporting bone health, immune function, and overall wellness. Each softgel delivers 5000 IU of vitamin D3 for optimal absorption.",
            "image_url": "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop",
            "serving_size": "1 softgel",
            "servings_per_container": 60,
            "ingredients": "Vitamin D3 (as Cholecalciferol), Olive Oil, Gelatin, Glycerin, Purified Water",
            "allergen_info": "None",
            "usage_instructions": "Take 1 softgel daily with a meal, or as directed by your healthcare professional.",
            "warnings": "Do not exceed recommended dose. Consult your physician if pregnant, nursing, taking medication, or have a medical condition.",
            "expiry_date": expiry_date,
            "manufacturer": "Pure Health Labs",
            "country_of_origin": "USA",
            "certification": "FDA Registered, GMP Certified",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 80},
                {"size": "60 servings", "stock_quantity": 120},
            ]
        },
        {
            "slug": "multivitamin-men",
            "product_type": "Vitamins & Minerals",
            "product_name": "Daily Multivitamin for Men",
            "price": 29.99,
            "sale_price": 24.99,
            "stock": 150,
            "blurb": "Complete daily nutrition tailored for men's health",
            "description": "Comprehensive multivitamin formulated specifically for men, featuring essential vitamins, minerals, and antioxidants to support energy, immunity, and overall health.",
            "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop",
            "serving_size": "2 tablets",
            "servings_per_container": 30,
            "ingredients": "Vitamin A, C, D, E, B Complex, Zinc, Selenium, Magnesium, Lycopene, Saw Palmetto",
            "allergen_info": "Contains Soy",
            "usage_instructions": "Take 2 tablets daily with food.",
            "warnings": "Keep out of reach of children. Consult physician before use if you have any medical conditions.",
            "expiry_date": expiry_date,
            "manufacturer": "VitaMax",
            "country_of_origin": "USA",
            "certification": "GMP, NSF Certified",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 150},
            ]
        },
        
        # Protein & Fitness
        {
            "slug": "whey-protein-isolate-chocolate",
            "product_type": "Protein & Fitness",
            "product_name": "Whey Protein Isolate - Chocolate",
            "price": 49.99,
            "sale_price": 39.99,
            "stock": 180,
            "blurb": "Premium whey isolate with 25g protein per serving",
            "description": "100% pure whey protein isolate with 25g of protein per scoop. Fast-absorbing formula perfect for post-workout recovery and muscle building. Great-tasting chocolate flavor.",
            "image_url": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=500&h=500&fit=crop",
            "serving_size": "1 scoop (30g)",
            "servings_per_container": 30,
            "ingredients": "Whey Protein Isolate, Natural Cocoa Powder, Natural Flavors, Stevia, Sunflower Lecithin",
            "allergen_info": "Contains Milk",
            "usage_instructions": "Mix 1 scoop with 8-10 oz of cold water or milk. Consume post-workout or between meals.",
            "warnings": "Consult physician if pregnant or nursing. Keep refrigerated after opening.",
            "expiry_date": expiry_date,
            "manufacturer": "NutriFit Labs",
            "country_of_origin": "USA",
            "certification": "GMP, NSF Certified for Sport",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 100},
                {"size": "60 servings", "stock_quantity": 80},
            ]
        },
        {
            "slug": "bcaa-powder-fruit-punch",
            "product_type": "Protein & Fitness",
            "product_name": "BCAA 2:1:1 Powder - Fruit Punch",
            "price": 34.99,
            "sale_price": 27.99,
            "stock": 120,
            "blurb": "Branch Chain Amino Acids for muscle recovery",
            "description": "Scientifically formulated BCAA powder with 2:1:1 ratio of Leucine, Isoleucine, and Valine. Supports muscle recovery, reduces fatigue, and promotes lean muscle growth.",
            "image_url": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?w=500&h=500&fit=crop",
            "serving_size": "1 scoop (7g)",
            "servings_per_container": 30,
            "ingredients": "L-Leucine, L-Isoleucine, L-Valine, Natural Flavors, Citric Acid, Stevia",
            "allergen_info": "None",
            "usage_instructions": "Mix 1 scoop with 8-12 oz water. Take before, during, or after workout.",
            "warnings": "Consult healthcare provider before use if pregnant, nursing, or have medical conditions.",
            "expiry_date": expiry_date,
            "manufacturer": "PowerFuel",
            "country_of_origin": "USA",
            "certification": "GMP, Informed-Sport Certified",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 120},
            ]
        },
        
        # Weight Management
        {
            "slug": "green-tea-extract-fat-burner",
            "product_type": "Weight Management",
            "product_name": "Green Tea Extract Fat Burner",
            "price": 24.99,
            "sale_price": 19.99,
            "stock": 140,
            "blurb": "Natural thermogenic with EGCG for metabolism support",
            "description": "Powerful green tea extract standardized to 50% EGCG. Supports healthy metabolism, fat oxidation, and energy levels. Caffeine-free option available.",
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop",
            "serving_size": "2 capsules",
            "servings_per_container": 30,
            "ingredients": "Green Tea Extract (50% EGCG), Vegetable Cellulose Capsule",
            "allergen_info": "None",
            "usage_instructions": "Take 2 capsules daily with meals. Do not exceed recommended dose.",
            "warnings": "Contains caffeine. Not for use by pregnant or nursing women. Discontinue if adverse reactions occur.",
            "expiry_date": expiry_date,
            "manufacturer": "SlimNature",
            "country_of_origin": "USA",
            "certification": "Non-GMO, Gluten-Free, GMP",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 90},
                {"size": "60 servings", "stock_quantity": 50},
            ]
        },
        {
            "slug": "cla-conjugated-linoleic-acid",
            "product_type": "Weight Management",
            "product_name": "CLA 1000mg (Conjugated Linoleic Acid)",
            "price": 22.99,
            "sale_price": None,
            "stock": 100,
            "blurb": "Support lean muscle and healthy body composition",
            "description": "Pure CLA derived from safflower oil. Supports lean muscle maintenance, fat metabolism, and healthy body composition when combined with exercise and diet.",
            "image_url": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500&h=500&fit=crop",
            "serving_size": "3 softgels",
            "servings_per_container": 30,
            "ingredients": "CLA (Conjugated Linoleic Acid from Safflower Oil), Gelatin, Glycerin, Purified Water",
            "allergen_info": "None",
            "usage_instructions": "Take 3 softgels daily with meals.",
            "warnings": "Consult physician before use if pregnant, nursing, or taking medications.",
            "expiry_date": expiry_date,
            "manufacturer": "LeanBody",
            "country_of_origin": "USA",
            "certification": "GMP, Non-GMO",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 100},
            ]
        },
        
        # Beauty & Skin
        {
            "slug": "collagen-peptides-powder",
            "product_type": "Beauty & Skin",
            "product_name": "Collagen Peptides Powder - Unflavored",
            "price": 39.99,
            "sale_price": 32.99,
            "stock": 160,
            "blurb": "Grass-fed collagen for skin, hair, and joint health",
            "description": "Premium grass-fed collagen peptides powder. Supports skin elasticity, hair strength, nail growth, and joint health. Easily mixes in hot or cold beverages.",
            "image_url": "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=500&h=500&fit=crop",
            "serving_size": "2 scoops (20g)",
            "servings_per_container": 30,
            "ingredients": "Hydrolyzed Collagen Peptides (Bovine)",
            "allergen_info": "None",
            "usage_instructions": "Mix 2 scoops into coffee, tea, smoothies, or water daily. Can be used in cooking and baking.",
            "warnings": "Consult physician if pregnant, nursing, or have medical condition.",
            "expiry_date": expiry_date,
            "manufacturer": "VitaGlow",
            "country_of_origin": "USA",
            "certification": "Grass-Fed, Non-GMO, Paleo Friendly",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 90},
                {"size": "60 servings", "stock_quantity": 70},
            ]
        },
        {
            "slug": "biotin-10000mcg-hair-growth",
            "product_type": "Beauty & Skin",
            "product_name": "Biotin 10,000mcg for Hair Growth",
            "price": 16.99,
            "sale_price": 12.99,
            "stock": 180,
            "blurb": "High-potency biotin for healthy hair, skin, and nails",
            "description": "Maximum strength biotin supplement supporting hair growth, skin health, and strong nails. Vegetarian-friendly softgels for easy absorption.",
            "image_url": "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=500&h=500&fit=crop",
            "serving_size": "1 softgel",
            "servings_per_container": 90,
            "ingredients": "Biotin (as D-Biotin), Soybean Oil, Gelatin, Glycerin, Purified Water",
            "allergen_info": "Contains Soy",
            "usage_instructions": "Take 1 softgel daily, preferably with a meal.",
            "warnings": "Consult healthcare provider before use if pregnant or nursing.",
            "expiry_date": expiry_date,
            "manufacturer": "BeautyVit",
            "country_of_origin": "USA",
            "certification": "GMP, Gluten-Free",
            "sizes": [
                {"size": "90 servings", "stock_quantity": 180},
            ]
        },
        
        # Digestive Health
        {
            "slug": "probiotic-50-billion-cfu",
            "product_type": "Digestive Health",
            "product_name": "Probiotic 50 Billion CFU",
            "price": 34.99,
            "sale_price": 28.99,
            "stock": 130,
            "blurb": "Advanced probiotic blend for gut health and immunity",
            "description": "Powerful probiotic formula with 50 billion CFU and 10 probiotic strains. Supports digestive health, immune function, and nutrient absorption. Shelf-stable delayed-release capsules.",
            "image_url": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500&h=500&fit=crop",
            "serving_size": "1 capsule",
            "servings_per_container": 60,
            "ingredients": "Probiotic Blend (Lactobacillus acidophilus, Bifidobacterium lactis, and 8 other strains), Vegetable Cellulose Capsule, Rice Flour",
            "allergen_info": "Contains Milk (from probiotic strains)",
            "usage_instructions": "Take 1 capsule daily on an empty stomach or as directed by healthcare professional.",
            "warnings": "Consult physician before use if immunocompromised, pregnant, or nursing.",
            "expiry_date": expiry_date,
            "manufacturer": "GutHealth Pro",
            "country_of_origin": "USA",
            "certification": "GMP, Non-GMO, Gluten-Free",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 60},
                {"size": "60 servings", "stock_quantity": 70},
            ]
        },
        
        # Brain & Focus
        {
            "slug": "omega3-fish-oil-triple-strength",
            "product_type": "Brain & Focus",
            "product_name": "Omega-3 Fish Oil Triple Strength",
            "price": 29.99,
            "sale_price": 24.99,
            "stock": 140,
            "blurb": "High-potency EPA & DHA for brain and heart health",
            "description": "Premium fish oil supplement with 900mg EPA and 600mg DHA per serving. Supports brain function, cardiovascular health, and reduces inflammation. Molecularly distilled and mercury-free.",
            "image_url": "https://images.unsplash.com/photo-1609133522720-5ab4e4c6c609?w=500&h=500&fit=crop",
            "serving_size": "2 softgels",
            "servings_per_container": 60,
            "ingredients": "Fish Oil Concentrate (Anchovy, Sardine, Mackerel), Gelatin, Glycerin, Natural Lemon Flavor, Mixed Tocopherols",
            "allergen_info": "Contains Fish",
            "usage_instructions": "Take 2 softgels daily with meals.",
            "warnings": "Consult physician if taking blood thinners. Keep refrigerated after opening.",
            "expiry_date": expiry_date,
            "manufacturer": "OceanPure",
            "country_of_origin": "USA",
            "certification": "IFOS Certified, Mercury-Free, Sustainably Sourced",
            "sizes": [
                {"size": "60 servings", "stock_quantity": 140},
            ]
        },
        {
            "slug": "lions-mane-mushroom-extract",
            "product_type": "Brain & Focus",
            "product_name": "Lion's Mane Mushroom Extract",
            "price": 27.99,
            "sale_price": None,
            "stock": 90,
            "blurb": "Cognitive support and mental clarity nootropic",
            "description": "Organic Lion's Mane mushroom extract standardized to 30% polysaccharides. Supports cognitive function, memory, focus, and nervous system health. Vegan-friendly capsules.",
            "image_url": "https://images.unsplash.com/photo-1618775817208-04d9a3f9c6d3?w=500&h=500&fit=crop",
            "serving_size": "2 capsules",
            "servings_per_container": 30,
            "ingredients": "Organic Lion's Mane Mushroom Extract (Hericium erinaceus), Vegetable Cellulose Capsule",
            "allergen_info": "None",
            "usage_instructions": "Take 2 capsules daily with or without food.",
            "warnings": "Consult healthcare provider before use if pregnant, nursing, or taking medications.",
            "expiry_date": expiry_date,
            "manufacturer": "FungiFocus",
            "country_of_origin": "USA",
            "certification": "USDA Organic, Non-GMO, Vegan",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 90},
            ]
        },
        
        # Immune Support
        {
            "slug": "vitamin-c-1000mg-immunity",
            "product_type": "Immune Support",
            "product_name": "Vitamin C 1000mg with Rose Hips",
            "price": 18.99,
            "sale_price": 14.99,
            "stock": 200,
            "blurb": "Powerful immune support and antioxidant protection",
            "description": "High-potency Vitamin C with added rose hips for enhanced absorption. Supports immune function, collagen production, and provides antioxidant protection against free radicals.",
            "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop",
            "serving_size": "1 tablet",
            "servings_per_container": 90,
            "ingredients": "Vitamin C (as Ascorbic Acid), Rose Hips Extract, Cellulose, Stearic Acid, Silicon Dioxide",
            "allergen_info": "None",
            "usage_instructions": "Take 1 tablet daily with a meal.",
            "warnings": "Consult physician before use if pregnant, nursing, or have kidney issues.",
            "expiry_date": expiry_date,
            "manufacturer": "ImmunePlus",
            "country_of_origin": "USA",
            "certification": "GMP, Non-GMO, Gluten-Free",
            "sizes": [
                {"size": "90 servings", "stock_quantity": 200},
            ]
        },
        {
            "slug": "elderberry-zinc-immunity-gummies",
            "product_type": "Immune Support",
            "product_name": "Elderberry + Zinc Immunity Gummies",
            "price": 21.99,
            "sale_price": 17.99,
            "stock": 150,
            "blurb": "Delicious immune support with elderberry and zinc",
            "description": "Great-tasting elderberry gummies fortified with zinc and vitamin C. Supports immune health year-round. Perfect for adults and kids over 12. Natural berry flavor.",
            "image_url": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop",
            "serving_size": "2 gummies",
            "servings_per_container": 30,
            "ingredients": "Elderberry Extract, Zinc (as Zinc Citrate), Vitamin C, Glucose Syrup, Sugar, Pectin, Natural Flavors, Citric Acid",
            "allergen_info": "None",
            "usage_instructions": "Adults and children 12+: Take 2 gummies daily. Do not exceed recommended dose.",
            "warnings": "Keep out of reach of children. Consult physician if pregnant or nursing.",
            "expiry_date": expiry_date,
            "manufacturer": "BerryBoost",
            "country_of_origin": "USA",
            "certification": "Gluten-Free, Gelatin-Free, Non-GMO",
            "sizes": [
                {"size": "30 servings", "stock_quantity": 100},
                {"size": "60 servings", "stock_quantity": 50},
            ]
        },
    ]
    
    print(f"\n📦 Creating {len(supplements)} supplement products...")
    
    for data in supplements:
        # Extract sizes
        sizes_data = data.pop("sizes", [])
        
        # Create product
        product = Product(**data)
        db.add(product)
        db.flush()  # Get product ID
        
        # Create sizes
        for size_data in sizes_data:
            product_size = ProductSize(
                product_id=product.id,
                size=size_data["size"],
                stock_quantity=size_data["stock_quantity"]
            )
            db.add(product_size)
        
        print(f"  ✓ {product.product_name} ({product.product_type})")
    
    db.commit()
    print(f"\n✅ Successfully created {len(supplements)} supplement products!")


def main():
    """Main seed function"""
    print("=" * 60)
    print("🌱 SUPPLEMENT PRODUCTS SEED SCRIPT")
    print("=" * 60)
    
    db = get_db_session()
    
    try:
        # Step 1: Clear existing products
        clear_existing_products(db)
        
        # Step 2: Create supplement products
        create_supplement_products(db)
        
        # Step 3: Verify
        total_products = db.query(Product).count()
        total_sizes = db.query(ProductSize).count()
        
        print("\n" + "=" * 60)
        print("📊 DATABASE SUMMARY")
        print("=" * 60)
        print(f"Total Products: {total_products}")
        print(f"Total Size Variants: {total_sizes}")
        
        # Show breakdown by category
        print("\nProducts by Category:")
        categories = db.query(Product.product_type).distinct().all()
        for (category,) in categories:
            count = db.query(Product).filter(Product.product_type == category).count()
            print(f"  - {category}: {count} products")
        
        print("\n🎉 Seed completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
