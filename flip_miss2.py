from pathlib import Path
import shutil
import argparse
import sys
import os
import flip_cmd

PROGRAM_NAME = os.path.basename(sys.argv[0])
ROOT_DIR = Path(__file__).parent

ROTATION_ANGLES = [0, 90, 180, 270]

NO_FLIP = 0
FLIP_X = 1
FLIP_Y = 2
FLIP_XY = 3

def get_filename(path):
    str_path = str(path)
    i = str_path.rfind('\\') + 1
    j = str_path.rfind('.')
    return str_path[i:j]

def get_comment(line: str):
    comment_pointer = line.find("//")
    if comment_pointer != -1:
        return line[comment_pointer + 2:]
    return None

def get_whitespaces(line: str):
    result = ""
    for chr in line:
        if chr == ' ' or chr == '\t':
            result += chr
        else:
            break
    return result

def sum_dict(dict_1: dict, dict_2: dict):
    for opcode in dict_2:
        n_times = dict_1.get(opcode)
        if n_times is not None:
            dict_1[opcode] += dict_2[opcode]
        else:
            dict_1[opcode] = dict_2[opcode]

def add_item_dict(dict1: dict, key, value):
    if key in dict1:
        dict1[key] += value
    else:
        dict1[key] = value

def read_and_get_statistical(miss2_path) -> tuple[dict,dict,dict]:

    dec_opcodes_dict = dict()
    exec_opcodes_dict = dict()
    bool_opcodes_dict = dict()

    print(f"\nFile {get_filename(miss2_path)}.mis: \n")

    with open(miss2_path, 'r') as file:

        for line in file:
            for opcode in flip_cmd.DEC_OPCODES_LIST:
                if opcode in line:
                    add_item_dict(dec_opcodes_dict, opcode, 1)
                    break
            for opcode in flip_cmd.EXEC_OPCODES_LIST:
                if opcode in line:
                    add_item_dict(exec_opcodes_dict, opcode, 1)
                    break
            for opcode in flip_cmd.BOOL_OPCODES_LIST:
                if opcode in line:
                    #print(opcode)
                    add_item_dict(bool_opcodes_dict, opcode, line.count(opcode))

    return dec_opcodes_dict, exec_opcodes_dict, bool_opcodes_dict


def flip_script_info(miss2_path, flip_code, output_path):

    print(f"\nOpening file {get_filename(miss2_path)}.mis: \n")

    with open(miss2_path, 'r') as source_file:
        with open(output_path, 'w+') as output_file:

            for line in source_file:
                
                comment = get_comment(line)
                # remove comment from line if it exists
                if comment is not None:
                    line = line[ : line.find("//") ]

                tabs_whitespaces = get_whitespaces(line)
                
                if flip_cmd.is_dec_opcode_flippable(line):
                    new_line = flip_cmd.flip_dec_opcode(line, flip_code)
                elif flip_cmd.is_exec_opcode_flippable(line):
                    new_line = flip_cmd.flip_exec_opcode(line, flip_code)
                elif flip_cmd.is_bool_opcode_flippable(line):
                    new_line = flip_cmd.flip_bool_line(line, flip_code)
                else:
                    if comment is not None:
                        line += " // " + comment
                    output_file.write(line)
                    continue
                
                if comment is not None:
                    new_line += " // " + comment

                new_line = tabs_whitespaces + new_line + "\n"
                output_file.write(new_line)

def get_flip(flip_x, flip_y):
    if not flip_x and not flip_y:
        return NO_FLIP
    if flip_x and not flip_y:
        return FLIP_X
    if not flip_x and flip_y:
        return FLIP_Y
    return FLIP_XY

