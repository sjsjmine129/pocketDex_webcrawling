const fs = require("fs");

// Path to the data file
const filePath = "./cardData_en.js";

// Read the file content
let fileContent = fs.readFileSync(filePath, "utf8");

// Use regex to replace the image field dynamically based on the id
fileContent = fileContent.replace(
	/id:\s*(\d+),([\s\S]*?)image:\s*require\('assets\/CardImages\/.*?'\)/g,
	(match, id, rest) =>
		`id: ${id},${rest}image: require('assets/CardImages/${id}.webp')`
);

// Write the updated content back to the file
fs.writeFileSync(filePath, fileContent, "utf8");
console.log("Image fields updated successfully!");
