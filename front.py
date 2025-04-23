import consts as c 
import back as Back

import pygame

def draw_interface():
    draw_rectangle((0,0),(c.X_SCREEN_OFFSET,c.HEIGHT),(120,120,120))
    draw_rectangle((c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X,0),(c.WIDTH-c.X_SCREEN_OFFSET-c.SQUARE_SIZE*c.ROOM_SIZE_X,c.HEIGHT),(40,40,40))

    draw_label(f"|- Setting object -> {Back.setting_obj} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Outdoor temperature -> {Back.outdoor_temp} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Regulation Type -> {Back.regulationType} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50+50),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
    draw_label(f"|- Sensors group -> {Back.sensor_group+1} -|", pygame.font.SysFont("notosansmono",16),(c.X_SCREEN_OFFSET+c.SQUARE_SIZE*c.ROOM_SIZE_X+10,0+10+50+50+50),(400,40),c.MAIN_TEXT_COLOR,(210,210,210))
def draw_field():
    for i in range(c.ROOM_SIZE_Y):
        for j in range(c.ROOM_SIZE_X):    
            pygame.draw.rect(Back.screen, Back.colors[i][j], Back.squares[i][j])
            draw_text(f"{int(Back.temperatures[-1][i][j])}",c.SQUARE_FONT, Back.squares[i][j], c.MAIN_TEXT_COLOR)
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

