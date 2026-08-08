from datasets import load_dataset

dataset = load_dataset("HuggingFaceH4/MATH-500", split="test")

print("Total problems:", len(dataset))
print("\n--- Example 1 ---")
print(dataset[0])
print("\n--- Example 2 ---")
print(dataset[1])