import csv
import os
from google.cloud import bigquery

def stream_csv_to_bq(project_id, dataset_id, table_id, file_path):
    """
    Reads a CSV file and streams the data to a BigQuery table.

    This function reads the CSV row by row and inserts the data in batches.

    Args:
        project_id (str): Your Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.
        table_id (str): The BigQuery table ID.
        file_path (str): The path to the CSV file.
    """
    client = bigquery.Client(project=project_id)
    table_ref = client.dataset(dataset_id).table(table_id)

    try:
        # Check if the table exists.
        table = client.get_table(table_ref)
        print(f"Streaming data to table {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e:
        print(f"Table {project_id}.{dataset_id}.{table_id} not found. Please ensure the table exists and the schema matches the CSV headers.")
        print(f"Error: {e}")
        return

    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Get headers from the first row

        # Define an inner generator function to act as the iterator
        def row_iterator():
            for row in reader:
                yield dict(zip(headers, row))

        batch_size = 1000
        rows_to_insert = []
        for row_dict in row_iterator():
            rows_to_insert.append(row_dict)
            if len(rows_to_insert) == batch_size:
                errors = client.insert_rows_json(table, rows_to_insert)
                if not errors:
                    print(f"Successfully inserted {len(rows_to_insert)} rows.")
                else:
                    print(f"Encountered errors while inserting rows: {errors}")
                rows_to_insert = [] # Reset the batch

        # Insert any remaining rows
        if rows_to_insert:
            errors = client.insert_rows_json(table, rows_to_insert)
            if not errors:
                print(f"Successfully inserted {len(rows_to_insert)} rows.")
            else:
                print(f"Encountered errors while inserting rows: {errors}")

    print(f"Finished streaming data from {file_path} to {project_id}.{dataset_id}.{table_id}")

if __name__ == "__main__":
    # --- PLEASE PROVIDE YOUR BIGQUERY DETAILS ---
    PROJECT_ID = "your-gcp-project-id"
    DATASET_ID = "your-dataset-id"
    TABLE_ID = "your-table-id"
    # -----------------------------------------

    FILE_PATH = "data/large_data.csv"

    if PROJECT_ID == "your-gcp-project-id" or DATASET_ID == "your-dataset-id" or TABLE_ID == "your-table-id":
        print("Please update the script `src/upload_to_bq.py` with your BigQuery project, dataset, and table IDs before running.")
    else:
        stream_csv_to_bq(PROJECT_ID, DATASET_ID, TABLE_ID, FILE_PATH)
