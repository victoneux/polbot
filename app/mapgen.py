import numpy as np
import PIL
import PIL.Image
import json
import pathlib
import random

# Assumption: the bot will only ever deal with exactly ONE save at a time.

program_dir = str(pathlib.Path(__file__).parent.parent.absolute())
save_dir = program_dir + "/saves/" + "test" # To do: prompt user for this somehow? a file prolly

coasts_map = np.asarray(PIL.Image.open(save_dir + "/coasts.bmp"))
politics_map = np.asarray(PIL.Image.open(save_dir + "/political.bmp"))

final = coasts_map.copy()

regions = json.loads(open(save_dir + "/regions.json").read())
nations = json.loads(open(save_dir + "/nations.json").read())

regions_map = np.empty((len(coasts_map), len(coasts_map[0]), 2))
regions_map.fill(-1)

for region_id in range(len(regions.keys())):
    region = list(regions.keys())[region_id]
    nation_id = list(nations.keys()).index(regions[region]["owner_code"])
    
    color = [int(x) for x in region.split(",")]
    indices = np.where(np.all(politics_map == color, axis=-1))
    r,c = indices
    coords = list(zip(r,c))
    for i in range(len(coords)):
        regions_map[coords[i][0],coords[i][1],0] = nation_id
        regions_map[coords[i][0],coords[i][1],1] = region_id
        final[coords[i][0],coords[i][1]] = nations[regions[region]["owner_code"]]["color"]

minimal_region_borders = []
minimal_national_borders = []

for y in range(len(regions_map)):
    last_nation = -1
    last_region = -1
    for x in range(len(regions_map[0])):
        nation = regions_map[y][x][0]
        region = regions_map[y][x][1]
        if last_region != -1 and region != -1:
            if region != last_region:
                if nation == last_nation:
                    if coasts_map[y][x][0] != 0:
                        minimal_region_borders.append([y,x])
                else:
                    if coasts_map[y][x][0] != 0:
                        minimal_national_borders.append([y,x])
                    if coasts_map[y][x-1][0] != 0:
                        minimal_national_borders.append([y,x-1])
        last_nation = nation
        last_region = region
        
for x in range(len(regions_map[0])):
    last_nation = -1
    last_region = -1
    for y in range(len(regions_map)):
        nation = regions_map[y][x][0]
        region = regions_map[y][x][1]
        if last_region != -1 and region != -1:
            if region != last_region:
                if nation == last_nation:
                    if coasts_map[y][x][0] != 0:
                        minimal_region_borders.append([y,x])
                else:
                    if coasts_map[y][x][0] != 0:
                        minimal_national_borders.append([y,x])
                    if coasts_map[y-1][x][0] != 0:
                        minimal_national_borders.append([y-1,x])
        last_nation = nation
        last_region = region
        
def border_improvement_protocol(border_pixels, national):
    border_array = np.empty((len(coasts_map), len(coasts_map[0])))
    new_borders = border_pixels.copy()
    border_array.fill(0)
    for y,x in border_pixels:
        border_array[y,x] = 1
    for y,x in border_pixels:
        if x > 0:
            if y > 0:
                if (border_array[y-1][x-1] == 1 or coasts_map[y-1,x-1][0] == 0) and national:
                    new_borders.append([y,x-1])
                    new_borders.append([y-1,x])
            if y < len(border_array)-1:
                if (border_array[y+1][x-1] == 1 or coasts_map[y+1,x-1][0] == 0) and national:
                    new_borders.append([y,x-1])
                    new_borders.append([y+1,x])
        if x < len(border_array[0])-1:
            if y > 0:
                if border_array[y-1][x+1] == 1 or coasts_map[y-1,x+1][0] == 0:
                    if national:
                        new_borders.append([y,x+1])
                    new_borders.append([y-1,x])
            if y < len(border_array)-1:
                if (border_array[y+1][x+1] == 1 or coasts_map[y+1,x+1][0] == 0) and national:
                    new_borders.append([y,x+1])
                    new_borders.append([y+1,x])
                        
    return new_borders
                
new_region_borders = border_improvement_protocol(minimal_region_borders,False)
new_national_borders = border_improvement_protocol(minimal_national_borders,True)

final_noborder = final.copy()

def draw_borders(border_pixels, diff):
    for y,x in border_pixels:
        color = final_noborder[y,x]
        new_color = color.copy()
        for i in range(len(color)):
            new_color[i] = color[i] + int((255 - color[i]) / diff)
        final[y,x] = new_color

coastal_pixels = np.where(np.all(coasts_map == [0,0,0], axis=-1))
coastal_pixels = list(zip(coastal_pixels[0],coastal_pixels[1]))

draw_borders(new_region_borders,12)
draw_borders(new_national_borders,-5)
draw_borders(coastal_pixels,-2)
        
new_im = PIL.Image.fromarray(final)
new_im.save(save_dir + "/final.bmp")