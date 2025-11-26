"""
Local 211 / Brevard County Scraper
Scrapes local service providers and programs from 211 and county resources
"""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from loguru import logger

from .base_scraper import BaseScraper


class Local211Scraper(BaseScraper):
    """Scraper for local 211 Brevard and community resources."""

    @property
    def source_name(self) -> str:
        return "211 Brevard / Local"

    @property
    def base_url(self) -> str:
        return "https://211brevard.org"

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape local programs and providers.
        Returns curated local resources since 211 databases often require API access.
        """
        programs = []
        providers = []

        # Add curated local programs
        programs.extend(self._get_local_programs())

        # Add local service providers
        providers.extend(self._get_local_providers())

        return {
            "programs": programs,
            "providers": providers
        }

    def parse_program(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Parse a 211 program page."""
        # Most 211 systems require API access
        # This would be implemented if we get API access to 211
        return None

    def _get_local_programs(self) -> List[Dict[str, Any]]:
        """Return curated local Brevard County programs."""
        return [
            {
                "program_code": "211-INFO",
                "program_name": "211 Information & Referral",
                "program_name_es": "Información y Referencias 211",
                "category": "financial",
                "description": "211 is a free, confidential service that connects people with local resources for food, housing, utilities, healthcare, childcare, and more. Available 24 hours a day, 7 days a week. Trained specialists help you find the right programs and services.",
                "description_es": "211 es un servicio gratuito y confidencial que conecta a las personas con recursos locales para alimentos, vivienda, servicios públicos, atención médica, cuidado infantil y más. Disponible las 24 horas del día, los 7 días de la semana.",
                "benefits_summary": "Free information and referral service. Specialists can help you find: emergency food, shelter, utility assistance, healthcare, mental health services, childcare, employment help, and more. Available in English and Spanish.",
                "eligibility_summary": "Anyone can call 211. No income requirements or documentation needed. Service is free and confidential.",
                "eligibility_parsed": {
                    "has_income_limit": False,
                    "serves_everyone": True
                },
                "how_to_apply": "Dial 2-1-1 from any phone, or text your ZIP code to 898211. You can also search online at 211brevard.org or 211.org.",
                "source_name": "211 Brevard",
                "confidence_score": 1.0,
                "is_active": True,
                "is_emergency": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "211",
                "contact_website": "https://211brevard.org"
            },
            {
                "program_code": "SALVATION-ARMY-EA",
                "program_name": "Salvation Army Emergency Assistance",
                "program_name_es": "Asistencia de Emergencia del Ejército de Salvación",
                "category": "financial",
                "description": "The Salvation Army provides emergency assistance to individuals and families in crisis. Services may include help with rent, utilities, food, and other emergency needs. Assistance is provided based on available funding and individual circumstances.",
                "description_es": "El Ejército de Salvación proporciona asistencia de emergencia a individuos y familias en crisis. Los servicios pueden incluir ayuda con el alquiler, servicios públicos, alimentos y otras necesidades de emergencia.",
                "benefits_summary": "Emergency financial assistance for rent, utilities, and other needs. Amount varies based on funding and need. May also provide food boxes, clothing, and referrals to other services.",
                "benefit_frequency": "one-time",
                "eligibility_summary": "Must demonstrate financial need and crisis situation. May need to provide ID, proof of income, and documentation of the emergency (eviction notice, utility shutoff notice, etc.). Limited to Brevard County residents.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "serves_families": True,
                    "emergency_assistance": True
                },
                "how_to_apply": "Call or visit the Salvation Army Melbourne location. May need to call ahead to schedule an appointment for assistance.",
                "source_name": "Salvation Army",
                "confidence_score": 0.85,
                "is_active": True,
                "is_emergency": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 724-2689"
            },
            {
                "program_code": "DAILY-BREAD-FOOD",
                "program_name": "Daily Bread Food Pantry",
                "program_name_es": "Despensa de Alimentos Daily Bread",
                "category": "food",
                "description": "Daily Bread is a nonprofit organization providing food assistance to hungry families in Brevard County. They operate food pantries and provide free groceries to those in need. No proof of income required - just show ID and proof of Brevard County residence.",
                "description_es": "Daily Bread es una organización sin fines de lucro que proporciona asistencia alimentaria a familias hambrientas en el Condado de Brevard. Operan despensas de alimentos y proporcionan comestibles gratis.",
                "benefits_summary": "Free groceries including fresh produce, meat, dairy, canned goods, and bread. Can visit once per week. Serves individuals and families. No limit on family size.",
                "benefit_frequency": "weekly",
                "eligibility_summary": "Must be a Brevard County resident. Bring photo ID and proof of address (utility bill, lease, etc.). No proof of income required.",
                "eligibility_parsed": {
                    "has_income_limit": False,
                    "serves_families": True,
                    "serves_everyone": True
                },
                "how_to_apply": "Visit during distribution hours. No appointment needed. Main location in Melbourne with additional pantry sites throughout Brevard.",
                "source_name": "Daily Bread",
                "confidence_score": 0.90,
                "is_active": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 723-1060",
                "contact_website": "https://dailybreadinc.org"
            },
            {
                "program_code": "COMMUNITY-HOPE",
                "program_name": "Community of Hope Homeless Services",
                "program_name_es": "Servicios para Personas sin Hogar Community of Hope",
                "category": "housing",
                "description": "Community of Hope provides services for individuals and families experiencing homelessness in Brevard County. Services include emergency shelter, transitional housing, case management, and support services to help people achieve stable housing.",
                "description_es": "Community of Hope proporciona servicios para individuos y familias que experimentan falta de vivienda en el Condado de Brevard. Los servicios incluyen refugio de emergencia, vivienda de transición y apoyo.",
                "benefits_summary": "Emergency shelter beds, transitional housing programs, case management, employment assistance, and supportive services. Focus on helping people become self-sufficient and obtain permanent housing.",
                "eligibility_summary": "Must be homeless or at imminent risk of homelessness in Brevard County. Different programs have different eligibility requirements. Contact for intake assessment.",
                "eligibility_parsed": {
                    "serves_homeless": True,
                    "serves_families": True,
                    "emergency_assistance": True
                },
                "how_to_apply": "Call the main office for intake information. May also be referred through 211 or coordinated entry system.",
                "source_name": "Community of Hope",
                "confidence_score": 0.85,
                "is_active": True,
                "is_emergency": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 632-5100"
            },
            {
                "program_code": "BREVARD-SCHOOLS-FOOD",
                "program_name": "Brevard Schools Free Meals Program",
                "program_name_es": "Programa de Comidas Gratis de las Escuelas de Brevard",
                "category": "food",
                "description": "Brevard Public Schools provides free breakfast and lunch to all students at participating Community Eligibility Provision (CEP) schools. At non-CEP schools, free and reduced-price meals are available based on family income.",
                "description_es": "Las Escuelas Públicas de Brevard proporcionan desayuno y almuerzo gratis a todos los estudiantes en escuelas participantes.",
                "benefits_summary": "Free breakfast and lunch at CEP schools (no application needed). Free or reduced-price meals at other schools based on income eligibility. Summer meal programs also available.",
                "benefit_frequency": "daily",
                "eligibility_summary": "All students at CEP schools qualify for free meals. At other schools, families must complete an application and meet income guidelines (130% FPL for free, 185% FPL for reduced).",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "fpl_percentage": 185,
                    "serves_children": True,
                    "serves_families": True
                },
                "how_to_apply": "At CEP schools, meals are automatically free. At other schools, complete the meal application form available at your child's school or online through Brevard Schools website.",
                "source_name": "Brevard Public Schools",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 633-1000",
                "contact_website": "https://www.brevardschools.org"
            },
            {
                "program_code": "CCFL-CHILDCARE",
                "program_name": "School Readiness (Subsidized Childcare)",
                "program_name_es": "Preparación Escolar (Cuidado Infantil Subsidiado)",
                "category": "childcare",
                "description": "The School Readiness program helps low-income families pay for childcare so parents can work or attend school. Also known as subsidized childcare or the child care subsidy program. Administered by the Early Learning Coalition.",
                "description_es": "El programa de Preparación Escolar ayuda a las familias de bajos ingresos a pagar el cuidado infantil para que los padres puedan trabajar o asistir a la escuela.",
                "benefits_summary": "Pays a portion of childcare costs at participating providers. Family pays a copay based on income. Covers care for children birth through age 12 (or 13 for special needs).",
                "benefit_frequency": "ongoing",
                "eligibility_summary": "Family income at or below 150% FPL (200% to remain eligible). Parent must be working, in school, or in job training. Child must be under 13 (or under 19 with special needs). Must be Florida resident.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "fpl_percentage": 150,
                    "serves_families": True,
                    "serves_children": True,
                    "work_requirements": True
                },
                "how_to_apply": "Apply through the Early Learning Coalition of Brevard at (321) 637-1800 or online. Wait list may apply.",
                "source_name": "Early Learning Coalition of Brevard",
                "confidence_score": 0.90,
                "is_active": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 637-1800",
                "contact_website": "https://www.elcbrevard.org"
            },
            {
                "program_code": "VPK-FL",
                "program_name": "Voluntary Prekindergarten (VPK)",
                "program_name_es": "Prekindergarten Voluntario (VPK)",
                "category": "childcare",
                "description": "Florida's VPK program is a free educational program for all 4-year-olds. It prepares children for kindergarten with early learning activities. Available at schools, childcare centers, and other approved providers throughout Brevard County.",
                "description_es": "El programa VPK de Florida es un programa educativo gratuito para todos los niños de 4 años. Prepara a los niños para el kindergarten con actividades de aprendizaje temprano.",
                "benefits_summary": "FREE program for all eligible 4-year-olds. School year program: 540 hours (3 hours/day). Summer program: 300 hours. No income requirements - it's free for everyone!",
                "benefit_frequency": "annual",
                "eligibility_summary": "Child must be 4 years old on or before September 1 of the program year. Must be a Florida resident. No income requirements - VPK is free for all eligible children.",
                "eligibility_parsed": {
                    "has_income_limit": False,
                    "serves_children": True,
                    "serves_families": True,
                    "age_requirement": True
                },
                "how_to_apply": "Obtain a VPK certificate from the Early Learning Coalition of Brevard (online or by phone), then enroll at a VPK provider of your choice.",
                "application_url": "https://familyservices.floridaearlylearning.com/",
                "source_name": "Florida Office of Early Learning",
                "confidence_score": 0.95,
                "is_active": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 637-1800",
                "contact_website": "https://www.elcbrevard.org"
            },
            {
                "program_code": "BREVARD-CARES-EA",
                "program_name": "Brevard CARES Emergency Assistance",
                "program_name_es": "Asistencia de Emergencia Brevard CARES",
                "category": "housing",
                "description": "Brevard CARES provides emergency financial assistance to Brevard County residents facing housing crises. Funded through various sources including CDBG and local funds. Helps prevent homelessness by assisting with rent and utility costs.",
                "description_es": "Brevard CARES proporciona asistencia financiera de emergencia a residentes del Condado de Brevard que enfrentan crisis de vivienda.",
                "benefits_summary": "Emergency assistance with rent, utilities, and mortgage (limited). Assistance amount varies based on funding availability. May provide one-time or short-term assistance.",
                "benefit_frequency": "one-time",
                "eligibility_summary": "Must be Brevard County resident. Must demonstrate financial hardship and risk of losing housing. Income requirements apply (typically below 80% AMI). Must provide documentation of emergency situation.",
                "eligibility_parsed": {
                    "has_income_limit": True,
                    "serves_families": True,
                    "emergency_assistance": True
                },
                "how_to_apply": "Contact Brevard County Housing and Human Services or call 211 for referral. Intake may be required.",
                "source_name": "Brevard County",
                "confidence_score": 0.80,
                "is_active": True,
                "is_emergency": True,
                "serves_county": ["Brevard"],
                "serves_state": ["FL"],
                "contact_phone": "(321) 633-2076"
            }
        ]

    def _get_local_providers(self) -> List[Dict[str, Any]]:
        """Return local service providers in Brevard County."""
        return [
            {
                "provider_name": "Florida Department of Children and Families - Brevard",
                "provider_name_es": "Departamento de Niños y Familias de Florida - Brevard",
                "provider_type": "government",
                "address_street": "2535 N Courtenay Pkwy",
                "address_city": "Merritt Island",
                "address_state": "FL",
                "address_zip": "32953",
                "address_county": "Brevard",
                "phone": "(321) 504-2000",
                "website": "https://www.myflfamilies.com/",
                "hours_of_operation": {
                    "monday": "8:00 AM - 5:00 PM",
                    "tuesday": "8:00 AM - 5:00 PM",
                    "wednesday": "8:00 AM - 5:00 PM",
                    "thursday": "8:00 AM - 5:00 PM",
                    "friday": "8:00 AM - 5:00 PM"
                },
                "services_offered": ["SNAP", "Medicaid", "TANF", "Food Assistance", "Cash Assistance"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "Daily Bread - Melbourne",
                "provider_type": "nonprofit",
                "address_street": "815 E Fee Ave",
                "address_city": "Melbourne",
                "address_state": "FL",
                "address_zip": "32901",
                "address_county": "Brevard",
                "phone": "(321) 723-1060",
                "website": "https://dailybreadinc.org",
                "hours_of_operation": {
                    "monday": "9:00 AM - 12:00 PM",
                    "tuesday": "9:00 AM - 12:00 PM",
                    "wednesday": "9:00 AM - 12:00 PM",
                    "thursday": "9:00 AM - 12:00 PM",
                    "friday": "9:00 AM - 12:00 PM"
                },
                "services_offered": ["Food Pantry", "Emergency Food"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "Salvation Army - Melbourne",
                "provider_type": "nonprofit",
                "address_street": "1515 S Hickory St",
                "address_city": "Melbourne",
                "address_state": "FL",
                "address_zip": "32901",
                "address_county": "Brevard",
                "phone": "(321) 724-2689",
                "services_offered": ["Emergency Assistance", "Food Pantry", "Utility Assistance", "Rent Assistance"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "Social Security Administration - Melbourne",
                "provider_type": "government",
                "address_street": "1480 Palm Bay Rd NE",
                "address_city": "Palm Bay",
                "address_state": "FL",
                "address_zip": "32905",
                "address_county": "Brevard",
                "phone": "1-800-772-1213",
                "website": "https://www.ssa.gov",
                "hours_of_operation": {
                    "monday": "9:00 AM - 4:00 PM",
                    "tuesday": "9:00 AM - 4:00 PM",
                    "wednesday": "9:00 AM - 12:00 PM",
                    "thursday": "9:00 AM - 4:00 PM",
                    "friday": "9:00 AM - 4:00 PM"
                },
                "services_offered": ["Social Security", "SSI", "SSDI", "Medicare"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "Brevard County Housing Authority",
                "provider_type": "government",
                "address_street": "4149 S Washington Ave",
                "address_city": "Titusville",
                "address_state": "FL",
                "address_zip": "32780",
                "address_county": "Brevard",
                "phone": "(321) 631-5620",
                "website": "https://brevardhousing.org",
                "services_offered": ["Section 8 Housing Vouchers", "Public Housing"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "WIC - Brevard County Health Department",
                "provider_name_es": "WIC - Departamento de Salud del Condado de Brevard",
                "provider_type": "government",
                "address_street": "2555 Judge Fran Jamieson Way",
                "address_city": "Viera",
                "address_state": "FL",
                "address_zip": "32940",
                "address_county": "Brevard",
                "phone": "(321) 639-5793",
                "website": "https://brevard.floridahealth.gov",
                "services_offered": ["WIC", "Nutrition Education", "Breastfeeding Support"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "Early Learning Coalition of Brevard",
                "provider_type": "nonprofit",
                "address_street": "1800 Penn St Suite 10",
                "address_city": "Melbourne",
                "address_state": "FL",
                "address_zip": "32901",
                "address_county": "Brevard",
                "phone": "(321) 637-1800",
                "website": "https://www.elcbrevard.org",
                "services_offered": ["School Readiness", "VPK", "Childcare Assistance"],
                "languages_spoken": ["English", "Spanish"]
            },
            {
                "provider_name": "Community of Hope",
                "provider_type": "nonprofit",
                "address_street": "209 S New York Ave",
                "address_city": "Cocoa",
                "address_state": "FL",
                "address_zip": "32922",
                "address_county": "Brevard",
                "phone": "(321) 632-5100",
                "services_offered": ["Emergency Shelter", "Transitional Housing", "Homeless Services"],
                "languages_spoken": ["English"]
            },
            {
                "provider_name": "CareerSource Brevard",
                "provider_type": "government",
                "address_street": "295 Barnes Blvd",
                "address_city": "Rockledge",
                "address_state": "FL",
                "address_zip": "32955",
                "address_county": "Brevard",
                "phone": "(321) 504-7600",
                "website": "https://careersourcebrevard.com",
                "hours_of_operation": {
                    "monday": "8:00 AM - 5:00 PM",
                    "tuesday": "8:00 AM - 5:00 PM",
                    "wednesday": "8:00 AM - 5:00 PM",
                    "thursday": "8:00 AM - 5:00 PM",
                    "friday": "8:00 AM - 5:00 PM"
                },
                "services_offered": ["Job Search Assistance", "Resume Help", "Training Programs", "Unemployment"],
                "languages_spoken": ["English", "Spanish"]
            }
        ]
