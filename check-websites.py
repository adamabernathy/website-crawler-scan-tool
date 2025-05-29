import csv
import argparse
import json
from does_my_website_require_js_to_run import CheckWebsiteRendering
from does_my_website_require_js_to_run import Helpers
from time import sleep



def csv_to_json(csv_filepath, json_filepath):
    """
    Converts a CSV file to a JSON file.

    Args:
        csv_filepath (str): The path to the CSV file.
        json_filepath (str): The path to the output JSON file.
    """
    data = []
    with open(csv_filepath, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            data.append(row)

    with open(json_filepath, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)


def csv_to_dict(csv_filename):
    data = []
    with open(csv_filename, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            data.append(row)
    
    return data

def write_row(filename, fieldnames, row):
    with open(filename, "a", newline="\n") as file:  # Append
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(row)

def write_header(filename, fieldnames):
    with open(filename, "w", newline="\n") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Is website bot friendly?")

    parser.add_argument("--input", "-i", dest="input_filename", help="Input filename; CSV Format")
    parser.add_argument("--output", "-o", dest="output_filename", help="Output filename; CSV Format")

    parser.add_argument("--url-column", dest="url", help="Column Name with URL")
    parser.add_argument("--biz-id-column", dest="business_id", help="Column Name with Business ID")
    parser.add_argument("--site-id-column", dest="site_id", help="Column Name with Site ID")

    args = parser.parse_args()

    input_data = csv_to_dict(args.input_filename)

    checker = CheckWebsiteRendering(verbose=True, quiet=False)


    output_report_field_names = [
        "business_id", "site_id", "url", "n_h1_disabled", 
        "n_h2_disabled", "schema", "js_required", "completion_check",
    ]

    write_header(args.output_filename, output_report_field_names)

    results = []
    for count, row in enumerate(input_data):
        print(f"{count} -- {row[args.business_id]} - {row[args.site_id]} -- {row[args.url]}")

        result = checker.compare_runs(
            f"https://{row[args.url]}",
            tags={
                "business_id": row[args.business_id],
                "site_id": row[args.site_id],
            }
        )
        results.append(result)

        formatted_results = {
            "business_id": result["tags"]["business_id"],
            "site_id": result["tags"]["site_id"],
            "url": result["url"],
            "n_h1_disabled": len(result["js_disabled"].get("h1", [])),
            "n_h2_disabled": len(result["js_disabled"].get("h2", [])),
            "schema": result["js_disabled"].get("schema", {}).get("found", False),
            "js_required": result["js_required"],
            "completion_check": result["completion_check"],
        }
    
        write_row(args.output_filename, output_report_field_names, formatted_results)

        if count % 5 == 0: sleep(1)  # cool off

        if count > 15: break
    
    print("😎 Done!")
