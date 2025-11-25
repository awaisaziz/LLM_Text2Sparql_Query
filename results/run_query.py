import json
import time
from tqdm import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON

DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"


def run_sparql_query(endpoint_url: str, query: str):
    """
    Execute SPARQL query and return JSON results.
    """
    try:
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()
    except Exception as e:
        print(f"\nSPARQL Error: {e}")
        return {"results": {"bindings": []}, "head": {"vars": []}}


def normalize_multi_bindings(bindings, var_map):
    normalized = []

    for row in bindings:
        new_row = {}
        for orig, new in var_map.items():
            if orig in row:
                new_row[new] = row[orig]
        normalized.append(new_row)

    return normalized


def build_canonical_var_map(head_vars):
    canonical = {}
    for i, var in enumerate(head_vars):
        canonical[var] = "x" if i == 0 else f"x{i+1}"
    return canonical


def extract_en_question(question_list):
    """
    Extract only the English question.
    """
    for q in question_list:
        if q.get("language") == "en":
            return [{"language": "en", "string": q["string"]}]
    return []


def process_dataset(input_path: str, output_path: str = "output.json"):
    """
    Main function (includes tqdm progress bar + 5-second delay).
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = []

    print("\n⚡ Processing dataset with SPARQL queries...\n")

    # for item in tqdm(data, desc="Progress", unit="item"):
    for idx, item in enumerate(tqdm(data, desc="Progress", unit="item")):
        item_id = item.get("id")
        
        # TAKE ENGLISH QUESTION FROM "en_ques"
        question_en = [
            {
                "language": "en",
                "string": item.get("en_ques", "").strip()
            }
        ]

        # TAKE SPARQL FROM "sparql"
        sparql_query = item.get("sparql", "").strip()

        # Execute query
        result = run_sparql_query(DBPEDIA_ENDPOINT, sparql_query)

        # Extract answers
        head_vars = result.get("head", {}).get("vars", [])
        bindings = result.get("results", {}).get("bindings", [])

        # Build mapping: uri→x, label→x2, name→x3
        # Normalize: replace orig vars by "x", "x2", ...
        # var_map = build_canonical_var_map(head_vars)
        # bindings = normalize_multi_bindings(bindings, var_map)
        
        # Canonical vars for final output
        # canonical_vars = list(var_map.values())

        processed_item = {
            "id": item_id,
            "question": question_en,
            "query": {"sparql": sparql_query},
            "answers": [
                {
                    "head": {"vars": head_vars},
                    # "head": {"vars": canonical_vars},
                    "results": {"bindings": bindings}
                }
            ]
        }
        
        print(f"\nProcessed item: {processed_item}\n")

        processed.append(processed_item)

        # Sleep after every 20 queries
        if (idx + 1) % 20 == 0:
            print("⏳ Pausing for 5 seconds to avoid rate-limit...")
            time.sleep(5)

    # Save output JSON
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump({"questions": processed}, out, indent=4, ensure_ascii=False)

    print(f"\n🎉 Done! Processed dataset saved to: {output_path}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filter EN questions + execute SPARQL")
    parser.add_argument("--input", required=True, help="Path to input JSON dataset")
    parser.add_argument("--output", default="output.json", help="Path to save output JSON")

    args = parser.parse_args()

    process_dataset(args.input, args.output)
