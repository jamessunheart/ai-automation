"""
Stripe Payment Integration for AI Automation Services

This script creates Stripe products and payment links for the three AI automation packages.
Requires: pip install stripe
"""

import stripe
import os
import json

# Set your Stripe API key (will be loaded from environment or vault)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def create_products_and_prices():
    """Create Stripe products and recurring prices for all three packages"""

    products = []

    # AI Employee Package
    ai_employee = stripe.Product.create(
        name="AI Employee",
        description="1 autonomous AI agent for single workflow automation. 24/7 operation with weekly reports.",
        metadata={
            "package_id": "ai-employee",
            "agents": "1",
            "workflows": "single",
            "support": "email"
        }
    )

    ai_employee_price = stripe.Price.create(
        product=ai_employee.id,
        unit_amount=300000,  # $3,000.00 in cents
        currency="usd",
        recurring={"interval": "month"},
        metadata={
            "package": "ai-employee"
        }
    )

    products.append({
        "name": "AI Employee",
        "product_id": ai_employee.id,
        "price_id": ai_employee_price.id,
        "amount": "$3,000/month"
    })

    # AI Team Package (Featured)
    ai_team = stripe.Product.create(
        name="AI Team",
        description="3 coordinated AI agents for multi-workflow automation. Custom integrations with priority support.",
        metadata={
            "package_id": "ai-team",
            "agents": "3",
            "workflows": "multi",
            "support": "priority",
            "featured": "true"
        }
    )

    ai_team_price = stripe.Price.create(
        product=ai_team.id,
        unit_amount=700000,  # $7,000.00 in cents
        currency="usd",
        recurring={"interval": "month"},
        metadata={
            "package": "ai-team"
        }
    )

    products.append({
        "name": "AI Team",
        "product_id": ai_team.id,
        "price_id": ai_team_price.id,
        "amount": "$7,000/month"
    })

    # AI Department Package
    ai_department = stripe.Product.create(
        name="AI Department",
        description="5+ AI agents with orchestration for complete department automation. Dedicated success manager and white-glove support.",
        metadata={
            "package_id": "ai-department",
            "agents": "5+",
            "workflows": "complete",
            "support": "white-glove",
            "success_manager": "dedicated"
        }
    )

    ai_department_price = stripe.Price.create(
        product=ai_department.id,
        unit_amount=1500000,  # $15,000.00 in cents
        currency="usd",
        recurring={"interval": "month"},
        metadata={
            "package": "ai-department"
        }
    )

    products.append({
        "name": "AI Department",
        "product_id": ai_department.id,
        "price_id": ai_department_price.id,
        "amount": "$15,000/month"
    })

    return products


def create_payment_links(products):
    """Create Stripe payment links for each product"""

    payment_links = []

    for product in products:
        link = stripe.PaymentLink.create(
            line_items=[{
                "price": product["price_id"],
                "quantity": 1
            }],
            after_completion={
                "type": "redirect",
                "redirect": {
                    "url": "https://fullpotential.com/ai?success=true"
                }
            },
            allow_promotion_codes=True,
            metadata={
                "package": product["name"],
                "source": "ai-automation-landing"
            }
        )

        payment_links.append({
            "package": product["name"],
            "payment_link_url": link.url,
            "payment_link_id": link.id
        })

    return payment_links


def create_pilot_coupon():
    """Create 50% off coupon for pilot customers"""

    coupon = stripe.Coupon.create(
        percent_off=50,
        duration="once",  # First month only
        name="Pilot Program - 50% Off First Month",
        metadata={
            "program": "pilot",
            "valid_until": "2025-12-31"
        }
    )

    return coupon


def setup_stripe_automation():
    """Main function to set up all Stripe resources"""

    print("🚀 Setting up Stripe for AI Automation Services...\n")

    # Check if API key is set
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not set!")
        print("\nTo set up Stripe:")
        print("1. Get your secret key from https://dashboard.stripe.com/apikeys")
        print("2. Set environment variable: export STRIPE_SECRET_KEY='sk_...'")
        print("3. Or store in credential vault")
        return False

    try:
        # Create products and prices
        print("📦 Creating products and prices...")
        products = create_products_and_prices()

        for p in products:
            print(f"  ✅ {p['name']}: {p['amount']}")
            print(f"     Product ID: {p['product_id']}")
            print(f"     Price ID: {p['price_id']}")

        # Create payment links
        print("\n🔗 Creating payment links...")
        payment_links = create_payment_links(products)

        for link in payment_links:
            print(f"  ✅ {link['package']}")
            print(f"     {link['payment_link_url']}")

        # Create pilot coupon
        print("\n🎫 Creating pilot program coupon...")
        coupon = create_pilot_coupon()
        print(f"  ✅ Coupon: {coupon.name}")
        print(f"     Code: {coupon.id}")
        print(f"     {coupon.percent_off}% off first month")

        # Save configuration
        config = {
            "products": products,
            "payment_links": payment_links,
            "pilot_coupon": {
                "id": coupon.id,
                "code": coupon.id,
                "discount": f"{coupon.percent_off}%"
            }
        }

        with open('/Users/jamessunheart/Development/SERVICES/ai-automation/stripe_config.json', 'w') as f:
            json.dump(config, f, indent=2)

        print("\n✅ Stripe setup complete!")
        print("📄 Configuration saved to: stripe_config.json")
        print("\n🎯 Next steps:")
        print("1. Add payment links to landing page")
        print("2. Share pilot coupon code with prospects")
        print("3. Set up webhook for subscription events")

        return True

    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # This will be run when Stripe API key is available
    setup_stripe_automation()
