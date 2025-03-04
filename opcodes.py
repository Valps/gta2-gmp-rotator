from enum import Enum, auto, verify, UNIQUE
import sys

# declare / create opcodes
DEC_OPCODES_LIST = ["OBJ_DATA", "GENERATOR", "CHAR_DATA", "CREATE_CHAR", "PARKED_CAR_DATA",
                    "CAR_DATA", "THREAD_WAIT_FOR_CHAR_IN_AREA", "LIGHT", "CRANE_DATA", "CREATE_OBJ", 
                     "CREATE_CAR", "CREATE_SOUND", "CREATE_LIGHT", "CREATE_GANG_CAR", "DOOR_DATA", 
                    "SOUND", "DECLARE_CRANE_POWERUP", "CRUSHER", "DESTRUCTOR", "SET_GANG_INFO", 
                    "RADIO_STATION", "CONVEYOR", "PLAYER_PED", "THREAD_WAIT_FOR_CHAR_IN_BLOCK"
                    ]

# execution opcodes
EXEC_OPCODES_LIST = ["POINT_ARROW_AT", "SET_CHAR_OBJECTIVE", "CHANGE_BLOCK", "REMOVE_BLOCK", 
                     "ADD_PATROL_POINT", "EXPLODE_NO_RING", "EXPLODE_LARGE", "EXPLODE_SMALL", 
                     "EXPLODE_WALL", "EXPLODE", "ADD_NEW_BLOCK", "WARP_FROM_CAR_TO_POINT", 
                    "LOWER_LEVEL", "SET_DIR_OF_TV_VANS", "PERFORM_SAVE_GAME", "SWITCH_ROAD"
                    ]

# boolean opcodes
BOOL_OPCODES_LIST = ["IS_CAR_IN_BLOCK", "LOCATE_CHARACTER_ANY_MEANS", "LOCATE_CHARACTER_BY_CAR", 
                     "LOCATE_CHARACTER_ON_FOOT", "IS_POINT_ONSCREEN", "CHECK_CAR_WRECKED_IN_AREA", 
                     "LOCATE_STOPPED_CHARACTER_ANY_MEANS", "LOCATE_STOPPED_CHARACTER_ON_FOOT", 
                     "LOCATE_STOPPED_CHARACTER_BY_CAR", "IS_CHAR_FIRING_IN_AREA"
                     ]

MAP_MAX_X = 256
MAP_MAX_Y = 256

@verify(UNIQUE)
class Cmd(Enum):
    OPCODE = auto()
    VAR_NAME = auto()
    EQUAL = auto()
    COORD_XY_F = auto()      # F = float
    COORD_XYZ_F = auto()
    COORD_XY_U8 = auto()     # U8 = unsigned integer 8 bits
    COORD_XYZ_U8 = auto()
    PARAM_ENUM = auto()         # generic enum param
    PARAM_NUM = auto()          # generic number param
    PARAM_XYZ_F = auto()
    PARAM_XYZ_WH_F = auto()
    WIDTH_HEIGHT = auto()
    ROTATION = auto()
    TWO_PARAMS_XYZ_U8 = auto()
    END = auto()
    OPT_PARAM_ENUM = auto()
    OPT_PARAM_NUM = auto()
    GANG_INFO = auto()
    PARAM_XYZ_F_OR_VAR = auto()
    COORD_XYZ_F_OR_VAR = auto()
    OPT_PARAM_ENUM_OR_NUM = auto()
    PARAM_FLOAT = auto()
    RGB = auto()
    TWO_PARAMS_XYZ_F = auto()
    COORD_XYZ_WH_F = auto()
    THREAD_AREA_TYPE = auto()
    THREAD_BLOCK_TYPE = auto()

# Rotation stuff

def rotate_tuple(coords: tuple, rotation_angle: int) -> tuple:
    # (123, 125)
    # (123, 125, 2)
    # (123.50, 125.50)
    # (123.50, 125.50, 2.0)
    # (123.50, 125.50, 2.0, 1.0, 1.0)
    coords_list = list(coords)
    if rotation_angle == 180:
        coords_list[0] = MAP_MAX_X - coords[0]
        coords_list[1] = MAP_MAX_Y - coords[1]
    elif rotation_angle == 90:
        coords_list[0] = MAP_MAX_Y - coords[1]
        coords_list[1] = coords[0]
        if len(coords_list) == 5:   # swap width and height
            coords_list[3], coords_list[4] = coords_list[4], coords_list[3]
    elif rotation_angle == 270:
        coords_list[0] = coords[1]
        coords_list[1] = MAP_MAX_X - coords[0]
        if len(coords_list) == 5:   # swap width and height
            coords_list[3], coords_list[4] = coords_list[4], coords_list[3]
    return tuple(coords_list)

def rotate_params(cmd: list, rotation_angle: int, rotation_param_indexes: list[int] | None = [], width_height_tuple_indexes: list[int] | None = []):
    for i, param in enumerate(cmd):
        if i in rotation_param_indexes:
            # rotate rotation parameter
            assert type(param) == int
            cmd[i] = (param - rotation_angle)   # rotate clockwise
            if cmd[i] < 0:      # mod 360
                cmd[i] += 360

        elif type(param) == tuple:
            # rotate position coordinates
            if i not in width_height_tuple_indexes:
                cmd[i] = rotate_tuple(param, rotation_angle)
            else:
                assert len(param) == 2
                # swap width and height if rot_ang = 90 or 270
                if rotation_angle == 90 or rotation_angle == 270:
                    cmd[i] = tuple(reversed(param)) #swap_tuple(param)
            
    return cmd