def main_flip_miss(miss2_path, flip_code):
    filename = get_filename(miss2_path)

    # create output folder, if it not exists
    flip_type = "x" if flip_code == FLIP_X else "y"
    output_folder = miss2_path.parent / (filename + f"_flip_{flip_type}")
    if (not output_folder.exists()):
        output_folder.mkdir()

    # create a copy of the base script

    output_path = output_folder / (filename + ".mis")
    # TODO shutil.copy(miss2_path, output_path)
    
    # rotate script info
    flip_script_info(miss2_path, flip_code, output_path)

    # get statistic data
    dec_dict, exec_dict, bool_dict = read_and_get_statistical(miss2_path)

    # check if it has missions

    missions_path = miss2_path.parent / filename
    missions_output_folder = None

    if missions_path.exists():
        for mission_path in missions_path.iterdir():
            if str(mission_path).endswith(".mis"):
                #print(f"Found file: {str(mission_path)}")

                # create output folder, if it not exists
                if (missions_output_folder is None):
                    missions_output_folder = output_folder / filename

                    if (not missions_output_folder.exists()):
                        missions_output_folder.mkdir()

                # create a copy of the mission script

                filename = get_filename(mission_path)
                output_path = missions_output_folder / (filename + ".mis")
                #shutil.copy(mission_path, output_path)
                
                flip_script_info(mission_path, flip_code, output_path)

                # get statistic data
                miss_dec_dict, miss_exec_dict, miss_bool_dict = read_and_get_statistical(mission_path)
                sum_dict(dec_dict, miss_dec_dict)
                sum_dict(exec_dict, miss_exec_dict)
                sum_dict(bool_dict, miss_bool_dict)


    else:
        print("No missions script found.")
    
    #print(dec_dict)
    #print(exec_dict)
    
    # print statistic:

    dec_list = [ (freq, opcode) for opcode, freq in dec_dict.items() ]
    exec_list = [ (freq, opcode) for opcode, freq in exec_dict.items() ]
    bool_list = [ (freq, opcode) for opcode, freq in bool_dict.items() ]

    dec_list.sort(reverse=True)
    exec_list.sort(reverse=True)
    bool_list.sort(reverse=True)

    #dec_dict = sorted(dec_dict, key=lambda x: (x[0], x[1]), reverse=True)
    #exec_dict = sorted(exec_dict, key=lambda x: (x[0], x[1]), reverse=True)
    #bool_dict = sorted(bool_dict, key=lambda x: (x[0], x[1]), reverse=True)

    #print(bool_dict)

    print("\nDeclarations opcodes:")
    for freq, opcode in dec_list:
        print(f"{opcode}: {freq}")

    print("\nExecutions opcodes:")
    for freq, opcode in exec_list:
        print(f"{opcode}: {freq}")

    print("\nBoolean opcodes:")
    for freq, opcode in bool_list:
        print(f"{opcode}: {freq}")

    return 0

def main():
    parser = argparse.ArgumentParser(PROGRAM_NAME)
    parser.add_argument("miss2_path")
    parser.add_argument("-x", "--flip_x", action='store_true')
    parser.add_argument("-y", "--flip_y", action='store_true')
    args = parser.parse_args()

    if not args.miss2_path:
        print("Usage: python [program path] [miss2 path] [rotation = 0,90,180,270]")
        sys.exit(-1)

    if ("\\" not in args.miss2_path and "/" not in args.miss2_path):
        miss2_path = ROOT_DIR / args.miss2_path
    else:
        miss2_path = Path(args.miss2_path)

    #rotation_angle = int(args.rot_angle)
    flip_code = get_flip(args.flip_x, args.flip_y)    # 0 = No flip, 1 = Flip x, 2 = Flip y, 3 = Flip x & y

    if flip_code == FLIP_XY:
        print("ERROR: XY flip not supported yet. Rotate 180° instead.")
        sys.exit(-1)

    if (not miss2_path.exists()):
        print("File not found.")
        sys.exit(-1)

    if not str(miss2_path).endswith(".mis"):
        print(f"The file {miss2_path} isn't a miss2 script file")
        sys.exit(-1)

    main_flip_miss(miss2_path, flip_code)
    return


if __name__ == "__main__":
    main()
    #line = "	zaibatsu_leader_fm = CREATE_CHAR (221.50, 45.50, 3.00) 8 0 CRIMINAL_TYPE1 END"
    #print(has_coordinates(line))