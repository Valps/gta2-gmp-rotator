from pathlib import Path
import shutil
import argparse
import sys
import os

PROGRAM_NAME = os.path.basename(sys.argv[0])
ROOT_DIR = Path(__file__).parent

ROTATION_ANGLES = [0, 90, 180, 270]

MAP_WIDTH = 255
MAP_HEIGHT = 255

BLOCK_INFO_SIZE = 12
LIGHT_INFO_SIZE = 16
ZONE_TYPE_COORDS_DATA_SIZE = 5     # not includes the name length neither the name itself

LIGHT_MAX_X = 32767     # 255*128 + 64 - 1, where 64 = max offset
LIGHT_MAX_Y = 32767     # 255*128 + 64 - 1

AIR_TYPE = 0
ROAD_TYPE = 1
PAVEMENT_TYPE = 2
FIELD_TYPE = 3

NO_FLIP = 0
FLIP_X = 1
FLIP_Y = 2
FLIP_XY = 3

def two_nibble_from_byte(byte):
    upper_nibble = byte // 16
    lower_nibble = byte % 16
    return (upper_nibble, lower_nibble)

def get_filename(file_path):
    str_file_path = str(file_path)
    i = str_file_path.rfind('\\') + 1
    j = str_file_path.rfind('.')
    return str_file_path[i:j]

def return_rotation_value_str(binary_rotation_type):
    if (binary_rotation_type == 0):
        return "0"
    elif (binary_rotation_type == 1):
        return "90"
    elif (binary_rotation_type == 2):
        return "180"
    elif (binary_rotation_type == 3):
        return "270"
    else:
        print(f"Error: wrong binary rotation type: {binary_rotation_type}")
        sys.exit(-1)

def return_block_type_str(binary_block_type):
    if (binary_block_type == AIR_TYPE):
        return "air"
    elif (binary_block_type == ROAD_TYPE):
        return "road"
    elif (binary_block_type == PAVEMENT_TYPE):
        return "pavement"
    elif (binary_block_type == FIELD_TYPE):
        return "field"
    else:
        print(f"Error: wrong binary block type: {binary_block_type}")
        sys.exit(-1)

def convert_binary_rot(old_rotation, rotation_angle):
    rotation_angle_bin = ROTATION_ANGLES.index(rotation_angle)
    new_rotation = (old_rotation + rotation_angle_bin) % 4    # sum rotations and get mod 4
    return new_rotation

def detect_headers_and_get_chunks(gmp_path):

    chunk_info = dict(UMAP = [None, None], 
                   CMAP = [None, None], 
                   DMAP = [None, None], 
                   ZONE = [None, None], 
                   MOBJ = [None, None], 
                   PSXM = [None, None], 
                   ANIM = [None, None],
                   LGHT = [None, None],
                   EDIT = [None, None],
                   THSR = [None, None],
                   RGEN = [None, None])
    

    with open(gmp_path, 'rb') as file:

        try:
            signature = file.read(4).decode('ascii')
        except UnicodeDecodeError:
            return -1

        if (signature != "GBMP"):
            print("Error!\n")
            print(f"{gmp_path} is not a gmp file!")
            sys.exit(-1)

        version_code = int.from_bytes(file.read(2),'little')

        print(f"File Header: {signature}")
        print(f"Version Code: {version_code}", end="\n\n")

        data_offset = file.tell()
        size = file.seek(0, os.SEEK_END)
        file.seek(data_offset)

        print("File Size: {:,} bytes".format(size))

        current_offset = data_offset

        while (current_offset < size):
            chunk_header = file.read(4).decode('ascii')
            current_offset += 4
            if (chunk_header == "UMAP" 
                or chunk_header == "CMAP"
                or chunk_header == "DMAP"
                or chunk_header == "ZONE"
                or chunk_header == "MOBJ"
                or chunk_header == "PSXM"
                or chunk_header == "ANIM"
                or chunk_header == "LGHT"
                or chunk_header == "EDIT"
                or chunk_header == "THSR"
                or chunk_header == "RGEN"
                ):
                header_data_offset = file.tell() + 4
                chunk_info[chunk_header][0] = header_data_offset

                header_size = int.from_bytes(file.read(4),'little')
                chunk_info[chunk_header][1] = header_size

                print(f"Header {chunk_header} found! Offset: {hex(header_data_offset)}, Size: {hex(header_size)}")

                file.read(header_size)  # skip data
                current_offset += header_size
    print("")
    return chunk_info

def convert_fix16(f_var, get_offset: bool):
    if (get_offset):
        int_part = f_var // 128
        offset = f_var - int_part*128
        return (int_part, offset)
    else:
        return f_var / 128


