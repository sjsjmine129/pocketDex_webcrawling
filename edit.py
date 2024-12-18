import json

# Load the existing JSON data
file_path = 'cardsData.json'
with open(file_path, 'r') as file:
    data = json.load(file)

# Add the "image" field to each card based on the id
for card in data:
    print(card)
    card['image'] = f"assets/CardImages/{card['id']}.png"

# Save the modified data back to the file (or a new file)
output_file_path = 'cardData_en.json'
with open(output_file_path, 'w') as output_file:
    json.dump(data, output_file, indent=4)

print(f"Updated file saved as {output_file_path}")
