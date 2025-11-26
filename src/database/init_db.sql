-- Community Assist Database Schema
-- PostgreSQL 15+

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Programs: Core program information
CREATE TABLE IF NOT EXISTS programs (
    id SERIAL PRIMARY KEY,
    program_code VARCHAR(50) UNIQUE,
    program_name VARCHAR(255) NOT NULL,
    program_name_es VARCHAR(255),
    category VARCHAR(100), -- food, housing, healthcare, financial, childcare, employment, legal, senior, disability, veteran, education, transportation
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
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
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
CREATE TABLE IF NOT EXISTS eligibility_criteria (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    criterion_type VARCHAR(50), -- income, household, categorical, geographic, situational
    criterion_name VARCHAR(100),
    criterion_value JSONB, -- flexible storage for different criteria types
    is_required BOOLEAN DEFAULT true,
    notes TEXT,
    notes_es TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Income limits by program and household size
CREATE TABLE IF NOT EXISTS income_limits (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    household_size INTEGER NOT NULL,
    annual_limit DECIMAL(10,2),
    monthly_limit DECIMAL(10,2),
    fpl_percentage INTEGER, -- 100%, 130%, 200%, etc.
    effective_date DATE,
    expiration_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(program_id, household_size, effective_date)
);

-- Federal Poverty Level reference table
CREATE TABLE IF NOT EXISTS fpl_tables (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    household_size INTEGER NOT NULL,
    annual_amount DECIMAL(10,2) NOT NULL,
    monthly_amount DECIMAL(10,2) NOT NULL,
    state VARCHAR(2) DEFAULT 'FL', -- Different for AK and HI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, household_size, state)
);

-- Service providers/locations
CREATE TABLE IF NOT EXISTS providers (
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
CREATE TABLE IF NOT EXISTS program_providers (
    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    provider_id INTEGER REFERENCES providers(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    PRIMARY KEY (program_id, provider_id)
);

-- Required documents catalog
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    document_name_es VARCHAR(255),
    document_type VARCHAR(100), -- id, income, residence, medical, legal
    description TEXT,
    description_es TEXT,
    how_to_obtain TEXT,
    how_to_obtain_es TEXT,
    alternatives TEXT[], -- acceptable alternatives
    is_common BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Program-document relationship
CREATE TABLE IF NOT EXISTS program_documents (
    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    is_required BOOLEAN DEFAULT true,
    conditions TEXT, -- when this document is needed
    PRIMARY KEY (program_id, document_id)
);

-- =============================================================================
-- SCRAPING TABLES
-- =============================================================================

-- Raw scraped pages (for reprocessing)
CREATE TABLE IF NOT EXISTS raw_pages (
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
CREATE TABLE IF NOT EXISTS scraped_documents (
    id SERIAL PRIMARY KEY,
    source_url VARCHAR(1000),
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size_bytes INTEGER,
    local_path VARCHAR(500),
    full_text TEXT,
    tables_extracted JSONB,
    processed_at TIMESTAMP,
    linked_program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INTERNATIONALIZATION
-- =============================================================================

-- Translations table for all UI text
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    translation_key VARCHAR(255) UNIQUE NOT NULL,
    text_en TEXT NOT NULL,
    text_es TEXT,
    context VARCHAR(100), -- ui, program, category, document
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- OPERATIONAL TABLES
-- =============================================================================

-- Scrape job tracking
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50),
    source_name VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_added INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality tracking
CREATE TABLE IF NOT EXISTS data_gaps (
    id SERIAL PRIMARY KEY,
    program_id INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    missing_field VARCHAR(100),
    field_importance VARCHAR(20), -- critical, high, medium, low
    possible_sources TEXT[],
    notes TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_programs_category ON programs(category);
CREATE INDEX IF NOT EXISTS idx_programs_county ON programs USING GIN(serves_county);
CREATE INDEX IF NOT EXISTS idx_programs_state ON programs USING GIN(serves_state);
CREATE INDEX IF NOT EXISTS idx_programs_active ON programs(is_active);
CREATE INDEX IF NOT EXISTS idx_programs_emergency ON programs(is_emergency);
CREATE INDEX IF NOT EXISTS idx_programs_confidence ON programs(confidence_score);

CREATE INDEX IF NOT EXISTS idx_eligibility_program ON eligibility_criteria(program_id);
CREATE INDEX IF NOT EXISTS idx_eligibility_type ON eligibility_criteria(criterion_type);

CREATE INDEX IF NOT EXISTS idx_income_limits_program ON income_limits(program_id);
CREATE INDEX IF NOT EXISTS idx_income_limits_size ON income_limits(household_size);

CREATE INDEX IF NOT EXISTS idx_fpl_year ON fpl_tables(year);

CREATE INDEX IF NOT EXISTS idx_providers_county ON providers(address_county);
CREATE INDEX IF NOT EXISTS idx_providers_zip ON providers(address_zip);
CREATE INDEX IF NOT EXISTS idx_providers_type ON providers(provider_type);

CREATE INDEX IF NOT EXISTS idx_raw_pages_domain ON raw_pages(domain);
CREATE INDEX IF NOT EXISTS idx_raw_pages_url ON raw_pages(url);

CREATE INDEX IF NOT EXISTS idx_translations_key ON translations(translation_key);
CREATE INDEX IF NOT EXISTS idx_translations_context ON translations(context);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Programs with complete data (high confidence)
CREATE OR REPLACE VIEW programs_complete AS
SELECT *
FROM programs
WHERE confidence_score >= 0.7
  AND eligibility_summary IS NOT NULL
  AND is_active = true;

-- Programs by category with counts
CREATE OR REPLACE VIEW programs_by_category AS
SELECT
    category,
    COUNT(*) as total_programs,
    COUNT(*) FILTER (WHERE is_emergency) as emergency_programs,
    COUNT(*) FILTER (WHERE confidence_score >= 0.7) as high_confidence,
    AVG(confidence_score) as avg_confidence
FROM programs
WHERE is_active = true
GROUP BY category
ORDER BY total_programs DESC;

-- Data completeness summary
CREATE OR REPLACE VIEW data_completeness_summary AS
SELECT
    'Total Programs' as metric,
    COUNT(*)::TEXT as value
FROM programs WHERE is_active = true
UNION ALL
SELECT
    'With Income Limits',
    COUNT(DISTINCT program_id)::TEXT
FROM income_limits
UNION ALL
SELECT
    'With Eligibility Criteria',
    COUNT(DISTINCT program_id)::TEXT
FROM eligibility_criteria
UNION ALL
SELECT
    'With Benefit Amounts',
    COUNT(*)::TEXT
FROM programs
WHERE is_active = true AND benefit_amount_min IS NOT NULL
UNION ALL
SELECT
    'With Application URL',
    COUNT(*)::TEXT
FROM programs
WHERE is_active = true AND application_url IS NOT NULL
UNION ALL
SELECT
    'High Confidence (>=0.7)',
    COUNT(*)::TEXT
FROM programs
WHERE is_active = true AND confidence_score >= 0.7;

-- =============================================================================
-- INITIAL DATA: FPL Tables (2024)
-- =============================================================================

INSERT INTO fpl_tables (year, household_size, annual_amount, monthly_amount, state)
VALUES
    (2024, 1, 15060, 1255, 'FL'),
    (2024, 2, 20440, 1703, 'FL'),
    (2024, 3, 25820, 2152, 'FL'),
    (2024, 4, 31200, 2600, 'FL'),
    (2024, 5, 36580, 3048, 'FL'),
    (2024, 6, 41960, 3497, 'FL'),
    (2024, 7, 47340, 3945, 'FL'),
    (2024, 8, 52720, 4393, 'FL')
ON CONFLICT (year, household_size, state) DO UPDATE
SET annual_amount = EXCLUDED.annual_amount,
    monthly_amount = EXCLUDED.monthly_amount;

-- =============================================================================
-- INITIAL DATA: Common Documents
-- =============================================================================

INSERT INTO documents (document_name, document_name_es, document_type, description, description_es, how_to_obtain, how_to_obtain_es, is_common)
VALUES
    ('Government-issued Photo ID', 'Identificación con foto emitida por el gobierno', 'id',
     'Driver''s license, state ID, passport, or military ID',
     'Licencia de conducir, identificación estatal, pasaporte o identificación militar',
     'Visit your local DMV or apply online at your state''s DMV website',
     'Visite su DMV local o solicite en línea en el sitio web del DMV de su estado',
     true),

    ('Social Security Card', 'Tarjeta de Seguro Social', 'id',
     'Original Social Security card for each household member',
     'Tarjeta de Seguro Social original para cada miembro del hogar',
     'Request a replacement at ssa.gov or visit your local Social Security office',
     'Solicite un reemplazo en ssa.gov o visite su oficina local del Seguro Social',
     true),

    ('Proof of Income - Pay Stubs', 'Comprobante de ingresos - Talones de pago', 'income',
     'Recent pay stubs from the last 30 days showing gross income',
     'Talones de pago recientes de los últimos 30 días que muestren el ingreso bruto',
     'Request from your employer''s HR or payroll department',
     'Solicite al departamento de recursos humanos o nómina de su empleador',
     true),

    ('Proof of Residence - Utility Bill', 'Comprobante de residencia - Factura de servicios', 'residence',
     'Recent utility bill (electric, water, gas) showing your name and address',
     'Factura de servicios reciente (electricidad, agua, gas) que muestre su nombre y dirección',
     'Use your most recent bill or request a copy from your utility provider',
     'Use su factura más reciente o solicite una copia a su proveedor de servicios',
     true),

    ('Lease or Rental Agreement', 'Contrato de arrendamiento', 'residence',
     'Current lease showing your name, address, and monthly rent amount',
     'Contrato actual que muestre su nombre, dirección y monto del alquiler mensual',
     'Request a copy from your landlord or property management company',
     'Solicite una copia a su arrendador o compañía de administración de propiedades',
     true),

    ('Birth Certificate', 'Certificado de nacimiento', 'id',
     'Official birth certificate for identity verification',
     'Certificado de nacimiento oficial para verificación de identidad',
     'Order from vitalchek.com or your state''s vital records office',
     'Ordene en vitalchek.com o en la oficina de registros vitales de su estado',
     true),

    ('Bank Statements', 'Estados de cuenta bancarios', 'financial',
     'Bank statements from the last 30-60 days showing all accounts',
     'Estados de cuenta bancarios de los últimos 30-60 días mostrando todas las cuentas',
     'Download from your bank''s website or request paper statements',
     'Descargue del sitio web de su banco o solicite estados de cuenta en papel',
     true),

    ('Proof of Immigration Status', 'Comprobante de estatus migratorio', 'legal',
     'Green card, work permit, visa, or naturalization certificate',
     'Tarjeta verde, permiso de trabajo, visa o certificado de naturalización',
     'Keep your original documents safe; contact USCIS for replacements',
     'Mantenga sus documentos originales seguros; contacte a USCIS para reemplazos',
     true)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- INITIAL DATA: UI Translations
-- =============================================================================

INSERT INTO translations (translation_key, text_en, text_es, context)
VALUES
    -- Navigation
    ('nav.home', 'Home', 'Inicio', 'ui'),
    ('nav.finder', 'Find Help', 'Encontrar Ayuda', 'ui'),
    ('nav.programs', 'All Programs', 'Todos los Programas', 'ui'),
    ('nav.calculator', 'Benefit Calculator', 'Calculadora de Beneficios', 'ui'),
    ('nav.locations', 'Service Locations', 'Ubicaciones de Servicios', 'ui'),

    -- Crisis Banner
    ('crisis.banner', 'In crisis? Call 211 (24/7) • Suicide: 988 • Emergency: 911',
     '¿En crisis? Llame al 211 (24/7) • Suicidio: 988 • Emergencia: 911', 'ui'),

    -- Finder Steps
    ('finder.title', 'Find Programs You May Qualify For', 'Encuentre Programas Para Los Que Puede Calificar', 'ui'),
    ('finder.intro', 'Answer a few questions to find assistance programs that match your situation.',
     'Responda algunas preguntas para encontrar programas de asistencia que coincidan con su situación.', 'ui'),

    ('finder.step1.title', 'Your Household', 'Su Hogar', 'ui'),
    ('finder.step1.intro', 'Let''s find help for you. First, tell me about your household...',
     'Encontremos ayuda para usted. Primero, cuénteme sobre su hogar...', 'ui'),
    ('finder.step1.who_lives', 'Who lives with you?', '¿Quién vive con usted?', 'ui'),

    ('finder.household.just_me', 'Just me', 'Solo yo', 'ui'),
    ('finder.household.partner', 'Me + partner', 'Yo + pareja', 'ui'),
    ('finder.household.children', 'Me + child(ren)', 'Yo + hijo(s)', 'ui'),
    ('finder.household.family', 'Family (4+)', 'Familia (4+)', 'ui'),

    ('finder.step2.title', 'Income', 'Ingresos', 'ui'),
    ('finder.step2.intro', 'Now let''s talk about income. This helps match you with programs you''re likely to qualify for...',
     'Ahora hablemos de ingresos. Esto ayuda a encontrar programas para los que probablemente califique...', 'ui'),

    ('finder.step3.title', 'What Help Do You Need?', '¿Qué Ayuda Necesita?', 'ui'),
    ('finder.step3.intro', 'What kind of help are you looking for? Select all that apply...',
     '¿Qué tipo de ayuda está buscando? Seleccione todo lo que aplique...', 'ui'),

    ('finder.step4.title', 'Current Situation', 'Situación Actual', 'ui'),
    ('finder.step4.intro', 'Are you facing any urgent situations right now?',
     '¿Está enfrentando alguna situación urgente en este momento?', 'ui'),

    -- Categories
    ('category.food', 'Food Assistance', 'Asistencia Alimentaria', 'category'),
    ('category.housing', 'Housing & Utilities', 'Vivienda y Servicios', 'category'),
    ('category.healthcare', 'Healthcare', 'Atención Médica', 'category'),
    ('category.financial', 'Financial Assistance', 'Asistencia Financiera', 'category'),
    ('category.childcare', 'Childcare & Family', 'Cuidado Infantil y Familia', 'category'),
    ('category.employment', 'Employment & Training', 'Empleo y Capacitación', 'category'),
    ('category.legal', 'Legal Aid', 'Asistencia Legal', 'category'),
    ('category.senior', 'Senior Services', 'Servicios para Adultos Mayores', 'category'),
    ('category.disability', 'Disability Services', 'Servicios para Discapacidades', 'category'),
    ('category.veteran', 'Veteran Services', 'Servicios para Veteranos', 'category'),
    ('category.education', 'Education', 'Educación', 'category'),
    ('category.transportation', 'Transportation', 'Transporte', 'category'),

    -- Results
    ('results.title', 'Programs You May Qualify For', 'Programas Para Los Que Puede Calificar', 'ui'),
    ('results.found', 'Found {count} programs for you', 'Se encontraron {count} programas para usted', 'ui'),
    ('results.match', '% match', '% coincidencia', 'ui'),
    ('results.view_details', 'View Details', 'Ver Detalles', 'ui'),

    -- Program Details
    ('program.overview', 'Overview', 'Descripción General', 'ui'),
    ('program.benefits', 'What You Could Receive', 'Lo Que Podría Recibir', 'ui'),
    ('program.eligibility', 'Eligibility', 'Elegibilidad', 'ui'),
    ('program.documents', 'Documents You''ll Need', 'Documentos Que Necesitará', 'ui'),
    ('program.how_to_apply', 'How to Apply', 'Cómo Aplicar', 'ui'),
    ('program.contact', 'Contact & Help', 'Contacto y Ayuda', 'ui'),
    ('program.last_verified', 'Last verified', 'Última verificación', 'ui'),

    -- Buttons
    ('button.continue', 'Continue', 'Continuar', 'ui'),
    ('button.back', 'Back', 'Atrás', 'ui'),
    ('button.start_over', 'Start Over', 'Comenzar de Nuevo', 'ui'),
    ('button.apply_online', 'Apply Online', 'Aplicar en Línea', 'ui'),
    ('button.get_directions', 'Get Directions', 'Obtener Direcciones', 'ui'),
    ('button.call_now', 'Call Now', 'Llamar Ahora', 'ui'),

    -- Footer
    ('footer.disclaimer', 'This tool provides information only. It does not submit applications or guarantee eligibility. Your information is not stored.',
     'Esta herramienta solo proporciona información. No envía solicitudes ni garantiza elegibilidad. Su información no se almacena.', 'ui'),
    ('footer.call_211', 'Need help? Call 211', '¿Necesita ayuda? Llame al 211', 'ui')

ON CONFLICT (translation_key) DO UPDATE
SET text_en = EXCLUDED.text_en,
    text_es = EXCLUDED.text_es,
    updated_at = CURRENT_TIMESTAMP;

-- =============================================================================
-- TRIGGER: Update timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_programs_updated_at ON programs;
CREATE TRIGGER update_programs_updated_at
    BEFORE UPDATE ON programs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_providers_updated_at ON providers;
CREATE TRIGGER update_providers_updated_at
    BEFORE UPDATE ON providers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