# Line parser stuff

def is_dec_opcode_rotatable(line):
    for opcode in DEC_OPCODES_LIST:
        if opcode in line:
            return True
    return False

def is_exec_opcode_rotatable(line):
    for opcode in EXEC_OPCODES_LIST:
        if opcode in line:
            return True
    return False

def is_bool_opcode_rotatable(line):
    for opcode in BOOL_OPCODES_LIST:
        if opcode in line:
            return True
    return False

def get_next_name(line) -> tuple[str, int]:
    """Get the next word in the line. It can be a var name (without being between parenthesis) 
    or an enum.

    It also returns the string position after that word. If it has reached the end of line, 
    return -1 instead.
    """
    name = ""
    for i, chr in enumerate(line):
        if not chr.isalnum() and not chr == '_':
            if len(name) != 0:
                return ( name , i )
            continue
        name += chr
    return ( name , -1 )    # finish of command line

def get_var_name(line):
    """Get the var name between parenthesis."""
    params_tuple = line[ line.find('(') + 1 : line.find(')') ]
    params = params_tuple.split(',')
    return params, line.find(')') + 1

def get_next_numeric_param(line):
    """Get the next parameter as number. It also returns the string position after it.

    If the line has ended after that number, it will return -1 as second return value.

    If there are not numbers until the end of line, the function will return (None, -2). This
    is the case of optional parameters that doesn't exists.
    """
    number_str = ""
    for i, chr in enumerate(line):
        if not chr.isdigit():
            if len(number_str) != 0:
                return ( int(number_str) , i )
            continue
        number_str += chr
    
    if number_str:
        return ( int(number_str) , -1 )  # last param: end of line
    else:
        return ( None , -2 )       # optional var doesn't exist

def is_next_param_num(line: str) -> bool:
    """Check if the next param is a number (return True) 
    or if it's either an enum or end of line (return False)
    """
    string = []
    for i, chr in enumerate(line):
        if not chr.isalnum():
            continue
        if chr.isdigit():   # check first alpha-num char
            return True     # it's a number
        else:
            return False    # it's an enum
    return False            # reached at the end of line (i.e. there is no param)

def get_next_float(line: str):
    """Get the next parameter as float. It also returns the string position after it."""
    float_str = ""
    for i, chr in enumerate(line):
        if not chr.isdigit() and chr != '.':
            if len(float_str) != 0:
                return ( float(float_str) , i )
            continue
        float_str += chr
    
    if float_str:
        return ( float(float_str) , -1 )  # last param: end of line
    else:
        return ( None , -2 )       # optional var doesn't exist

def get_coords(line, is_float: bool) -> tuple[tuple, int]:
    """Get the next coordinates in 'line' as a tuple.

    It also returns the string position of the first ')' plus one

    Ex: "(195.5, 15.5, 2.0) 25 0 END"  ->  (195.5, 15.5, 2.0) , 18
        "(195.5, 15.5) 25 0 END"       ->  (195.5, 15.5) , 13
    """
    end_point = line.find(')')
    coords_tuple = line[ line.find('(') + 1 : end_point ]

    params = coords_tuple.split(',')
    assert len(params) == 2 or len(params) == 3

    if is_float:
        params = [ float(param) for param in params ]
    else:
        params = [ int(param) for param in params ]
    
    return  tuple(params) , end_point + 1

def get_params_coords(line, num_params, is_float):
    """Get the next parameters in 'line' containing coordinates.

    If 'num_params' = 0, then 'line' must start with "(x,y,z)" or "(x,y,z, width, height)"
    If 'num_params' = 1, then 'line' must start with "(var1, x,y,z)" or "(var1, x,y,z, width, height)"
    If 'num_params' = 2, then 'line' must start with "(var1, var2, x,y,z)" etc.

    It also returns the string position at the end of the first parenthesis.
    """
    end_point = line.find(')')
    param_coords_tuple = line[ line.find('(') + 1 : end_point ]

    params = param_coords_tuple.split(',')

    if num_params:  # 1 or more parameters
        names = params[:num_params]
        coords = params[num_params:]
    else:           # coordinates only
        names = []
        coords = params

    assert len(coords) == 2 or len(coords) == 3 or len(coords) == 5

    if is_float:
        coords = [ float(coord.strip()) for coord in coords ]
    else:
        coords = [ int(coord.strip()) for coord in coords ]

    params = names
    params.append(tuple(coords))
    return ( params , end_point + 1 )

def get_gang_info(line):
    """Very specific function to get info from 'SET_GANG_INFO'. """
    param_tuple = line[ line.find('(') + 1 : line.find(')') ]
    params = param_tuple.split(',')
    assert len(params) == 12
    # cleaning
    params = [param.strip() for param in params]
    # SET_GANG_INFO (gang_name,remap, BASIC_WEAPON,ANGRY_WEAPON,HATE_WEAPON, arrow_colour,X,Y,Z, respect, MODEL,car_remap)
    x = float(params[6])
    y = float(params[7])
    z = float(params[8])

    # format coordinates to tuple
    formatted_params = params[:6]
    formatted_params.append( ( x, y, z ) )
    formatted_params += params[9:]

    return formatted_params

def get_info_manually(line, integer_indexes: list | None = [], float_indexes: list | None = []):
    """Get all parameters between parenthesis.
    
    If 'integer_indexes' is specified, then this function will convert each index to 'int' type.

    Analogously for 'float_indexes'.

    It also returns the string position at the end of parenthesis.
    """
    end_point = line.find(')')
    params = line[ line.find('(') + 1 : end_point ].split(',')
    
    # convert some params to int (if integer_indexes is specified)
    params = [ int(param) if i in integer_indexes else param for i, param in enumerate(params) ]
    # convert some params to float (if float_indexes is specified)
    params = [ float(param) if i in float_indexes else param for i, param in enumerate(params) ]

    return params, end_point + 1

