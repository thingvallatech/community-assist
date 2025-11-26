"""
Community Assist - Main Scraper Pipeline
Orchestrates data collection from all sources
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Dict, List

from loguru import logger

from src.config import get_settings
from src.database.connection import get_db_connection
from src.scrapers import FloridaDCFScraper, BenefitsGovScraper, Local211Scraper, SNAP_INCOME_LIMITS_2024


def setup_logging():
    """Configure logging."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Add file handler
    logger.add(
        f"logs/scraper_{datetime.now().strftime('%Y%m%d')}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.log_level
    )


async def run_florida_dcf_scraper() -> List[Dict[str, Any]]:
    """Run the Florida DCF scraper."""
    logger.info("Starting Florida DCF scraper...")

    async with FloridaDCFScraper() as scraper:
        programs = await scraper.scrape()

    logger.info(f"Florida DCF: Extracted {len(programs)} programs")
    return programs


async def run_benefits_gov_scraper() -> List[Dict[str, Any]]:
    """Run the Benefits.gov scraper."""
    logger.info("Starting Benefits.gov scraper...")

    async with BenefitsGovScraper() as scraper:
        programs = await scraper.scrape()

    logger.info(f"Benefits.gov: Extracted {len(programs)} programs")
    return programs


async def run_local_211_scraper() -> Dict[str, List[Dict[str, Any]]]:
    """Run the local 211 scraper."""
    logger.info("Starting Local 211 scraper...")

    scraper = Local211Scraper()
    # This returns both programs and providers
    data = await scraper.scrape()

    programs = data.get("programs", [])
    providers = data.get("providers", [])

    logger.info(f"Local 211: {len(programs)} programs, {len(providers)} providers")
    return data


