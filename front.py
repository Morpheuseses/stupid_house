import consts as c 
import back as Back

import pygame
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import numpy as np


class Button:
    def __init__(self,pos,size,function,text,font):
        self.onePress         = False
        self.isAlreadyPressed = False
        self.height    = size[0]
        self.width     = size[1]
        self.X         = pos[0]
        self.Y         = pos[1]
        self.function  = function
        self.text      = text

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect    = pygame.Rect(self.X, self.Y, self.width, self.height)
        self.buttonSurf    = font.render(text,True,(20,20,20))
        self.colors = {
            'normal': (240,240,240),
            'hover':  (150,150,150),
            'pressed':(40,40,40)
        }
    def process(self):
        mousePos = pygame.mouse.get_pos()
        self.buttonSurface.fill(self.colors['normal'])
        if self.buttonRect.collidepoint(mousePos):
            self.buttonSurface.fill(self.colors['hover'])
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.buttonSurface.fill(self.colors['pressed'])
                if self.onePress:
                    self.function()
                elif not self.isAlreadyPressed:
                    self.function()
                    self.isAlreadyPressed = True
            else:
                self.isAlreadyPressed = False
        self.buttonSurface.blit(self.buttonSurf, [
            self.buttonRect.width / 2 - self.buttonSurf.get_rect().width / 2,
            self.buttonRect.height / 2 - self.buttonSurf.get_rect().height / 2
        ])
        Back.screen.blit(self.buttonSurface, self.buttonRect)

def printSomething():
    print("something")

def adjustDesiredTemp():
    Back.desired_temp += 1
def descendDesiredTemp():
    Back.desired_temp -= 1
def adjustOutdoorTemp():
    Back.outdoor_temp += 1
def descendOutdoorTemp():
    Back.outdoor_temp -= 1

objects = []

objects.append(Button((c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10+410,0+10+50*4),(40,40),descendDesiredTemp,'<',c.SQUARE_FONT))
objects.append(Button((c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10+410+50,0+10+50*4),(40,40),adjustDesiredTemp,'>',c.SQUARE_FONT))
objects.append(Button((c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10+410,0+10+50),(40,40),descendOutdoorTemp,'<',c.SQUARE_FONT))
objects.append(Button((c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10+410+50,0+10+50),(40,40),adjustOutdoorTemp,'>',c.SQUARE_FONT))

def draw_interface():
    draw_rectangle((0,0),(c.X_SCREEN_OFFSET,c.HEIGHT),(120,120,120))
    draw_rectangle((c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X,0),(c.WIDTH-c.X_SCREEN_OFFSET-c.SQUARE_SIZE*c.ROOM_SIZE_X,c.HEIGHT),(40,40,40))

    draw_label(f"|- Setting object -> {Back.setting_obj} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Outdoor temperature -> {Back.outdoor_temp} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Regulation Type -> {Back.regulationType} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50+50),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Sensors group -> {Back.sensor_group+1} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50+50+50),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Regulation temperature -> {Back.desired_temp} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50*4),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    
    for obj in objects:
        obj.process()

    if Back.show_plot:
        draw_plot(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50*5,desired_temp=Back.desired_temp)

def draw_field():
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):    
            pygame.draw.rect(Back.screen, Back.colors[i][j], Back.squares[i][j])
            if Back.colors[i][j] != c.HEATER_COLOR:
                draw_text(f"{int(Back.temperatures[-1][i][j])}",c.SQUARE_FONT, Back.squares[i][j], c.MAIN_TEXT_COLOR)
            elif Back.colors[i][j] == c.HEATER_COLOR:
                draw_text(f"H",c.SQUARE_FONT, Back.squares[i][j], c.MAIN_TEXT_COLOR)
    for i in range(len(Back.sensors)):
        for j in range(len(Back.sensors[i])):
            pygame.draw.circle(Back.screen, c.SENSOR_COLOR,
                           (Back.sensors[i][j].X * c.SQUARE_SIZE + c.X_SCREEN_OFFSET + c.SQUARE_SIZE // 2,
                            Back.sensors[i][j].Y * c.SQUARE_SIZE + c.Y_SCREEN_OFFSET + c.SQUARE_SIZE // 2),
                           c.SQUARE_SIZE // 2)

def draw_text(text, font, rect, color):
    text_surface = font.render(text,True,color)
    text_rect = text_surface.get_rect(center=rect.center)
    Back.screen.blit(text_surface, text_rect)

def draw_rectangle(off, size, color):
    x_off  = off[0]
    y_off  = off[1]
    width  = size[0]
    height = size[1]
    rect = pygame.Rect(x_off,
                    y_off,
                    width,
                    height)
    
    pygame.draw.rect(Back.screen, color, rect)
    
    return rect  

def draw_label(text, font, off, size, colortext, color):
    rect = draw_rectangle(off,size,color)
    text_surface = font.render(text,True,colortext)
    text_rect = text_surface.get_rect(center=rect.center)
    
    Back.screen.blit(text_surface, text_rect)

def draw_Button():
    pass

def create_plot(desired_temp):
    x = np.linspace(0, len(Back.sensors_average_history),len(Back.sensors_average_history))
    y = []
    
    for j in range(len(Back.sensors_average_history[0])):
        y.append([Back.sensors_average_history[i][j] for i in range(len(Back.sensors_average_history))])
    
    # y = [sensors_average_history[i][0] for i in range(len(sensors_average_history))]
    
    fig, ax = plt.subplots(figsize=(4, 3))
    coloreshehe = ['red', 'yellow', 'orange','purple','blue']
    for j in range(len(Back.sensors_average)):
        ax.plot(x, y[j],c=coloreshehe[j])
    ax.plot([0,len(Back.sensors_average_history)], [desired_temp, desired_temp],c='green',linestyle='dotted')
    # ax.plot(x, y,c='red')
    ax.set_title("Sensors temprature history")
    plt.legend(["temperature"])

    canvas = FigureCanvas(fig)
    canvas.draw()

    buf = BytesIO()
    canvas.print_figure(buf, format='png', dpi=100)
    buf.seek(0)

    plot_image = pygame.image.load(buf)

    return plot_image

def create_plot_another(desired_temp):
    x = np.linspace(0, len(Back.sensors_average_history),len(Back.sensors_average_history))
    y = []
    
    for j in range(len(Back.sensors_average_history[0])):
        y.append([Back.sensors_average_history[i][j] for i in range(len(Back.sensors_average_history))])
    
    # y = [sensors_average_history[i][0] for i in range(len(sensors_average_history))]
    
    fig, ax = plt.subplots(figsize=(4, 3))
    coloreshehe = ['red', 'yellow', 'orange','purple','blue']
    for j in range(len(Back.sensors_average)):
        ax.plot(x, y[j],c=coloreshehe[j])
    ax.plot([0,len(Back.sensors_average_history)], [desired_temp, desired_temp],c='green',linestyle='dotted')
    # ax.plot(x, y,c='red')
    ax.set_title("Sensors temprature history")
    plt.legend(["temperature"])

    canvas = FigureCanvas(fig)
    canvas.draw()

    renderer = canvas.get_renderer()
    raw_data = renderer.tostring_argb()
    
    return raw_data, canvas 


def draw_plot(x_offset, y_offset,desired_temp):
    # plot_image = create_plot(desired_temp)
    # Back.screen.blit(plot_image, (x_offset,y_offset))
    raw_data, canvas = create_plot_another(desired_temp)
    plot_data = pygame.image.fromstring(raw_data,canvas.get_width_height(),"ARGB")
    Back.screen.blit(plot_data,(x_offset,y_offset))