def read_line(line, *args) -> list:
    """Read a command line string and return all parameters and opcodes from it as a list.
    """
    command = []
    pointer = 0
    for arg in args:
        
        is_float = True

        if (arg == Cmd.OPCODE 
            or arg == Cmd.VAR_NAME 
            or arg == Cmd.PARAM_ENUM
            or arg == Cmd.OPT_PARAM_ENUM):

            name, pointer = get_next_name(line)
            if name:
                command.append(name)
                if pointer == -1:       # has command line finished?
                    break
                line = line[pointer:]   # forward position in string
            
        elif arg == Cmd.EQUAL:
            line = line.replace('=','') # just remove the equal sign
            
        elif arg == Cmd.PARAM_NUM or arg == Cmd.ROTATION or arg == Cmd.OPT_PARAM_NUM:
            number, pointer = get_next_numeric_param(line)
            if number is not None:       # if it got a number
                command.append(number)
                if pointer == -1:
                    break               # command line has finished with last param
                line = line[pointer:]
            else:
                break                   # command line has finished with no optional last param

        elif (arg == Cmd.COORD_XYZ_F 
            or arg == Cmd.COORD_XYZ_U8
            or arg == Cmd.COORD_XY_F 
            or arg == Cmd.COORD_XY_U8 
            or arg == Cmd.WIDTH_HEIGHT
            or arg == Cmd.RGB):

            if arg == Cmd.COORD_XYZ_U8 or arg == Cmd.COORD_XY_U8 or arg == Cmd.RGB:
                is_float = False
            coords, pointer = get_coords(line, is_float=is_float)
            command.append(coords)      # note: always use "append" for "get_coords" just for ensure.
            line = line[pointer:]

        elif arg == Cmd.PARAM_XYZ_F or arg == Cmd.PARAM_XYZ_WH_F:
            params, pointer = get_params_coords(line, num_params=1, is_float=True)
            command.extend(params)
            line = line[pointer:]

        elif arg == Cmd.TWO_PARAMS_XYZ_U8 or arg == Cmd.TWO_PARAMS_XYZ_F:
            if arg == Cmd.TWO_PARAMS_XYZ_U8:
                is_float = False
            params, pointer = get_params_coords(line, num_params=2, is_float=is_float)
            command.extend(params)
            line = line[pointer:]

        elif arg == Cmd.PARAM_XYZ_F_OR_VAR:
            try:
                params, pointer = get_params_coords(line, num_params=1, is_float=True)
                command.extend(params)
            except AssertionError:
                name, pointer = get_var_name(line)
                command.extend(name)
            finally:
                line = line[pointer:]

        elif arg == Cmd.COORD_XYZ_F_OR_VAR:
            try:
                params, pointer = get_coords(line, is_float=True)
                command.append(params)
            except AssertionError:
                name, pointer = get_var_name(line)
                command.extend(name)
            finally:
                line = line[pointer:]
        
        elif arg == Cmd.OPT_PARAM_ENUM_OR_NUM:
            if is_next_param_num(line):
                number, pointer = get_next_numeric_param(line)
                command.append(number)
            else:
                name, pointer = get_next_name(line)
                if name:
                    command.append(name)
                    if pointer == -1:       # has command line finished?
                        break
                    line = line[pointer:]   # forward position in string

        elif arg == Cmd.PARAM_FLOAT:
            f_number, pointer = get_next_float(line)
            if f_number is not None:       # if it got a float number
                command.append(f_number)
                if pointer == -1:
                    break               # command line has finished with last param
                line = line[pointer:]
            else:
                break                   # command line has finished with no optional last param
        
        elif arg == Cmd.COORD_XYZ_WH_F:
            coords, pointer = get_params_coords(line, num_params=0, is_float=True)
            command.extend(coords)
            line = line[pointer:]

        elif arg == Cmd.THREAD_AREA_TYPE:
            raw_params, pointer = get_info_manually(line, float_indexes=[1,2,3,4,5])
            params = [raw_params[0]] + [tuple(raw_params[1:6])] + raw_params[6:]
            command.extend(params)
            line = line[pointer:]

        elif arg == Cmd.THREAD_BLOCK_TYPE:
            raw_params, pointer = get_info_manually(line, float_indexes=[1,2,3])
            params = [raw_params[0]] + [tuple(raw_params[1:4])] + raw_params[4:]
            command.extend(params)
            line = line[pointer:]

        elif arg == Cmd.GANG_INFO:
            params = get_gang_info(line)
            command.extend(params)
            break
        
        #elif arg == Cmd.RGB:



    # remove whitespaces
    for i, param in enumerate(command):
        if type(param) == str:
            command[i] = param.strip()

    return command

def get_comment(line):
    comment_pointer = line.find("//")
    if comment_pointer != -1:
        return line[comment_pointer + 2:]
    return None



# TODO
def rotate_xy(old_x, old_y, rotation_ang, is_float=True):
    new_x , new_y = old_x, old_y    # placeholder
    if not is_float:
        pass
    return

