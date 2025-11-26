# Community Assist - Project Specification

## Executive Summary

**Community Assist** is a bilingual (English/Spanish), mobile-first web application that helps people discover, understand, and self-qualify for social services and assistance programs. The platform aggregates program data from multiple sources (211 databases, government websites, local nonprofits), extracts structured eligibility criteria, and presents users with personalized program matches through an intuitive, conversational-style questionnaire.

The system is designed to be location-agnostic but will initially launch targeting **Brevard County, Florida**.

---

## Core Concept

### The Problem
People in need often don't know what help is available or whether they qualify. Navigating the social services landscape is confusing, time-consuming, and frustrating. Many give up before finding programs that could help them.

### The Solution
A "one-stop shop" that:
1. **Aggregates** program data from 211, government agencies, and local providers
2. **Extracts** structured eligibility criteria (income limits, household requirements, etc.)
3. **Matches** users to programs through a friendly, guided questionnaire
4. **Explains** each program clearly with eligibility breakdowns, benefit estimates, and next steps
5. **Empowers** users with document checklists, service locations, and application guidance

### Target Audience
- Individuals and families facing financial hardship
- People in crisis (eviction, utility shutoff, food insecurity)
- Seniors on fixed incomes
- Veterans seeking benefits
- People with disabilities
- Caregivers seeking support
- Social workers and case managers helping clients
- 211 call center staff as a reference tool

---

## Technical Architecture

### Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend** | Python 3.10+ | Consistent with Farm Assist, excellent scraping libraries |
| **Web Framework** | Flask 3.0 | Lightweight, proven, good for APIs |
| **Database** | PostgreSQL 15 | JSONB support, robust, scalable |
| **ORM** | SQLAlchemy | Mature, flexible |
| **Scraping** | Playwright, BeautifulSoup4, httpx | JS rendering, HTML parsing, async HTTP |
| **PDF Processing** | pdfplumber, camelot-py | Text and table extraction |
| **NLP** | spaCy | Entity extraction, text processing |
| **Frontend** | Jinja2 + Tailwind CSS | Server-rendered, mobile-first |
| **Deployment** | Digital Ocean App Platform | Managed, auto-deploy from GitHub |
| **Containerization** | Docker | Consistent environments |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMUNITY ASSIST PLATFORM                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION LAYER                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   211 Sources   │  Gov Websites   │   Local Providers           │
│   - 211 APIs    │  - benefits.gov │   - Food banks              │
│   - 211 web     │  - DCF Florida  │   - Shelters                │
│   - AIRS data   │  - SSA.gov      │   - Nonprofits              │
│                 │  - HUD          │   - Churches                │
│                 │  - USDA/SNAP    │   - Community centers       │
└────────┬────────┴────────┬────────┴──────────────┬──────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRACTION & PROCESSING                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Web Scraper │  │ PDF Processor│  │ Eligibility Parser     │  │
│  │ - Discovery │  │ - Text/Tables│  │ - Income limits        │  │
│  │ - Content   │  │ - Forms      │  │ - Household rules      │  │
│  │ - Links     │  │ - Guides     │  │ - Categorical criteria │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ programs     │ │ providers    │ │ eligibility_criteria     │ │
│  │ - name       │ │ - name       │ │ - income_limits          │ │
│  │ - category   │ │ - address    │ │ - household_rules        │ │
│  │ - benefits   │ │ - hours      │ │ - categorical_flags      │ │
│  │ - how_to     │ │ - services   │ │ - fpl_percentage         │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ documents    │ │ fpl_tables   │ │ translations             │ │
│  │ - required   │ │ - year       │ │ - en/es content          │ │
│  │ - by_program │ │ - thresholds │ │ - all user-facing text   │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEB APPLICATION (Flask)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    BILINGUAL FRONTEND                     │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │   │
│  │  │   Finder    │ │  Programs   │ │  Benefit Calculator │ │   │
│  │  │  (Hybrid    │ │  (Browse/   │ │  (SNAP, Medicaid,   │ │   │
│  │  │   Wizard)   │ │   Search)   │ │   TANF estimates)   │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘ │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │   │
│  │  │  Program    │ │  Service    │ │  Document           │ │   │
│  │  │  Details    │ │  Locator    │ │  Checklist          │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

