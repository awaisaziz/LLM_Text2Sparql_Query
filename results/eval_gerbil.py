from gerbil_api_wrapper.gerbil import Gerbil
import json

# Paths to your converted JSON files
gold_file = "executed/qald_9_train_100_executed.json"
test_file = "executed/predicted_zero_shot.json"
# test_file = "pred_qald.json"

wrapper = Gerbil(
    gold_standard_file=gold_file,
    test_results_file=test_file,
    test_results_name="MyRun",
    gold_standard_name="MyGold",
    language="en"
)

print("Results URL:", wrapper.get_results_url())

results = wrapper.get_results()
path = "gerbil_result/zero_shot_100_result.json"

with open(path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
