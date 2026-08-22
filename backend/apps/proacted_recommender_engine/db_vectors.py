# python_scripts/db_vectors.py
from typing import List, Dict, Any
from django.conf import settings
import psycopg2  # or use Django ORM if preferred

def get_all_course_vectors() -> List[Dict[str, Any]]:
    """
    Fetch ALL courses with their pre-computed embeddings from PostgreSQL (pgvector).
    Returns list of rich dictionaries.
    """
    conn_params = {
        "dbname": settings.DATABASES['default']['NAME'],
        "user": settings.DATABASES['default']['USER'],
        "password": settings.DATABASES['default']['PASSWORD'],
        "host": settings.DATABASES['default']['HOST'],
        "port": settings.DATABASES['default']['PORT'],
    }

    query = """
    SELECT 
        id AS course_id,
        program_name,
        cluster_number,
        level,                    -- degree/diploma/certificate/artisan
        institution_name,
        institution_type,         -- public/private
        location,
        cutoff_2024,
        cutoff_2023,
        cutoff_2022,
        approx_annual_fees_ksh,
        embedding_vector          -- pgvector column
    FROM courses
    WHERE embedding_vector IS NOT NULL
    ORDER BY id;
    """

    courses = []

    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                for row in rows:
                    courses.append({
                        "course_id": row[0],
                        "program_name": row[1],
                        "cluster": row[2],               # int for degree, str/int for others
                        "level": row[3],
                        "institution": row[4],
                        "institution_type": row[5],
                        "location": row[6],
                        "prev_cutoff_2024": float(row[7]) if row[7] else None,
                        "prev_cutoff_2023": float(row[8]) if row[8] else None,
                        "prev_cutoff_2022": float(row[9]) if row[9] else None,
                        "approx_fees_annual": int(row[10]) if row[10] else None,
                        "vector": list(row[11])          # pgvector → list[float]
                    })

        return courses

    except Exception as e:
        raise RuntimeError(f"Failed to load course vectors: {str(e)}")