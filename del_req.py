import re

# JavaScript 파일 경로
input_file = "cardData_en_250228.js"
# 출력 파일 경로
output_file = "CardData_no_image.js"

def remove_image_fields(js_file, output_file):
    with open(js_file, "r", encoding="utf-8") as file:
        content = file.read()

        # image 필드를 제거 (정규식 사용)
        content_without_images = re.sub(r"image:\s*require\([^)]+\),\s*", "", content)

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(content_without_images)

# 실행
remove_image_fields(input_file, output_file)

print(f"File without image fields created: {output_file}")