```sql
-- Programs: Core program information
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    program_code VARCHAR(50) UNIQUE,
    program_name VARCHAR(255) NOT NULL,
    program_name_es VARCHAR(255),
    category VARCHAR(100), -- food, housing, healthcare, financial, childcare, employment, legal, senior, disability
    subcategory VARCHAR(100),
    description TEXT,
    description_es TEXT,
    benefits_summary TEXT,
    benefits_summary_es TEXT,
    benefit_amount_min DECIMAL(10,2),
    benefit_amount_max DECIMAL(10,2),
    benefit_frequency VARCHAR(50), -- monthly, one-time, annual, varies
    how_to_apply TEXT,
    how_to_apply_es TEXT,
    application_url VARCHAR(500),
    application_deadline DATE,
    enrollment_period_start DATE,
    enrollment_period_end DATE,
    processing_time VARCHAR(100),
    eligibility_summary TEXT,
    eligibility_summary_es TEXT,
    eligibility_parsed JSONB, -- structured eligibility criteria
    documents_required JSONB, -- list of required documents
    source_url VARCHAR(500),
    source_name VARCHAR(255),
    last_verified DATE,
    confidence_score DECIMAL(3,2),
    is_active BOOLEAN DEFAULT true,
    is_emergency BOOLEAN DEFAULT false,
    serves_county VARCHAR(100)[],
    serves_state VARCHAR(2)[],
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    contact_website VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Eligibility criteria: Structured qualification rules
CREATE TABLE eligibility_criteria (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id),
    criterion_type VARCHAR(50), -- income, household, categorical, geographic, situational
    criterion_name VARCHAR(100),
    criterion_value JSONB, -- flexible storage for different criteria types
    is_required BOOLEAN DEFAULT true,
    notes TEXT,
    notes_es TEXT
);

-- Income limits by program and household size
CREATE TABLE income_limits (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id),
    household_size INTEGER,
    annual_limit DECIMAL(10,2),
    monthly_limit DECIMAL(10,2),
    fpl_percentage INTEGER, -- 100%, 130%, 200%, etc.
    effective_date DATE,
    expiration_date DATE
);

-- Federal Poverty Level reference table
CREATE TABLE fpl_tables (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    household_size INTEGER,
    annual_amount DECIMAL(10,2),
    monthly_amount DECIMAL(10,2),
    state VARCHAR(2) DEFAULT 'FL', -- Different for AK and HI
    UNIQUE(year, household_size, state)
);

-- Service providers/locations
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(255) NOT NULL,
    provider_name_es VARCHAR(255),
    provider_type VARCHAR(100), -- government, nonprofit, religious, community
    address_street VARCHAR(255),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    address_zip VARCHAR(10),
    address_county VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    hours_of_operation JSONB, -- {"monday": "9am-5pm", ...}
    services_offered TEXT[],
    languages_spoken VARCHAR(50)[],
    accessibility_features TEXT[],
    is_active BOOLEAN DEFAULT true,
    last_verified DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Program-provider relationship
CREATE TABLE program_providers (
    program_id INTEGER REFERENCES programs(id),
    provider_id INTEGER REFERENCES providers(id),
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    PRIMARY KEY (program_id, provider_id)
);

-- Required documents catalog
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255),
    document_name_es VARCHAR(255),
    document_type VARCHAR(100), -- id, income, residence, medical, legal
    description TEXT,
    description_es TEXT,
    how_to_obtain TEXT,
    how_to_obtain_es TEXT,
    alternatives TEXT[], -- acceptable alternatives
    is_common BOOLEAN DEFAULT false
);

-- Program-document relationship
CREATE TABLE program_documents (
    program_id INTEGER REFERENCES programs(id),
    document_id INTEGER REFERENCES documents(id),
    is_required BOOLEAN DEFAULT true,
    conditions TEXT, -- when this document is needed
    PRIMARY KEY (program_id, document_id)
);

-- Raw scraped pages (for reprocessing)
CREATE TABLE raw_pages (
    id SERIAL PRIMARY KEY,
    url VARCHAR(1000) UNIQUE,
    domain VARCHAR(255),
    page_type VARCHAR(100),
    raw_html TEXT,
    raw_text TEXT,
    links JSONB,
    scrape_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_code INTEGER,
    last_processed TIMESTAMP
);

-- Scraped documents (PDFs, etc.)
CREATE TABLE scraped_documents (
    id SERIAL PRIMARY KEY,
    source_url VARCHAR(1000),
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size_bytes INTEGER,
    local_path VARCHAR(500),
    full_text TEXT,
    tables_extracted JSONB,
    processed_at TIMESTAMP,
    linked_program_id INTEGER REFERENCES programs(id)
);

-- Translations table for all UI text
CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    translation_key VARCHAR(255) UNIQUE,
    text_en TEXT NOT NULL,
    text_es TEXT,
    context VARCHAR(100), -- ui, program, category, document
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scrape job tracking
CREATE TABLE scrape_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50),
    source_name VARCHAR(100),
    status VARCHAR(50), -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    records_processed INTEGER,
    records_added INTEGER,
    records_updated INTEGER,
    error_log TEXT
);

-- Data quality tracking
CREATE TABLE data_gaps (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id),
    missing_field VARCHAR(100),
    field_importance VARCHAR(20), -- critical, high, medium, low
    possible_sources TEXT[],
    notes TEXT,
    resolved_at TIMESTAMP
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_programs_category ON programs(category);
CREATE INDEX idx_programs_county ON programs USING GIN(serves_county);
CREATE INDEX idx_programs_active ON programs(is_active);
CREATE INDEX idx_programs_emergency ON programs(is_emergency);
CREATE INDEX idx_eligibility_program ON eligibility_criteria(program_id);
CREATE INDEX idx_income_limits_program ON income_limits(program_id);
CREATE INDEX idx_providers_county ON providers(address_county);
CREATE INDEX idx_providers_zip ON providers(address_zip);
CREATE INDEX idx_raw_pages_domain ON raw_pages(domain);
```

