import os

import psycopg

conn = psycopg.connect(os.environ["DATABASE_URL"])
