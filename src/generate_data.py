import csv
import os
import random
import string

def generate_random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def generate_csv_data(file_path, num_records, num_columns):
    """Generate a CSV file with random data."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    headers = [f'Column_{i+1}' for i in range(num_columns)]
    
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for _ in range(num_records):
            row = [generate_random_string() for _ in range(num_columns)]
            writer.writerow(row)
            
    print(f"Successfully generated {file_path} with {num_records} records and {num_columns} columns.")

if __name__ == "__main__":
    DATA_DIR = "data"
    FILE_NAME = "large_data.csv"
    FILE_PATH = os.path.join(DATA_DIR, FILE_NAME)
    NUM_RECORDS = 100000
    NUM_COLUMNS = 10
    
    generate_csv_data(FILE_PATH, NUM_RECORDS, NUM_COLUMNS)
