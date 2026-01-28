import consts as c
import pygame

# BASIC STRUCTS (без изменений)
class HasTemp:
    def __init__(self, row, col, curtemp=0, settemp=0):
        self.curtemp = curtemp
        self.settemp = settemp
        self.X = col
        self.Y = row

class Heater(HasTemp):
    def __init__(self, row, col, curtemp=100, settemp=100, sensor_group=0):
        super().__init__(row, col, curtemp=curtemp, settemp=settemp)
        self.sensor_group = sensor_group

class Window(HasTemp):
    def __init__(self, row, col, curtemp=0, settemp=0, sensor_group=0):
        super().__init__(row, col, curtemp=curtemp, settemp=settemp)
        self.sensor_group = sensor_group
        self.open = False

class Door(HasTemp):
    def __init__(self, row, col, curtemp=0, settemp=0, sensor_group=0):
        super().__init__(row, col, curtemp=curtemp, settemp=settemp)
        self.sensor_group = sensor_group
        self.open = False

class Sensor(HasTemp):
    def __init__(self, row, col):
        super().__init__(row, col)

# Precomputed temperature palette for fast color mapping
_TEMP_MIN, _TEMP_MAX = -60, 120
_TEMP_PALETTE = [
    (0, 0, 255) if t <= -30 else
    (0, int(255 * (t + 30) / 30), int(255 * (1 - (t + 30) / 30))) if t <= 0 else
    (int(255 * t / 30), 255, 0) if t <= 30 else
    (255, int(255 * (1 - (t - 30) / 30)), 0) if t <= 60 else
    (255, 0, 0)
    for t in range(_TEMP_MIN, _TEMP_MAX + 1)
]

def temperature_to_color(temp):
    idx = int(round(temp)) - _TEMP_MIN
    if idx < 0:
        return _TEMP_PALETTE[0]
    if idx >= len(_TEMP_PALETTE):
        return _TEMP_PALETTE[-1]
    return _TEMP_PALETTE[idx]

# Neighbor data precomputation (critical optimization)
_neighbor_data = None
_neighbor_data_dirty = True

def _rebuild_neighbor_data():
    global _neighbor_data, _neighbor_data_dirty
    _neighbor_data = [[[] for _ in range(c.ROOM_SIZE_X)] for _ in range(c.ROOM_SIZE_Y)]
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            neighbors = []
            for dr, dc in dirs:
                ni, nj = i + dr, j + dc
                if 0 <= ni < c.ROOM_SIZE_Y and 0 <= nj < c.ROOM_SIZE_X:
                    ncolor = colors[ni][nj]
                    if ncolor == c.WALLS_COLOR:
                        neighbors.append((ni, nj, K_wall, False))
                    elif ncolor == c.WINDOW_COLOR:
                        neighbors.append((ni, nj, K_window, False))
                    elif ncolor == c.HEATER_COLOR:
                        neighbors.append((ni, nj, 0.0, True))  # heater handled separately
                    else:
                        neighbors.append((ni, nj, K_air, False))
            _neighbor_data[i][j] = neighbors
    _neighbor_data_dirty = False

# Global heater signal (computed once per step)
_heater_signal = 0.0

# Constants for heat transfer
K_window, K_door, K_wall, K_air = 0.02, 0.01, 0.008, 0.1
K_signal = 0.001  # Heater influence coefficient

# Main functions (optimized)
def recalc():
    global _heater_signal
    flush_history()
    change_sensor()
    calc_average_sensors()
    
    # Compute heater signal ONCE per step using sensor history (not full temp grids!)
    if sensors and sensors[0]:
        hot = [avg[0] for avg in sensors_average_history] if sensors_average_history else [desired_temp]
        if regulationType == 'r':
            signal = ReleRegulation(100, desired_temp, hot)
        elif regulationType == 'p':
            signal = PRegulation(1.5, desired_temp, hot)
        elif regulationType == 'pi':
            signal = PIRegulation(1.5, 0.5, desired_temp, hot)
        else:
            signal = 0.0
        _heater_signal = max(signal, 0.0)
    else:
        _heater_signal = 0.0
    
    recalc_temp()

def flush_history():
    global sensors_average_history
    if len(sensors_average_history) >= 300:
        del sensors_average_history[:140]  # In-place deletion (no copy!)

def recalc_temp():
    set_outdoor_temp(outdoor_temp)
    recalculate_temp(regulationType, desired_temp)

# Basic functions (optimized versions)
def change_color(row, col, color):
    colors[row][col] = color

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
    global _neighbor_data_dirty
    match setting_obj:
        case 'heater':
            set_heater(pos[0], pos[1])
        case 'wall':
            set_wall(pos[0], pos[1])
        case 'floor':
            set_floor(pos[0], pos[1])
        case 'door':
            set_door(pos[0], pos[1])
        case 'sensor':
            set_sensor(pos[0], pos[1])
        case 'window':
            set_window(pos[0], pos[1])
        case 'outdoor':
            set_outdoor(pos[0], pos[1])
    _neighbor_data_dirty = True  # Mark for rebuild

def set_heater(row, col):
    global sensor_group, _neighbor_data_dirty
    change_color(row, col, c.HEATER_COLOR)
    temperatures[0][row][col] = 100.0  # Direct access to current temp grid
    dont_change_mask[row][col] = False
    heaters.append(Heater(row, col, sensor_group=sensor_group))
    _neighbor_data_dirty = True

def set_wall(row, col):
    global _neighbor_data_dirty
    change_color(row, col, c.WALLS_COLOR)
    dont_change_mask[row][col] = False
    _neighbor_data_dirty = True

def set_floor(row, col):
    global _neighbor_data_dirty
    change_color(row, col, c.FLOOR_COLOR)
    dont_change_mask[row][col] = True
    _neighbor_data_dirty = True