def parse_light(gmp_path, chunk_infos):
    lights = []
    with open(gmp_path, 'rb') as file:
        
        lght_offset = chunk_infos["LGHT"][0]
        size = chunk_infos["LGHT"][1]

        file.seek(lght_offset)
        
        current_offset = lght_offset
        while (current_offset < lght_offset + size):
            argb = int.from_bytes(file.read(4),'little')
            fix16_x = int.from_bytes(file.read(2),'little')
            fix16_y = int.from_bytes(file.read(2),'little')
            fix16_z = int.from_bytes(file.read(2),'little')
            fix16_radius = int.from_bytes(file.read(2),'little')
            intensity = int.from_bytes(file.read(1),'little')
            shape = int.from_bytes(file.read(1),'little')
            on_time = int.from_bytes(file.read(1),'little')
            off_time = int.from_bytes(file.read(1),'little')

            lights.append((fix16_x, fix16_y))

            x, off_x = convert_fix16(fix16_x, get_offset=True)
            y, off_y = convert_fix16(fix16_y, get_offset=True)
            z, off_z = convert_fix16(fix16_z, get_offset=True)
            radius = convert_fix16(fix16_radius, get_offset=False)

            print(f"Light: x = {x} off = {off_x}, y = {y} off = {off_y}, z = {z} off = {off_z}, radius = {radius}")
            current_offset += 16
    print("")
    return lights

def read_lid_info(lid):
    data = []

    tile_texture_idx = (lid % 1024)
    data.append(tile_texture_idx)
    lid = lid >> 10

    lighting_filter = (lid % 4)
    data.append(lighting_filter)
    lid = lid >> 2

    flat = (lid % 2)
    data.append(flat)
    lid = lid >> 1

    flip = (lid % 2)
    data.append(flip)
    lid = lid >> 1

    tile_rotation = lid
    data.append(tile_rotation)

    print(f"Lid tile: {tile_texture_idx}")
    print(f"Tile rotation: {return_rotation_value_str(tile_rotation)}°")
    print(f"Filter: {lighting_filter}")
    print(f"Flat: {flat}")
    print(f"Flip: {flip}")
    return data

def read_block_side_info(side):
    data = []

    tile_texture_idx = (lid % 1024)
    data.append(tile_texture_idx)
    lid = lid >> 10

    wall = (lid % 2)
    data.append(wall)
    lid = lid >> 1

    bullet_wall = (lid % 2)
    data.append(bullet_wall)
    lid = lid >> 1

    flat = (lid % 2)
    data.append(flat)
    lid = lid >> 1

    flip = (lid % 2)
    data.append(flip)
    lid = lid >> 1

    tile_rotation = lid
    data.append(tile_rotation)

    print(f"Lid tile: {tile_texture_idx}")
    print(f"Tile rotation: {return_rotation_value_str(tile_rotation)}°")
    print(f"Wall: {wall}, Bullet Wall: {bullet_wall}")
    print(f"Flat: {flat}")
    print(f"Flip: {flip}")
    return data

def read_slope_info(slope_byte):
    block_type = (slope_byte % 4)
    slope_byte = slope_byte >> 2

    slope_type = slope_byte

    print(f"Block type: {return_block_type_str(block_type)}")
    print(f"Slope type: {slope_type}\n")
    return

def read_first_blocks_UMAP(gmp_path, chunk_infos, num_blocks, print_last_block_only: bool):
    with open(gmp_path, 'rb') as file:
        
        umap_offset = chunk_infos["UMAP"][0]

        size = BLOCK_INFO_SIZE*num_blocks    # block_info size: 0xC = 12

        file.seek(umap_offset)
        
        current_offset = umap_offset

        x = 0
        y = 0
        z = 0

        block_idx = 0

        while (current_offset < umap_offset + size):
            
            left = int.from_bytes(file.read(2),'little')
            right = int.from_bytes(file.read(2),'little')
            top = int.from_bytes(file.read(2),'little')
            bottom = int.from_bytes(file.read(2),'little')
            lid = int.from_bytes(file.read(2),'little')

            arrows = int.from_bytes(file.read(1),'little')
            slope_type = int.from_bytes(file.read(1),'little')

            current_offset += BLOCK_INFO_SIZE

            if ( ( print_last_block_only and block_idx == (num_blocks - 1) )
                or not print_last_block_only ):
                print(f"-------- Block ({x}, {y}, {z}):")
                read_lid_info(lid)
                read_slope_info(slope_type)

            x += 1
            if (x > 255):
                x = 0
                y += 1
            if (y > 255):
                y = 0
                z += 1

            block_idx += 1

def get_umap_block_idx_from_xyz(x, y, z):
    return x + y*256 + z*256*256