def rotate_dec_opcode(line: str, rotation_angle: int):

    # TODO: remove this; do it before calling this function
    if not is_dec_opcode_rotatable(line):
        return line     # do nothing
    
    new_line = line
    comment = get_comment(line)

    # remove comment from line if it exists
    if comment is not None:
        line = line[ : line.find("//") ]
    
    line_uppercase = line.upper()

    # now start parsing the line
    
    if "PLAYER_PED" in line_uppercase:
        # PLAYER_PED p1 = (97.50, 73.50, 2.00) 5 1
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION)
        cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[4])
        new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4])
        return new_line
    
    elif ("PARKED_CAR_DATA" in line_uppercase       # TODO: simplify: just CAR_DATA
        or "CAR_DATA" in line_uppercase):
        # PARKED_CAR_DATA auto14 = (38.50, 26.50, 255.00) 2 170 PICKUP
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM)
        cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[4])

        if len(cmd_rot) == 6:
            if len(cmd_rot[2]) == 3:
                new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5])
            else:
                new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5])

        elif len(cmd_rot) == 7:
            if len(cmd_rot[2]) == 3:
                new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6])
            else:
                new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6])

        return new_line

    elif "CRANE_DATA" in line_uppercase:
        # CRANE_DATA crane7 = (250.50, 39.50) 90 NO_HOMECRANE
        # CRANE_DATA crane1 = (4.50, 72.50) 200 NO_HOMECRANE FIRST (5.50, 75.50) 180
        # CRANE_DATA crane4 = (238.50, 64.50) 320 crane3 SECOND (235.50, 64.50) 180
        
        num_parenthesis = line.count('(')
        if num_parenthesis == 1:
            cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XY_F, Cmd.ROTATION, Cmd.VAR_NAME)
            cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[3])
            new_line = "{} {} = ({:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4])
        elif num_parenthesis == 2:
            cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XY_F, Cmd.ROTATION, Cmd.VAR_NAME, Cmd.PARAM_ENUM, Cmd.COORD_XY_F, Cmd.ROTATION)
            cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[3,7])
            new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {} ({:.2f}, {:.2f}) {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6][0], cmd_rot[6][1], cmd_rot[7])
        
        return new_line

    elif "CHAR_DATA" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM)
        if len(cmd) > 2: # if not just declaring var
            cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[4])
            if len(cmd_rot[2]) == 3:
                new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5])
            else:
                new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5])
        return new_line

    elif "CREATE_CHAR" in line_uppercase:
        # l_e_1_guard_1 = CREATE_CHAR (157.50, 9.50, 3.00) 8 0 CRIMINAL END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM)
        cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[4])
        if len(cmd_rot[2]) == 3:
            new_line = "{} = {} ({:.2f}, {:.2f}, {:.2f}) {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5])
        else:
            new_line = "{} = {} ({:.2f}, {:.2f}) {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5])
        return new_line

    elif "OBJ_DATA" in line_uppercase:
        # OBJ_DATA obj4 = (120.50, 120.50, 3.00) 0 TUNNEL_BLOCKER
        # OBJ_DATA shop1 = (6.50, 181.50, 2.00) 0 CAR_SHOP MACHINEGUN_SHOP
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM_OR_NUM)
        if len(cmd) > 2: # if not just declaring var
            cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[3])
            if len(cmd_rot) == 5:
                if len(cmd_rot[2]) == 3:
                    new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4])
                else:
                    new_line = "{} {} = ({:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4])
            elif len(cmd_rot) == 6:
                if len(cmd_rot[2]) == 3:
                    new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5])
                else:
                    new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5])
        
        return new_line

    elif "CREATE_OBJ" in line_uppercase:
        # l_e_1_molotov_1 = CREATE_OBJ (160.50, 11.50, 3.00) 0 COLLECT_04 10 END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM_OR_NUM)
        if type(cmd[-1]) == str and cmd[-1].upper() == "END":
            cmd.pop()

        cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[3])

        if len(cmd_rot[2]) == 3:
            new_line = "{} = {} ({:.2f}, {:.2f}, {:.2f}) {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5])
        else:
            new_line = "{} = {} ({:.2f}, {:.2f}) {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5])

        #print(cmd)
        return new_line
    
    elif ("CREATE_CAR" in line_uppercase 
        or "CREATE_GANG_CAR" in line_uppercase):
        # auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK END
        # name = CREATE_CAR (X,Y) remap rotation MODEL TRAILERMODEL END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM)
        if cmd[-1].upper() == "END":
            cmd.pop()

        cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[4])
        
        if len(cmd_rot) == 6:
            if len(cmd_rot[2]) == 3:
                new_line = "{} = {} ({:.2f}, {:.2f}, {:.2f}) {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5])
            else:
                new_line = "{} = {} ({:.2f}, {:.2f}) {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5])

        elif len(cmd_rot) == 7:
            if len(cmd_rot[2]) == 3:
                new_line = "{} = {} ({:.2f}, {:.2f}, {:.2f}) {} {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6])
            else:
                new_line = "{} = {} ({:.2f}, {:.2f}) {} {} {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6])
        return new_line

    elif "CREATE_SOUND" in line_uppercase:
        # sound28 = CREATE_SOUND (113.50, 123.50, 2.00) CHURCH_SINGING PLAY_FOREVER END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM)
        cmd_rot = rotate_params(cmd, rotation_angle)
        new_line = "{} = {} ({:.2f}, {:.2f}, {:.2f}) {} {} END".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4])
        return new_line

    elif "SOUND" in line_uppercase:
        # SOUND sound1 = (155.50, 139.50, 6.00) CHURCH_SINGING PLAY_FOREVER
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM)
        cmd_rot = rotate_params(cmd, rotation_angle)
        new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4])
        return new_line

    elif "RADIO_STATION" in line_uppercase:
        # RADIO_STATION radio1 = STATION_ZAIBATSU (247.50, 67.50)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.PARAM_ENUM, Cmd.COORD_XY_F)
        cmd_rot = rotate_params(cmd, rotation_angle)
        new_line = "{} {} = {} ({:.2f}, {:.2f})".format(cmd_rot[0], cmd_rot[1], cmd_rot[2], cmd_rot[3][0], cmd_rot[3][1])
        return new_line

    elif "DECLARE_CRANE_POWERUP" in line_uppercase:
        # DECLARE_CRANE_POWERUP (crane6, gen3, 197, 221, 3)
        cmd = read_line(line, Cmd.OPCODE, Cmd.TWO_PARAMS_XYZ_U8)
        cmd_rot = rotate_params(cmd, rotation_angle)
        print(cmd_rot)
        new_line = "{} ({}, {}, {}, {}, {})".format(cmd_rot[0], cmd_rot[1], cmd_rot[2], cmd_rot[3][0], cmd_rot[3][1], cmd_rot[3][2])
        return new_line

    elif "CONVEYOR" in line_uppercase:
        # CONVEYOR conv1 = (9.50, 77.50, 3.00) (1.00, 13.00) 0 1   xyz/xy width height speed_x speed_y
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.WIDTH_HEIGHT, Cmd.PARAM_NUM, Cmd.PARAM_NUM)
        cmd_rot = rotate_params(cmd, rotation_angle, width_height_tuple_indexes=[3])

        # rotate conveyor speeds
        if rotation_angle == 180:
            cmd_rot[4], cmd_rot[5] = -cmd_rot[4], -cmd_rot[5]
        elif rotation_angle == 90:
            cmd_rot[4], cmd_rot[5] = -cmd_rot[5], cmd_rot[4]
        elif rotation_angle == 270:
            cmd_rot[4], cmd_rot[5] = cmd_rot[5], -cmd_rot[4]

        if len(cmd_rot[2]) == 3:
            new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) ({:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3][0], cmd_rot[3][1], cmd_rot[4], cmd_rot[5])
        else:
            new_line = "{} {} = ({:.2f}, {:.2f}) ({:.2f}, {:.2f}) {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3][0], cmd_rot[3][1], cmd_rot[4], cmd_rot[5])
        
        return new_line

    elif "GENERATOR" in line_uppercase:
        # GENERATOR gen1 = (4.50, 83.50, 3.00) 0 MOVING_COLLECT_01 80 80
        # GENERATOR name = (X,Y) rotation WEAPON_TYPE mindelay maxdelay
        # GENERATOR name = (X,Y,Z) rotation WEAPON_TYPE mindelay maxdelay ammo
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.PARAM_NUM, Cmd.PARAM_NUM, Cmd.OPT_PARAM_NUM)
        cmd_rot = rotate_params(cmd, rotation_angle, rotation_param_indexes=[3])

        if len(cmd_rot) == 7:
            if len(cmd_rot[2]) == 3:
                new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6])
            else:
                new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6])
        elif len(cmd_rot) == 8:
            if len(cmd_rot[2]) == 3:
                new_line = "{} {} = ({:.2f}, {:.2f}, {:.2f}) {} {} {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[2][2], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6], cmd_rot[7])
            else:
                new_line = "{} {} = ({:.2f}, {:.2f}) {} {} {} {} {}".format(cmd_rot[0], cmd_rot[1], cmd_rot[2][0], cmd_rot[2][1], cmd_rot[3], cmd_rot[4], cmd_rot[5], cmd_rot[6], cmd_rot[7])

        return new_line

    elif "DESTRUCTOR" in line_uppercase:
        # DESTRUCTOR des1 = (9.50, 83.50, 3.00) (1.00, 1.00)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.WIDTH_HEIGHT)

        # xyz
        return new_line

    elif "CREATE_LIGHT" in line_uppercase:
        # r_h_2_prison_alarm_light_1 = CREATE_LIGHT (29.00, 241.00, 1.00) 7.99 255 (255, 0, 0) 30 100 5
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_FLOAT, Cmd.PARAM_NUM, Cmd.RGB, Cmd.PARAM_NUM, Cmd.PARAM_NUM, Cmd.PARAM_NUM)
        return new_line

    elif "LIGHT" in line_uppercase:
        # LIGHT light1 = (182.50, 174.50, 2.00) 3.00 255 (98, 204, 140) 0 0 0
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_FLOAT, Cmd.PARAM_NUM, Cmd.RGB, Cmd.PARAM_NUM, Cmd.PARAM_NUM, Cmd.PARAM_NUM)
        return new_line

    elif "DOOR_DATA" in line_uppercase:
        # DOOR_DATA door2 = DOUBLE (179, 81, 2) (178.00, 82.50, 2.00, 3.00, 2.00) 
        # BOTTOM 0 ANY_PLAYER_ONE_CAR CLOSE_WHEN_OPEN_RULE_FAILS 0 FLIP_RIGHT NOT_REVERSED
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.PARAM_ENUM, Cmd.COORD_XYZ_U8, Cmd.COORD_XYZ_WH_F,
                        Cmd.PARAM_ENUM, Cmd.PARAM_NUM, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.PARAM_NUM, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM_OR_NUM)
        return new_line

    elif "SET_GANG_INFO" in line_uppercase:
        # SET_GANG_INFO (redngang, 5, PISTOL, MACHINE_GUN, MOLOTOV, 4, 47.50, 49.50, 255.00, 1, PICKUP, 3)
        cmd = read_line(line, Cmd.OPCODE, Cmd.GANG_INFO)

        # xyz
        return new_line

    elif "CRUSHER" in line_uppercase:
        # CRUSHER crusher1 = (244.50, 243.50)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XY_F)

        # xy
        return new_line

    elif "THREAD_WAIT_FOR_CHAR_IN_AREA" in line_uppercase:  # and "THREAD_WAIT_FOR_CHAR_IN_AREA_ANY_MEANS"
        # THREAD_TRIGGER thr_kill_frenzy_6 = THREAD_WAIT_FOR_CHAR_IN_AREA (p1, 112.50, 241.50, 2.00, 0.50, 0.50, do_kill_frenzy_6:)
        # THREAD_TRIGGER thr_kill_frenzy_6 = THREAD_WAIT_FOR_CHAR_IN_AREA_ANY_MEANS (p1, 112.50, 241.50, 2.00, 0.50, 0.50, do_kill_frenzy_6:)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.THREAD_AREA_TYPE)
        return new_line

    elif "THREAD_WAIT_FOR_CHAR_IN_BLOCK" in line_uppercase:
        # THREAD_TRIGGER test1 = THREAD_WAIT_FOR_CHAR_IN_BLOCK (p1, 112.50, 241.50, 2.00, do_something:)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.THREAD_BLOCK_TYPE)
        return new_line

    return new_line

