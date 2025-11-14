import os
import csv
import time
import asyncio
import aiofiles
from aiocsv import AsyncReader
from google.cloud import bigquery

# This is the custom, "classic" asynchronous iterator class.
class AsyncCSVIterator:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self._file = None
        self._reader = None
        self.header = None

    async def _init_reader(self):
        """Asynchronously opens the file and initializes the reader."""
        if self._file is None:
            self._file = await aiofiles.open(self.csv_path, mode='r', encoding='utf-8', newline='')
            self._reader = AsyncReader(self._file)
            self.header = await self._reader.__anext__()

    async def __aiter__(self):
        """Returns itself, as it's an async iterator."""
        await self._init_reader()
        return self

    async def __anext__(self):
        """Returns the next row from the CSV asynchronously."""
        if self._reader is None:
            await self._init_reader()
        
        try:
            row = await self._reader.__anext__()
            return dict(zip(self.header, row))
        except StopAsyncIteration:
            # When the reader is exhausted, clean up and re-raise.
            if self._file:
                await self._file.close()
            raise

class AsyncCSV2BQ:
    """
    An asynchronous version of CSV2BQ that uses a classic async iterator class.
    """

    def __init__(self, csv_path: str, bq_table_id: str, proxy: str = None):
        if proxy:
            os.environ['HTTPS_PROXY'] = f'http://{proxy}'
            print(f"Using proxy: {os.environ['HTTPS_PROXY']}")

        self.csv_path = csv_path
        self.bq_table_id = bq_table_id
        self.bq_client = bigquery.Client()

    def __aiter__(self):
        """Returns a new instance of our custom async iterator class."""
        return AsyncCSVIterator(self.csv_path)

    async def stream_to_bq(self):
        total_rows_streamed = 0
        total_rows_with_errors = 0
        start_time = time.time()
        loop = asyncio.get_running_loop()

        print(f"Starting to stream data to {self.bq_table_id} one row at a time (asynchronously)...")

        i = 0
        async for row in self:
            try:
                errors = await loop.run_in_executor(
                    None, self.bq_client.insert_rows_json, self.bq_table_id, [row]
                )
                
                if not errors:
                    total_rows_streamed += 1
                else:
                    print(f"Encountered error on row {i+1}: {errors}")
                    total_rows_with_errors += 1

            except Exception as e:
                print(f"An unexpected error occurred on row {i+1}: {e}")
                total_rows_with_errors += 1
            
            i += 1
            if i % 10 == 0:
                elapsed_time = time.time() - start_time
                print(f"Processed {i} rows in {elapsed_time:.2f} seconds...")

        end_time = time.time()
        
        print("\n--- Streaming Summary ---")
        print(f"Total rows successfully streamed: {total_rows_streamed}")
        print(f"Total rows with insertion errors: {total_rows_with_errors}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds.")
        print("--------------------------")

async def main():
    CSV_FILE_PATH = 'data/small_data_200.csv'
    BQ_TABLE_ID = "jason-hsbc.DS1.test_table1"
    PROXY_ADDRESS = "10.0.1.223:7890"
    
    async_csv_to_bq = AsyncCSV2BQ(
        csv_path=CSV_FILE_PATH, 
        bq_table_id=BQ_TABLE_ID, 
        proxy=PROXY_ADDRESS
    )
    
    await async_csv_to_bq.stream_to_bq()

if __name__ == '__main__':
    # To run this script, you might need to install aiofiles and aiocsv:
    # pip install aiofiles aiocsv
    asyncio.run(main())
