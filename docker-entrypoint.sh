#!/bin/bash
set -e

echo "Starting Community Assist..."

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    for i in {1..30}; do
        if python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; then
            echo "Database is ready!"
            break
        fi
        echo "Waiting for database... ($i/30)"
        sleep 2
    done
fi

# Import SQL dump if provided (for initial data seeding)
if [ -n "$SQL_DUMP_URL" ]; then
    echo "Checking for SQL dump import..."
    python -c "
import os
import urllib.request
import psycopg2

db_url = os.environ.get('DATABASE_URL')
sql_url = os.environ.get('SQL_DUMP_URL')

if db_url and sql_url:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Check if data already exists
    cur.execute('SELECT COUNT(*) FROM programs')
    count = cur.fetchone()[0]

    if count == 0:
        print(f'Importing data from {sql_url}...')
        try:
            response = urllib.request.urlopen(sql_url)
            sql_content = response.read().decode('utf-8')

            # Execute SQL statements
            for statement in sql_content.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cur.execute(statement)
                    except Exception as e:
                        print(f'Warning: {e}')

            conn.commit()
            print('Data import complete!')
        except Exception as e:
            print(f'Error importing data: {e}')
    else:
        print(f'Database already has {count} programs, skipping import.')

    cur.close()
    conn.close()
"
fi

# Execute the main command
exec "$@"
