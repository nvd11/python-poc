import os
import csv
import time
import psycopg2

# --- Database Configuration ---
DB_USER = 'nvd11'
# 从环境变量读取, 禁止硬编码; 运行前 export DB_PASSWORD=...
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = '34.39.2.90'
DB_PORT = 5432
DB_NAME = 'default_db'
DB_TABLE = 'test_table1'

# --- File Configuration ---
CSV_FILE_PATH = 'data/small_data_200.csv'

# --- Classic Sync Iterator Class ---
class CSVIterator:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.file_handler = open(self.csv_path, 'r', encoding='utf-8-sig')
        self.reader = csv.reader(self.file_handler)
        self.header = next(self.reader)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            row = next(self.reader)
            return dict(zip(self.header, row))
        except StopIteration:
            self.file_handler.close()
            raise

# --- Main Container and Task Runner Class (Sync Version) ---
class CSV2PG_Sync:
    def __init__(self, csv_path, db_user, db_password, db_host, db_port, db_name, db_table):
        self.csv_path = csv_path
        self.db_conn_info = f"dbname='{db_name}' user='{db_user}' host='{db_host}' port='{db_port}' password='{db_password}'"

    def __iter__(self):
        return CSVIterator(self.csv_path)

    def stream_to_pg_sync(self):
        start_time = time.time()
        connection = None
        total_inserted = 0
        total_failed = 0

        try:
            connection = psycopg2.connect(self.db_conn_info)
            cursor = connection.cursor()
            print(f"Sync connection to PostgreSQL at {DB_HOST} established.")
            
            sql_insert = f"""
                INSERT INTO {DB_TABLE} (Column_1, Column_2, Column_3, Column_4, Column_5, Column_6, Column_7, Column_8, Column_9, Column_10)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (Column_1) DO NOTHING;
            """
            
            print("Starting synchronous row-by-row insertion...")
            for i, row in enumerate(self):
                try:
                    values = (
                        row['Column_1'], row['Column_2'], row['Column_3'], row['Column_4'],
                        row['Column_5'], row['Column_6'], row['Column_7'], row['Column_8'],
                        row['Column_9'], row['Column_10']
                    )
                    cursor.execute(sql_insert, values)
                    total_inserted += 1
                except Exception as e:
                    print(f"Error inserting row {row.get('Column_1', 'N/A')}: {e}")
                    total_failed += 1
                
                if (i + 1) % 20 == 0:
                    elapsed_time = time.time() - start_time
                    print(f"Processed {i + 1} rows in {elapsed_time:.2f}s")
            
            connection.commit() # Commit all the successful inserts

        except Exception as e:
            if connection:
                connection.rollback()
            print(f"A critical error occurred: {e}")
        finally:
            if connection:
                connection.close()
                print("Connection closed.")

        end_time = time.time()
        print("\n--- Sync Insert Summary ---")
        print(f"Total rows successfully inserted: {total_inserted}")
        print(f"Total rows failed: {total_failed}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds.")
        print("---------------------------")

def main():
    streamer = CSV2PG_Sync(
        csv_path=CSV_FILE_PATH,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
        db_table=DB_TABLE
    )
    streamer.stream_to_pg_sync()

if __name__ == '__main__':
    main()
