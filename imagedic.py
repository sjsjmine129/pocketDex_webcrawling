# Python code to generate a JavaScript file with the specified format

def generate_js_file(start_num, end_num, output_file="imageMap.js"):
    # Open the file to write JavaScript content
    with open(output_file, "w", encoding="utf-8") as file:
        # Write the opening of the object
        file.write("const imageMap = {\n")

        # Iterate through the range of numbers and generate the lines
        for num in range(start_num, end_num + 1):
            # Use the same number for image_id
            image_id = num
            # Write each line to the file
            file.write(f"  {num}: require('assets/CardImages/{image_id}.webp'),\n")

        # Close the object
        file.write("};\n\nexport default imageMap;\n")

    print(f"JavaScript file '{output_file}' has been generated successfully.")

# Example usage
if __name__ == "__main__":
    # Input the start and end numbers from the user
    start = int(input("Enter the start number: "))
    end = int(input("Enter the end number: "))

    # Call the function to generate the JavaScript file
    generate_js_file(start, end)