### Views

```sql
-- Programs with complete data
CREATE VIEW programs_complete AS
SELECT * FROM programs
WHERE confidence_score >= 0.7
  AND eligibility_summary IS NOT NULL
  AND is_active = true;

-- Programs by category with counts
CREATE VIEW programs_by_category AS
SELECT
    category,
    COUNT(*) as total_programs,
    COUNT(*) FILTER (WHERE is_emergency) as emergency_programs,
    AVG(confidence_score) as avg_confidence
FROM programs
WHERE is_active = true
GROUP BY category;
```

---

## Feature Specifications

### 1. Program Finder (Hybrid Wizard)

**Purpose:** Guide users through a friendly questionnaire to find programs they may qualify for.

**UX Design Principles:**
- Conversational tone with helper persona
- Large, touch-friendly selection cards
- Progress indicator showing steps
- Contextual help explaining why questions are asked
- Skip options for sensitive questions
- Mobile-first responsive design
- Bilingual throughout

**Questionnaire Flow:**

```
STEP 1: HOUSEHOLD COMPOSITION
─────────────────────────────
💬 "Let's find help for you. First, tell me about your household..."

Who lives with you?
┌─────────┐ ┌─────────┐ ┌───────────┐ ┌───────────┐
│ 👤      │ │ 👥      │ │ 👨‍👩‍👧      │ │ 👨‍👩‍👧‍👦      │
│ Just me │ │ Me +    │ │ Me +      │ │ Family    │
│         │ │ partner │ │ child(ren)│ │ (4+)      │
└─────────┘ └─────────┘ └───────────┘ └───────────┘

[If children selected]
How many children under 18? [1] [2] [3] [4+]

Are any household members:
☐ 60 years or older
☐ Pregnant
☐ Have a disability
☐ A veteran or active military

ℹ️ "Household size helps us find programs with the right requirements"

STEP 2: INCOME
──────────────
💬 "Now let's talk about income. This helps match you with programs
    you're likely to qualify for..."

What's your approximate monthly household income?
(Include wages, benefits, child support - before taxes)

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Under    │ │ $1,500 - │ │ $3,000 - │ │ Over     │
│ $1,500   │ │ $3,000   │ │ $5,000   │ │ $5,000   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
            [Prefer not to say]

Current employment status:
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ Employed   │ │ Unemployed │ │ Part-time  │ │ Unable to  │
│ full-time  │ │            │ │ or gig     │ │ work       │
└────────────┘ └────────────┘ └────────────┘ └────────────┘

ℹ️ "Income limits vary by program - we'll show you all possible matches"

STEP 3: WHAT HELP DO YOU NEED?
──────────────────────────────
💬 "What kind of help are you looking for? Select all that apply..."

┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 🍎      │ │ 🏠      │ │ 💊      │ │ 💰      │
│ Food    │ │ Housing │ │ Health- │ │ Money / │
│         │ │ & Rent  │ │ care    │ │ Bills   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 👶      │ │ 💼      │ │ ⚖️      │ │ 🚗      │
│ Child-  │ │ Job     │ │ Legal   │ │ Trans-  │
│ care    │ │ Help    │ │ Help    │ │ port    │
└─────────┘ └─────────┘ └─────────┘ └─────────┘

STEP 4: CURRENT SITUATION
─────────────────────────
💬 "Are you facing any urgent situations right now?"

┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ ⚠️ Eviction    │ │ ⚠️ Utilities   │ │ ⚠️ No food     │
│ notice         │ │ shutoff        │ │ today          │
└────────────────┘ └────────────────┘ └────────────────┘
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ ⚠️ Homeless/   │ │ ⚠️ Domestic    │ │ ⚠️ Medical     │
│ need shelter   │ │ violence       │ │ emergency      │
└────────────────┘ └────────────────┘ └────────────────┘
         [None of these - I'm planning ahead]

🆘 "If you're in immediate danger, call 911"
📞 "For any crisis, call 211 (24/7)"

STEP 5: RESULTS
───────────────
💬 "Great news! Based on what you told me, here are programs
    you may qualify for..."

Found 23 programs for you

[Sort by: Best Match ▼] [Filter by category ▼]

┌─────────────────────────────────────────────────────────┐
│ ⭐ 95% MATCH                                    🍎 Food │
│ SNAP (Food Stamps)                                      │
│ Monthly food assistance: $234-$835/month estimated      │
│ ✅ Income likely qualifies                              │
│ ✅ Household size qualifies                             │
│ ⚡ Can apply online today                               │
│                                [View Details →]         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ⭐ 90% MATCH                              🏠 Housing    │
│ Emergency Rental Assistance                             │
│ Up to $3,000 for rent/utilities                        │
│ ✅ Income likely qualifies                              │
│ ✅ Eviction situation qualifies                         │
│ ⏰ Apply by: Dec 31, 2024                              │
│                                [View Details →]         │
└─────────────────────────────────────────────────────────┘
```

