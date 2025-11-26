# Community Assist

A bilingual (English/Spanish), mobile-first web application that helps people discover, understand, and self-qualify for social services and assistance programs.

## Overview

Community Assist aggregates program data from multiple sources (211 databases, government websites, local nonprofits), extracts structured eligibility criteria, and presents users with personalized program matches through an intuitive, conversational-style questionnaire.

**Key Features:**
- 🔍 **Smart Program Finder** - Guided questionnaire to match users with relevant programs
- 📋 **Program Database** - Comprehensive listings with eligibility, benefits, and how to apply
- 🧮 **Benefit Calculator** - Estimate SNAP, Medicaid, and other program benefits
- 📍 **Service Locator** - Find nearby providers and offices
- 🌐 **Bilingual Support** - Full English and Spanish translations
- 📱 **Mobile-First Design** - Optimized for phone users

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Docker (optional, for local development)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thingvallatech/community-assist.git
   cd community-assist
   ```

2. **Set up environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start PostgreSQL with Docker:**
   ```bash
   docker-compose up -d postgres
   ```

4. **Initialize the database:**
   ```bash
   psql $DATABASE_URL < src/database/init_db.sql
   ```

5. **Run the web application:**
   ```bash
   flask --app webapp.app run --debug
   ```

6. **Visit** http://localhost:5000

### Using Docker Compose

```bash
# Start everything (database + web app)
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop
docker-compose down
```

## Project Structure

```
community-assist/
├── src/                    # Backend/scraping code
│   ├── scrapers/          # Data collection from various sources
│   ├── parsers/           # Eligibility and benefit parsing
│   ├── database/          # Database schema and connections
│   └── config.py          # Configuration management
├── webapp/                 # Flask web application
│   ├── app.py             # Main application
│   ├── templates/         # Jinja2 templates
│   └── static/            # CSS, JS, images
├── translations/          # i18n files (en.json, es.json)
├── data/                  # Scraped data, PDFs
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── .do/                   # Digital Ocean deployment config
```

## Configuration

Key environment variables (see `.env.example` for all options):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | Flask secret key | Required in production |
| `DEFAULT_LANGUAGE` | Default UI language | `en` |
| `TARGET_STATE` | Target state for programs | `FL` |
| `TARGET_COUNTY` | Target county for programs | `Brevard` |
| `ENABLE_CALCULATOR` | Enable benefit calculator | `true` |
| `ENABLE_LOCATOR` | Enable service locator | `true` |

## Data Sources

The platform collects data from:
- **211 Services** - Local 211 databases and websites
- **Benefits.gov** - Federal benefit program database
- **Florida DCF** - SNAP, Medicaid, TANF information
- **HUD** - Housing assistance programs
- **Local Nonprofits** - Community organizations

## Deployment

### Digital Ocean App Platform

1. Fork this repository
2. Create a new App in Digital Ocean
3. Connect your GitHub repository
4. The `.do/app.yaml` configuration will be detected automatically
5. Set the required environment variables (SECRET_KEY)
6. Deploy!

### Manual Deployment

```bash
# Build the Docker image
docker build -t community-assist -f Dockerfile.web .

# Run with environment variables
docker run -p 8080:8080 \
  -e DATABASE_URL=your_db_url \
  -e SECRET_KEY=your_secret \
  community-assist
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Include Spanish translations for any user-facing text
4. Add tests for new functionality
5. Submit a pull request

## Privacy

**We do not store personal information.** User responses during the program finder are:
- Stored only in browser cookies
- Never sent to external services
- Used only to calculate program matches
- Automatically expire after 7 days

## License

[MIT License](LICENSE)

## Support

- **Need help using the app?** Call 211 (available 24/7)
- **Found a bug?** Open an issue on GitHub
- **Want to contribute?** See CONTRIBUTING.md

---

Built with ❤️ to help people access the resources they need.
