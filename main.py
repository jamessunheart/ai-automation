"""AI Automation Services - Landing Page & Lead Capture"""

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from typing import Optional

# Import marketing engine API
from marketing_engine.api import router as marketing_router
from marketing_engine.dashboard import router as dashboard_router
from marketing_engine.api_prospects import router as prospects_router

app = FastAPI(
    title="AI Automation Services",
    description="Productized AI automation packages for businesses + AI Marketing Engine",
    version="1.0.0"
)

# Include marketing engine API routes
app.include_router(marketing_router)
app.include_router(dashboard_router, prefix="/api/marketing")
app.include_router(prospects_router)

# Get the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.get("/")
async def root():
    """Serve main AI automation landing page"""
    index_path = os.path.join(BASE_DIR, "index.html")
    return FileResponse(index_path)


@app.get("/health")
async def health():
    """UDC Endpoint 1: Health check"""
    return {
        "status": "active",
        "service": "ai-automation",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/capabilities")
async def capabilities():
    """UDC Endpoint 2: Service capabilities"""
    return {
        "version": "1.0.0",
        "features": [
            "AI automation landing page",
            "Lead capture & qualification",
            "ROI calculator",
            "Package information",
            "Marketing engine integration"
        ],
        "dependencies": ["marketing_engine"],
        "udc_version": "1.0",
        "metadata": {
            "packages": ["ai-employee", "ai-team", "ai-department"],
            "revenue_potential": "$120k MRR"
        }
    }


@app.get("/state")
async def state():
    """UDC Endpoint 3: Resource usage and performance"""
    return {
        "uptime_seconds": 0,
        "requests_total": 0,
        "requests_per_minute": 0.0,
        "errors_last_hour": 0,
        "last_restart": datetime.utcnow().isoformat() + "Z",
        "resource_usage": {
            "status": "operational",
            "load": "normal"
        }
    }


@app.get("/dependencies")
async def dependencies():
    """UDC Endpoint 4: Service dependencies"""
    return {
        "required": [],
        "optional": ["marketing_engine"],
        "missing": [],
        "integrations": {
            "sendgrid": "email",
            "stripe": "payments",
            "crm": "lead_tracking"
        }
    }


@app.post("/message")
async def message(payload: dict):
    """UDC Endpoint 5: Inter-service messaging"""
    return {
        "status": "received",
        "message_id": f"msg-{datetime.utcnow().timestamp()}",
        "processed_at": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/api/leads")
async def capture_lead(
    name: str = Form(...),
    email: str = Form(...),
    company: str = Form(...),
    package: str = Form(...),
    message: Optional[str] = Form(None)
):
    """
    Capture lead information from inquiry forms

    In production, this would:
    1. Store in database
    2. Send to CRM
    3. Trigger email notification
    4. Schedule follow-up

    For now, we'll log it and return success
    """

    lead_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "name": name,
        "email": email,
        "company": company,
        "package": package,
        "message": message,
        "source": "ai-automation-landing"
    }

    # TODO: Send to CRM/database
    # TODO: Trigger notification email
    # TODO: Add to email sequence

    # Log the lead (in production, this would go to proper logging)
    print(f"🎯 NEW LEAD: {name} ({company}) - Interested in: {package}")
    print(f"   Email: {email}")
    if message:
        print(f"   Message: {message}")

    return {
        "success": True,
        "message": "Thank you! We'll be in touch within 24 hours.",
        "next_steps": "Check your email for confirmation and next steps."
    }


@app.get("/api/roi-calculator")
async def roi_calculator(
    current_salary: float = 60000,
    num_employees: int = 1,
    package: str = "ai-team"
):
    """
    Calculate ROI for different packages

    Returns comparison between human employees and AI automation
    """

    # Package pricing
    package_pricing = {
        "ai-employee": 3000,
        "ai-team": 7000,
        "ai-department": 15000
    }

    monthly_cost = package_pricing.get(package, 7000)

    # Human employee costs (annual)
    base_salary = current_salary * num_employees
    benefits = base_salary * 0.30  # 30% benefits
    payroll_tax = base_salary * 0.0765  # 7.65% payroll tax
    training = 5000 * num_employees
    equipment = 3000 * num_employees

    total_human_annual = base_salary + benefits + payroll_tax + training + equipment

    # AI costs (annual)
    total_ai_annual = monthly_cost * 12

    # Calculate savings
    annual_savings = total_human_annual - total_ai_annual
    monthly_savings = annual_savings / 12
    roi_percentage = (annual_savings / total_ai_annual) * 100 if total_ai_annual > 0 else 0

    # Productivity multiplier
    # Human: ~2000 hours/year
    # AI: 8760 hours/year (24/7)
    productivity_multiplier = 8760 / 2000

    return {
        "human_costs": {
            "annual": round(total_human_annual, 2),
            "monthly": round(total_human_annual / 12, 2),
            "breakdown": {
                "salary": base_salary,
                "benefits": benefits,
                "payroll_tax": payroll_tax,
                "training": training,
                "equipment": equipment
            },
            "hours_per_year": 2000 * num_employees
        },
        "ai_costs": {
            "annual": total_ai_annual,
            "monthly": monthly_cost,
            "hours_per_year": 8760
        },
        "savings": {
            "annual": round(annual_savings, 2),
            "monthly": round(monthly_savings, 2),
            "roi_percentage": round(roi_percentage, 2)
        },
        "productivity": {
            "multiplier": round(productivity_multiplier, 2),
            "additional_hours": 8760 - (2000 * num_employees)
        },
        "package": package,
        "recommendation": get_package_recommendation(total_human_annual)
    }


def get_package_recommendation(annual_budget: float) -> dict:
    """Recommend package based on current spend"""

    if annual_budget < 50000:
        return {
            "package": "ai-employee",
            "reason": "Perfect for single-workflow automation"
        }
    elif annual_budget < 120000:
        return {
            "package": "ai-team",
            "reason": "Ideal for coordinated multi-workflow automation"
        }
    else:
        return {
            "package": "ai-department",
            "reason": "Best for complete department-level automation"
        }


@app.get("/api/packages")
async def get_packages():
    """Return available packages with details"""
    return {
        "packages": [
            {
                "id": "ai-employee",
                "name": "AI Employee",
                "price": 3000,
                "currency": "USD",
                "billing": "monthly",
                "features": [
                    "1 autonomous AI agent",
                    "Single workflow automation",
                    "24/7 operation",
                    "Weekly performance reports",
                    "Email support",
                    "Basic integrations"
                ],
                "best_for": "Small businesses, solopreneurs, single-process automation",
                "target_clients": "3-5 clients = $9-15k/month"
            },
            {
                "id": "ai-team",
                "name": "AI Team",
                "price": 7000,
                "currency": "USD",
                "billing": "monthly",
                "featured": True,
                "features": [
                    "3 coordinated AI agents",
                    "Multi-workflow automation",
                    "24/7 operation",
                    "Custom tool integrations",
                    "Daily monitoring & optimization",
                    "Priority support",
                    "Performance optimization",
                    "Monthly strategy calls"
                ],
                "best_for": "Growing businesses, multi-function automation, coordinated workflows",
                "target_clients": "2-3 clients = $14-21k/month"
            },
            {
                "id": "ai-department",
                "name": "AI Department",
                "price": 15000,
                "currency": "USD",
                "billing": "monthly",
                "features": [
                    "5+ AI agents + orchestration",
                    "Complete function automation",
                    "24/7 operation & monitoring",
                    "Custom integrations unlimited",
                    "Dedicated success manager",
                    "White-glove support",
                    "Advanced analytics & reporting",
                    "Continuous optimization",
                    "Weekly strategy sessions"
                ],
                "best_for": "Enterprise teams, complete department replacement, complex operations",
                "target_clients": "1-2 clients = $15-30k/month"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8700)