def set_door(row, col):
    global _neighbor_data_dirty
    change_color(row, col, c.DOOR_COLOR)
    dont_change_mask[row][col] = False
    _neighbor_data_dirty = True

def set_sensor(row, col):
    global sensor_group
    sensors[sensor_group].append(Sensor(row, col))

def set_window(row, col):
    global _neighbor_data_dirty
    change_color(row, col, c.WINDOW_COLOR)
    dont_change_mask[row][col] = False
    _neighbor_data_dirty = True

def set_outdoor(row, col):
    global _neighbor_data_dirty
    change_color(row, col, c.OUTDOOR_COLOR)
    dont_change_mask[row][col] = False
    dont_change_temp[row][col] = False
    _neighbor_data_dirty = True

def set_outdoor_temp(set_temperature):
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if colors[i][j] == c.OUTDOOR_COLOR:
                temperatures[0][i][j] = set_temperature

def change_sensor():
    for group in sensors:
        for sensor in group:
            sensor.curtemp = temperatures[0][sensor.Y][sensor.X]
            sensor.settemp = desired_temp

def calc_average_sensors():
    global sensors_average, sensors_average_history
    sensors_average = []
    for group in sensors:
        if group:
            avg = sum(s.curtemp for s in group) / len(group)
            sensors_average.append(avg)
        else:
            sensors_average.append(0.0)
    sensors_average_history.append(sensors_average[:])

# Regulation functions (unchanged)
def ReleRegulation(KR, desired_t, current_t):
    return KR * (desired_t > current_t[-1])

def PRegulation(KP, desired_t, current_t):
    return KP * (desired_t - current_t[-1])

def PIRegulation(KP, KI, desired_t, current_t):
    si = 0.0
    for i in range(max(0, len(current_t) - 10), len(current_t)):
        si += desired_t - current_t[i]
    return KI * si + KP * (desired_t - current_t[-1])

def PIDRegulation(KP, KI, KD, desired_t, current_t):
    if len(current_t) >= 2:
        return (KP * (desired_t - current_t[-1]) + 
                KD * (current_t[-2] - current_t[-1]) + 
                KI * (desired_t * len(current_t) - sum(current_t)))
    else:
        return KI * (desired_t * len(current_t) - sum(current_t)) + KP * (desired_t - current_t[-1])

# CRITICAL OPTIMIZATION: Temperature calculation with precomputed neighbors
def recalculate_temp(regulationType, t_desired):
    global temperatures, _neighbor_data, _neighbor_data_dirty, _heater_signal
    
    # Rebuild neighbor data if layout changed
    if _neighbor_data_dirty:
        _rebuild_neighbor_data()
    
    # Use single grid buffer (no history growth)
    old_temps = temperatures[0]
    new_temps = [[0.0] * c.ROOM_SIZE_X for _ in range(c.ROOM_SIZE_Y)]
    
    # Local variables for speed (avoid global lookups in hot loop)
    colors_loc = colors
    dont_change_mask_loc = dont_change_mask
    neighbor_data_loc = _neighbor_data
    heater_sig = _heater_signal
    K_signal_loc = K_signal
    
    # Compute new temperatures (Jacobi iteration for stability/speed)
    for i in range(c.ROOM_SIZE_Y):
        old_row = old_temps[i]
        new_row = new_temps[i]
        for j in range(c.ROOM_SIZE_X):
            temp_here = old_row[j]
            dtemp = 0.0
            
            # Fast neighbor processing using precomputed data
            for ni, nj, k_base, is_heater in neighbor_data_loc[i][j]:
                dt_local = old_temps[ni][nj] - temp_here
                if is_heater:
                    dtemp += K_signal_loc * heater_sig * dt_local
                else:
                    dtemp += k_base * dt_local
            
            # Apply constraints (heaters/outdoor don't change temp)
            if colors_loc[i][j] in (c.HEATER_COLOR, c.OUTDOOR_COLOR):
                dtemp = 0.0
            
            new_row[j] = temp_here + dtemp
    
    # Update temperature buffer (single grid)
    temperatures[0] = new_temps
    
    # Update colors ONLY for non-static cells (floor-like)
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):
            if dont_change_mask_loc[i][j]:
                colors[i][j] = temperature_to_color(new_temps[i][j])

# Pygame initialization (unchanged)
screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
clock = pygame.time.Clock()

# Simulation parameters (unchanged)
regulationType = 'p'  # r, p, pi, pid
outdoor_temp = 20
desired_temp = 17
setting_obj = 'heater'
sensor_group = 0
show_plot = False

# Data structures initialization
sensors = [[] for _ in range(c.SENSORS_GROUPS_COUNT)]
heaters = []
windows = []
doors = []
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

# CRITICAL: Single temperature grid (no history)
temperatures = [[
    [20.0 for _ in range(c.ROOM_SIZE_X)]
    for _ in range(c.ROOM_SIZE_Y)
]]

# Initialize room layout
colors = walls_coloring(colors, 0, c.OUTDOOR_COLOR)
colors = walls_coloring(colors, 1, c.WALLS_COLOR)

dont_change_mask = [
    [colors[i][j] not in (c.OUTDOOR_COLOR, c.WALLS_COLOR) for j in range(c.ROOM_SIZE_X)]
    for i in range(c.ROOM_SIZE_Y)
]
dont_change_temp = [
    [colors[i][j] != c.OUTDOOR_COLOR for j in range(c.ROOM_SIZE_X)]
    for i in range(c.ROOM_SIZE_Y)
]

# Rebuild neighbor data after initial layout
_rebuild_neighbor_data()
_neighbor_data_dirty = False
