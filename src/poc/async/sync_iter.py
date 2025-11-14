import os
import csv
import time
from google.cloud import bigquery

class CSV2BQ:
    """
    Reads data from a CSV file and streams it to a BigQuery table.
    """

    def __init__(self, csv_path: str, bq_table_id: str, proxy: str = None):
        """
        Initializes the CSV2BQ class.

        Args:
            csv_path (str): The path to the CSV file.
            bq_table_id (str): The BigQuery table ID in the format 'project.dataset.table'.
            proxy (str, optional): Proxy address in the format 'host:port'. Defaults to None.
        """
        if proxy:
            # Set the proxy for the Google Cloud client libraries
            os.environ['HTTPS_PROXY'] = f'http://{proxy}'
            print(f"Using proxy: {os.environ['HTTPS_PROXY']}")

        self.csv_path = csv_path
        self.bq_table_id = bq_table_id
        self.bq_client = bigquery.Client()

    def __iter__(self):
        """
        An iterator that reads the CSV file row by row.
        """
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)  # Returns an iterator to read row by row, not all content at once
            header = next(reader)  # Skip header. Equivalent to reader.__next__()
            for row in reader:
                # zip() returns a zip object, which is an iterator.
                # This iterator doesn't create all pairs at once. Instead, it generates
                # one tuple at a time upon request. For example:
                # 1. It pairs the first element from 'header' and 'row', e.g., ('id', '101').
                # 2. On the next request, it pairs the second elements, e.g., ('name', 'product_a').
                # This continues until one of the lists is exhausted.
                # The dict() function then consumes the entire zip iterator to build a dictionary.
                yield dict(zip(header, row))

    def stream_to_bq(self):
        """
        Streams the data from the CSV file to the BigQuery table, one row at a time.
        This is memory-efficient but will be very slow due to one API call per row.
        """
        total_rows_streamed = 0
        total_rows_with_errors = 0
        start_time = time.time()

        print(f"Starting to stream data to {self.bq_table_id} one row at a time...")

        # The `for` loop implicitly calls the `__iter__()` method on the `self` object.
        # This is part of Python's iteration protocol. `__iter__()` returns an iterator
        # (the generator defined in our `__iter__` method), which the loop then uses.
        #
        # enumerate(self) wraps the iterator and returns an enumerate object.
        # During iteration, it yields a tuple containing:
        # 1. A counter 'i' (starting from 0).
        # 2. The original value 'row' from the iterator.
        # This allows us to get both the row data and its index simultaneously.
        for i, row in enumerate(self):
            # The `insert_rows_json` method requires a list of rows for its second argument.
            # Since we are inserting only one row at a time in this loop, we wrap the
            # single 'row' dictionary in a list `[row]` to meet the method's format requirement.
            errors = self.bq_client.insert_rows_json(self.bq_table_id, [row])
            
            if not errors:
                total_rows_streamed += 1
            else:
                print(f"Encountered error on row {i+1}: {errors}")
                total_rows_with_errors += 1
            
            if (i + 1) % 1000 == 0:
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
    # IMPORTANT: Before running, make sure you have authenticated with Google Cloud CLI:
    # `gcloud auth application-default login`
    # And that you have created the dataset and table in BigQuery.
    
    CSV_FILE_PATH = 'data/large_data.csv'
    BQ_TABLE_ID = "jason-hsbc.DS1.test_table1"
    PROXY_ADDRESS = "10.0.1.223:7890"
    
    csv_to_bq_streamer = CSV2BQ(
        csv_path=CSV_FILE_PATH, 
        bq_table_id=BQ_TABLE_ID, 
        proxy=PROXY_ADDRESS
    )
    csv_to_bq_streamer.stream_to_bq()
