import joblib

bundle = joblib.load("models/fraud_xgb_v3.joblib")
pipeline = bundle["pipeline"]
print(pipeline)
print()

for name, step in pipeline.named_steps.items():
    print(name, "->", step)
    if hasattr(step, "transformers_"):
        for tname, transformer, cols in step.transformers_:
            print("  ", tname, cols)
            if hasattr(transformer, "categories_"):
                print("     categories:", transformer.categories_)