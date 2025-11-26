"""
Benefits.gov Scraper
Scrapes federal benefit program information from benefits.gov
"""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from loguru import logger

from .base_scraper import BaseScraper


class BenefitsGovScraper(BaseScraper):
    """Scraper for benefits.gov federal programs."""

    @property
    def source_name(self) -> str:
        return "Benefits.gov"

    @property
    def base_url(self) -> str:
        return "https://www.benefits.gov"

    # Categories to scrape
    CATEGORIES = [
        "food-nutrition",
        "healthcare-medical",
        "housing-shelter",
        "income-expenses",
        "family-children",
        "employment",
        "education-training",
        "disability",
    ]

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape programs from benefits.gov."""
        programs = []

        # Use curated list of federal programs relevant to Florida
        programs.extend(self._get_curated_federal_programs())

        # Optionally, discover more programs from category pages
        # This is slower but more comprehensive
        # for category in self.CATEGORIES:
        #     category_programs = await self._scrape_category(category)
        #     programs.extend(category_programs)

        return programs

    async def _scrape_category(self, category: str) -> List[Dict[str, Any]]:
        """Scrape all programs in a category."""
        programs = []
        url = f"{self.base_url}/categories/{category}"

        html = await self.fetch_page(url)
        if not html:
            return programs

        soup = self.parse_html(html)

        # Find program links
        program_links = soup.select("a[href*='/benefits/']")

        for link in program_links[:10]:  # Limit per category
            program_url = self.make_absolute_url(link.get("href"))
            program_html = await self.fetch_page(program_url)

            if program_html:
                program_soup = self.parse_html(program_html)
                program = self.parse_program(program_soup, program_url)
                if program:
                    programs.append(program)
                    logger.info(f"Extracted: {program.get('program_name')}")

        return programs

    def parse_program(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse a benefits.gov program page."""
        try:
            title = self.extract_text(soup, "h1")
            if not title:
                return None

            # Get description
            description = ""
            desc_section = soup.select_one(".program-description, .description, #program-details")
            if desc_section:
                description = desc_section.get_text(strip=True)

            # Get eligibility
            eligibility = ""
            elig_section = soup.select_one("#eligibility, .eligibility")
            if elig_section:
                eligibility = elig_section.get_text(strip=True)

            # Get how to apply
            how_to_apply = ""
            apply_section = soup.select_one("#how-to-apply, .how-to-apply")
            if apply_section:
                how_to_apply = apply_section.get_text(strip=True)

            return {
                "program_name": title,
                "category": self._determine_category(title, description),
                "description": description[:2000] if description else None,
                "eligibility_summary": eligibility[:2000] if eligibility else None,
                "how_to_apply": how_to_apply[:2000] if how_to_apply else None,
                "source_url": url,
                "source_name": self.source_name,
                "serves_state": ["FL"],  # Filter for Florida
            }

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

    def _determine_category(self, title: str, description: str) -> str:
        """Determine category from content."""
        text = (title + " " + description).lower()

        if any(word in text for word in ["snap", "food", "nutrition", "wic"]):
            return "food"
        if any(word in text for word in ["medicaid", "medicare", "health", "medical"]):
            return "healthcare"
        if any(word in text for word in ["housing", "hud", "section 8", "rent", "shelter"]):
            return "housing"
        if any(word in text for word in ["ssi", "ssdi", "disability"]):
            return "disability"
        if any(word in text for word in ["veteran", "va "]):
            return "veteran"
        if any(word in text for word in ["child", "family", "tanf"]):
            return "childcare"
        if any(word in text for word in ["job", "employment", "work", "unemployment"]):
            return "employment"
        if any(word in text for word in ["education", "pell", "student"]):
            return "education"

        return "financial"

    def _get_curated_federal_programs(self) -> List[Dict[str, Any]]:
        """Return curated federal programs available in Florida."""
        return [
            {
                "program_code": "SSI",
                "program_name": "Supplemental Security Income (SSI)",
                "program_name_es": "Ingreso de Seguridad Suplementario (SSI)",
                "category": "disability",
                "description": "SSI provides monthly cash payments to people with limited income and resources who are 65 or older, blind, or disabled. SSI is designed to meet basic needs for food, clothing, and shelter.",
                "description_es": "SSI proporciona pagos mensuales en efectivo a personas con ingresos y recursos limitados que tienen 65 años o más, son ciegos o están discapacitados.",
                "benefits_summary": "Maximum federal SSI payment (2024): $943/month for individuals, $1,415/month for couples. Florida does not provide a state supplement. Actual payment depends on income and living situation.",
                "benefit_amount_min": 0,
                "benefit_amount_max": 943,
                "benefit_frequency": "monthly",
                "eligibility_summary": "Must be 65 or older, blind, or disabled. Must have limited income (generally under $1,971/month for individuals). Must have limited resources (under $2,000 for individuals, $3,000 for couples). Must be a U.S. citizen or qualifying non-citizen.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "serves_seniors": True,
                    "serves_disabled": True,
                    "citizenship_required": True,
                    "asset_limit": True
                },
                "how_to_apply": "Apply at your local Social Security office, call 1-800-772-1213 (TTY 1-800-325-0778), or start your application online at ssa.gov.",
                "application_url": "https://www.ssa.gov/benefits/ssi/",
                "processing_time": "3-6 months (can take longer for disability determination)",
                "source_url": "https://www.ssa.gov/ssi/",
                "source_name": "Social Security Administration",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-800-772-1213",
                "contact_website": "https://www.ssa.gov/ssi/"
            },
            {
                "program_code": "SSDI",
                "program_name": "Social Security Disability Insurance (SSDI)",
                "program_name_es": "Seguro de Incapacidad del Seguro Social (SSDI)",
                "category": "disability",
                "description": "SSDI pays benefits to you and certain family members if you worked long enough and paid Social Security taxes, and now have a medical condition that prevents you from working for at least 12 months or is expected to result in death.",
                "description_es": "SSDI paga beneficios a usted y ciertos miembros de su familia si trabajó suficiente tiempo y pagó impuestos del Seguro Social, y ahora tiene una condición médica que le impide trabajar por al menos 12 meses.",
                "benefits_summary": "Monthly payment based on your lifetime earnings. Average SSDI payment (2024): approximately $1,537/month. Maximum payment: $3,822/month. You may also receive Medicare after 24 months of SSDI eligibility.",
                "benefit_frequency": "monthly",
                "eligibility_summary": "Must have worked and paid into Social Security (earned enough work credits). Must have a qualifying disability that prevents substantial work. Disability must be expected to last at least 12 months or result in death.",
                "eligibility_parsed": {
                    "has_income_limit": False,
                    "serves_disabled": True,
                    "work_history_required": True
                },
                "how_to_apply": "Apply online at ssa.gov, call 1-800-772-1213, or visit your local Social Security office. Have medical records and work history ready.",
                "application_url": "https://www.ssa.gov/applyfordisability/",
                "processing_time": "3-5 months (may be longer, appeals can take 1-2 years)",
                "source_url": "https://www.ssa.gov/benefits/disability/",
                "source_name": "Social Security Administration",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-800-772-1213",
                "contact_website": "https://www.ssa.gov/benefits/disability/"
            },
            {
                "program_code": "SECTION8-HCV",
                "program_name": "Section 8 Housing Choice Voucher",
                "program_name_es": "Vales de Elección de Vivienda Sección 8",
                "category": "housing",
                "description": "The Housing Choice Voucher program helps very low-income families, the elderly, and the disabled afford decent, safe, and sanitary housing. You can use the voucher to rent a house, apartment, or townhome in the private market.",
                "description_es": "El programa de Vales de Elección de Vivienda ayuda a familias de muy bajos ingresos, ancianos y discapacitados a pagar una vivienda decente, segura y sanitaria.",
                "benefits_summary": "Voucher pays the difference between 30% of your income and the fair market rent. You typically pay about 30% of your monthly income toward rent. The voucher covers the rest, up to a payment standard set by your housing authority.",
                "benefit_frequency": "monthly",
                "eligibility_summary": "Income must be below 50% of area median income (very low income). Priority often given to extremely low income (below 30% AMI). Must pass background check. Must be a U.S. citizen or eligible immigrant.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "serves_families": True,
                    "serves_seniors": True,
                    "serves_disabled": True,
                    "citizenship_required": True,
                    "background_check": True
                },
                "how_to_apply": "Apply through your local Public Housing Authority (PHA). In Brevard County, contact Brevard County Housing Authority at (321) 631-5620. Note: Wait lists are often long (years) and may be closed.",
                "processing_time": "Wait list varies by location (often 2-5+ years)",
                "source_url": "https://www.hud.gov/topics/housing_choice_voucher_program_section_8",
                "source_name": "HUD",
                "confidence_score": 0.90,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "(321) 631-5620",
                "contact_website": "https://www.hud.gov/topics/housing_choice_voucher_program_section_8"
            },
            {
                "program_code": "MEDICARE",
                "program_name": "Medicare",
                "program_name_es": "Medicare",
                "category": "healthcare",
                "description": "Medicare is federal health insurance for people 65 and older, and for some younger people with disabilities or specific conditions like End-Stage Renal Disease. It has four parts: Part A (hospital), Part B (medical), Part C (Medicare Advantage), and Part D (prescription drugs).",
                "description_es": "Medicare es un seguro de salud federal para personas de 65 años o más, y para algunas personas más jóvenes con discapacidades o condiciones específicas.",
                "benefits_summary": "Part A: Hospital stays, skilled nursing, hospice (usually premium-free if you paid Medicare taxes). Part B: Doctor visits, outpatient care, preventive services (standard premium $174.70/month in 2024). Part D: Prescription drug coverage (premiums vary).",
                "benefit_frequency": "ongoing",
                "eligibility_summary": "Age 65 or older, or under 65 with a qualifying disability (after 24 months of SSDI), or any age with End-Stage Renal Disease or ALS. Must be a U.S. citizen or permanent resident for 5+ years.",
                "eligibility_parsed": {
                    "has_income_limit": False,
                    "serves_seniors": True,
                    "serves_disabled": True,
                    "citizenship_required": True
                },
                "how_to_apply": "Enroll online at ssa.gov/medicare, call 1-800-772-1213, or visit your local Social Security office. Initial enrollment period is 3 months before to 3 months after your 65th birthday.",
                "application_url": "https://www.ssa.gov/medicare/",
                "source_url": "https://www.medicare.gov/",
                "source_name": "CMS / Medicare",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-800-MEDICARE (1-800-633-4227)",
                "contact_website": "https://www.medicare.gov/"
            },
            {
                "program_code": "PELL-GRANT",
                "program_name": "Federal Pell Grant",
                "program_name_es": "Beca Federal Pell",
                "category": "education",
                "description": "Pell Grants provide need-based financial aid to low-income undergraduate students to help pay for college or career school. Unlike loans, Pell Grants do not have to be repaid (unless you withdraw from school).",
                "description_es": "Las Becas Pell proporcionan ayuda financiera basada en necesidad a estudiantes universitarios de bajos ingresos para ayudar a pagar la universidad o escuela vocacional.",
                "benefits_summary": "Maximum award for 2024-25: $7,395 per year. Actual amount depends on your Expected Family Contribution (EFC), cost of attendance, enrollment status (full/part-time), and whether you attend for a full academic year.",
                "benefit_amount_max": 7395,
                "benefit_frequency": "annual",
                "eligibility_summary": "Must demonstrate financial need (determined by FAFSA). Must be an undergraduate student without a bachelor's degree. Must be enrolled in an eligible program. Must be a U.S. citizen or eligible noncitizen. Must have a high school diploma or GED.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "citizenship_required": True,
                    "education_requirement": True
                },
                "how_to_apply": "Complete the Free Application for Federal Student Aid (FAFSA) at studentaid.gov. The FAFSA opens October 1 each year for the following school year.",
                "application_url": "https://studentaid.gov/h/apply-for-aid/fafsa",
                "source_url": "https://studentaid.gov/understand-aid/types/grants/pell",
                "source_name": "Federal Student Aid",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-800-433-3243",
                "contact_website": "https://studentaid.gov/"
            },
            {
                "program_code": "UI-FL",
                "program_name": "Unemployment Insurance",
                "program_name_es": "Seguro de Desempleo",
                "category": "employment",
                "description": "Unemployment Insurance provides temporary financial assistance to workers who lose their jobs through no fault of their own. Benefits help you meet basic needs while you look for new employment.",
                "description_es": "El Seguro de Desempleo proporciona asistencia financiera temporal a trabajadores que pierden sus empleos sin culpa propia.",
                "benefits_summary": "Florida weekly benefit: $125-$275 per week for up to 12 weeks. One of the lowest in the nation. Benefits are based on your earnings during the base period (typically the first four of the last five completed calendar quarters).",
                "benefit_amount_min": 125,
                "benefit_amount_max": 275,
                "benefit_frequency": "weekly",
                "eligibility_summary": "Must have lost your job through no fault of your own. Must have earned enough wages during the base period. Must be able and available to work. Must be actively seeking work. Must register with CareerSource Florida.",
                "eligibility_parsed": {
                    "work_history_required": True,
                    "active_job_search": True
                },
                "how_to_apply": "Apply online at FloridaJobs.org/Reemployment-Assistance-Service-Center or call 1-800-204-2418. Apply within 14 days of losing your job.",
                "application_url": "https://www.floridajobs.org/Reemployment-Assistance-Service-Center/reemployment-assistance/claimants",
                "processing_time": "2-4 weeks",
                "source_url": "https://www.floridajobs.org/",
                "source_name": "Florida DEO",
                "confidence_score": 0.90,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-800-204-2418",
                "contact_website": "https://www.floridajobs.org/"
            },
            {
                "program_code": "FREE-LUNCH",
                "program_name": "National School Lunch Program (Free/Reduced Lunch)",
                "program_name_es": "Programa Nacional de Almuerzo Escolar (Almuerzo Gratis/Reducido)",
                "category": "food",
                "description": "The National School Lunch Program provides nutritionally balanced, low-cost or free lunches to children at school. Children from families with incomes at or below 130% of poverty get free meals; those between 130-185% get reduced-price meals.",
                "description_es": "El Programa Nacional de Almuerzo Escolar proporciona almuerzos nutritivos y balanceados, de bajo costo o gratis, a niños en la escuela.",
                "benefits_summary": "Free meals for children in households at or below 130% FPL. Reduced-price meals (40 cents for lunch, 30 cents for breakfast) for households between 130-185% FPL. Many Florida schools now offer free meals to all students through Community Eligibility.",
                "benefit_frequency": "daily",
                "eligibility_summary": "Child must attend a participating school. Household income at or below 185% FPL for reduced price, 130% FPL for free. Children in households receiving SNAP, TANF, or FDPIR automatically qualify for free meals.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "fpl_percentage": 185,
                    "serves_children": True,
                    "serves_families": True
                },
                "how_to_apply": "Complete the free/reduced meal application through your child's school. Forms are typically sent home at the start of the school year. Many schools allow online applications.",
                "source_name": "USDA Food and Nutrition Service",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_website": "https://www.fns.usda.gov/nslp"
            }
        ]
