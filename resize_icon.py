from PIL import Image
img = Image.open("D:/TraeProject/python/RIShadowing/RIShadowing.png").convert("RGBA")
img.resize((64, 64), Image.LANCZOS).save("D:/TraeProject/python/RIShadowing/RIShadowing_icon.png")
print("Created 64x64 PNG icon")