lines = [
"PLAYER_PED p1 = (113.50, 124.70, 255.00) 25 1",
"PARKED_CAR_DATA parked_church_car = (111.50, 126.50, 255.00) 1 121 SPIDER",
"OBJ_DATA obj4 = (120.50, 120.50, 3.00) 0 COLLECT_05",
"OBJ_DATA shop1 = (6.50, 181.50, 2.00) 0 CAR_SHOP MACHINEGUN_SHOP",
"OBJ_DATA obj1",
"CRANE_DATA crane6 = (195.50, 224.50) 180 crane5 SECOND (195.50, 221.50) 270",
"CRANE_DATA crane8 = (197.50, 245.50) 200 NO_HOMECRANE FIRST (197.50, 248.50) 180",
"CRANE_DATA crane10 = (234.50, 153.50) 0 NO_HOMECRANE",
"auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK END",
"auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK TRNKTRAIL END",
"sound28 = CREATE_SOUND (113.50, 123.50, 2.00) CHURCH_SINGING PLAY_FOREVER END",
"RADIO_STATION radio1 = STATION_ZAIBATSU (247.50, 67.50)",
"DECLARE_CRANE_POWERUP (crane6, gen3, 197, 221, 3)",
"CONVEYOR conv1 = (9.50, 77.50, 3.00) (1.00, 13.00) 0 1",
"GENERATOR gen1 = (4.50, 83.50, 3.00) 0 MOVING_COLLECT_01 80 80",
"GENERATOR molotova2 = ( 142.5 , 133.5 , 5.0 ) 0 COLLECT_04 1800 1800 20 ",
"DESTRUCTOR des1 = (9.50, 83.50, 3.00) (1.00, 1.00)",
"SET_GANG_INFO (sciegang, 7, PISTOL, MACHINE_GUN, FLAME_THROWER, 5, 211.50, 219.50, 255.00, 1, STRATOSB, 10)",
"r_e_1_pickup_car = CREATE_GANG_CAR (24.00, 41.50, 2.00) 3 90 PICKUP END",
"l_e_1_molotov_1 = CREATE_OBJ (160.50, 11.50, 3.00) 0 COLLECT_04 10 END",
"l_e_1_guard_1 = CREATE_CHAR (157.50, 9.50, 3.00) 8 0 CRIMINAL END",
"LIGHT light1 = (182.50, 174.50, 2.00) 3.00 255 (98, 204, 140) 0 0 0",
"r_h_2_prison_alarm_light_1 = CREATE_LIGHT (29.00, 241.00, 1.00) 7.99 255 (255, 0, 0) 30 100 5",
"DOOR_DATA door12 = DOUBLE (77, 200, 2) (76.00, 201.50, 2.00, 3.00, 2.00) BOTTOM 0 ANY_PLAYER_ONE_CAR CLOSE_WHEN_OPEN_RULE_FAILS 0 FLIP_RIGHT NOT_REVERSED",
"CRUSHER crusher1 = (244.50, 243.50)",
"SOUND sound1 = (155.50, 139.50, 6.00) CHURCH_SINGING PLAY_FOREVER",
"THREAD_TRIGGER thr_kill_frenzy_6 = THREAD_WAIT_FOR_CHAR_IN_AREA (p1, 112.50, 241.50, 2.00, 0.50, 0.50, do_kill_frenzy_6:)",
"THREAD_TRIGGER thr_kill_frenzy_6 = THREAD_WAIT_FOR_CHAR_IN_AREA_ANY_MEANS (p1, 112.50, 241.50, 2.00, 0.50, 0.50, do_kill_frenzy_6:)",
"THREAD_TRIGGER test1 = THREAD_WAIT_FOR_CHAR_IN_BLOCK (p1, 112.50, 241.50, 2.00, do_something:)",
]

