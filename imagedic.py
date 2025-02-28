import re

# JavaScript 파일 경로
input_file = "cardData_en_250228.js"
# 출력할 매핑 파일 경로
output_file = "imageMap.js"

def extract_mappings(js_file):
    mappings = {}
    with open(js_file, "r", encoding="utf-8") as file:
        content = file.read()

        # id와 image 경로 추출 (정규식 사용)
        matches = re.findall(r"id:\s*(\d+),.*?image:\s*require\((.*?)\)", content, re.DOTALL)
        for match in matches:
            card_id = match[0].strip()
            image_path = match[1].strip().strip('"').strip("'")
            mappings[card_id] = image_path

    return mappings

def write_image_map(mappings, output_file):
    # JS 파일로 매핑을 생성
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("// Auto-generated mapping file\n\n")
        file.write("const imageMap = {\n")
        for card_id, image_path in mappings.items():
            file.write(f'  {card_id}: require("{image_path}"),\n')  # 경로에 따옴표 추가
        file.write("};\n\n")
        file.write("export default imageMap;\n")

# 실행
mappings = extract_mappings(input_file)
write_image_map(mappings, output_file)

print(f"Image mapping file created: {output_file}")
