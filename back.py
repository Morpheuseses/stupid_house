import consts as c 

import pygame 

# BASIC STRUCTS 
class HasTemp:
    def __init__(self, row, col, curtemp=0,settemp=0):
        self.curtemp = curtemp
        self.settemp = settemp
        self.X = col
        self.Y = row

class Heater(HasTemp):
    def __init__(self, row, col, curtemp=100, settemp=100,sensor_group=0):
        super().__init__(row, col, curtemp=curtemp,settemp=settemp)
        self.sensor_group = sensor_group
class Window(HasTemp):
    def __init__(self, row, col, curtemp=0, settemp=0,sensor_group=0):
        super().__init__(row, col, curtemp=curtemp,settemp=settemp)
        self.sensor_group = sensor_group
        self.open = False
class Door(HasTemp):
    def __init__(self, row, col,curtemp=0, settemp=0,sensor_group=0):
        super().__init__(row, col, curtemp=curtemp,settemp=settemp)
        self.sensor_group = sensor_group
        self.open = False

class Sensor(HasTemp):
    def __init__(self, row, col):
        super().__init__(row, col)

# Main functions
def recalc():
    flush_history()
    change_sensor()
    calc_average_sensors()
    recalc_temp()
    # print (sensors_average_history[-1])
def flush_history():
    global sensors_average_history
    if (len(sensors_average_history) >= 300):
        sensors_average_history = sensors_average_history[140:]
def recalc_temp():
    set_outdoor_temp(outdoor_temp)
    recalculate_temp(regulationType, desired_temp)

# Basic functions
def getNeighbours4(arr, row, col):
    neighbours = []
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in dirs:
        nr, nc = row + dr, col + dc
        if 0 <= nr < len(arr) and 0 <= nc < len(arr[0]):
            neighbours.append((nr, nc))

    return neighbours

def change_color(row, col, color):
    colors[row][col] = color

def temperature_to_color(temp):
    if temp <= -30:
        return (0, 0, 255)
    elif -30 < temp <= 0:
        t = (temp + 30) / 30
        r = 0
        g = int(255 * t)
        b = int(255 * (1 - t))
        return (r, g, b)
    elif 0 < temp <= 30:
        t = temp / 30
        r = int(255 * t)
        g = 255
        b = 0
        return (r, g, b)
    elif 30 < temp <= 60:
        t = (temp - 30) / 30
        r = 255
        g = int(255 * (1 - t))
        b = 0
        return (r, g, b)
    else:
        return (255, 0, 0)

def walls_coloring(colors, offset, color):
    for j in range(offset, len(colors[0]) - offset):
        colors[offset][j] = color
    for i in range(1, len(colors) - 1):
        colors[i][offset] = color
    for j in range(offset, len(colors[0]) - offset):
        colors[len(colors) - 1 - offset][j] = color
    for i in range(offset, len(colors) - offset):
        colors[i][len(colors[0]) - 1 - offset] = color
    return colors

def set_object(pos, setting_obj):
    match setting_obj:
        case 'heater':
            set_heater(pos[0],pos[1])
        case 'wall':
            set_wall(pos[0],pos[1])
        case 'floor':
            set_floor(pos[0],pos[1])
        case 'door':
            set_door(pos[0],pos[1])
        case 'sensor':
            set_sensor(pos[0],pos[1])
        case 'window':
            set_window(pos[0],pos[1])
        case 'outdoor':
            set_outdoor(pos[0],pos[1])

def set_heater(row, col):
    global sensor_group
    change_color(row, col, c.HEATER_COLOR)
    temperatures[-1][row][col] = 100
    dont_change_mask[row][col] = False
    heaters.append(Heater(row,col,sensor_group=sensor_group))


def set_wall(row, col):
    change_color(row, col, c.WALLS_COLOR)
    dont_change_mask[row][col] = False


def set_floor(row, col):
    change_color(row, col, c.FLOOR_COLOR)
    dont_change_mask[row][col] = True


def set_door(row, col):
    change_color(row, col, c.DOOR_COLOR)
    dont_change_mask[row][col] = False

def set_sensor(row, col):
    global sensor_group
    sensors[sensor_group].append(Sensor(row,col))

def set_window(row, col):
    change_color(row, col, c.WINDOW_COLOR)
    dont_change_mask[row][col] = False

def set_outdoor(row, col):
    change_color(row, col, c.OUTDOOR_COLOR)
    dont_change_mask[row][col] = False
    dont_change_temp[row][col] = False

def set_outdoor_temp(set_temprature):
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if colors[i][j] == c.OUTDOOR_COLOR:
                temperatures[-1][i][j] = set_temprature 
def change_sensor():
    for i in range(len(sensors)):
        for j in range(len(sensors[i])):
            sensors[i][j].curtemp = temperatures[-1][sensors[i][j].Y][sensors[i][j].X]
            sensors[i][j].settemp = desired_temp 
def calc_average_sensors():
    global sensors_average, sensors_average_history
    sensors_average = []
    for i in range(len(sensors)):
        if len(sensors[i]) != 0:
            sensors_average.append(sum([v.curtemp for v in sensors[i]]) / len(sensors[i]))
        else:
            sensors_average.append(0)
    sensors_average_history.append(sensors_average)

# temp calculation
def ReleRegulation(KR, desired_t, current_t):
    return KR * (desired_t > current_t[-1])

def PRegulation(KP, desired_t, current_t):
    return KP * (desired_t - current_t[-1])