#line_1 = "SOUND sound1 = (155.50, 139.50, 6.00) CHURCH_SINGING PLAY_FOREVER"
#rotate_dec_opcode(line_1, 0)

for line in lines:
    new_line = rotate_dec_opcode(line, 270)
    print(new_line)


def rotate_exec_opcode(line: str, rotation_angle: int):

    # TODO: remove this; do it before calling this function
    if not is_exec_opcode_rotatable(line):
        return line     # do nothing
    
    new_line = line
    comment = get_comment(line)

    # remove comment from line if it exists
    if comment is not None:
        line = line[ : line.find("//") ]
    
    line_uppercase = line.upper()
    
    if "POINT_ARROW_AT" in line_uppercase:      #  also "LEVEL_END_POINT_ARROW_AT"
        
        cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_XYZ_F_OR_VAR)
        print(cmd)
        # xyz
        
        return new_line

    elif "EXPLODE_WALL" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_ENUM)

        # xyz
        print(cmd)
        return new_line
    
    elif ("EXPLODE_NO_RING" in line_uppercase       # TODO: refactor to EXPLODE
          or "EXPLODE_LARGE" in line_uppercase
          or "EXPLODE_SMALL" in line_uppercase
          or "EXPLODE" in line_uppercase):
        
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XYZ_F_OR_VAR)

        # xyz
        print(cmd)
        return new_line

    elif "SET_CHAR_OBJECTIVE" in line_uppercase:
        # SET_CHAR_OBJECTIVE (charname, objective type)
        # SET_CHAR_OBJECTIVE (charname, objective type, second_item)
        # SET_CHAR_OBJECTIVE (m_5_chr1, GOTO_AREA_ON_FOOT, 17.50, 200.50, 2.00)
        # SET_CHAR_OBJECTIVE (m_13_chr2, FOLLOW_CAR_ON_FOOT_WITH_OFFSET, m_13_auto1, 90, 1.00)

        # filter the cases in which there are rotation or coordinates
        params = line[ line.find('(') : line.find(')') + 1 ].split(',')
        if len(params) == 5:
            if "FOLLOW_CAR_ON_FOOT_WITH_OFFSET" in line:
                cmd = read_line(line, Cmd.OPCODE)
                params, pointer = get_info_manually(line, integer_indexes=[3], float_indexes=[4])
                cmd.extend(params)
            else:
                cmd = read_line(line, Cmd.OPCODE, Cmd.TWO_PARAMS_XYZ_F)
            print(cmd)

    elif "ADD_PATROL_POINT" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_XYZ_F)
        print(cmd)

    elif "REMOVE_BLOCK" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE)
        params, pointer = get_info_manually(line, integer_indexes=[0,1,2])
        cmd.append( tuple(params[0:3]) )
        cmd.append(params[-1])
        print(cmd)

    elif "ADD_NEW_BLOCK" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XYZ_U8)
        print(cmd)

    elif "CHANGE_BLOCK" in line_uppercase:
        if "SIDE" in line_uppercase:
            cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_ENUM, Cmd.COORD_XYZ_U8, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.ROTATION, Cmd.PARAM_NUM)
            print(cmd)
        elif "LID" in line_uppercase:
            cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_ENUM, Cmd.COORD_XYZ_U8, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_NUM)
            print(cmd)

    elif "SWITCH_ROAD" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_ENUM, Cmd.COORD_XYZ_U8)

        # xyz
        print(cmd)
        return new_line

    elif "LOWER_LEVEL" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XY_U8, Cmd.COORD_XY_U8)

        # xy xy
        print(cmd)
        return new_line
    
    elif "WARP_FROM_CAR_TO_POINT" in line_uppercase:
        # WARP_FROM_CAR_TO_POINT (name, X,Y,Z, rotation)
        # WARP_FROM_CAR_TO_POINT (p1, 200.50, 125.50, 2.00, 0)
        cmd = read_line(line, Cmd.OPCODE)
        params, pointer = get_info_manually(line, float_indexes=[1,2,3], integer_indexes=[4])
        cmd.append( tuple(params[1:4]) )
        cmd.append(params[-1])

        # xyz
        print(cmd)
        return new_line
    
    elif "PERFORM_SAVE_GAME" in line_uppercase:
        # PERFORM_SAVE_GAME (thr_savepoint_1, 113.00, 123.00, 2.00, 1.00, 1.00)
        cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_XYZ_WH_F)

        # xyz
        print(cmd)

    elif "SET_DIR_OF_TV_VANS" in line_uppercase:
        # SET_DIR_OF_TV_VANS (113.00, 123.00)
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XY_F)

        # xy
        print(cmd)