**Matching Algorithm:**

```python
def calculate_match_score(user_profile: dict, program: Program) -> float:
    """
    Calculate how well a user matches a program's eligibility criteria.
    Returns a score from 0.0 to 1.0
    """
    score = 0.0
    weights = {
        'income': 0.30,
        'household': 0.20,
        'category_match': 0.25,
        'situation': 0.15,
        'geographic': 0.10
    }

    # Income check
    if program.income_limits:
        user_monthly = user_profile.get('monthly_income')
        household_size = user_profile.get('household_size', 1)
        limit = get_income_limit(program.id, household_size)
        if user_monthly and limit:
            if user_monthly <= limit:
                score += weights['income']
            elif user_monthly <= limit * 1.1:  # Within 10%
                score += weights['income'] * 0.5
    else:
        score += weights['income']  # No income requirement

    # Household composition
    household_match = check_household_criteria(user_profile, program)
    score += weights['household'] * household_match

    # Category/need match
    user_needs = user_profile.get('needs', [])
    if program.category in user_needs:
        score += weights['category_match']

    # Situational criteria (emergency, veteran, disability, etc.)
    situation_match = check_situational_criteria(user_profile, program)
    score += weights['situation'] * situation_match

    # Geographic match
    if user_profile.get('county') in program.serves_county:
        score += weights['geographic']

    return min(score, 1.0)
```

### 2. Program Listings & Search

**Features:**
- Browse all programs with category filters
- Full-text search (bilingual)
- Filter by: category, eligibility type, application method
- Sort by: name, relevance, deadline
- Emergency programs highlighted

**Categories:**
- 🍎 Food Assistance
- 🏠 Housing & Utilities
- 💊 Healthcare & Mental Health
- 💰 Financial Assistance
- 👶 Childcare & Family
- 💼 Employment & Training
- ⚖️ Legal Aid
- 👴 Senior Services
- ♿ Disability Services
- 🎖️ Veteran Services
- 📚 Education
- 🚗 Transportation

### 3. Program Detail Pages

**Content Structure:**

