"""
Community Assist - Flask Web Application
Bilingual, mobile-first social services navigator
"""

import os
from functools import wraps
from typing import Dict, List, Optional

from flask import Flask, g, render_template, request, jsonify, redirect, url_for, make_response
from loguru import logger

from src.config import get_settings
from src.database import get_db_connection

# Initialize Flask app
app = Flask(__name__)
settings = get_settings()
app.secret_key = settings.secret_key

# =============================================================================
# Language & Translation Support
# =============================================================================

SUPPORTED_LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = settings.default_language


def get_current_language() -> str:
    """Get current language from request args, cookie, or default."""
    # Check URL parameter first
    lang = request.args.get("lang")
    if lang in SUPPORTED_LANGUAGES:
        return lang

    # Then check cookie
    lang = request.cookies.get("lang")
    if lang in SUPPORTED_LANGUAGES:
        return lang

    # Default
    return DEFAULT_LANGUAGE


@app.before_request
def set_language():
    """Set language for current request."""
    g.lang = get_current_language()
    g.translations = {}

    # Load translations
    try:
        db = get_db_connection()
        g.translations = db.get_all_translations(g.lang)
    except Exception as e:
        logger.warning(f"Could not load translations: {e}")


@app.after_request
def save_language_preference(response):
    """Save language preference to cookie if changed."""
    if "lang" in request.args:
        response.set_cookie(
            "lang",
            request.args["lang"],
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=True,
            samesite="Lax"
        )
    return response


def t(key: str, **kwargs) -> str:
    """Get translation for a key."""
    text = g.translations.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


# Make translation function available in templates
app.jinja_env.globals["t"] = t
app.jinja_env.globals["lang"] = lambda: g.lang


# =============================================================================
# Template Helpers
# =============================================================================

@app.context_processor
def inject_globals():
    """Inject global variables into all templates."""
    return {
        "lang": g.lang,
        "settings": settings,
        "categories": [
            {"id": "food", "icon": "🍎", "key": "category.food"},
            {"id": "housing", "icon": "🏠", "key": "category.housing"},
            {"id": "healthcare", "icon": "💊", "key": "category.healthcare"},
            {"id": "financial", "icon": "💰", "key": "category.financial"},
            {"id": "childcare", "icon": "👶", "key": "category.childcare"},
            {"id": "employment", "icon": "💼", "key": "category.employment"},
            {"id": "legal", "icon": "⚖️", "key": "category.legal"},
            {"id": "senior", "icon": "👴", "key": "category.senior"},
            {"id": "disability", "icon": "♿", "key": "category.disability"},
            {"id": "veteran", "icon": "🎖️", "key": "category.veteran"},
            {"id": "education", "icon": "📚", "key": "category.education"},
            {"id": "transportation", "icon": "🚗", "key": "category.transportation"},
        ]
    }


# =============================================================================
# Routes: Core Pages
# =============================================================================

@app.route("/")
def home():
    """Home page with quick access to finder and stats."""
    try:
        db = get_db_connection()
        stats = db.get_program_stats()
        category_counts = db.get_category_counts()
        emergency_programs = db.get_emergency_programs()[:5]  # Top 5
    except Exception as e:
        logger.error(f"Error loading home page data: {e}")
        stats = {}
        category_counts = []
        emergency_programs = []

    return render_template(
        "home.html",
        stats=stats,
        category_counts=category_counts,
        emergency_programs=emergency_programs
    )


@app.route("/finder")
def finder():
    """Program finder wizard - main entry point."""
    step = request.args.get("step", "1")
    return render_template(f"finder/step{step}.html", step=int(step))


