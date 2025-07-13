import json

# Load the original data
with open('data.json', 'r') as f:
    data = json.load(f)

# Only keep objects from your app, change this to match your app name
APP_NAME = 'pet_adoption_and_care'

filtered_data = [entry for entry in data if entry['model'].startswith(APP_NAME)]

# Save the cleaned version
with open('cleaned_data.json', 'w') as f:
    json.dump(filtered_data, f, indent=2)

print(f"✅ Done. Original: {len(data)} entries → Cleaned: {len(filtered_data)} entries.")