def save_programs_to_db(programs: List[Dict[str, Any]]) -> int:
    """Save programs to database."""
    db = get_db_connection()
    saved = 0
    updated = 0

    for program in programs:
        try:
            # Check if program already exists
            existing = None
            if program.get("program_code"):
                results = db.execute_query(
                    "SELECT id FROM programs WHERE program_code = :code",
                    {"code": program["program_code"]}
                )
                existing = results[0] if results else None

            if existing:
                # Update existing program
                program["id"] = existing["id"]
                db.execute_write("""
                    UPDATE programs SET
                        program_name = :program_name,
                        program_name_es = :program_name_es,
                        category = :category,
                        description = :description,
                        description_es = :description_es,
                        benefits_summary = :benefits_summary,
                        benefits_summary_es = :benefits_summary_es,
                        benefit_amount_min = :benefit_amount_min,
                        benefit_amount_max = :benefit_amount_max,
                        benefit_frequency = :benefit_frequency,
                        eligibility_summary = :eligibility_summary,
                        eligibility_summary_es = :eligibility_summary_es,
                        eligibility_parsed = :eligibility_parsed,
                        how_to_apply = :how_to_apply,
                        how_to_apply_es = :how_to_apply_es,
                        application_url = :application_url,
                        processing_time = :processing_time,
                        source_url = :source_url,
                        source_name = :source_name,
                        confidence_score = :confidence_score,
                        is_active = :is_active,
                        is_emergency = :is_emergency,
                        serves_county = :serves_county,
                        serves_state = :serves_state,
                        contact_phone = :contact_phone,
                        contact_website = :contact_website,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """, {
                    "id": program["id"],
                    "program_name": program.get("program_name"),
                    "program_name_es": program.get("program_name_es"),
                    "category": program.get("category"),
                    "description": program.get("description"),
                    "description_es": program.get("description_es"),
                    "benefits_summary": program.get("benefits_summary"),
                    "benefits_summary_es": program.get("benefits_summary_es"),
                    "benefit_amount_min": program.get("benefit_amount_min"),
                    "benefit_amount_max": program.get("benefit_amount_max"),
                    "benefit_frequency": program.get("benefit_frequency"),
                    "eligibility_summary": program.get("eligibility_summary"),
                    "eligibility_summary_es": program.get("eligibility_summary_es"),
                    "eligibility_parsed": json.dumps(program.get("eligibility_parsed")) if program.get("eligibility_parsed") else None,
                    "how_to_apply": program.get("how_to_apply"),
                    "how_to_apply_es": program.get("how_to_apply_es"),
                    "application_url": program.get("application_url"),
                    "processing_time": program.get("processing_time"),
                    "source_url": program.get("source_url"),
                    "source_name": program.get("source_name"),
                    "confidence_score": program.get("confidence_score", 0.5),
                    "is_active": program.get("is_active", True),
                    "is_emergency": program.get("is_emergency", False),
                    "serves_county": program.get("serves_county"),
                    "serves_state": program.get("serves_state"),
                    "contact_phone": program.get("contact_phone"),
                    "contact_website": program.get("contact_website"),
                })
                updated += 1
            else:
                # Insert new program
                db.execute_write("""
                    INSERT INTO programs (
                        program_code, program_name, program_name_es, category,
                        description, description_es, benefits_summary, benefits_summary_es,
                        benefit_amount_min, benefit_amount_max, benefit_frequency,
                        eligibility_summary, eligibility_summary_es, eligibility_parsed,
                        how_to_apply, how_to_apply_es, application_url, processing_time,
                        source_url, source_name, confidence_score, is_active, is_emergency,
                        serves_county, serves_state, contact_phone, contact_website
                    ) VALUES (
                        :program_code, :program_name, :program_name_es, :category,
                        :description, :description_es, :benefits_summary, :benefits_summary_es,
                        :benefit_amount_min, :benefit_amount_max, :benefit_frequency,
                        :eligibility_summary, :eligibility_summary_es, :eligibility_parsed,
                        :how_to_apply, :how_to_apply_es, :application_url, :processing_time,
                        :source_url, :source_name, :confidence_score, :is_active, :is_emergency,
                        :serves_county, :serves_state, :contact_phone, :contact_website
                    )
                """, {
                    "program_code": program.get("program_code"),
                    "program_name": program.get("program_name"),
                    "program_name_es": program.get("program_name_es"),
                    "category": program.get("category"),
                    "description": program.get("description"),
                    "description_es": program.get("description_es"),
                    "benefits_summary": program.get("benefits_summary"),
                    "benefits_summary_es": program.get("benefits_summary_es"),
                    "benefit_amount_min": program.get("benefit_amount_min"),
                    "benefit_amount_max": program.get("benefit_amount_max"),
                    "benefit_frequency": program.get("benefit_frequency"),
                    "eligibility_summary": program.get("eligibility_summary"),
                    "eligibility_summary_es": program.get("eligibility_summary_es"),
                    "eligibility_parsed": json.dumps(program.get("eligibility_parsed")) if program.get("eligibility_parsed") else None,
                    "how_to_apply": program.get("how_to_apply"),
                    "how_to_apply_es": program.get("how_to_apply_es"),
                    "application_url": program.get("application_url"),
                    "processing_time": program.get("processing_time"),
                    "source_url": program.get("source_url"),
                    "source_name": program.get("source_name"),
                    "confidence_score": program.get("confidence_score", 0.5),
                    "is_active": program.get("is_active", True),
                    "is_emergency": program.get("is_emergency", False),
                    "serves_county": program.get("serves_county"),
                    "serves_state": program.get("serves_state"),
                    "contact_phone": program.get("contact_phone"),
                    "contact_website": program.get("contact_website"),
                })
                saved += 1

            logger.debug(f"Processed: {program.get('program_name')}")

        except Exception as e:
            logger.error(f"Error saving program {program.get('program_name')}: {e}")

    logger.info(f"Database: {saved} new programs, {updated} updated")
    return saved + updated


