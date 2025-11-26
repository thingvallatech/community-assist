"""
Database Connection Management
Handles PostgreSQL connections and common CRUD operations
"""

import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Generator

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import get_settings


class DatabaseConnection:
    """Manages database connections and operations."""

    def __init__(self, connection_string: Optional[str] = None):
        settings = get_settings()
        self.connection_string = connection_string or settings.database_connection_string
        self._engine: Optional[Engine] = None
        self._session_factory = None

    @property
    def engine(self) -> Engine:
        """Lazy initialization of database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False
            )
            self._session_factory = sessionmaker(bind=self._engine)
            logger.info("Database engine initialized")
        return self._engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a SELECT query and return results as list of dicts."""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def execute_write(self, query: str, params: Optional[Dict] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result.rowcount

    # =========================================================================
    # Program Operations
    # =========================================================================

    def get_all_programs(self, active_only: bool = True, category: Optional[str] = None) -> List[Dict]:
        """Get all programs, optionally filtered."""
        query = """
            SELECT *
            FROM programs
            WHERE 1=1
        """
        params = {}

        if active_only:
            query += " AND is_active = true"

        if category:
            query += " AND category = :category"
            params["category"] = category

        query += " ORDER BY confidence_score DESC, program_name"

        return self.execute_query(query, params)

    def get_program_by_id(self, program_id: int) -> Optional[Dict]:
        """Get a single program by ID."""
        query = "SELECT * FROM programs WHERE id = :id"
        results = self.execute_query(query, {"id": program_id})
        return results[0] if results else None

    def search_programs(self, search_term: str, lang: str = "en") -> List[Dict]:
        """Search programs by name or description."""
        name_field = "program_name_es" if lang == "es" else "program_name"
        desc_field = "description_es" if lang == "es" else "description"

        query = f"""
            SELECT *
            FROM programs
            WHERE is_active = true
              AND (
                  {name_field} ILIKE :term
                  OR {desc_field} ILIKE :term
                  OR program_name ILIKE :term
                  OR description ILIKE :term
              )
            ORDER BY confidence_score DESC
        """
        return self.execute_query(query, {"term": f"%{search_term}%"})

    def get_programs_by_category(self, category: str) -> List[Dict]:
        """Get all programs in a category."""
        return self.get_all_programs(active_only=True, category=category)

    def get_emergency_programs(self) -> List[Dict]:
        """Get all emergency/crisis programs."""
        query = """
            SELECT *
            FROM programs
            WHERE is_active = true AND is_emergency = true
            ORDER BY category, program_name
        """
        return self.execute_query(query)

    def upsert_program(self, program_data: Dict) -> int:
        """Insert or update a program."""
        # Check if program exists by code
        if program_data.get("program_code"):
            existing = self.execute_query(
                "SELECT id FROM programs WHERE program_code = :code",
                {"code": program_data["program_code"]}
            )
            if existing:
                # Update existing
                program_data["id"] = existing[0]["id"]
                return self._update_program(program_data)

        # Insert new
        return self._insert_program(program_data)

    def _insert_program(self, data: Dict) -> int:
        """Insert a new program."""
        query = """
            INSERT INTO programs (
                program_code, program_name, program_name_es, category, subcategory,
                description, description_es, benefits_summary, benefits_summary_es,
                benefit_amount_min, benefit_amount_max, benefit_frequency,
                how_to_apply, how_to_apply_es, application_url,
                application_deadline, enrollment_period_start, enrollment_period_end,
                processing_time, eligibility_summary, eligibility_summary_es,
                eligibility_parsed, documents_required, source_url, source_name,
                last_verified, confidence_score, is_active, is_emergency,
                serves_county, serves_state, contact_phone, contact_email, contact_website
            ) VALUES (
                :program_code, :program_name, :program_name_es, :category, :subcategory,
                :description, :description_es, :benefits_summary, :benefits_summary_es,
                :benefit_amount_min, :benefit_amount_max, :benefit_frequency,
                :how_to_apply, :how_to_apply_es, :application_url,
                :application_deadline, :enrollment_period_start, :enrollment_period_end,
                :processing_time, :eligibility_summary, :eligibility_summary_es,
                :eligibility_parsed, :documents_required, :source_url, :source_name,
                :last_verified, :confidence_score, :is_active, :is_emergency,
                :serves_county, :serves_state, :contact_phone, :contact_email, :contact_website
            )
            RETURNING id
        """
        # Set defaults for missing fields
        defaults = {
            "program_code": None, "program_name_es": None, "subcategory": None,
            "description_es": None, "benefits_summary": None, "benefits_summary_es": None,
            "benefit_amount_min": None, "benefit_amount_max": None, "benefit_frequency": None,
            "how_to_apply_es": None, "application_url": None, "application_deadline": None,
            "enrollment_period_start": None, "enrollment_period_end": None,
            "processing_time": None, "eligibility_summary_es": None,
            "eligibility_parsed": None, "documents_required": None,
            "source_url": None, "source_name": None, "last_verified": None,
            "confidence_score": 0.5, "is_active": True, "is_emergency": False,
            "serves_county": None, "serves_state": None,
            "contact_phone": None, "contact_email": None, "contact_website": None
        }

        params = {**defaults, **data}
        results = self.execute_query(query, params)
        return results[0]["id"] if results else 0

    def _update_program(self, data: Dict) -> int:
        """Update an existing program."""
        query = """
            UPDATE programs SET
                program_name = COALESCE(:program_name, program_name),
                program_name_es = COALESCE(:program_name_es, program_name_es),
                category = COALESCE(:category, category),
                description = COALESCE(:description, description),
                description_es = COALESCE(:description_es, description_es),
                benefits_summary = COALESCE(:benefits_summary, benefits_summary),
                eligibility_summary = COALESCE(:eligibility_summary, eligibility_summary),
                eligibility_parsed = COALESCE(:eligibility_parsed, eligibility_parsed),
                confidence_score = COALESCE(:confidence_score, confidence_score),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """
        return self.execute_write(query, data)

    # =========================================================================
    # Income Limits Operations
    # =========================================================================

    def get_income_limits(self, program_id: int) -> List[Dict]:
        """Get income limits for a program."""
        query = """
            SELECT *
            FROM income_limits
            WHERE program_id = :program_id
            ORDER BY household_size
        """
        return self.execute_query(query, {"program_id": program_id})

    def get_income_limit(self, program_id: int, household_size: int) -> Optional[float]:
        """Get monthly income limit for a specific household size."""
        query = """
            SELECT monthly_limit
            FROM income_limits
            WHERE program_id = :program_id AND household_size = :size
            ORDER BY effective_date DESC
            LIMIT 1
        """
        results = self.execute_query(query, {
            "program_id": program_id,
            "size": household_size
        })
        return results[0]["monthly_limit"] if results else None

    # =========================================================================
    # Provider Operations
    # =========================================================================

    def get_providers_by_county(self, county: str) -> List[Dict]:
        """Get service providers in a county."""
        query = """
            SELECT *
            FROM providers
            WHERE address_county ILIKE :county AND is_active = true
            ORDER BY provider_name
        """
        return self.execute_query(query, {"county": f"%{county}%"})

    def get_providers_for_program(self, program_id: int) -> List[Dict]:
        """Get providers that offer a specific program."""
        query = """
            SELECT p.*
            FROM providers p
            JOIN program_providers pp ON p.id = pp.provider_id
            WHERE pp.program_id = :program_id AND p.is_active = true
            ORDER BY pp.is_primary DESC, p.provider_name
        """
        return self.execute_query(query, {"program_id": program_id})

    # =========================================================================
    # Translation Operations
    # =========================================================================

    def get_translation(self, key: str, lang: str = "en") -> str:
        """Get a translated string by key."""
        field = "text_es" if lang == "es" else "text_en"
        query = f"""
            SELECT {field} as text, text_en
            FROM translations
            WHERE translation_key = :key
        """
        results = self.execute_query(query, {"key": key})
        if results:
            return results[0]["text"] or results[0]["text_en"]
        return key  # Return key if translation not found

    def get_all_translations(self, lang: str = "en") -> Dict[str, str]:
        """Get all translations for a language."""
        field = "text_es" if lang == "es" else "text_en"
        query = f"""
            SELECT translation_key, COALESCE({field}, text_en) as text
            FROM translations
        """
        results = self.execute_query(query)
        return {r["translation_key"]: r["text"] for r in results}

    # =========================================================================
    # FPL Operations
    # =========================================================================

    def get_fpl_table(self, year: int = 2024, state: str = "FL") -> Dict[int, Dict]:
        """Get FPL amounts for a year."""
        query = """
            SELECT household_size, annual_amount, monthly_amount
            FROM fpl_tables
            WHERE year = :year AND state = :state
            ORDER BY household_size
        """
        results = self.execute_query(query, {"year": year, "state": state})
        return {
            r["household_size"]: {
                "annual": float(r["annual_amount"]),
                "monthly": float(r["monthly_amount"])
            }
            for r in results
        }

    # =========================================================================
    # Statistics Operations
    # =========================================================================

    def get_program_stats(self) -> Dict[str, Any]:
        """Get program statistics for dashboard."""
        query = """
            SELECT
                COUNT(*) as total_programs,
                COUNT(*) FILTER (WHERE is_emergency) as emergency_programs,
                COUNT(*) FILTER (WHERE confidence_score >= 0.7) as high_confidence,
                COUNT(DISTINCT category) as categories
            FROM programs
            WHERE is_active = true
        """
        results = self.execute_query(query)
        return results[0] if results else {}

    def get_category_counts(self) -> List[Dict]:
        """Get program counts by category."""
        query = """
            SELECT category, COUNT(*) as count
            FROM programs
            WHERE is_active = true AND category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """
        return self.execute_query(query)

    def close(self):
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connection closed")


# Global database instance
_db: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get or create database connection."""
    global _db
    if _db is None:
        _db = DatabaseConnection()
        # Initialize engine
        _ = _db.engine
    return _db