```
┌─────────────────────────────────────────────────────────────┐
│ 🍎 Food Assistance                                          │
│ ═══════════════════════════════════════════════════════════│
│ SNAP (Supplemental Nutrition Assistance Program)            │
│                                                             │
│ 📋 OVERVIEW                                                 │
│ ─────────────────────────────────────────────────────────── │
│ SNAP provides monthly benefits to buy food for you and      │
│ your family. Benefits are loaded onto an EBT card that      │
│ works like a debit card at grocery stores.                  │
│                                                             │
│ 💰 WHAT YOU COULD RECEIVE                                   │
│ ─────────────────────────────────────────────────────────── │
│ Maximum monthly benefit by household size:                  │
│ • 1 person: $234/month                                      │
│ • 2 people: $430/month                                      │
│ • 3 people: $616/month                                      │
│ • 4 people: $782/month                                      │
│ [Calculate Your Estimate →]                                 │
│                                                             │
│ ✅ ELIGIBILITY                                              │
│ ─────────────────────────────────────────────────────────── │
│ Income Limits (Gross Monthly):                              │
│ • 1 person: $1,580/month (130% FPL)                        │
│ • 2 people: $2,137/month                                    │
│ • 3 people: $2,694/month                                    │
│ • 4 people: $3,250/month                                    │
│                                                             │
│ You may qualify if you:                                     │
│ ✓ Meet income guidelines above                              │
│ ✓ Are a U.S. citizen or qualified non-citizen              │
│ ✓ Have a Social Security number                            │
│ ✓ Meet work requirements (or are exempt)                   │
│                                                             │
│ 📄 DOCUMENTS YOU'LL NEED                                    │
│ ─────────────────────────────────────────────────────────── │
│ ☐ Photo ID for all adults                                   │
│ ☐ Proof of income (pay stubs, benefit letters)             │
│ ☐ Proof of address (utility bill, lease)                   │
│ ☐ Social Security cards for all household members          │
│ ☐ Bank statements (last 30 days)                           │
│ [📋 Get Full Checklist]                                     │
│                                                             │
│ 📝 HOW TO APPLY                                             │
│ ─────────────────────────────────────────────────────────── │
│ Option 1: Online (Fastest)                                  │
│ Apply at MyACCESS Florida: myflorida.com/accessflorida     │
│ [Apply Online →]                                            │
│                                                             │
│ Option 2: In Person                                         │
│ Visit your local DCF office:                               │
│ 📍 DCF Brevard County - Rockledge                          │
│    2535 N Courtenay Pkwy, Merritt Island, FL 32953         │
│    ☎️ (321) 504-2000                                        │
│    🕐 Mon-Fri 8am-5pm                                       │
│ [Get Directions →]                                          │
│                                                             │
│ Option 3: By Phone                                          │
│ Call DCF Customer Call Center: 1-866-762-2237              │
│                                                             │
│ ⏰ Processing Time: 7-30 days                               │
│                                                             │
│ 📞 NEED HELP?                                               │
│ ─────────────────────────────────────────────────────────── │
│ • Call 211 for assistance with your application            │
│ • DCF Customer Service: 1-866-762-2237                     │
│ • Visit a local food bank while you wait                   │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│ Last verified: November 2024 | Source: Florida DCF         │
└─────────────────────────────────────────────────────────────┘
```

### 4. Benefit Calculator

**Purpose:** Estimate potential benefits based on household information.

**Calculators to Include:**
- **SNAP Estimator:** Based on FPL tables and household deductions
- **Medicaid Eligibility:** Based on Modified Adjusted Gross Income
- **TANF Estimator:** Florida-specific benefit amounts
- **LIHEAP:** Utility assistance estimates
- **Section 8 Income Check:** HUD income limits by area

**SNAP Calculator Logic:**

```python
def estimate_snap_benefit(household_size: int, gross_monthly_income: float,
                          rent: float = 0, utilities: float = 0) -> dict:
    """
    Estimate SNAP benefits using simplified calculation.
    Note: Actual benefits may vary - this is an estimate only.
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
    if gross_monthly_income > income_limits[size]:
        return {
            'eligible': False,
            'reason': 'Income exceeds 130% of Federal Poverty Level',
            'income_limit': income_limits[size]
        }

    # Calculate net income
    net_income = gross_monthly_income - standard_deduction[size]

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
        'eligible': True,
        'estimated_monthly': round(benefit),
        'maximum_possible': max_benefits[size],
        'disclaimer': 'This is an estimate. Actual benefits determined by DCF.'
    }
```

### 5. Document Checklist Generator

**Purpose:** Generate a personalized list of documents needed based on matched programs.

**Features:**
- Consolidates documents across multiple programs
- Groups by document type (ID, income, residence, etc.)
- Explains how to obtain each document
- Notes acceptable alternatives
- Printable/saveable format

