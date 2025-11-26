"""
Florida DCF Scraper
Scrapes information about SNAP, Medicaid, TANF, and other DCF programs
"""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from loguru import logger

from .base_scraper import BaseScraper


class FloridaDCFScraper(BaseScraper):
    """Scraper for Florida Department of Children and Families programs."""

    @property
    def source_name(self) -> str:
        return "Florida DCF"

    @property
    def base_url(self) -> str:
        return "https://www.myflfamilies.com"

    # Known program pages to scrape
    PROGRAM_URLS = [
        # SNAP (Food Assistance)
        "/service-programs/access/food-assistance-snap",
        # Medicaid
        "/service-programs/access/medicaid",
        # TANF (Cash Assistance)
        "/service-programs/access/temporary-cash-assistance",
        # General ACCESS info
        "/service-programs/access",
    ]

    # Additional useful pages
    INFO_URLS = [
        "/service-programs/access/how-to-apply",
        "/service-programs/access/program-eligibility",
    ]

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape all Florida DCF programs."""
        programs = []

        # Scrape known program pages
        for path in self.PROGRAM_URLS:
            url = self.make_absolute_url(path)
            html = await self.fetch_page(url)

            if html:
                soup = self.parse_html(html)
                program = self.parse_program(soup, url)
                if program:
                    programs.append(program)
                    logger.info(f"Extracted program: {program.get('program_name')}")

        # Add manually curated core programs with accurate data
        programs.extend(self._get_curated_programs())

        return programs

    def parse_program(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse a DCF program page."""
        try:
            # Get title
            title = self.extract_text(soup, "h1") or self.extract_text(soup, "title")
            if not title:
                return None

            # Get main content
            content = soup.select_one(".content, .main-content, article, main")
            if not content:
                content = soup.body

            description = ""
            if content:
                # Get first few paragraphs
                paragraphs = content.find_all("p", limit=5)
                description = " ".join(p.get_text(strip=True) for p in paragraphs)

            # Extract eligibility info
            eligibility_text = self._extract_section(soup, ["eligibility", "qualify", "requirements"])

            # Extract how to apply
            how_to_apply = self._extract_section(soup, ["apply", "application", "how to"])

            return {
                "program_name": self._clean_title(title),
                "category": self._determine_category(title, description),
                "description": description[:2000] if description else None,
                "eligibility_summary": eligibility_text[:2000] if eligibility_text else None,
                "how_to_apply": how_to_apply[:2000] if how_to_apply else None,
                "application_url": "https://www.myflorida.com/accessflorida/",
                "source_url": url,
                "source_name": self.source_name,
                "serves_state": ["FL"],
                "contact_phone": "1-866-762-2237",
                "contact_website": "https://www.myflorida.com/accessflorida/",
            }

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

    def _extract_section(self, soup: BeautifulSoup, keywords: List[str]) -> str:
        """Extract content from a section containing keywords."""
        text_parts = []

        # Look for headings containing keywords
        for heading in soup.find_all(["h2", "h3", "h4"]):
            heading_text = heading.get_text(strip=True).lower()
            if any(kw in heading_text for kw in keywords):
                # Get content until next heading
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in ["h2", "h3", "h4"]:
                    if sibling.name in ["p", "ul", "ol", "li"]:
                        text_parts.append(sibling.get_text(strip=True))
                    sibling = sibling.find_next_sibling()

        return " ".join(text_parts)

    def _clean_title(self, title: str) -> str:
        """Clean up title text."""
        # Remove site name suffixes
        title = re.sub(r"\s*[-|]\s*Florida.*$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*[-|]\s*DCF.*$", "", title, flags=re.IGNORECASE)
        return title.strip()

    def _determine_category(self, title: str, description: str) -> str:
        """Determine program category from title/description."""
        text = (title + " " + description).lower()

        if any(word in text for word in ["snap", "food", "nutrition"]):
            return "food"
        if any(word in text for word in ["medicaid", "health", "medical"]):
            return "healthcare"
        if any(word in text for word in ["tanf", "cash", "temporary assistance"]):
            return "financial"
        if any(word in text for word in ["child", "family"]):
            return "childcare"

        return "financial"

    def _get_curated_programs(self) -> List[Dict[str, Any]]:
        """
        Return manually curated program data with accurate information.
        This ensures we have high-quality core programs even if scraping fails.
        """
        return [
            {
                "program_code": "SNAP-FL",
                "program_name": "SNAP (Food Stamps)",
                "program_name_es": "SNAP (Cupones de Alimentos)",
                "category": "food",
                "description": "The Supplemental Nutrition Assistance Program (SNAP) provides monthly benefits to help low-income households buy the food they need for good health. Benefits are provided on an Electronic Benefits Transfer (EBT) card, which works like a debit card at authorized retail stores.",
                "description_es": "El Programa de Asistencia Nutricional Suplementaria (SNAP) proporciona beneficios mensuales para ayudar a los hogares de bajos ingresos a comprar los alimentos que necesitan para una buena salud. Los beneficios se proporcionan en una tarjeta de Transferencia Electrónica de Beneficios (EBT), que funciona como una tarjeta de débito en tiendas autorizadas.",
                "benefits_summary": "Monthly food benefits loaded onto an EBT card. Maximum monthly benefits: 1 person: $234, 2 people: $430, 3 people: $616, 4 people: $782, 5 people: $929, 6 people: $1,114, 7 people: $1,232, 8 people: $1,408. Additional household members: +$176 each.",
                "benefits_summary_es": "Beneficios mensuales de alimentos cargados en una tarjeta EBT. Beneficios mensuales máximos: 1 persona: $234, 2 personas: $430, 3 personas: $616, 4 personas: $782, 5 personas: $929, 6 personas: $1,114, 7 personas: $1,232, 8 personas: $1,408.",
                "benefit_amount_min": 23,
                "benefit_amount_max": 1408,
                "benefit_frequency": "monthly",
                "eligibility_summary": "Must meet income limits (gross monthly income at or below 130% of poverty level). Must be a U.S. citizen or qualified non-citizen. Must have a Social Security number. Must meet work requirements (unless exempt). Resources/assets are generally not counted in Florida.",
                "eligibility_summary_es": "Debe cumplir con los límites de ingresos (ingreso mensual bruto igual o inferior al 130% del nivel de pobreza). Debe ser ciudadano estadounidense o no ciudadano calificado. Debe tener un número de Seguro Social. Debe cumplir con los requisitos de trabajo (a menos que esté exento).",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "fpl_percentage": 130,
                    "serves_families": True,
                    "serves_seniors": True,
                    "serves_disabled": True,
                    "citizenship_required": True,
                    "work_requirements": True
                },
                "how_to_apply": "Apply online at ACCESS Florida (myflorida.com/accessflorida), call 1-866-762-2237, or visit your local DCF service center. You will need: Photo ID, Social Security cards, proof of income, proof of residence, and bank statements.",
                "how_to_apply_es": "Solicite en línea en ACCESS Florida (myflorida.com/accessflorida), llame al 1-866-762-2237, o visite su centro de servicio DCF local. Necesitará: Identificación con foto, tarjetas de Seguro Social, comprobante de ingresos, comprobante de residencia y estados de cuenta bancarios.",
                "application_url": "https://www.myflorida.com/accessflorida/",
                "processing_time": "30 days (7 days for emergency/expedited)",
                "source_url": "https://www.myflfamilies.com/service-programs/access/food-assistance-snap",
                "source_name": "Florida DCF",
                "confidence_score": 0.95,
                "is_active": True,
                "is_emergency": False,
                "serves_state": ["FL"],
                "contact_phone": "1-866-762-2237",
                "contact_website": "https://www.myflorida.com/accessflorida/"
            },
            {
                "program_code": "MEDICAID-FL",
                "program_name": "Florida Medicaid",
                "program_name_es": "Medicaid de Florida",
                "category": "healthcare",
                "description": "Florida Medicaid provides free or low-cost health coverage for eligible low-income adults, children, pregnant women, elderly adults, and people with disabilities. Medicaid covers doctor visits, hospital stays, prescriptions, mental health services, and more.",
                "description_es": "Medicaid de Florida proporciona cobertura de salud gratuita o de bajo costo para adultos de bajos ingresos, niños, mujeres embarazadas, adultos mayores y personas con discapacidades elegibles.",
                "benefits_summary": "Comprehensive health coverage including: doctor visits, hospital care, prescription drugs, lab tests, mental health services, substance abuse treatment, dental (limited for adults), vision (children), medical equipment, home health care, nursing home care.",
                "benefit_frequency": "ongoing",
                "eligibility_summary": "Income limits vary by category. Children: up to 210% FPL. Pregnant women: up to 191% FPL. Parents/caretakers: up to 31% FPL. Aged/disabled: up to 88% FPL. Must be a Florida resident. Must be a U.S. citizen or qualified immigrant.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "serves_families": True,
                    "serves_seniors": True,
                    "serves_disabled": True,
                    "serves_children": True,
                    "citizenship_required": True
                },
                "how_to_apply": "Apply online at ACCESS Florida, call 1-866-762-2237, or visit your local DCF office. Children may also apply through Florida KidCare at 1-888-540-5437.",
                "application_url": "https://www.myflorida.com/accessflorida/",
                "processing_time": "45 days (90 days for disability-based)",
                "source_url": "https://www.myflfamilies.com/service-programs/access/medicaid",
                "source_name": "Florida DCF",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-866-762-2237",
                "contact_website": "https://www.myflorida.com/accessflorida/"
            },
            {
                "program_code": "TANF-FL",
                "program_name": "Temporary Cash Assistance (TANF)",
                "program_name_es": "Asistencia Temporal en Efectivo (TANF)",
                "category": "financial",
                "description": "Temporary Cash Assistance provides cash benefits to families with children when the parents or other responsible relatives cannot provide for the family's basic needs. The program helps families become self-sufficient through employment.",
                "description_es": "La Asistencia Temporal en Efectivo proporciona beneficios en efectivo a familias con niños cuando los padres u otros familiares responsables no pueden satisfacer las necesidades básicas de la familia.",
                "benefits_summary": "Monthly cash benefit amounts vary by family size and income. Typical ranges: 1-person family: up to $180/month, 2-person: up to $241/month, 3-person: up to $303/month, 4-person: up to $364/month. Benefits are time-limited (48 months lifetime).",
                "benefit_amount_min": 180,
                "benefit_amount_max": 364,
                "benefit_frequency": "monthly",
                "eligibility_summary": "Must have a child under 18 (or 18 if still in high school). Must meet income and asset limits. Must participate in work activities. Must cooperate with child support enforcement. Must be a U.S. citizen or qualified non-citizen.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "serves_families": True,
                    "requires_children": True,
                    "work_requirements": True,
                    "citizenship_required": True,
                    "time_limited": True
                },
                "how_to_apply": "Apply online at ACCESS Florida, call 1-866-762-2237, or visit your local DCF service center.",
                "application_url": "https://www.myflorida.com/accessflorida/",
                "processing_time": "30 days",
                "source_url": "https://www.myflfamilies.com/service-programs/access/temporary-cash-assistance",
                "source_name": "Florida DCF",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-866-762-2237",
                "contact_website": "https://www.myflorida.com/accessflorida/"
            },
            {
                "program_code": "LIHEAP-FL",
                "program_name": "Low Income Home Energy Assistance Program (LIHEAP)",
                "program_name_es": "Programa de Asistencia de Energía para Hogares de Bajos Ingresos (LIHEAP)",
                "category": "housing",
                "description": "LIHEAP helps low-income households pay their home energy bills. The program provides a one-time payment to help with heating or cooling costs, or crisis assistance if you're facing disconnection or have already been disconnected.",
                "description_es": "LIHEAP ayuda a los hogares de bajos ingresos a pagar sus facturas de energía del hogar. El programa proporciona un pago único para ayudar con los costos de calefacción o refrigeración.",
                "benefits_summary": "One-time payment typically ranging from $150-$600, paid directly to your utility company. Crisis assistance available for households facing utility disconnection. Amount depends on income, household size, and energy costs.",
                "benefit_amount_min": 150,
                "benefit_amount_max": 600,
                "benefit_frequency": "one-time",
                "eligibility_summary": "Household income must be at or below 150% of the Federal Poverty Level. Must be responsible for home energy costs (directly or included in rent). Priority given to households with elderly, disabled, or children under 6.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "fpl_percentage": 150,
                    "serves_families": True,
                    "serves_seniors": True,
                    "serves_disabled": True
                },
                "how_to_apply": "Apply through your local Community Action Agency. In Brevard County, contact Community Action Agency at (321) 631-2766. Applications typically open October 1st each year.",
                "source_name": "Florida DCF / LIHEAP",
                "confidence_score": 0.90,
                "is_active": True,
                "is_emergency": True,
                "serves_state": ["FL"],
                "contact_phone": "1-866-762-2237"
            },
            {
                "program_code": "WIC-FL",
                "program_name": "Women, Infants, and Children (WIC)",
                "program_name_es": "Mujeres, Infantes y Niños (WIC)",
                "category": "food",
                "description": "WIC provides nutritious foods, nutrition education, breastfeeding support, and referrals to health and social services for pregnant and postpartum women, infants, and children up to age 5 who are at nutritional risk.",
                "description_es": "WIC proporciona alimentos nutritivos, educación nutricional, apoyo para la lactancia y referencias a servicios de salud y sociales para mujeres embarazadas y posparto, bebés y niños hasta los 5 años que están en riesgo nutricional.",
                "benefits_summary": "Monthly food package including milk, cheese, eggs, cereal, juice, beans, peanut butter, fruits and vegetables. Infant formula provided if not breastfeeding. Approximate value: $50-100/month per participant.",
                "benefit_frequency": "monthly",
                "eligibility_summary": "Must be pregnant, postpartum (up to 6 months), breastfeeding (up to 1 year), an infant, or a child under 5. Must meet income guidelines (185% FPL). Must be at nutritional risk (determined by WIC staff). Florida resident.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "fpl_percentage": 185,
                    "serves_families": True,
                    "serves_pregnant": True,
                    "serves_children": True
                },
                "how_to_apply": "Call your local WIC office to schedule an appointment. In Brevard County: (321) 639-5793. Bring ID, proof of address, proof of income, and immunization records for children.",
                "source_name": "Florida Department of Health",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_state": ["FL"],
                "contact_phone": "1-800-342-3556",
                "contact_website": "https://www.floridahealth.gov/programs-and-services/wic/"
            }
        ]


# Income limits table for Florida DCF programs (2024)
SNAP_INCOME_LIMITS_2024 = [
    {"household_size": 1, "monthly_limit": 1580, "fpl_percentage": 130},
    {"household_size": 2, "monthly_limit": 2137, "fpl_percentage": 130},
    {"household_size": 3, "monthly_limit": 2694, "fpl_percentage": 130},
    {"household_size": 4, "monthly_limit": 3250, "fpl_percentage": 130},
    {"household_size": 5, "monthly_limit": 3807, "fpl_percentage": 130},
    {"household_size": 6, "monthly_limit": 4364, "fpl_percentage": 130},
    {"household_size": 7, "monthly_limit": 4921, "fpl_percentage": 130},
    {"household_size": 8, "monthly_limit": 5478, "fpl_percentage": 130},
]