def save_providers_to_db(providers: List[Dict[str, Any]]) -> int:
    """Save providers to database."""
    db = get_db_connection()
    saved = 0

    for provider in providers:
        try:
            # Check if provider exists
            results = db.execute_query(
                "SELECT id FROM providers WHERE provider_name = :name AND address_city = :city",
                {"name": provider["provider_name"], "city": provider.get("address_city", "")}
            )

            if results:
                # Update
                db.execute_write("""
                    UPDATE providers SET
                        provider_name_es = :provider_name_es,
                        provider_type = :provider_type,
                        address_street = :address_street,
                        address_city = :address_city,
                        address_state = :address_state,
                        address_zip = :address_zip,
                        address_county = :address_county,
                        phone = :phone,
                        website = :website,
                        hours_of_operation = :hours_of_operation,
                        services_offered = :services_offered,
                        languages_spoken = :languages_spoken,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE provider_name = :provider_name AND address_city = :city_check
                """, {
                    **provider,
                    "hours_of_operation": json.dumps(provider.get("hours_of_operation")) if provider.get("hours_of_operation") else None,
                    "city_check": provider.get("address_city", "")
                })
            else:
                # Insert
                db.execute_write("""
                    INSERT INTO providers (
                        provider_name, provider_name_es, provider_type,
                        address_street, address_city, address_state, address_zip, address_county,
                        phone, website, hours_of_operation, services_offered, languages_spoken
                    ) VALUES (
                        :provider_name, :provider_name_es, :provider_type,
                        :address_street, :address_city, :address_state, :address_zip, :address_county,
                        :phone, :website, :hours_of_operation, :services_offered, :languages_spoken
                    )
                """, {
                    "provider_name": provider.get("provider_name"),
                    "provider_name_es": provider.get("provider_name_es"),
                    "provider_type": provider.get("provider_type"),
                    "address_street": provider.get("address_street"),
                    "address_city": provider.get("address_city"),
                    "address_state": provider.get("address_state"),
                    "address_zip": provider.get("address_zip"),
                    "address_county": provider.get("address_county"),
                    "phone": provider.get("phone"),
                    "website": provider.get("website"),
                    "hours_of_operation": json.dumps(provider.get("hours_of_operation")) if provider.get("hours_of_operation") else None,
                    "services_offered": provider.get("services_offered"),
                    "languages_spoken": provider.get("languages_spoken"),
                })
                saved += 1

        except Exception as e:
            logger.error(f"Error saving provider {provider.get('provider_name')}: {e}")

    logger.info(f"Providers: {saved} saved/updated")
    return saved


def save_income_limits_to_db() -> int:
    """Save SNAP income limits to database."""
    db = get_db_connection()
    saved = 0

    # Get SNAP program ID
    results = db.execute_query(
        "SELECT id FROM programs WHERE program_code = 'SNAP-FL'"
    )

    if not results:
        logger.warning("SNAP-FL program not found, skipping income limits")
        return 0

    snap_id = results[0]["id"]

    for limit in SNAP_INCOME_LIMITS_2024:
        try:
            db.execute_write("""
                INSERT INTO income_limits (
                    program_id, household_size, monthly_limit, fpl_percentage, effective_date
                ) VALUES (
                    :program_id, :household_size, :monthly_limit, :fpl_percentage, '2024-01-01'
                )
                ON CONFLICT (program_id, household_size, effective_date) DO UPDATE SET
                    monthly_limit = :monthly_limit,
                    fpl_percentage = :fpl_percentage
            """, {
                "program_id": snap_id,
                "household_size": limit["household_size"],
                "monthly_limit": limit["monthly_limit"],
                "fpl_percentage": limit["fpl_percentage"],
            })
            saved += 1
        except Exception as e:
            logger.error(f"Error saving income limit: {e}")

    logger.info(f"Income limits: {saved} saved")
    return saved


async def run_pipeline(skip_scraping: bool = False):
    """Run the full data collection pipeline."""
    logger.info("=" * 60)
    logger.info("COMMUNITY ASSIST DATA PIPELINE")
    logger.info("=" * 60)

    all_programs = []

    if not skip_scraping:
        # Run scrapers
        try:
            dcf_programs = await run_florida_dcf_scraper()
            all_programs.extend(dcf_programs)
        except Exception as e:
            logger.error(f"Florida DCF scraper failed: {e}")

        try:
            benefits_programs = await run_benefits_gov_scraper()
            all_programs.extend(benefits_programs)
        except Exception as e:
            logger.error(f"Benefits.gov scraper failed: {e}")

    # Local 211 data (curated, always runs)
    local_data = await run_local_211_scraper()
    all_programs.extend(local_data.get("programs", []))
    providers = local_data.get("providers", [])

    # Save to database
    logger.info("-" * 40)
    logger.info("Saving to database...")

    programs_saved = save_programs_to_db(all_programs)
    providers_saved = save_providers_to_db(providers)
    limits_saved = save_income_limits_to_db()

    # Summary
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"  Programs: {programs_saved}")
    logger.info(f"  Providers: {providers_saved}")
    logger.info(f"  Income Limits: {limits_saved}")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Community Assist Data Pipeline")
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Only seed curated data (skip web scraping)"
    )
    parser.add_argument(
        "--scraper",
        choices=["dcf", "benefits", "local", "all"],
        default="all",
        help="Which scraper to run"
    )

    args = parser.parse_args()

    setup_logging()

    logger.info("Starting Community Assist data pipeline...")

    try:
        asyncio.run(run_pipeline(skip_scraping=args.seed_only))
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
