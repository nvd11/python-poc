import asyncio
import os
import aiofiles
from aiocsv import AsyncReader
import asyncpg
import time

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

# --- Classic Async Iterator Class ---
class AsyncCSVIterator:
    """A classic, reusable async iterator to read a CSV file."""
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self._file = None
        self._reader = None
        self.header = None

    async def _initialize(self):
        """Private helper to ensure the file is opened and reader is ready."""
        if self._file is None:
            self._file = await aiofiles.open(self.csv_path, mode='r', encoding='utf-8-sig', newline='')
            self._reader = AsyncReader(self._file)
            self.header = await self._reader.__anext__()

    async def __aiter__(self):
        await self._initialize()
        return self

    async def __anext__(self):
        # Ensure the reader is initialized before trying to read from it.
        if self._reader is None:
            await self._initialize()
            
        try:
            row = await self._reader.__anext__()
            return dict(zip(self.header, row))
        except StopAsyncIteration:
            if self._file:
                await self._file.close()
            raise

# --- Main Container and Task Runner Class ---
class CSV2PG:
    """
    A versatile class that is both an ASYNC ITERABLE for row-by-row processing
    and a TASK RUNNER for serial row-by-row inserts on a single connection.
    """
    def __init__(self, csv_path, db_user, db_password, db_host, db_port, db_name, db_table):
        self.csv_path = csv_path
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_table = db_table

    def __aiter__(self):
        """Makes CSV2PG instances async iterable by returning a new, independent iterator."""
        print("--- Called __aiter__: Returning a new AsyncCSVIterator instance. ---")
        return AsyncCSVIterator(self.csv_path)

    async def stream_to_pg_serially(self):
        """
        Connects to the DB and performs serial row-by-row inserts on a single connection.
        This is NOT performant, but correctly demonstrates async iteration.
        """
        start_time = time.time()
        connection = None
        total_inserted = 0
        total_failed = 0

        try:
            connection = await asyncpg.connect(
                user=self.db_user, password=self.db_password, host=self.db_host,
                port=self.db_port, database=self.db_name
            )
            print(f"Single connection to PostgreSQL at {self.db_host} established.")
            
            stmt = await connection.prepare(f"""
                INSERT INTO {self.db_table} (Column_1, Column_2, Column_3, Column_4, Column_5, Column_6, Column_7, Column_8, Column_9, Column_10)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (Column_1) DO NOTHING;
            """)
            print("Prepared statement created. Starting serial insertion...")

            i = 0
            async for row in self:
                i += 1
                try:
                    # Using .fetchval() is a correct way to execute a prepared statement
                    # when we don't expect any rows in return. It's lightweight.
                    await stmt.fetchval(
                        row['Column_1'], row['Column_2'], row['Column_3'], row['Column_4'],
                        row['Column_5'], row['Column_6'], row['Column_7'], row['Column_8'],
                        row['Column_9'], row['Column_10']
                    )
                    total_inserted += 1
                except Exception as e:
                    print(f"Error inserting row {row.get('Column_1', 'N/A')}: {e}")
                    total_failed += 1
                
                if i % 20 == 0:
                    elapsed_time = time.time() - start_time
                    print(f"Processed {i} rows in {elapsed_time:.2f}s")

        except Exception as e:
            print(f"A critical error occurred: {e}")
        finally:
            if connection:
                await connection.close()
                print("Connection closed.")

        end_time = time.time()
        print("\n--- Serial Insert Summary ---")
        print(f"Total rows successfully inserted: {total_inserted}")
        print(f"Total rows failed: {total_failed}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds.")
        print("-----------------------------")

async def main():
    """
    Main function to demonstrate both functionalities of the CSV2PG class.
    """
    streamer = CSV2PG(
        csv_path=CSV_FILE_PATH,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_name=DB_NAME,
        db_table=DB_TABLE
    )
    
    # --- Demonstration 1: Using the class as an async iterator ---
    print("--- DEMO 1: Using the class as an async iterator ---")
    count = 0
    async for row in streamer:
        if count < 5:
            print(row)
            count += 1
        else:
            break
    print("-" * 50)

    # --- Demonstration 2: Using the class for serial row-by-row insert ---
    print("--- DEMO 2: Using the class for serial row-by-row insert ---")
    await streamer.stream_to_pg_serially()


if __name__ == '__main__':
    asyncio.run(main())