@app.route("/finder/results")
def finder_results():
    """Show program finder results based on user selections."""
    # Get user selections from query params (stored in session/cookie by JS)
    household_size = int(request.args.get("household_size", 1))
    income_range = request.args.get("income_range", "")
    needs = request.args.getlist("needs")
    situations = request.args.getlist("situations")
    has_children = request.args.get("has_children") == "true"
    has_senior = request.args.get("has_senior") == "true"
    has_disability = request.args.get("has_disability") == "true"
    is_veteran = request.args.get("is_veteran") == "true"

    # Build user profile for matching
    user_profile = {
        "household_size": household_size,
        "income_range": income_range,
        "needs": needs,
        "situations": situations,
        "has_children": has_children,
        "has_senior": has_senior,
        "has_disability": has_disability,
        "is_veteran": is_veteran,
        "county": settings.target_county
    }

    # Get and score programs
    try:
        db = get_db_connection()
        all_programs = db.get_all_programs(active_only=True)

        # Score each program
        scored_programs = []
        for program in all_programs:
            score = calculate_match_score(user_profile, program)
            if score > 0.1:  # Only include programs with some relevance
                scored_programs.append({
                    **program,
                    "match_score": round(score * 100)
                })

        # Sort by score descending
        scored_programs.sort(key=lambda x: x["match_score"], reverse=True)

    except Exception as e:
        logger.error(f"Error in finder results: {e}")
        scored_programs = []

    return render_template(
        "finder/results.html",
        programs=scored_programs,
        user_profile=user_profile,
        total_count=len(scored_programs)
    )


def calculate_match_score(user_profile: Dict, program: Dict) -> float:
    """
    Calculate how well a user matches a program's criteria.
    Returns score from 0.0 to 1.0
    """
    score = 0.0
    weights = {
        "category_match": 0.35,
        "situation": 0.25,
        "demographic": 0.20,
        "income": 0.20
    }

    # Category/need match
    user_needs = user_profile.get("needs", [])
    program_category = program.get("category", "")
    if program_category in user_needs:
        score += weights["category_match"]
    elif program_category:
        # Partial credit for related categories
        score += weights["category_match"] * 0.2

    # Situational match (emergency situations)
    user_situations = user_profile.get("situations", [])
    if program.get("is_emergency") and user_situations:
        score += weights["situation"]
    elif user_situations:
        # Check if program addresses user situations
        eligibility = program.get("eligibility_parsed") or {}
        for situation in user_situations:
            if eligibility.get(situation):
                score += weights["situation"] * 0.5
                break

    # Demographic match
    demographic_score = 0
    eligibility = program.get("eligibility_parsed") or {}

    if user_profile.get("has_children") and eligibility.get("serves_families"):
        demographic_score += 0.25
    if user_profile.get("has_senior") and eligibility.get("serves_seniors"):
        demographic_score += 0.25
    if user_profile.get("has_disability") and eligibility.get("serves_disabled"):
        demographic_score += 0.25
    if user_profile.get("is_veteran") and eligibility.get("serves_veterans"):
        demographic_score += 0.25

    if demographic_score == 0:
        demographic_score = 0.5  # Default if no specific demographics

    score += weights["demographic"] * demographic_score

    # Income match (simplified - assume match if we don't have specific data)
    # In a full implementation, this would check income_limits table
    if program.get("eligibility_parsed", {}).get("has_income_limit"):
        # Would check actual limits here
        score += weights["income"] * 0.7
    else:
        score += weights["income"]  # No income requirement = full match

    return min(score, 1.0)


# =============================================================================
# Routes: Programs
# =============================================================================

@app.route("/programs")
def programs_list():
    """Browse all programs with filtering."""
    category = request.args.get("category")
    search = request.args.get("q")

    try:
        db = get_db_connection()

        if search:
            programs = db.search_programs(search, g.lang)
        elif category:
            programs = db.get_programs_by_category(category)
        else:
            programs = db.get_all_programs(active_only=True)

        category_counts = db.get_category_counts()

    except Exception as e:
        logger.error(f"Error loading programs: {e}")
        programs = []
        category_counts = []

    return render_template(
        "programs/index.html",
        programs=programs,
        category_counts=category_counts,
        current_category=category,
        search_query=search
    )


@app.route("/program/<int:program_id>")
def program_detail(program_id: int):
    """Show detailed program information."""
    try:
        db = get_db_connection()
        program = db.get_program_by_id(program_id)

        if not program:
            return render_template("errors/404.html"), 404

        income_limits = db.get_income_limits(program_id)
        providers = db.get_providers_for_program(program_id)

    except Exception as e:
        logger.error(f"Error loading program {program_id}: {e}")
        return render_template("errors/500.html"), 500

    return render_template(
        "programs/detail.html",
        program=program,
        income_limits=income_limits,
        providers=providers
    )


# =============================================================================
# Routes: Calculator
# =============================================================================

