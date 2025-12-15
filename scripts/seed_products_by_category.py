"""
Seed script to create 10 products for each category
Categories: Protein & Fitness, Weight Management, Beauty & Wellness, 
           Probiotics & Digestive Health, Brain & Focus, Immune Support, Omega-3 & Heart Health
"""
import sys
import os
from datetime import date, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_db_session
from app.models.sqlalchemy import Product, ProductSize, Category
from app.models.sqlalchemy.join_tables import product_categories
from sqlalchemy.orm import Session


# Categories from UI
CATEGORIES = [
    "Protein & Fitness",
    "Weight Management", 
    "Beauty & Wellness",
    "Probiotics & Digestive Health",
    "Brain & Focus",
    "Immune Support",
    "Omega-3 & Heart Health"
]

# Product templates for each category
PRODUCT_TEMPLATES = {
    "Protein & Fitness": [
        {"name": "Whey Protein Isolate", "base_price": 49.99, "keywords": ["muscle", "recovery", "workout"], "img": "https://images.unsplash.com/photo-1579722820308-d74e571900a9?w=500&h=500&fit=crop"},
        {"name": "BCAA Energy Powder", "base_price": 34.99, "keywords": ["amino acids", "energy", "endurance"], "img": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=500&h=500&fit=crop"},
        {"name": "Creatine Monohydrate", "base_price": 24.99, "keywords": ["strength", "performance", "muscle"], "img": "https://images.unsplash.com/photo-1594737626072-90dc274bc2bd?w=500&h=500&fit=crop"},
        {"name": "Pre-Workout Formula", "base_price": 39.99, "keywords": ["energy", "focus", "pump"], "img": "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=500&h=500&fit=crop"},
        {"name": "Plant-Based Protein", "base_price": 44.99, "keywords": ["vegan", "organic", "clean"], "img": "https://images.unsplash.com/photo-1610970881699-44a5587cabec?w=500&h=500&fit=crop"},
        {"name": "Casein Protein Night", "base_price": 42.99, "keywords": ["slow-release", "recovery", "overnight"], "img": "https://images.unsplash.com/photo-1628863353691-0071c8c1874c?w=500&h=500&fit=crop"},
        {"name": "Mass Gainer Shake", "base_price": 54.99, "keywords": ["calories", "bulk", "growth"], "img": "https://images.unsplash.com/photo-1622484211484-22c39f9e8c0f?w=500&h=500&fit=crop"},
        {"name": "L-Glutamine Powder", "base_price": 29.99, "keywords": ["recovery", "immune", "gut"], "img": "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop"},
        {"name": "Beta-Alanine", "base_price": 27.99, "keywords": ["endurance", "performance", "fatigue"], "img": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop"},
        {"name": "EAA Complex", "base_price": 36.99, "keywords": ["essential amino acids", "muscle", "recovery"], "img": "https://images.unsplash.com/photo-1590736969955-71cc94901144?w=500&h=500&fit=crop"},
    ],
    "Weight Management": [
        {"name": "Garcinia Cambogia Extract", "base_price": 24.99, "keywords": ["appetite", "fat", "metabolism"], "img": "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop"},
        {"name": "Green Tea Fat Burner", "base_price": 19.99, "keywords": ["thermogenic", "energy", "antioxidant"], "img": "https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?w=500&h=500&fit=crop"},
        {"name": "CLA Softgels", "base_price": 29.99, "keywords": ["lean muscle", "fat loss", "body composition"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
        {"name": "Metabolism Booster", "base_price": 27.99, "keywords": ["energy", "calorie burn", "thyroid"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Appetite Control Formula", "base_price": 22.99, "keywords": ["cravings", "satiety", "fiber"], "img": "https://images.unsplash.com/photo-1603899122634-f086ca5f5ddd?w=500&h=500&fit=crop"},
        {"name": "Keto BHB Salts", "base_price": 34.99, "keywords": ["ketosis", "energy", "fat burn"], "img": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop"},
        {"name": "Carb Blocker Complex", "base_price": 26.99, "keywords": ["carbohydrate", "weight", "control"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "L-Carnitine Liquid", "base_price": 31.99, "keywords": ["fat metabolism", "energy", "endurance"], "img": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500&h=500&fit=crop"},
        {"name": "Forskolin Extract", "base_price": 21.99, "keywords": ["metabolism", "lean mass", "thermogenic"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Apple Cider Vinegar Gummies", "base_price": 18.99, "keywords": ["detox", "metabolism", "digestion"], "img": "https://images.unsplash.com/photo-1591952991455-e238997efbca?w=500&h=500&fit=crop"},
    ],
    "Beauty & Wellness": [
        {"name": "Collagen Peptides Powder", "base_price": 39.99, "keywords": ["skin", "hair", "nails"], "img": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&h=500&fit=crop"},
        {"name": "Biotin Hair Growth", "base_price": 16.99, "keywords": ["hair", "strong", "growth"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Hyaluronic Acid Serum", "base_price": 24.99, "keywords": ["hydration", "skin", "anti-aging"], "img": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop"},
        {"name": "Keratin Complex", "base_price": 29.99, "keywords": ["hair", "strength", "shine"], "img": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&h=500&fit=crop"},
        {"name": "MSM Beauty Blend", "base_price": 22.99, "keywords": ["joint", "skin", "sulfur"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Silica Supplement", "base_price": 19.99, "keywords": ["hair", "skin", "nails"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "Vitamin E Beauty Oil", "base_price": 17.99, "keywords": ["antioxidant", "skin", "moisturizer"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Marine Collagen", "base_price": 44.99, "keywords": ["skin elasticity", "wrinkles", "premium"], "img": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&h=500&fit=crop"},
        {"name": "Resveratrol Anti-Aging", "base_price": 34.99, "keywords": ["longevity", "antioxidant", "cellular"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Bamboo Extract Silica", "base_price": 21.99, "keywords": ["natural", "hair", "nails"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
    ],
    "Probiotics & Digestive Health": [
        {"name": "Multi-Strain Probiotic", "base_price": 32.99, "keywords": ["gut health", "immunity", "digestion"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "Digestive Enzymes Complex", "base_price": 24.99, "keywords": ["digestion", "bloating", "absorption"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Probiotic 50 Billion CFU", "base_price": 39.99, "keywords": ["gut flora", "immune", "balance"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
        {"name": "Prebiotic Fiber Powder", "base_price": 19.99, "keywords": ["gut health", "fiber", "regularity"], "img": "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop"},
        {"name": "L-Glutamine Gut Repair", "base_price": 28.99, "keywords": ["intestinal", "healing", "barrier"], "img": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop"},
        {"name": "Activated Charcoal", "base_price": 16.99, "keywords": ["detox", "bloating", "cleanse"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Ginger Root Extract", "base_price": 18.99, "keywords": ["nausea", "digestion", "anti-inflammatory"], "img": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&h=500&fit=crop"},
        {"name": "Aloe Vera Digestive", "base_price": 22.99, "keywords": ["soothing", "gut", "healing"], "img": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop"},
        {"name": "Psyllium Husk Fiber", "base_price": 14.99, "keywords": ["regularity", "fiber", "cleanse"], "img": "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop"},
        {"name": "Lactobacillus Acidophilus", "base_price": 26.99, "keywords": ["probiotic", "gut", "immunity"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
    ],
    "Brain & Focus": [
        {"name": "Omega-3 Fish Oil Brain", "base_price": 29.99, "keywords": ["DHA", "EPA", "cognitive"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
        {"name": "Lion's Mane Mushroom", "base_price": 34.99, "keywords": ["nootropic", "memory", "focus"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Alpha GPC Choline", "base_price": 27.99, "keywords": ["memory", "learning", "acetylcholine"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "Bacopa Monnieri Extract", "base_price": 24.99, "keywords": ["memory", "stress", "adaptogen"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Rhodiola Rosea", "base_price": 26.99, "keywords": ["stress", "energy", "mental clarity"], "img": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&h=500&fit=crop"},
        {"name": "Ginkgo Biloba", "base_price": 19.99, "keywords": ["circulation", "memory", "antioxidant"], "img": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop"},
        {"name": "L-Theanine Calm Focus", "base_price": 22.99, "keywords": ["relaxation", "focus", "stress"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Phosphatidylserine", "base_price": 32.99, "keywords": ["memory", "cognitive", "brain cell"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "Ashwagandha KSM-66", "base_price": 28.99, "keywords": ["stress", "cortisol", "adaptogen"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Acetyl L-Carnitine", "base_price": 31.99, "keywords": ["energy", "brain", "mitochondria"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
    ],
    "Immune Support": [
        {"name": "Vitamin C 1000mg", "base_price": 14.99, "keywords": ["immunity", "antioxidant", "cold"], "img": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop"},
        {"name": "Zinc Picolinate 50mg", "base_price": 12.99, "keywords": ["immune", "healing", "testosterone"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "Elderberry Syrup", "base_price": 19.99, "keywords": ["immunity", "antiviral", "respiratory"], "img": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500&h=500&fit=crop"},
        {"name": "Echinacea Extract", "base_price": 16.99, "keywords": ["immune", "cold", "flu"], "img": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&h=500&fit=crop"},
        {"name": "Vitamin D3 + K2", "base_price": 24.99, "keywords": ["bone", "immune", "calcium"], "img": "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop"},
        {"name": "Quercetin Complex", "base_price": 29.99, "keywords": ["antioxidant", "anti-inflammatory", "immune"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Beta Glucan 1,3/1,6", "base_price": 34.99, "keywords": ["immune", "macrophage", "defense"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Transfer Factor Plus", "base_price": 44.99, "keywords": ["immune memory", "defense", "support"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
        {"name": "Astragalus Root", "base_price": 21.99, "keywords": ["adaptogen", "immune", "vitality"], "img": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop"},
        {"name": "Olive Leaf Extract", "base_price": 26.99, "keywords": ["antiviral", "immune", "cardiovascular"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
    ],
    "Omega-3 & Heart Health": [
        {"name": "Triple Strength Fish Oil", "base_price": 34.99, "keywords": ["EPA", "DHA", "heart"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
        {"name": "Krill Oil Antarctic", "base_price": 44.99, "keywords": ["astaxanthin", "omega-3", "premium"], "img": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500&h=500&fit=crop"},
        {"name": "CoQ10 Ubiquinol 200mg", "base_price": 39.99, "keywords": ["heart", "energy", "antioxidant"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
        {"name": "Plant-Based Omega-3", "base_price": 29.99, "keywords": ["algae", "vegan", "DHA"], "img": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop"},
        {"name": "Red Yeast Rice", "base_price": 24.99, "keywords": ["cholesterol", "heart", "statin"], "img": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop"},
        {"name": "Magnesium Glycinate", "base_price": 19.99, "keywords": ["heart rhythm", "muscle", "relaxation"], "img": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop"},
        {"name": "Hawthorn Berry Extract", "base_price": 22.99, "keywords": ["cardiovascular", "blood pressure", "heart"], "img": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&h=500&fit=crop"},
        {"name": "Garlic Extract Odorless", "base_price": 16.99, "keywords": ["cholesterol", "blood pressure", "circulation"], "img": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop"},
        {"name": "L-Arginine Plus", "base_price": 27.99, "keywords": ["nitric oxide", "circulation", "cardiovascular"], "img": "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop"},
        {"name": "Niacin Flush-Free", "base_price": 18.99, "keywords": ["cholesterol", "energy", "B3"], "img": "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop"},
    ],
}

MANUFACTURERS = ["NOW Foods", "Nature's Way", "Pure Encapsulations", "Garden of Life", "Thorne", "Life Extension", "Jarrow Formulas", "Solgar", "Nutricost", "Optimum Nutrition"]
CERTIFICATIONS = ["FDA Registered, GMP Certified", "GMP, NSF Certified", "USDA Organic, Non-GMO", "FDA Registered, Third-Party Tested", "GMP Certified, Vegan"]


def ensure_categories(db: Session):
    """Ensure all categories exist in database"""
    print("📋 Ensuring categories exist...")
    
    existing_categories = {cat.name: cat for cat in db.query(Category).all()}
    
    for cat_name in CATEGORIES:
        if cat_name not in existing_categories:
            category = Category(name=cat_name, description=f"{cat_name} supplements and products")
            db.add(category)
            print(f"  ✓ Created category: {cat_name}")
        else:
            print(f"  - Category exists: {cat_name}")
    
    db.commit()
    print("✓ All categories ready\n")


def create_products_for_category(db: Session, category_name: str):
    """Create 10 products for a specific category"""
    
    # Get category object
    category = db.query(Category).filter(Category.name == category_name).first()
    if not category:
        print(f"❌ Category not found: {category_name}")
        return
    
    templates = PRODUCT_TEMPLATES.get(category_name, [])
    expiry_date = date.today() + timedelta(days=730)  # 2 years from now
    
    print(f"\n🔨 Creating products for: {category_name}")
    
    for idx, template in enumerate(templates, 1):
        # Generate product data
        slug = f"{template['name'].lower().replace(' ', '-')}-{random.randint(1000, 9999)}"
        product_name = template['name']
        base_price = template['base_price']
        
        # Random sale price (30% of products on sale)
        sale_price = round(base_price * 0.8, 2) if random.random() < 0.3 else None
        
        # Random stock
        stock = random.randint(50, 200)
        
        # Generate description
        keywords = ", ".join(template['keywords'])
        blurb = f"Premium {product_name} for optimal {template['keywords'][0]} support"
        description = f"High-quality {product_name} supplement formulated to support {keywords}. Made with premium ingredients and manufactured under strict quality standards."
        
        # Random manufacturer and certification
        manufacturer = random.choice(MANUFACTURERS)
        certification = random.choice(CERTIFICATIONS)
        
        # Create product
        product = Product(
            slug=slug,
            product_type=category_name,
            product_name=product_name,
            price=base_price,
            sale_price=sale_price,
            stock=stock,
            blurb=blurb,
            description=description,
            image_url=template.get("img", "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop"),
            serving_size="1-2 capsules" if "Powder" not in product_name else "1 scoop",
            servings_per_container=random.choice([30, 60, 90]),
            ingredients=f"{product_name} Extract, Vegetable Cellulose, Rice Flour, Magnesium Stearate",
            allergen_info="Free from major allergens" if random.random() < 0.7 else "Contains Soy",
            usage_instructions="Take as directed on label or as recommended by healthcare professional.",
            warnings="Consult physician before use if pregnant, nursing, or taking medication.",
            expiry_date=expiry_date,
            manufacturer=manufacturer,
            country_of_origin="USA" if random.random() < 0.8 else "Canada",
            certification=certification
        )
        
        db.add(product)
        db.flush()  # Get product ID
        
        # Link to category using association table
        db.execute(
            product_categories.insert().values(
                product_id=product.id,
                category_id=category.id
            )
        )
        
        # Add product sizes
        sizes = [
            ProductSize(product_id=product.id, size="30 servings", stock_quantity=random.randint(20, 80)),
            ProductSize(product_id=product.id, size="60 servings", stock_quantity=random.randint(40, 120)),
        ]
        db.add_all(sizes)
        
        print(f"  ✓ [{idx}/10] {product_name} (${base_price})")
    
    db.commit()
    print(f"✅ Completed {category_name}: 10 products created")


def main():
    """Main function"""
    print("🚀 Starting product seeding process...\n")
    
    db = get_db_session()
    
    try:
        # Ensure categories exist
        ensure_categories(db)
        
        # Create products for each category
        for category_name in CATEGORIES:
            create_products_for_category(db, category_name)
        
        # Summary
        print("\n" + "="*60)
        print("📊 SEEDING SUMMARY")
        print("="*60)
        
        total_products = db.query(Product).count()
        print(f"Total products in database: {total_products}")
        
        print("\nProducts by category:")
        for category in db.query(Category).all():
            count = len(category.products)
            print(f"  - {category.name}: {count} products")
        
        print("\n✅ Seeding completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