def read_block_UMAP(gmp_path, chunk_infos, tgt_x, tgt_y, tgt_z):
    with open(gmp_path, 'rb') as file:
        
        umap_offset = chunk_infos["UMAP"][0]
        size = chunk_infos["UMAP"][1]

        file.seek(umap_offset)
        
        current_offset = umap_offset

        block_idx = tgt_x + tgt_y*256 + tgt_z*256*256

        file.seek(umap_offset + BLOCK_INFO_SIZE*block_idx)

        left = int.from_bytes(file.read(2),'little')
        right = int.from_bytes(file.read(2),'little')
        top = int.from_bytes(file.read(2),'little')
        bottom = int.from_bytes(file.read(2),'little')
        lid = int.from_bytes(file.read(2),'little')

        arrows = int.from_bytes(file.read(1),'little')
        slope_type = int.from_bytes(file.read(1),'little')

        print(f"-------- Block ({tgt_x}, {tgt_y}, {tgt_z}):")
        read_lid_info(lid)
        read_slope_info(slope_type)

def read_gmp(gmp_path, chunk_infos):
    old_lights = parse_light(gmp_path, chunk_infos)
    read_block_UMAP(gmp_path, chunk_infos, 150, 152, 5)



def get_block_info_data(gmp_path, chunk_infos):

    xyz_array = []

    with open(gmp_path, 'rb') as file:
        umap_offset = chunk_infos["UMAP"][0]
        size = chunk_infos["UMAP"][1]
        file.seek(umap_offset)
        current_offset = umap_offset

        x_array = []
        xy_array = []

        x = 0
        y = 0
        z = 0

        while (current_offset < umap_offset + size):

            block_data = file.read(BLOCK_INFO_SIZE)
            x_array.append(block_data)

            current_offset += BLOCK_INFO_SIZE

            x += 1

            if (x > 255):
                x = 0

                xy_array.append(x_array)
                x_array = []

                y += 1
            
            if (y > 255):
                y = 0

                xyz_array.append(xy_array)
                xy_array = []

                z += 1

    return xyz_array

def is_air_block(block_data):
    block_type_byte = block_data[-1]
    type = block_type_byte % 4
    if (type == AIR_TYPE):
        return True
    return False

def is_empty_block(block_data):
    if (is_air_block(block_data)):
        lid_word = int.from_bytes(block_data[8:10], 'little')
        lid_tile = lid_word % 1024
        if (lid_tile == 0):
            left_word = int.from_bytes(block_data[0:2], 'little')
            right_word = int.from_bytes(block_data[2:4], 'little')
            top_word = int.from_bytes(block_data[4:6], 'little')
            bottom_word = int.from_bytes(block_data[6:8], 'little')
            if (left_word == 0 and right_word == 0 and top_word == 0 and bottom_word == 0):
                return True
    return False

def is_road_field_block(block_data):
    block_type_byte = block_data[-1]
    type = block_type_byte % 4
    if (type == ROAD_TYPE or type == FIELD_TYPE):
        return True
    return False

def block_has_lid(block_data):
    lid_word = int.from_bytes(block_data[8:10], 'little')
    lid_tile = lid_word % 1024
    if (lid_tile != 0):
        return True
    return False

def is_slope(block_data):
    slope_byte = block_data[-1]
    slope_byte = slope_byte >> 2
    if (slope_byte == 0):
        return False
    if (slope_byte > 60):   # slopes 61, 62 and 63 are irrelevants for gmp rotation
        return False
    return True

################ rotate stuff

def swap_bits(nibble):
    """Swap the bits of nibble in group of two, for example:
    0110 -> 1001
    1110 -> 1101
    1101 -> 1110
    """
    new_nibble = ( 1*((nibble >> 1) % 2) 
                    + 2*(nibble % 2) 
                    + 4*((nibble >> 3) % 2) 
                    + 8*((nibble >> 2) % 2) )
    return new_nibble

def shuffle_bits(nibble, flip_code):
    
    if (flip_code == FLIP_X):
        # flip left and right arrows
        new_nibble = ( 1*((nibble >> 1) % 2)
                        + 2*(nibble % 2)
                        + 4*((nibble >> 2) % 2)
                        + 8*((nibble >> 3) % 2) )
    elif (flip_code == FLIP_Y):
        # flip up and down arrows
        new_nibble = ( 1*(nibble % 2)
                        + 2*((nibble >> 1) % 2)
                        + 4*((nibble >> 3) % 2)
                        + 8*((nibble >> 2) % 2) )
    return new_nibble

def flip_road_arrows(block_data, flip_code):
    old_red_arrows_nibble, old_green_arrows_nibble = two_nibble_from_byte(block_data[10])

    if old_green_arrows_nibble != 0:
        if (flip_code == FLIP_XY):
            new_green_arrows_nibble = swap_bits(old_green_arrows_nibble)
        elif (flip_code == FLIP_X):
            new_green_arrows_nibble = shuffle_bits(old_green_arrows_nibble, flip_code)
        elif (flip_code == FLIP_Y):
            new_green_arrows_nibble = shuffle_bits(old_green_arrows_nibble, flip_code)
    else:
        new_green_arrows_nibble = 0

    if old_red_arrows_nibble != 0:
        if (flip_code == FLIP_XY):
            new_red_arrows_nibble = swap_bits(old_red_arrows_nibble)
        elif (flip_code == FLIP_X):
            new_red_arrows_nibble = shuffle_bits(old_red_arrows_nibble, flip_code)
        elif (flip_code == FLIP_Y):
            new_red_arrows_nibble = shuffle_bits(old_red_arrows_nibble, flip_code)
    else:
        new_red_arrows_nibble = 0

    new_block_data = block_data[:10] + int.to_bytes(new_red_arrows_nibble*16 + new_green_arrows_nibble) + block_data[11:]
    return new_block_data