**Output Example:**

```
📋 YOUR DOCUMENT CHECKLIST
══════════════════════════
Based on: SNAP, Medicaid, Emergency Rental Assistance

IDENTIFICATION (bring for all adults)
☐ Driver's license or state ID
  └ Alternative: Passport, military ID, or birth certificate + photo

PROOF OF INCOME (last 30 days)
☐ Pay stubs from all jobs
☐ Unemployment benefit letters
☐ Social Security award letters
☐ Child support documentation
  └ If self-employed: Business records, tax returns

PROOF OF RESIDENCE
☐ Current utility bill (electric, water, gas)
  └ Alternative: Lease agreement, mortgage statement
☐ Lease or rental agreement (for rental assistance)

PROOF OF IDENTITY
☐ Social Security cards for all household members
  └ If lost: Request at ssa.gov or local SS office

PROOF OF EXPENSES (for SNAP)
☐ Rent/mortgage payment amount
☐ Utility bills
☐ Child care costs (if applicable)

ADDITIONAL FOR RENTAL ASSISTANCE
☐ Eviction notice or past-due rent notice
☐ Landlord contact information
☐ Proof of COVID-19 hardship (job loss letter, etc.)

💡 TIPS
• Make copies of everything before submitting
• If you don't have a document, apply anyway - caseworkers can help
• Keep originals safe; only submit copies
```

### 6. Service Locator

**Purpose:** Find nearby service providers by type and location.

**Features:**
- Filter by service type (food bank, shelter, DCF office, etc.)
- Show on map or list view
- Display hours, contact info, services offered
- Distance from user (if location shared)
- Transit/driving directions link

### 7. Crisis Resources Banner

**Always Visible:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🆘 In crisis? Call 211 (24/7) • Suicide: 988 • Emergency: 911│
└─────────────────────────────────────────────────────────────┘
```

**Emergency Detection:**
If user selects crisis situations (homeless, domestic violence, no food), show immediate resources prominently before other results.

---

## Data Sources to Scrape

### Primary Sources

| Source | URL | Data Type | Priority |
|--------|-----|-----------|----------|
| **211 Brevard** | 211brevard.org | Local programs, providers | Critical |
| **Florida DCF** | myflorida.com/accessflorida | SNAP, Medicaid, TANF | Critical |
| **Benefits.gov** | benefits.gov | Federal program database | High |
| **HUD** | hud.gov | Housing programs, income limits | High |
| **USDA SNAP** | fns.usda.gov/snap | SNAP details, FPL tables | High |
| **SSA** | ssa.gov | SSI, SSDI information | High |
| **Florida Housing** | floridahousing.org | State housing programs | Medium |
| **Feeding America** | feedingamerica.org | Food bank locator | Medium |
| **Florida Legal Aid** | floridalawhelp.org | Legal resources | Medium |

### Local Brevard Sources

| Source | Data Type |
|--------|-----------|
| Brevard County Government | Local assistance programs |
| Space Coast Health Foundation | 211 provider data |
| Salvation Army Brevard | Emergency services |
| Community of Hope | Homeless services |
| Daily Bread | Food assistance |
| Brevard Schools Foundation | Family resources |
| Local churches/nonprofits | Emergency assistance |

### API Integrations (If Available)

- **211 API** (requires partnership)
- **Benefits.gov API**
- **HUD Exchange API** (income limits)
- **Google Maps/Places API** (provider locations)

---

## Internationalization (i18n)

### Implementation Approach

```python
# translations.py
def get_text(key: str, lang: str = 'en') -> str:
    """Get translated text by key and language."""
    translation = db.query(Translation).filter_by(
        translation_key=key
    ).first()

    if lang == 'es' and translation.text_es:
        return translation.text_es
    return translation.text_en

# Usage in templates
{{ t('finder.welcome_message') }}
{{ t('program.eligibility_title') }}
```

### Language Toggle

```html
<!-- Always visible in header -->
<div class="language-toggle">
    <a href="?lang=en" class="{{ 'active' if lang=='en' }}">English</a>
    <a href="?lang=es" class="{{ 'active' if lang=='es' }}">Español</a>
</div>
```

### Cookie-Based Preference

```python
@app.before_request
def set_language():
    # Check URL param first, then cookie, then default
    lang = request.args.get('lang') or request.cookies.get('lang') or 'en'
    g.lang = lang if lang in ['en', 'es'] else 'en'