@app.route("/calculator")
def calculator():
    """Benefit calculator page."""
    if not settings.enable_calculator:
        return redirect(url_for("home"))

    return render_template("calculator/index.html")


@app.route("/api/calculate/snap", methods=["POST"])
def calculate_snap():
    """Calculate estimated SNAP benefits."""
    data = request.get_json()

    household_size = int(data.get("household_size", 1))
    gross_monthly_income = float(data.get("gross_income", 0))
    rent = float(data.get("rent", 0))
    utilities = float(data.get("utilities", 0))

    result = estimate_snap_benefit(household_size, gross_monthly_income, rent, utilities)

    return jsonify(result)


def estimate_snap_benefit(household_size: int, gross_income: float,
                          rent: float = 0, utilities: float = 0) -> Dict:
    """
    Estimate SNAP benefits using simplified calculation.
    Note: Actual benefits may vary.
    """
    # 2024 FPL 130% limits for Florida
    income_limits = {
        1: 1580, 2: 2137, 3: 2694, 4: 3250,
        5: 3807, 6: 4364, 7: 4921, 8: 5478
    }

    # Maximum SNAP benefits 2024
    max_benefits = {
        1: 234, 2: 430, 3: 616, 4: 782,
        5: 929, 6: 1114, 7: 1232, 8: 1408
    }

    # Standard deduction
    standard_deduction = {
        1: 198, 2: 198, 3: 198, 4: 208,
        5: 244, 6: 279, 7: 314, 8: 349
    }

    size = min(household_size, 8)

    # Check eligibility
    if gross_income > income_limits[size]:
        return {
            "eligible": False,
            "reason": "Income exceeds 130% of Federal Poverty Level",
            "income_limit": income_limits[size],
            "your_income": gross_income
        }

    # Calculate net income
    net_income = gross_income - standard_deduction[size]

    # Shelter deduction (simplified)
    shelter_costs = rent + utilities
    shelter_deduction = max(0, shelter_costs - (net_income * 0.5))
    shelter_deduction = min(shelter_deduction, 624)  # Cap for non-elderly/disabled

    net_income -= shelter_deduction
    net_income = max(0, net_income)

    # Calculate benefit
    benefit = max_benefits[size] - (net_income * 0.3)
    benefit = max(0, min(benefit, max_benefits[size]))

    return {
        "eligible": True,
        "estimated_monthly": round(benefit),
        "maximum_possible": max_benefits[size],
        "calculation_details": {
            "gross_income": gross_income,
            "standard_deduction": standard_deduction[size],
            "shelter_deduction": round(shelter_deduction),
            "net_income": round(net_income)
        },
        "disclaimer": "This is an estimate only. Actual benefits are determined by Florida DCF."
    }


# =============================================================================
# Routes: Service Locator
# =============================================================================

@app.route("/locations")
def locations():
    """Service location finder."""
    if not settings.enable_locator:
        return redirect(url_for("home"))

    try:
        db = get_db_connection()
        providers = db.get_providers_by_county(settings.target_county)
    except Exception as e:
        logger.error(f"Error loading locations: {e}")
        providers = []

    return render_template("locator/index.html", providers=providers)


# =============================================================================
# Routes: API Endpoints
# =============================================================================

@app.route("/api/programs")
def api_programs():
    """API endpoint for programs (for AJAX/mobile)."""
    category = request.args.get("category")
    search = request.args.get("q")

    try:
        db = get_db_connection()

        if search:
            programs = db.search_programs(search, g.lang)
        elif category:
            programs = db.get_programs_by_category(category)
        else:
            programs = db.get_all_programs(active_only=True)

    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "programs": programs,
        "count": len(programs)
    })


@app.route("/api/translations/<lang>")
def api_translations(lang: str):
    """Get all translations for a language."""
    if lang not in SUPPORTED_LANGUAGES:
        return jsonify({"error": "Unsupported language"}), 400

    try:
        db = get_db_connection()
        translations = db.get_all_translations(lang)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(translations)


# =============================================================================
# Routes: Health & Utility
# =============================================================================

@app.route("/health")
def health():
    """Health check endpoint for deployment."""
    try:
        db = get_db_connection()
        db.execute_query("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return jsonify({
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "language": g.lang
    })


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# =============================================================================
# Run Application
# =============================================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=settings.flask_debug
    )