def flip_lid(block_data, flip_code):
    lid_word = int.from_bytes(block_data[8:10], 'little')

    # verify if the lid tile is 1023 (used in slopes 49...52)
    tile_idx = lid_word % 1024
    if (tile_idx == 1023):
        return block_data   # do nothing
    
    #old_flip = ( lid_word >> 13 ) % 2
    
    if flip_code == FLIP_X or flip_code == FLIP_Y:
        
        lid_word = lid_word ^ (2**13)   # toggle flip on bit 13

        #if old_flip == 0:
        #    new_flip = 1
        #elif old_flip == 1:
        #    new_flip = 0

        old_rotation = lid_word >> 14
        
        if flip_code == FLIP_Y:
            new_rotation = convert_binary_rot(old_rotation, 180)
        else:
            new_rotation = old_rotation

    elif flip_code == FLIP_XY:
        new_rotation = convert_binary_rot(old_rotation, 180)
        #new_flip = old_flip
    else:
        new_rotation = old_rotation
        #new_flip = old_flip

    sum_bits = new_rotation * (2**14)   # shift left by 14
    lid_word = lid_word & 16383     # clear the last two bits
    lid_word += sum_bits
    
    new_byte_array = bytes([lid_word % 256, lid_word // 256])
    new_block_data = block_data[:8] + new_byte_array + block_data[10:]
    return new_block_data

    old_rotation = lid_word >> 14
    new_rotation = convert_binary_rot(old_rotation, rotation_angle)

    # fix flipped blocks for 270° and 90° rotations
    if (rotation_angle == 270):
        flip = ( lid_word >> 13 ) % 2
        if (flip == 1):
            new_rotation = convert_binary_rot(old_rotation, 90)
    elif (rotation_angle == 90):
        flip = ( lid_word >> 13 ) % 2
        if (flip == 1):
            new_rotation = convert_binary_rot(old_rotation, 270)

    sum_bits = new_rotation * (2**14)   # shift left by 14
    lid_word = lid_word & 16383     # clear the last two bits
    lid_word += sum_bits

    new_byte_array = bytes([lid_word % 256, lid_word // 256])
    new_block_data = block_data[:8] + new_byte_array + block_data[10:]
    return new_block_data

def flip_tile(side_word):
    return side_word ^ (2**13)

def has_side_tile(side_word):
    tile_idx = side_word % 1024
    return True if tile_idx != 0 else False

def flip_sides(block_data, flip_code):
    left_word = int.from_bytes(block_data[0:2], 'little')
    right_word = int.from_bytes(block_data[2:4], 'little')
    top_word = int.from_bytes(block_data[4:6], 'little')
    bottom_word = int.from_bytes(block_data[6:8], 'little')

    byte = block_data[-1]
    slope_type = byte >> 2

    # some slopes uses right or left sides only. Flip their sides accordingly if flip = FLIP_X
    if (45 <= slope_type <= 52
        and (flip_code == FLIP_X) ):    #  or rotation_angle == 270

        new_block_data = change_side_tile(block_data, slope_type, 180)  # rotate slopes by 180 degree
        fix_sides
        return new_block_data

    # flip side tiles as well
    if (flip_code != FLIP_XY):
        if has_side_tile(top_word):
            top_word = flip_tile(top_word)
        if has_side_tile(bottom_word):
            bottom_word = flip_tile(bottom_word)
        if has_side_tile(right_word):
            right_word = flip_tile(right_word)
        if has_side_tile(left_word):
            left_word = flip_tile(left_word)

    #array = [left_word, right_word, top_word, bottom_word]
    array = []

    if (flip_code == FLIP_X):
        array = [right_word, left_word, top_word, bottom_word]
    elif (flip_code == FLIP_XY):
        array = [right_word, left_word, bottom_word, top_word]
    elif (flip_code == FLIP_Y):
        array = [left_word, right_word, bottom_word, top_word]

    if (array == None):
        print(f"Error: wrong flip code: {flip_code}")
        sys.exit(-1)

    new_byte_array = bytes([array[0] % 256, 
                            array[0] // 256,
                            array[1] % 256, 
                            array[1] // 256,
                            array[2] % 256, 
                            array[2] // 256,
                            array[3] % 256, 
                            array[3] // 256])
    
    new_block_data = new_byte_array + block_data[8:]

    return new_block_data

def rotate_slope_90(array):
    #array = [a, b, c, d]
    new_array = [array[3], array[2], array[0], array[1]]
    return new_array

def rotate_slope_270(array):
    #array = [a, b, c, d]
    new_array = [array[2], array[3], array[1], array[0]]
    return new_array

def rotate_slope_180(array):
    #array = [a, b, c, d]
    new_array = [array[1], array[0], array[3], array[2]]
    return new_array

def shift_array(array, num_permutations):
    """Shift right a four-size array 'num_permutations' times"""
    new_array = [array[3], array[0], array[1], array[2]]
    if (num_permutations == 0):
        print("Error: invalid permutation")
        sys.exit(-1)
    if (num_permutations == 1):
        return new_array
    else:
        return shift_array(new_array, num_permutations - 1)


def fix_sides(block_data, side):
    left_word = int.from_bytes(block_data[0:2], 'little')
    right_word = int.from_bytes(block_data[2:4], 'little')
    top_word = int.from_bytes(block_data[4:6], 'little')
    bottom_word = int.from_bytes(block_data[6:8], 'little')

    #array = [left_word, right_word, top_word, bottom_word]

    array = []

    if (side == 'right'):
        array = [right_word, 0, 0, 0]
    elif (side == 'left'):
        array = [0, left_word, 0, 0]
    else:
        print("Error: wrong 'side' param in func 'fix_sides'.")
        sys.exit(-1)

    new_byte_array = bytes([array[0] % 256, 
                                array[0] // 256,
                                array[1] % 256, 
                                array[1] // 256,
                                array[2] % 256, 
                                array[2] // 256,
                                array[3] % 256, 
                                array[3] // 256])
        
    new_block_data = new_byte_array + block_data[8:]

    return new_block_data


# Fix the side of some slope types
def change_side_tile(block_data, slope_type, rotation_angle):
    if (slope_type == 46
        or slope_type == 48
        or slope_type == 50
        or slope_type == 52):   # right side

        # skip if the tile still in correct position
        if (rotation_angle == 90 and (slope_type == 46 or slope_type == 50)):
            return block_data

        if (rotation_angle == 270 and (slope_type == 48 or slope_type == 52)):
            return block_data
        
        # or else change the tile side
        new_block_data = fix_sides(block_data, 'right')
    elif (slope_type == 45
        or slope_type == 47
        or slope_type == 49
        or slope_type == 51):   # left side

        # skip if the tile still in correct position
        if (rotation_angle == 90 and (slope_type == 47 or slope_type == 51)):
            return block_data

        # or else change the tile side
        if (rotation_angle == 270 and (slope_type == 45 or slope_type == 49)):
            return block_data

        new_block_data = fix_sides(block_data, 'left')
    else:
        new_block_data = block_data
    
    return new_block_data

def swap_slope(array, flip_code):
    if flip_code == FLIP_X:
        return [array[0], array[1], array[3], array[2]]
    elif flip_code == FLIP_Y:
        return [array[1], array[0], array[2], array[3]]
    elif flip_code == FLIP_XY:
        return [array[1], array[0], array[3], array[2]]
    else:
        print(f"ERROR! Wrong flip code = {flip_code}")
        sys.exit(-1)
        return

def flip_slope(block_data, flip_code):
    byte = block_data[-1]
    slope_type = byte >> 2

    new_block_data = block_data

    new_slope_type = None

    if (1 <= slope_type <= 8):      # slope 1/2
        if (slope_type % 2 == 1):   # lower
            
            slope_array = [1, 3, 5, 7]
            idx = slope_array.index(slope_type)

            new_slope_array = swap_slope(slope_array, flip_code)
            
            new_slope_type = new_slope_array[idx]
            
        else:                       # higher

            slope_array = [2, 4, 6, 8]
            idx = slope_array.index(slope_type)

            new_slope_array = swap_slope(slope_array, flip_code)
            
            new_slope_type = new_slope_array[idx]

    elif (9 <= slope_type <= 40):       # slope 1/8

        if (9 <= slope_type <= 16):
            offset = slope_type - 9
            direction = 1    # up
        elif (17 <= slope_type <= 24):
            offset = slope_type - 17
            direction = 3  # down
        elif (25 <= slope_type <= 32):
            offset = slope_type - 25
            direction = 2  # left
        elif (33 <= slope_type <= 40):
            offset = slope_type - 33
            direction = 0 # right

        array = [0,1,2,3]
        idx = array.index(direction)

        if ( ( (25 <= slope_type <= 40) and (flip_code == FLIP_X) )
            or ( (9 <= slope_type <= 24) and (flip_code == FLIP_Y) ) ):

            new_array = shift_array(array, ROTATION_ANGLES.index(180))
            new_direction = new_array[idx]
        else:
            new_direction = direction   # do nothing

        if (new_direction == 0):
            new_slope_type = 33 + offset
        elif (new_direction == 1):
            new_slope_type = 9 + offset
        elif (new_direction == 2):
            new_slope_type = 25 + offset
        elif (new_direction == 3):
            new_slope_type = 17 + offset


    elif (41 <= slope_type <= 44):      # slope 1/1

        slope_array = [41, 42, 43, 44]
        idx = slope_array.index(slope_type)

        new_slope_array = swap_slope(slope_array, flip_code)
        
        new_slope_type = new_slope_array[idx]

    elif (45 <= slope_type <= 48):      # diagonal slope
        
        if flip_code == FLIP_X:
            slope_array = [45, 46, 47, 48]
        elif flip_code == FLIP_Y:
            slope_array = [45, 47, 46, 48]
        elif flip_code == FLIP_XY:
            slope_array = [45, 47, 46, 48]  # TODO: flip XY
            pass
        
        
        idx = slope_array.index(slope_type)
        new_slope_array = swap_slope(slope_array, FLIP_XY)

        new_slope_type = new_slope_array[idx]

    elif (49 <= slope_type <= 52):
        
        #slope_array = [49, 52, 51, 50]
        if flip_code == FLIP_X:
            slope_array = [49, 50, 51, 52]
        elif flip_code == FLIP_Y:
            slope_array = [49, 51, 50, 52]
        elif flip_code == FLIP_XY:
            slope_array = [49, 50, 51, 52]  # TODO: flip XY
            pass

        idx = slope_array.index(slope_type)
        new_slope_array = swap_slope(slope_array, FLIP_XY)
        
        new_slope_type = new_slope_array[idx]

    elif (53 <= slope_type <= 56):

        slope_array = [55, 56, 53, 54]
        idx = slope_array.index(slope_type)

        new_slope_array = swap_slope(slope_array, flip_code)
        
        new_slope_type = new_slope_array[idx]

    elif (57 <= slope_type <= 60):

        if flip_code == FLIP_X:
            slope_array = [57, 58, 59, 60]
        elif flip_code == FLIP_Y:
            slope_array = [58, 59, 57, 60]
        elif flip_code == FLIP_XY:
            slope_array = [57, 58, 59, 60]  # TODO: flip XY
            pass
        
        idx = slope_array.index(slope_type)
        new_slope_array = swap_slope(slope_array, FLIP_XY)

        new_slope_type = new_slope_array[idx]
    
    if (new_slope_type != None):
        new_slope_type = new_slope_type << 2
        # clear the last 6 bits
        byte = byte & 3
        byte += new_slope_type
        new_block_data = block_data[:-1] + int.to_bytes(byte)
    else:
        new_block_data = block_data

    return new_block_data


def flip_info(block_info_array, flip_code):
    """Flip tiles, slopes, road arrows, rotate tile rotations etc."""
    for z in range(len(block_info_array)):
        for y in range(len(block_info_array[z])):
            for x in range(len(block_info_array[z][y])):

                old_block_data = block_info_array[z][y][x]

                if (is_empty_block(old_block_data)):
                    continue
                
                # some field blocks can have arrows, which is the case of train railroads
                if (is_road_field_block(old_block_data)):
                    new_block_data = flip_road_arrows(old_block_data, flip_code)
                else:
                    new_block_data = old_block_data
                
                if block_has_lid(new_block_data):
                    new_block_data = flip_lid(new_block_data, flip_code)
                new_block_data = flip_sides(new_block_data, flip_code)

                if is_slope(new_block_data):
                    new_block_data = flip_slope(new_block_data, flip_code)

                block_info_array[z][y][x] = new_block_data

    return

def flip_map(output_path, chunk_infos, flip_code, block_info_array):
    with open(output_path, 'r+b') as file:
        
        umap_offset = chunk_infos["UMAP"][0]
        size = chunk_infos["UMAP"][1]

        file.seek(umap_offset)
        
        current_offset = umap_offset

        x = 0
        y = 0
        z = 0

        if (flip_code == FLIP_XY):

            while (current_offset < umap_offset + size):
                file.write(block_info_array[z][MAP_HEIGHT - y][MAP_WIDTH - x])
                
                x += 1

                if (x > 255):
                    x = 0
                    y += 1
                
                if (y > 255):
                    y = 0
                    z += 1
                
                if (z >= 8):
                    break
        
        elif (flip_code == FLIP_X):

            while (current_offset < umap_offset + size):
                file.write(block_info_array[z][y][MAP_WIDTH - x])
                
                x += 1

                if (x > 255):
                    x = 0
                    y += 1
                
                if (y > 255):
                    y = 0
                    z += 1
                
                if (z >= 8):
                    break

        elif (flip_code == FLIP_Y):

            while (current_offset < umap_offset + size):
                file.write(block_info_array[z][MAP_HEIGHT - y][x])
                
                x += 1

                if (x > 255):
                    x = 0
                    y += 1
                
                if (y > 255):
                    y = 0
                    z += 1
                
                if (z >= 8):
                    break

    #print(f"Map blocks flipped successfully")

def get_zones_info_data(gmp_path, chunk_infos):

    if chunk_infos["ZONE"][0] is None:
        return None # no zones

    zones_data_array = []
    with open(gmp_path, 'rb') as file:

        zone_offset = chunk_infos["ZONE"][0]
        size = chunk_infos["ZONE"][1]

        file.seek(zone_offset)
        
        current_offset = zone_offset
        while (current_offset < zone_offset + size):
            zone_info = file.read(ZONE_TYPE_COORDS_DATA_SIZE)

            current_offset += ZONE_TYPE_COORDS_DATA_SIZE

            name_length = int.from_bytes(file.read(1))
            zone_name_data = file.read(name_length)
            current_offset += 1 + name_length

            zone_data = zone_info + int.to_bytes(name_length) + zone_name_data
            zones_data_array.append(zone_data)

    return zones_data_array

def get_light_info_data(gmp_path, chunk_infos):

    if chunk_infos["LGHT"][0] is None:
        return None # no zones

    lights_data = []
    with open(gmp_path, 'rb') as file:

        lght_offset = chunk_infos["LGHT"][0]
        size = chunk_infos["LGHT"][1]

        file.seek(lght_offset)
        
        current_offset = lght_offset
        while (current_offset < lght_offset + size):
            light_data = file.read(LIGHT_INFO_SIZE)
            lights_data.append(light_data)

            current_offset += LIGHT_INFO_SIZE

    return lights_data

def flip_gmp_blocks(output_path, chunk_infos, flip_code, block_info_array):
    """Flip the UMAP info"""

    print("Flipping block info...")
    flip_info(block_info_array, flip_code)   # flip tiles, slopes etc.

    print("Flipping UMAP info...")
    flip_map(output_path, chunk_infos, flip_code, block_info_array)  # Now flip the map itself
    return

def flip_light_coordinates(light_data, flip_code):
    light_x = int.from_bytes(light_data[4:6], 'little')   # word
    light_y = int.from_bytes(light_data[6:8], 'little')   # word

    if (flip_code == FLIP_XY):
        light_x = LIGHT_MAX_X - light_x
        light_y = LIGHT_MAX_Y - light_y
    elif (flip_code == FLIP_X):
        light_x = LIGHT_MAX_X - light_x
    elif (flip_code == FLIP_Y):
        light_y = LIGHT_MAX_Y - light_y

    if (light_x > LIGHT_MAX_X or light_y > LIGHT_MAX_Y):
        print(f"Error: light coordinate overflow: x = {light_x}, y = {light_y}")
        sys.exit(-1)
    elif (light_x < 0 or light_y < 0):
        print(f"Error: negative light coordinates: x = {light_x}, y = {light_y}")
        sys.exit(-1)

    word_x = bytes([light_x % 256, light_x // 256])
    word_y = bytes([light_y % 256, light_y // 256])

    new_light_data = light_data[:4] + word_x + word_y + light_data[8:]

    return new_light_data

def flip_zone_coordinates(zone_data, flip_code):
    zone_x = zone_data[1]
    zone_y = zone_data[2]
    zone_w = zone_data[3]
    zone_h = zone_data[4]

    if (flip_code == FLIP_XY):
        zone_x = MAP_WIDTH - zone_x - zone_w + 1
        zone_y = MAP_HEIGHT - zone_y - zone_h + 1
    elif (flip_code == FLIP_X):
        zone_x = MAP_WIDTH - zone_x - zone_w + 1
    elif (flip_code == FLIP_Y):
        zone_y = MAP_HEIGHT - zone_y - zone_h + 1

    if (zone_x < 0 or zone_y < 0):
        print(f"Error: negative zone coordinates: x = {zone_x}, y = {zone_y}")
        sys.exit(-1)
    if (zone_x > MAP_WIDTH or zone_y > MAP_HEIGHT):
        print(f"Error: zone coordinates above {MAP_WIDTH}: x = {zone_x}, y = {zone_y}")
        sys.exit(-1)
    if (zone_x + zone_w > MAP_WIDTH + 1 or zone_y + zone_h > MAP_HEIGHT + 1):
        print(f"Error: zone coordinates overflow: x = {zone_x}, y = {zone_y}, w = {zone_w}, h = {zone_h}")
        sys.exit(-1)
    
    new_zone_data = (int.to_bytes(zone_data[0]) 
                    + int.to_bytes(zone_x) 
                    + int.to_bytes(zone_y) 
                    + int.to_bytes(zone_w) 
                    + int.to_bytes(zone_h) 
                    + zone_data[5:])

    return new_zone_data

def flip_light_info(light_info_array, flip_code):
    for i in range(len(light_info_array)):
        old_light_data = light_info_array[i]
        new_light_data = flip_light_coordinates(old_light_data, flip_code)
        light_info_array[i] = new_light_data
    return

def flip_zone_info(zones_info_array, rotation_angle):
    for i in range(len(zones_info_array)):
        old_zone_data = zones_info_array[i]
        new_zone_data = flip_zone_coordinates(old_zone_data, rotation_angle)
        zones_info_array[i] = new_zone_data
    return

def flip_gmp_zones(output_path, chunk_infos, rotation_angle, zones_info_array):
    if chunk_infos["ZONE"][0] is None:
        return  # no zones
    
    print("Rotating zones coordinates...")
    flip_zone_info(zones_info_array, rotation_angle)
    
    with open(output_path, 'r+b') as file:
        zone_offset = chunk_infos["ZONE"][0]
        size = chunk_infos["ZONE"][1]

        file.seek(zone_offset)
        
        current_offset = zone_offset

        zone_idx = 0

        while (current_offset < zone_offset + size):
            
            file.write(zones_info_array[zone_idx])
            current_offset += len(zones_info_array[zone_idx])
            zone_idx += 1

    return

def flip_gmp_lights(output_path, chunk_infos, flip_code, light_info_array):

    if chunk_infos["LGHT"][0] is None:
        return  # no lights
    
    print("Rotating lights coordinates...")
    flip_light_info(light_info_array, flip_code)
    
    with open(output_path, 'r+b') as file:
        lght_offset = chunk_infos["LGHT"][0]
        size = chunk_infos["LGHT"][1]

        file.seek(lght_offset)
        
        current_offset = lght_offset

        light_idx = 0

        while (current_offset < lght_offset + size):
            
            file.write(light_info_array[light_idx])
            current_offset += LIGHT_INFO_SIZE
            light_idx += 1

    return

def get_flip(flip_x, flip_y):
    if not flip_x and not flip_y:
        return NO_FLIP
    if flip_x and not flip_y:
        return FLIP_X
    if not flip_x and flip_y:
        return FLIP_Y
    return FLIP_XY

def flip_gmp(gmp_path, chunk_infos, flip_code, out_path):

    if chunk_infos["UMAP"][0] is None:
        print("Error: This GMP flipper only support uncompressed maps.")
        return -2

    if flip_code == FLIP_X:
        flip_type = "x"
    elif flip_code == FLIP_Y:
        flip_type = "y"
    else:
        flip_type = "xy"

    # create a copy of gmp file
    filename = get_filename(gmp_path)
    #output_path = ROOT_DIR / f"{filename}_flipped_{flip_type}.gmp"
    output_path = out_path / f"{filename}_flip_{flip_type}.gmp"

    print(f"Creating copy of {filename}.gmp")
    shutil.copyfile(gmp_path, output_path)

    # get block infos
    block_info_array = get_block_info_data(gmp_path, chunk_infos)
    zones_info_array = get_zones_info_data(gmp_path, chunk_infos)
    light_info_array = get_light_info_data(gmp_path, chunk_infos)

    

    # flip map
    flip_gmp_blocks(output_path, chunk_infos, flip_code, block_info_array)
    flip_gmp_zones(output_path, chunk_infos, flip_code, zones_info_array)
    flip_gmp_lights(output_path, chunk_infos, flip_code, light_info_array)

    print(f"\nSuccess! GMP flipped!")

    # TODO:  only ste.gmp use MOBJ header, but it can't be decompressed without corrupting gmp
    #rotate_gmp_objects(output_path, chunk_infos, rotation_angle, obj_info_array)
    return 0



def main():
    parser = argparse.ArgumentParser(PROGRAM_NAME)
    parser.add_argument("gmp_path")
    parser.add_argument("-x", "--flip_x", action='store_true')
    parser.add_argument("-y", "--flip_y", action='store_true')
    args = parser.parse_args()

    if (not args.gmp_path 
        or (not args.flip_x and not args.flip_y ) ):
        print("Usage: python [program path] [gmp path] [-x | --flip_x] [-y | --flip_y]")
        sys.exit(-1)

    if ("\\" not in args.gmp_path and "/" not in args.gmp_path):
        gmp_path = ROOT_DIR / args.gmp_path
    else:
        gmp_path = Path(args.gmp_path)

    if (not gmp_path.exists()):
        print("File not found.")
        sys.exit(-1)
    
    chunk_infos = detect_headers_and_get_chunks(gmp_path)
    flip_code = get_flip(args.flip_x, args.flip_y)  # 0 = No flip, 1 = Flip x, 2 = Flip y, 3 = Flip x & y
    flip_gmp(gmp_path, chunk_infos, flip_code, ROOT_DIR)
        
    return

if __name__ == "__main__":
    main()