lines2 = [
    "POINT_ARROW_AT (arrow1, auto1)", 
    "POINT_ARROW_AT (arrow1, 43.50, 249.50, 2.00)",
    "EXPLODE_LARGE (143.5, 151.5, 2.0)",
    "EXPLODE_LARGE (car8)",
    "EXPLODE_WALL (143.5, 151.5, 2.0) TOP",
    "SET_CHAR_OBJECTIVE (m_13_chr2, FOLLOW_CAR_ON_FOOT_WITH_OFFSET, m_13_auto1, 90, 1.00)",
    "SET_CHAR_OBJECTIVE (m_5_chr1, GOTO_AREA_ON_FOOT, 17.50, 200.50, 2.00)",
    "SWITCH_ROAD ON (255,106,2)",
    "CHANGE_BLOCK SIDE (200, 125, 2) BOTTOM NOT_WALL NOT_BULLET NOT_FLAT NOT_FLIP 0 791",
    "CHANGE_BLOCK LID (179, 228, 1) NOT_FLAT NOT_FLIP 0 0 978",
    "ADD_NEW_BLOCK (180, 232, 1)",
    "REMOVE_BLOCK (177, 229, 1, DONT_DROP)",
    "ADD_PATROL_POINT (z_e_1_srs_guard, 175.50, 230.50, 2.00)",
    "WARP_FROM_CAR_TO_POINT (p1, 200.50, 125.50, 2.00, 0)", 
    "PERFORM_SAVE_GAME (thr_savepoint_1, 113.00, 123.00, 2.00, 1.00, 1.00)", 
    "SET_DIR_OF_TV_VANS (113.00, 123.00)", 
]