@app.after_request
def save_language(response):
    if 'lang' in request.args:
        response.set_cookie('lang', request.args['lang'], max_age=365*24*60*60)
    return response
```

---

## Privacy & Data Handling

### Principles

1. **No Personal Data Storage:** User responses are session-only, stored in browser cookies
2. **No Accounts:** No user registration or login required
3. **No Tracking:** No analytics that identify individuals
4. **Clear Disclaimers:** "This is an informational tool, not an application"
5. **Transparent:** Explain how matching works

### Cookie Usage

```python
# Store user selections in encrypted cookie
COOKIE_CONFIG = {
    'name': 'community_assist_session',
    'max_age': 7 * 24 * 60 * 60,  # 7 days
    'httponly': True,
    'secure': True,  # HTTPS only
    'samesite': 'Lax'
}

# Cookie contents (encrypted)
session_data = {
    'lang': 'en',
    'household_size': 3,
    'income_range': '1500-3000',
    'needs': ['food', 'housing'],
    'matched_programs': [1, 5, 12, 23],  # Program IDs
    'last_visit': '2024-11-25'
}
```

### Disclaimer Text

```
IMPORTANT: This tool provides information only. It does not submit
applications or guarantee eligibility for any program. Actual
eligibility is determined by each program's administering agency.
Your information is not stored on our servers and is only kept
temporarily in your browser to improve your experience.
```

---

## Mobile-First Design

### Responsive Breakpoints

```css
/* Mobile first */
.container { padding: 1rem; }

/* Tablet */
@media (min-width: 768px) {
    .container { padding: 2rem; max-width: 720px; }
}

