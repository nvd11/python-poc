import os
import csv
import time
from google.cloud import bigquery

# This is the custom, "classic" iterator class.
class CSVIterator:
    """
    A classic iterator class that reads a CSV file row by row.
    It maintains its own state (file handle, reader position).
    """
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.file_handler = open(self.csv_path, 'r', encoding='utf-8')
        self.reader = csv.reader(self.file_handler)  # Returns an iterator to read row by row, not all content at once
        self.header = next(self.reader) # Read the header row upon initialization

    def __iter__(self):
        # An iterator's __iter__ method should always return itself.
        return self

    def __next__(self):
        """
        Returns the next row from the CSV as a dictionary.
        Raises StopIteration when the file is exhausted.
        """
        try:
            # Read the next row from the csv reader
            row = next(self.reader)
            # Combine header and row into a dictionary
            return dict(zip(self.header, row))
        except StopIteration:
            # When the reader is exhausted, it raises StopIteration.
            # We catch it, close the file to clean up resources, and then re-raise it
            # to signal the end of iteration to the for loop.
            self.file_handler.close()
            raise

class CSV2BQ:
    """
    Reads data from a CSV file and streams it to a BigQuery table.
    This version uses a classic, custom iterator class instead of a generator.
    """

    def __init__(self, csv_path: str, bq_table_id: str, proxy: str = None):
        """
        Initializes the CSV2BQ class (the iterable object).
        """
        if proxy:
            os.environ['HTTPS_PROXY'] = f'http://{proxy}'
            print(f"Using proxy: {os.environ['HTTPS_PROXY']}")

        self.csv_path = csv_path
        self.bq_table_id = bq_table_id
        self.bq_client = bigquery.Client()

    def __iter__(self):
        """
        This makes the CSV2BQ class iterable.
        It returns a new instance of our custom iterator class.
        """
        return CSVIterator(self.csv_path)

    def stream_to_bq(self):
        """
        Streams the data from the CSV file to the BigQuery table, one row at a time.
        """
        total_rows_streamed = 0
        total_rows_with_errors = 0
        start_time = time.time()

        print(f"Starting to stream data to {self.bq_table_id} one row at a time...")

        # The `for` loop implicitly calls `__iter__` on `self`, which returns our CSVIterator instance.
        # The loop then repeatedly calls `__next__` on that instance.
        for i, row in enumerate(self):
            errors = self.bq_client.insert_rows_json(self.bq_table_id, [row])
            
            if not errors:
                total_rows_streamed += 1
            else:
                print(f"Encountered error on row {i+1}: {errors}")
                total_rows_with_errors += 1
            
            if (i + 1) % 10 == 0:
                elapsed_time = time.time() - start_time
                print(f"Processed {i + 1} rows in {elapsed_time:.2f} seconds...")

        end_time = time.time()
        
        print("\n--- Streaming Summary ---")
        print(f"Total rows successfully streamed: {total_rows_streamed}")
        print(f"Total rows with insertion errors: {total_rows_with_errors}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds.")
        print("--------------------------")

# Example Usage:
if __name__ == '__main__':
    CSV_FILE_PATH = 'data/small_data_200.csv' # Use the new smaller file
    BQ_TABLE_ID = "jason-hsbc.DS1.test_table1"
    PROXY_ADDRESS = "10.0.1.223:7890"
    
    csv_to_bq_iterable = CSV2BQ(
        csv_path=CSV_FILE_PATH, 
        bq_table_id=BQ_TABLE_ID, 
        proxy=PROXY_ADDRESS
    )
    
    # Run the full streaming process for the test.
    csv_to_bq_iterable.stream_to_bq()