#for line in lines2:
#    rotate_exec_opcode(line, 0)

#rotate_exec_opcode(line, 0)






def rotate_bool_opcode(line: str, rotation_angle: int):

    # TODO: remove this; do it before calling this function
    if not is_bool_opcode_rotatable(line):
        return line     # do nothing
    
    new_line = line
    
    line_uppercase = line.upper()
    
    if ("IS_CAR_IN_BLOCK" in line_uppercase
        or "LOCATE_CHARACTER_" in line_uppercase
        or "LOCATE_STOPPED_" in line_uppercase
        or "CHECK_CAR_WRECKED_IN_AREA" in line_uppercase
        or "IS_CHAR_FIRING_IN_AREA" in line_uppercase):
        # IS_CAR_IN_BLOCK(r_m_3_tank_car, 235.50, 117.50, 2.00, 1.00, 1.00)
        # LOCATE_CHARACTER_ANY_MEANS(p1, 153.50, 138.50, 2.00, 1.00, 1.00)
        # LOCATE_CHARACTER_BY_CAR(p1, 246.50, 238.50, 2.00, 10.00, 4.00)
        # LOCATE_CHARACTER_ON_FOOT(p1, 45.50, 75.50, 3.00, 1.00, 1.00)
        # CHECK_CAR_WRECKED_IN_AREA(r_e_1_pickup_car, 48.50, 20.50, 2.00, 3.00, 1.00)
        # IS_CHAR_FIRING_IN_AREA(p1, 45.50, 75.50, 3.00, 1.00, 1.00)
        cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_XYZ_WH_F)
        print(cmd)
        
        return new_line
    
    elif "IS_POINT_ONSCREEN" in line_uppercase:
        # IS_POINT_ONSCREEN(44.50, 197.50, 4.00)
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XYZ_F)
        print(cmd)
    

lines3 = [
    "IS_CAR_IN_BLOCK(r_m_3_tank_car, 235.50, 117.50, 2.00, 1.00, 1.00)", 
    "LOCATE_CHARACTER_ANY_MEANS(p1, 153.50, 138.50, 2.00, 1.00, 1.00)",
    "LOCATE_CHARACTER_BY_CAR(p1, 246.50, 238.50, 2.00, 10.00, 4.00)",
    "LOCATE_CHARACTER_ON_FOOT(p1, 45.50, 75.50, 3.00, 1.00, 1.00)",
    "CHECK_CAR_WRECKED_IN_AREA(r_e_1_pickup_car, 48.50, 20.50, 2.00, 3.00, 1.00)",
    "IS_CHAR_FIRING_IN_AREA(p1, 45.50, 75.50, 3.00, 1.00, 1.00)",
]

for line in lines3:
    rotate_bool_opcode(line, 0)



line1 = " WHILE_EXEC ( NOT ( LOCATE_CHARACTER_ON_FOOT(p1, 159.50, 5.50, 2.00, 1.00, 1.00) ) )"

line2 = "IF ( ( ( IS_CAR_IN_BLOCK(r_m_3_tank_car, 235.50, 117.50, 2.00, 1.00, 1.00) )"
line3 = "OR ( IS_CAR_IN_BLOCK(r_m_3_tank_car, 236.50, 117.50, 2.00, 1.00, 1.00) ) )"

line4 = "IF ( ( ( IS_CAR_IN_BLOCK(r_m_3_tank_car, 235.50, 117.50, 2.00, 1.00, 1.00) ) OR ( IS_CAR_IN_BLOCK(r_m_3_tank_car, 236.50, 117.50, 2.00, 1.00, 1.00) ) ) AND ( r_m_3_cop_level_6_changed = 0 ) ) "

def get_boolean_command_from_line(line: str, opcode: str, offset: int | None = 0):
    """Get the next boolean opcode in 'line'.
    TODO: explain more
    """
    line_to_parse = line[offset:]
    if opcode in line_to_parse:
        opcode_str_pos = line_to_parse.find(opcode)

        # cut the left part
        left_part = line_to_parse[ : opcode_str_pos ]
        cmd_line = line_to_parse[ opcode_str_pos : ]  

        # cut the right part
        end_pos = cmd_line.find(')')
        right_part = cmd_line[ end_pos + 1 : ]
        cmd_line = cmd_line[ : end_pos + 1 ]
        
        return line[:offset] + left_part, cmd_line, right_part
    else:
        print(f"ERROR! Opcode not found in string: {line}")
        sys.exit(-1)

#results = get_boolean_command_from_line(line4, "IS_CAR_IN_BLOCK")
#for result in results:
#    print(result)

def get_bool_opcodes_from_line(line):
    opcodes_list = []
    pointer = 0
    while pointer != -1:
        name, pointer = get_next_name(line)
        if pointer != -1:
            line = line[pointer:]
            name = name.upper()
            if name in BOOL_OPCODES_LIST:
                opcodes_list.append(name)
    return opcodes_list

#print(get_bool_opcodes_from_line(line4))

def protoype_test(line):
    opcodes_in_line = get_bool_opcodes_from_line(line)      # EX:  ["IS_CAR_IN_BLOCK", "IS_CAR_IN_BLOCK", "LOCATE_CHAR_ANY_MEANS"]
    #result = line
    offset = 0
    for opcode in opcodes_in_line:
        left, cmd, right = get_boolean_command_from_line(line, opcode, offset)
        # cmd = rotate_bool_opcode(cmd, rotation)
        line = left + cmd + right
        offset += len(left) + len(cmd)
    return line


#print(protoype_test(line4))

