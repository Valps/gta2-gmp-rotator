from enum import Enum, auto

OPCODES_LIST = ["PLAYER_PED", "PARKED_CAR_DATA", "RADIO_STATION", "CONVEYOR", "GENERATOR",
            "DESTRUCTOR", "CRANE_DATA", "DECLARE_CRANE_POWERUP", "OBJ_DATA", "CREATE_CAR", 
            "CREATE_SOUND"]

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

def is_opcode_rotatable(line):
    for opcode in OPCODES_LIST:
        if opcode in line:
            return True
    return False

def get_next_name(line):
    name = ""
    for i, chr in enumerate(line):
        if not chr.isalnum() and not chr == '_':
            if len(name) != 0:
                return ( name , i )
            continue
        name += chr
    return ( name , -1 )    # finish of command line

def get_next_numeric_param(line):
    number_str = ""
    for i, chr in enumerate(line):
        if not chr.isdigit():
            if len(number_str) != 0:
                return ( int(number_str) , i )
            continue
        number_str += chr
    
    if number_str:
        return ( int(number_str) , -1 )
    else:
        return ( 0 , -2 )

def get_coords(line, is_float):
    coords_tuple = line[ line.find('(') + 1 : line.find(')') ]

    params = coords_tuple.split(',')
    assert len(params) == 2 or len(params) == 3

    if is_float:
        params = [ float(param) for param in params ]
    else:
        params = [ int(param) for param in params ]

    return ( params , line.find(')') + 1, len(params) )

def get_params_coords(line, num_params, is_float):
    param_coords_tuple = line[ line.find('(') + 1 : line.find(')') ]

    params = param_coords_tuple.split(',')
    names = params[:num_params]
    coords = params[num_params:]

    assert len(coords) == 2 or len(coords) == 3 or len(coords) == 5

    if is_float:
        coords = [ float(coord.strip()) for coord in coords ]
    else:
        coords = [ int(coord.strip()) for coord in coords ]

    params = names + coords
    return ( params , line.find(')') + 1, len(coords) )

def read_line(line, *args):
    command = []
    num_coords_array = []
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
            line = line.replace('=','')
            #command.append('=')
        elif arg == Cmd.PARAM_NUM or arg == Cmd.ROTATION or arg == Cmd.OPT_PARAM_NUM:
            number, pointer = get_next_numeric_param(line)
            if pointer != -2:       # has command line finished?
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
            coords, pointer, num_coords = get_coords(line, is_float=is_float)
            command.extend(coords)       # concatene lists
            num_coords_array.append(num_coords)  # 2 or 3
            line = line[pointer:]

        #elif arg == Cmd.COORD_XY_F or arg == Cmd.COORD_XY_U8 or arg == Cmd.WIDTH_HEIGHT:
        #    if arg == Cmd.COORD_XY_U8:
        #        is_float = False
        #    xy_coords, pointer = get_coords(line, is_float=is_float)
        #    command.extend(xy_coords)       # concatene lists
        #    line = line[pointer:]

        elif arg == Cmd.PARAM_XYZ_F or arg == Cmd.PARAM_XYZ_WH_F:
            params, pointer, num_coords = get_params_coords(line, num_params=1, is_float=True)
            command.extend(params)
            num_coords_array.append(num_coords)  # 3 or 5
            line = line[pointer:]

        elif arg == Cmd.TWO_PARAMS_XYZ_U8:
            params, pointer, num_coords = get_params_coords(line, num_params=2, is_float=False)
            command.extend(params)
            num_coords_array.append(num_coords)  # 3 or 5
            line = line[pointer:]

        #elif arg == Cmd.OPTIONAL_PARAM_ENUM:        # TODO: merge with the first if?
        #    param, pointer = get_next_name(line)
        #    if param:
        #        command.extend(params)
        #        line = line[pointer:]

    return command, num_coords_array

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

def rotate_opcode(line: str, rotation_angle: int):

    if not is_opcode_rotatable(line):
        return line     # do nothing
    
    new_line = line
    comment = get_comment(line)

    line_uppercase = line.upper()
    
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

        # xyz/xy
        print(cmd)
        return new_line
    
    elif "CREATE_CAR" in line_uppercase:
        # auto9 = CREATE_CAR (231.50, 90.50, 2.00) 0 90 TANK END
        # name = CREATE_CAR (X,Y) remap rotation MODEL TRAILERMODEL END
        cmd = read_line(line, Cmd.VAR_NAME, Cmd.EQUAL, Cmd.OPCODE, Cmd.COORD_XYZ_F, Cmd.PARAM_NUM, Cmd.ROTATION, Cmd.PARAM_ENUM, Cmd.OPT_PARAM_ENUM)
        if cmd[-1] == "END":
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
    return


#line = "PLAYER_PED p1 = (97.50, 73.50, 2.00) 5 1"
#line = "PARKED_CAR_DATA auto14 = (38.50, 26.50, 255.00) 2 170 PICKUP"
#line = "OBJ_DATA obj4 = (120.50, 120.50, 3.00) 0 COLLECT_05"
#line = "OBJ_DATA shop1 = (6.50, 181.50, 2.00) 0 CAR_SHOP MACHINEGUN_SHOP"
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
line = "DESTRUCTOR des1 = (9.50, 83.50, 3.00) (1.00, 1.00)"

rotate_opcode(line, 0)