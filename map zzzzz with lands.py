from PIL import Image, ImageDraw
import os
import json

def load_tiles(tile_folder):
    tile_paths = []
    for filename in os.listdir(tile_folder):
        if filename.endswith(".jpg"):
            parts = filename.split('_')
            if len(parts) >= 3:
                x = int(parts[1])
                y = int(parts[2].split('.')[0])
                tile_paths.append((os.path.join(tile_folder, filename), x, y))
    return tile_paths

def stitch_tiles(tile_paths, output_path):
    # Assuming each tile is 128x128 pixels
    tile_size = 128

    # Calculate the total width and height
    x_coords = [x for _, x, _ in tile_paths]
    y_coords = [y for _, _, y in tile_paths]
    map_width = (max(x_coords) - min(x_coords) + 1) * tile_size
    map_height = (max(y_coords) - min(y_coords) + 1) * tile_size

    # Create a new image with the correct total size
    map_image = Image.new('RGB', (map_width, map_height))

    # Paste the tiles into the correct position
    for img_path, x, y in tile_paths:
        img = Image.open(img_path)
        x_offset = (x - min(x_coords)) * tile_size
        y_offset = (max(y_coords) - y) * tile_size  # Correct the vertical alignment
        map_image.paste(img, (x_offset, y_offset))

    map_image.save(output_path)
    map_image.show()

def draw_land_claims(map_image_path, claims, output_path):
    map_image = Image.open(map_image_path)
    draw = ImageDraw.Draw(map_image)

    for claim in claims:
        x_coords = claim['x']
        z_coords = claim['z']
        color = claim['fillcolor']
        points = [(x, z) for x, z in zip(x_coords, z_coords)]
        draw.polygon(points, outline=color, fill=None)

    map_image.save(output_path)
    map_image.show()

# Paths
tile_folder = 'C:/Users/alexz/Desktop/LandClaimsChecker/tiles'
map_image_path = 'C:/Users/alexz/Desktop/LandClaimsChecker/combined_map.png'
land_claims_path = 'C:/Users/alexz/Desktop/LandClaimsChecker/land_claims.json'
output_path_with_claims = 'C:/Users/alexz/Desktop/LandClaimsChecker/combined_map_with_claims.png'

# Load tiles and stitch them
tile_paths = load_tiles(tile_folder)
stitch_tiles(tile_paths, map_image_path)

# Load land claims and draw them on the map
with open(land_claims_path, 'r') as f:
    claims = json.load(f)
draw_land_claims(map_image_path, claims, output_path_with_claims)
