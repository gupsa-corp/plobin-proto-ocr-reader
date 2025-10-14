from PIL import Image, ImageDraw, ImageFont

# Create a simple test image
img = Image.new('RGB', (800, 200), color='white')
d = ImageDraw.Draw(img)

# Add some text
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
except:
    font = ImageFont.load_default()

d.text((50, 50), "Hello World", fill='black', font=font)
d.text((50, 120), "OCR Test 123", fill='black', font=font)

# Save image
img.save('test_image.png')
print("✅ Test image created: test_image.png")