/* Desktop */
@media (min-width: 1024px) {
    .container { max-width: 960px; }
}
```

### Touch-Friendly Elements

- Minimum touch target: 48x48px
- Card-based selection (not small checkboxes)
- Large buttons with clear labels
- Adequate spacing between interactive elements
- No hover-dependent interactions

### Performance

- Target: <3s load time on 3G
- Lazy load non-critical content
- Compress images
- Minimal JavaScript
- Server-side rendering

---

## Project Structure

```
community-assist/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Pipeline orchestrator
│   ├── config.py               # Configuration management
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py     # Abstract base class
│   │   ├── discovery.py        # URL discovery and crawling
│   │   ├── extractor.py        # Content extraction
│   │   ├── pdf_processor.py    # PDF handling
│   │   ├── benefits_gov.py     # Benefits.gov scraper
│   │   ├── florida_dcf.py      # Florida DCF scraper
│   │   ├── hud_scraper.py      # HUD housing data
│   │   └── local_211.py        # 211 Brevard scraper
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── eligibility.py      # Eligibility criteria parser
│   │   ├── income_limits.py    # Income limit extraction
│   │   ├── fpl_calculator.py   # FPL calculations
│   │   └── benefit_calculator.py # Benefit estimation
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py       # DB connection management
│   │   ├── models.py           # SQLAlchemy models
│   │   └── init_db.sql         # Schema initialization
│   └── analyzers/
│       ├── __init__.py
│       └── data_quality.py     # Data completeness analysis
├── webapp/
│   ├── __init__.py
│   ├── app.py                  # Flask application
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py             # Home, about, etc.
│   │   ├── finder.py           # Program finder wizard
│   │   ├── programs.py         # Program listings/details
│   │   ├── calculator.py       # Benefit calculators
│   │   ├── locator.py          # Service locator
│   │   └── api.py              # JSON API endpoints
│   ├── templates/
│   │   ├── base.html           # Base template
│   │   ├── components/
│   │   │   ├── header.html
│   │   │   ├── footer.html
│   │   │   ├── crisis_banner.html
│   │   │   ├── program_card.html
│   │   │   └── language_toggle.html
│   │   ├── finder/
│   │   │   ├── index.html
│   │   │   ├── step_household.html
│   │   │   ├── step_income.html
│   │   │   ├── step_needs.html
│   │   │   ├── step_situation.html
│   │   │   └── results.html
│   │   ├── programs/
│   │   │   ├── index.html
│   │   │   ├── detail.html
│   │   │   └── search.html
│   │   ├── calculator/
│   │   │   ├── index.html
│   │   │   └── results.html
│   │   └── locator/
│   │       └── index.html
│   └── static/
│       ├── css/
│       │   └── styles.css      # Tailwind compiled
│       ├── js/
│       │   └── app.js          # Minimal JS
│       └── images/
├── translations/
│   ├── en.json                 # English strings
│   └── es.json                 # Spanish strings
├── data/
│   ├── fpl_tables/             # Federal Poverty Level data
│   ├── hud_income_limits/      # HUD income limits by area
│   └── pdfs/                   # Downloaded documents
├── tests/
│   ├── test_scrapers.py
│   ├── test_calculators.py
│   ├── test_matching.py
│   └── test_webapp.py
├── scripts/
│   ├── import_fpl_data.py
│   ├── import_hud_limits.py
│   ├── seed_translations.py
│   └── verify_data.py
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-web.txt
├── Dockerfile
├── Dockerfile.web
├── docker-compose.yml
├── .do/
│   └── app.yaml                # Digital Ocean config
├── README.md
├── QUICKSTART.md
└── PROJECT_SPECIFICATION.md
```

---

## Development Phases

### Phase 1: Foundation (MVP)
- [ ] Database schema implementation
- [ ] Basic Flask app structure
- [ ] Bilingual support infrastructure
- [ ] FPL tables and income limit data
- [ ] Program Finder wizard (basic)
- [ ] 10-20 manually entered core programs
- [ ] Mobile-responsive design

### Phase 2: Data Collection
- [ ] Florida DCF scraper (SNAP, Medicaid, TANF)
- [ ] Benefits.gov scraper
- [ ] HUD income limits integration
- [ ] Local 211 data (manual or scraped)
- [ ] PDF processing for program guides
- [ ] 50+ programs with structured data

### Phase 3: Enhanced Features
- [ ] SNAP benefit calculator
- [ ] Medicaid eligibility checker
- [ ] Document checklist generator
- [ ] Service locator with map
- [ ] Program detail pages (full)
- [ ] Search functionality

### Phase 4: Polish & Scale
- [ ] Performance optimization
- [ ] Accessibility audit (WCAG 2.1)
- [ ] Spanish translation review
- [ ] Data quality improvements
- [ ] Analytics (privacy-respecting)
- [ ] Feedback mechanism

### Phase 5: Expansion
- [ ] Additional Florida counties
- [ ] More programs and providers
- [ ] Partnership with 211
- [ ] Chatbot enhancement (optional)

---

## Success Metrics

### Data Quality
- 100+ programs with structured eligibility criteria
- 80%+ programs with income limits captured
- 70%+ programs with benefit amounts
- 90%+ programs with application instructions
- 50+ local service providers

### User Experience
- <3 second page load (3G)
- <3 minutes to complete finder
- Mobile Lighthouse score >90
- Accessibility score >90

### Coverage
- All major federal benefit programs
- All Florida-specific programs
- Key local Brevard resources
- Emergency/crisis resources

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/community_assist
POSTGRES_USER=community_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=community_assist

# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DEFAULT_LANGUAGE=en

# Scraping
SCRAPE_DELAY_SECONDS=2.5
MAX_CONCURRENT_REQUESTS=3
USER_AGENT=CommunityAssist/1.0 (contact@example.com)

# External APIs (if needed)
GOOGLE_MAPS_API_KEY=your-key
BENEFITS_GOV_API_KEY=your-key

# Feature Flags
ENABLE_CALCULATOR=true
ENABLE_LOCATOR=true
ENABLE_PDF_GENERATION=false

# Target Geography
TARGET_STATE=FL
TARGET_COUNTY=Brevard
```

---

## Getting Started (Development)

```bash
# Clone repository
git clone https://github.com/thingvallatech/community-assist.git
cd community-assist

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start database
docker-compose up -d postgres

# Initialize database
psql $DATABASE_URL < src/database/init_db.sql

# Seed initial data
python scripts/import_fpl_data.py
python scripts/seed_translations.py

# Run development server
flask --app webapp.app run --debug

# Run scrapers
python -m src.main --tier=1  # APIs first
python -m src.main --tier=2  # Web scraping
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow existing code style
4. Add tests for new features
5. Ensure Spanish translations are included
6. Submit a pull request

---

## License

[To be determined - recommend MIT or Apache 2.0 for open source]

---

## Contact

- GitHub Issues: [Project Issues](https://github.com/thingvallatech/community-assist/issues)
- 211 Brevard Partnership: [Contact info TBD]

---

*This specification is a living document and will be updated as the project evolves.*
