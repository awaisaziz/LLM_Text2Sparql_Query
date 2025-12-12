import sys
import json
from gerbil_api_wrapper.gerbil import Gerbil

def main():
    if len(sys.argv) != 3:
        print("Usage: python eval_gerbil.py <gold_file_name> <test_file_name>")
        print("Example: python eval_gerbil.py qald_9_train_100 deepseek-chat_CoT")
        sys.exit(1)

    gold_name = sys.argv[1]
    test_name = sys.argv[2]

    # Assume both are JSON files located in the "executed" folder
    gold_file = f"executed/{gold_name}_executed.json"
    test_file = f"executed/{test_name}_executed.json"

    print(f"Gold file: {gold_file}")
    print(f"Test file: {test_file}")

    wrapper = Gerbil(
        gold_standard_file=gold_file,
        test_results_file=test_file,
        test_results_name=test_name,
        gold_standard_name=gold_name,
        language="en",
    )

    results = wrapper.get_results()
    
    path = f"gerbil_result/{test_name}_result.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {path}")
    print(f"GERBIL Results URL: {wrapper.get_results_url()}")

if __name__ == "__main__":
    main()

