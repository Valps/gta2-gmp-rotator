from enum import Enum, auto

# declare / create opcodes
DEC_OPCODES_LIST = ["PLAYER_PED", "PARKED_CAR_DATA", "RADIO_STATION", "CONVEYOR", "GENERATOR",
            "DESTRUCTOR", "CRANE_DATA", "DECLARE_CRANE_POWERUP", "OBJ_DATA", "CREATE_CAR", 
            "CREATE_SOUND", "CAR_DATA", "SET_GANG_INFO", "CREATE_GANG_CAR"]

# execution opcodes
EXEC_OPCODES_LIST = ["POINT_ARROW_AT", "LEVEL_END_POINT_ARROW_AT", "EXPLODE",
                "EXPLODE_NO_RING", "EXPLODE_LARGE", "EXPLODE_SMALL", "EXPLODE_WALL"]

# boolean opcodes
BOOL_OPCODES_LIST = ["IS_CAR_IN_BLOCK", "CHECK_CAR_WRECKED_IN_AREA", "LOCATE_CHARACTER_ANY_MEANS", 
                     "LOCATE_CHARACTER_ON_FOOT", "LOCATE_CHARACTER_BY_CAR", 
                     "LOCATE_STOPPED_CHARACTER_ANY_MEANS", "LOCATE_STOPPED_CHARACTER_ON_FOOT", 
                     "LOCATE_STOPPED_CHARACTER_BY_CAR"]

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

    If 'num_params' = 1, then 'line' must start with "(var1, x,y,z)"
    If 'num_params' = 2, then 'line' must start with "(var1, var2, x,y,z)" etc.

    It also returns the string position at the end of the first parenthesis.
    """
    end_point = line.find(')')
    param_coords_tuple = line[ line.find('(') + 1 : end_point ]

    params = param_coords_tuple.split(',')
    names = params[:num_params]
    coords = params[num_params:]

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

def read_line(line, *args) -> list:
    """Read a command line string and return all parameters and opcodes from it as a list."""
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
                line = line[pointer:]
            
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
            or arg == Cmd.WIDTH_HEIGHT):

            if arg == Cmd.COORD_XYZ_U8 or arg == Cmd.COORD_XY_U8:
                is_float = False
            coords, pointer = get_coords(line, is_float=is_float)
            command.append(coords)      # note: always use "append" for "get_coords" just for ensure.
            line = line[pointer:]

        elif arg == Cmd.PARAM_XYZ_F or arg == Cmd.PARAM_XYZ_WH_F:
            params, pointer = get_params_coords(line, num_params=1, is_float=True)
            command.extend(params)
            line = line[pointer:]

        elif arg == Cmd.TWO_PARAMS_XYZ_U8:
            params, pointer = get_params_coords(line, num_params=2, is_float=False)
            command.extend(params)
            line = line[pointer:]

        elif arg == Cmd.GANG_INFO:
            params = get_gang_info(line)
            command.extend(params)
            break

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
        line_uppercase = line[ : line.find("//") ].upper()
    else:
        line_uppercase = line.upper()

    # now start parsing the line
    
    if "PLAYER_PED" in line_uppercase:
        # PLAYER_PED p1 = (97.50, 73.50, 2.00) 5 1
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION)
        print(cmd)
        # xyz
        #new_line = "PLAYER_PED {} = ({}, {}, {}) {} {}".format(cmd[1], cmd[2], cmd[3], cmd[4], cmd[5], cmd[6])
        #print(new_line)
        return new_line
    
    elif "PARKED_CAR_DATA" in line_uppercase:
        # PARKED_CAR_DATA auto14 = (38.50, 26.50, 255.00) 2 170 PICKUP
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM)

        # xyz/xy
        print(cmd)
        return new_line

    elif "CRANE_DATA" in line_uppercase:

        # CRANE_DATA crane1 = (4.50, 72.50) 200 NO_HOMECRANE FIRST (5.50, 75.50) 180
        # CRANE_DATA crane4 = (238.50, 64.50) 320 crane3 SECOND (235.50, 64.50) 180
        # CRANE_DATA crane7 = (250.50, 39.50) 90 NO_HOMECRANE
        num_parenthesis = line.count('(')
        if num_parenthesis == 1:
            cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XY_F, Cmd.ROTATION, Cmd.VAR_NAME)
        elif num_parenthesis == 2:
            cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XY_F, Cmd.ROTATION, Cmd.VAR_NAME, Cmd.PARAM_ENUM, Cmd.COORD_XY_F, Cmd.ROTATION)
        print(cmd)

    elif "OBJ_DATA" in line_uppercase:
        # OBJ_DATA obj4 = (120.50, 120.50, 3.00) 0 TUNNEL_BLOCKER
        # OBJ_DATA shop1 = (6.50, 181.50, 2.00) 0 CAR_SHOP MACHINEGUN_SHOP
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM)
        if len(cmd) > 2: # if not just declaring var
            # xyz/xy
            print(cmd)
        return new_line
    
    elif "CAR_DATA" in line_uppercase:      # TODO: merge with OBJ_DATA
        # CAR_DATA name = (X,Y) remap rotation MODEL
        # CAR_DATA name = (X,Y,Z) remap rotation MODEL TRAILERMODEL
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM)
        if len(cmd) > 2: # if not just declaring var
            # xyz/xy
            print(cmd)
        return new_line
    
    elif "CREATE_CAR" in line_uppercase or "CREATE_GANG_CAR" in line_uppercase:
        # auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK END
        # name = CREATE_CAR (X,Y) remap rotation MODEL TRAILERMODEL END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM)
        if cmd[-1].upper() == "END":
            cmd.pop()

        # xyz/xy
        print(cmd)

    elif "CREATE_SOUND" in line_uppercase:
        # sound28 = CREATE_SOUND (113.50, 123.50, 2.00) CHURCH_SINGING PLAY_FOREVER END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_ENUM, Cmd.PARAM_ENUM)
        print(cmd)

    elif "RADIO_STATION" in line_uppercase:
        # RADIO_STATION radio1 = STATION_ZAIBATSU (247.50, 67.50)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.PARAM_ENUM, Cmd.COORD_XY_F)
        print(cmd)

    elif "DECLARE_CRANE_POWERUP" in line_uppercase:
        # DECLARE_CRANE_POWERUP (crane6, gen3, 197, 221, 3)
        cmd = read_line(line, Cmd.OPCODE, Cmd.TWO_PARAMS_XYZ_U8)
        print(cmd)

    elif "CONVEYOR" in line_uppercase:
        # CONVEYOR conv1 = (9.50, 77.50, 3.00) (1.00, 13.00) 0 1   xyz/xy width height speed_x speed_y
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.WIDTH_HEIGHT, Cmd.PARAM_NUM, Cmd.PARAM_NUM)

        # xyz/xy
        print(cmd)

    elif "GENERATOR" in line_uppercase:
        # GENERATOR gen1 = (4.50, 83.50, 3.00) 0 MOVING_COLLECT_01 80 80
        # GENERATOR name = (X,Y) rotation WEAPON_TYPE mindelay maxdelay
        # GENERATOR name = (X,Y,Z) rotation WEAPON_TYPE mindelay maxdelay ammo
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.PARAM_NUM, Cmd.PARAM_NUM, Cmd.OPT_PARAM_NUM)

        # xyz/xy
        print(cmd)

    elif "DESTRUCTOR" in line_uppercase:
        # DESTRUCTOR des1 = (9.50, 83.50, 3.00) (1.00, 1.00)
        cmd = read_line(line, Cmd.OPCODE, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.COORD_XYZ_F, Cmd.WIDTH_HEIGHT)

        # xyz
        print(cmd)
    
    elif "SET_GANG_INFO" in line_uppercase:
        # SET_GANG_INFO (redngang, 5, PISTOL, MACHINE_GUN, MOLOTOV, 4, 47.50, 49.50, 255.00, 1, PICKUP, 3)
        cmd = read_line(line, Cmd.OPCODE, Cmd.GANG_INFO)

        # xyz
        print(cmd)
    return


#line = "PLAYER_PED p1 = (97.50, 73.50, 2.00) 5 1"
#line = "PARKED_CAR_DATA auto14 = (38.50, 26.50, 255.00) 2 170 PICKUP"
#line = "OBJ_DATA obj4 = (120.50, 120.50, 3.00) 0 COLLECT_05"
#line = "OBJ_DATA shop1 = (6.50, 181.50, 2.00) 0 CAR_SHOP MACHINEGUN_SHOP"
#line = "OBJ_DATA obj1"
#line = "CRANE_DATA crane1 = (4.50, 72.50) 200 NO_HOMECRANE FIRST (5.50, 75.50) 180"
#line = "CRANE_DATA crane4 = (238.50, 64.50) 320 crane3 SECOND (235.50, 64.50) 180"
#line = "CRANE_DATA crane7 = (250.50, 39.50) 90 NO_HOMECRANE"
#line = "auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK END"
#line = "auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK TRNKTRAIL END"
#line = "sound28 = CREATE_SOUND (113.50, 123.50, 2.00) CHURCH_SINGING PLAY_FOREVER END"
#line = "RADIO_STATION radio1 = STATION_ZAIBATSU (247.50, 67.50)"
#line = "DECLARE_CRANE_POWERUP (crane6, gen3, 197, 221, 3)"
#line = "CONVEYOR conv1 = (9.50, 77.50, 3.00) (1.00, 13.00) 0 1"
#line = "GENERATOR gen1 = (4.50, 83.50, 3.00) 0 MOVING_COLLECT_01 80 80"
#line = "DESTRUCTOR des1 = (9.50, 83.50, 3.00) (1.00, 1.00)"
#line = "SET_GANG_INFO (sciegang, 7, PISTOL, MACHINE_GUN, FLAME_THROWER, 5, 211.50, 219.50, 255.00, 1, STRATOSB, 10)"
#line = "r_e_1_pickup_car = CREATE_GANG_CAR (24.00, 41.50, 2.00) 3 90 PICKUP END"

#rotate_dec_opcode(line, 0)


def rotate_exec_opcode(line: str, rotation_angle: int):

    # TODO: remove this; do it before calling this function
    if not is_exec_opcode_rotatable(line):
        return line     # do nothing
    
    new_line = line
    comment = get_comment(line)

    line_uppercase = line.upper()
    
    if "POINT_ARROW_AT" in line_uppercase or "LEVEL_END_POINT_ARROW_AT" in line_uppercase:
        
        cmd = read_line(line, Cmd.OPCODE, Cmd.PARAM_XYZ_F_OR_VAR)
        print(cmd)
        # xyz
        
        return new_line

    elif "EXPLODE_WALL" in line_uppercase:
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_ENUM)

        # xyz
        print(cmd)
        return new_line
    
    elif ("EXPLODE_NO_RING" in line_uppercase
          or "EXPLODE_LARGE" in line_uppercase
          or "EXPLODE_SMALL" in line_uppercase
          or "EXPLODE" in line_uppercase):
        
        cmd = read_line(line, Cmd.OPCODE, Cmd.COORD_XYZ_F_OR_VAR)

        # xyz
        print(cmd)
        return new_line




#line = "POINT_ARROW_AT (arrow1, auto1)"
line = "POINT_ARROW_AT (arrow1, 43.50, 249.50, 2.00)"

#line = "EXPLODE_LARGE (143.5, 151.5, 2.0)"
#line = "EXPLODE_WALL (143.5, 151.5, 2.0) TOP"

rotate_exec_opcode(line, 0)