def PIRegulation(KP, KI, desired_t, current_t):
    si = 0
    breaker = 0
    for i in range(len(current_t)-1,0,-1):
        si += desired_t - current_t[i] 
        breaker += 1
        if breaker > 10:
            break
    return KI * si + KP * (desired_t - current_t[-1])


def PIDRegulation(KP, KI, KD, desired_t, current_t):
    if len(current_t) >= 2:
        return KP * (desired_t - current_t[-1]) + KD * (current_t[-2] - current_t[-1]) + KI * (
                desired_t * len(current_t) - sum(current_t))
    else:
        return KI * (desired_t * len(current_t) - sum(current_t)) + KP * (desired_t - current_t[-1])


K_window, K_door, K_wall, K_air = 0.02, 0.01, 0.008, 0.1


def recalculate_temp(regulationType,t_desired):
    # Пройдем по всем клеткам
    new_temp = []
    for i in range(c.ROOM_SIZE_Y):
        new_temp.append([])
        for j in range(c.ROOM_SIZE_X):
            new_temp[i].append(temperatures[-1][i][j])
    temperatures.append(new_temp)
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            dtemp = 0
            if dont_change_mask[i][j]:
                # Если клетка не помечена для изменения, пропускаем
                change_color(i, j, temperature_to_color(temperatures[-1][i][j]))
            # Если клетка является источником тепла (например, цвет 'heater'), то она меняет температуру у соседей
            neighbours = getNeighbours4(temperatures[-1], i, j)
            for neighbour in neighbours:
                # print([i, j], "Neighbour is", neighbour)
                nr, nc = neighbour.__getitem__(0), neighbour.__getitem__(1)
                # print("For them nr and nc are", nr, nc)
                # print(nr, nc)
                dt_local = temperatures[-1][nr][nc] - temperatures[-1][i][j]
                # теплообмен
                if colors[nr][nc] == c.WALLS_COLOR:
                    dtemp += K_wall * dt_local
                elif colors[nr][nc] == c.WINDOW_COLOR:
                    dtemp += K_window * dt_local
                elif colors[nr][nc] == c.HEATER_COLOR:
                    # print("T", temperature[-1][nr][nc], temperature[-1][i][j])
                    # print("Local temperature", dt_local)
                    # print(len(neighbours))
                    # print("We change", (i, j))
                    # print(nr, nc)

                    hot = []
                    for k in temperatures:
                        sum = 0   
                        for s in sensors[0]:
                            sum += k[s.Y][s.X]
                        if len(sensors[0]) > 0:
                            hot.append(sum / len(sensors[0]))

                    
                    # print(temperature[-1][nr][nc])
                    
                    #signal = RRegulation()*(regulationType == 'r') + PRegulation()*(regulationType == 'p') + PIRegulation(0.1, 0.00000005, temperatures[-1][nr][nc], hot)*(regulationType == 'pi')
                    signal = max((ReleRegulation(100, t_desired, hot)*(regulationType == 'r') +
                              PRegulation(1.5, t_desired, hot)*(regulationType == 'p') +
                              PIRegulation(1.5, 0.5, t_desired, hot)*(regulationType == 'pi')),0)
                    #signal = PIRegulation(0.1, 0.00000005, temperature[-1][nr][nc], sensors_average)

                    # print("signal is", signal)
                    K_signal = 0.001
                    dtemp += K_signal * signal * dt_local
                    # print("dtemp", dtemp)
                else:
                    dtemp += K_air * dt_local
                # если источник тепла - dtemp = 0
                if colors[i][j] == c.HEATER_COLOR or colors[i][j] == c.OUTDOOR_COLOR:
                    dtemp = 0
            temperatures[-1][i][j] += dtemp
            # if dtemp > 0:
            #     print("Temp ", i, j, "is changed to", temperature[-1][i][j])
    # print("Temperatures are:")
    # for i in range(ROOM_SIZE_Y):
    #     print(temperature[-1][i])


screen = pygame.display.set_mode((c.WIDTH,c.HEIGHT))

clock = pygame.time.Clock()

regulationType = 'p' # r, p, pi, pid
outdoor_temp   = 20
desired_temp   = 17
setting_obj    = 'heater'
sensor_group   = 0
show_plot      = False

sensors = [[] for i in range(c.SENSORS_GROUPS_COUNT)] 
heaters = []
windows = []
doors   = []

sensors_average = []
sensors_average_history = []


squares = [
    [
        pygame.Rect(x * c.SQUARE_SIZE + c.X_SCREEN_OFFSET,
                    y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET,
                    c.SQUARE_SIZE,
                    c.SQUARE_SIZE)
        for x in range(c.ROOM_SIZE_X)
    ]
    for y in range(c.ROOM_SIZE_Y)
]

colors = [
    [(200, 200, 200) for _ in range(c.ROOM_SIZE_X)]
    for _ in range(c.ROOM_SIZE_Y)
]

temperatures = [[
    [20 for x in range(c.ROOM_SIZE_X)]
    for y in range(c.ROOM_SIZE_Y)
]]

colors = walls_coloring(colors, 0, c.OUTDOOR_COLOR)
colors = walls_coloring(colors, 1, c.WALLS_COLOR)

dont_change_mask = [
    [not (colors[i][j] in [c.OUTDOOR_COLOR, c.WALLS_COLOR]) for j in range(c.ROOM_SIZE_X)]
    for i in range(c.ROOM_SIZE_Y)
]
dont_change_temp = [ 
    [not (colors[i][j] in [c.OUTDOOR_COLOR]) for j in range(c.ROOM_SIZE_X)]
    for i in range(c.ROOM_SIZE_Y)
]
