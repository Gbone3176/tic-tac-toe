#此版本实现颜色阈值调参调与正确的作弊检测

import sensor
import time
from machine import UART
import display
import minimax2
import array
# OpenMV4 H7 Plus, OpenMV4 H7, OpenMV3 M7, OpenMV2 M4 的UART(3)是P4-TX P5-RX
uart = UART(3, 115200)   #OpenMV RT 注释掉这一行，用下一行UART(1)
#uart = UART(1, 115200)  #OpenMV RT 用UART(1)这行，注释掉上一行UART(3)
# OpenMV RT 只有串口UART(1)，对应P4-TX P5-RX; OpenMV4 H7 Plus, OpenMV4 H7, OpenMV3 M7 的UART(1)是P0-RX P1-TX

sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # grayscale is faster (160x120 max on OpenMV-M7)
sensor.set_framesize(sensor.QQVGA)
sensor.set_vflip(True)
sensor.set_hmirror(True)
sensor.skip_frames(time=2000)
clock = time.clock()
lcd = display.SPIDisplay()#在外界lcd屏幕上显示帧缓冲区
#在绿色背景下黑色和白色的阈值，如果你们不使用绿色背景，需要在openMV IDE的工具->机器视觉->阈值编辑器里调整得到区分黑白棋子的阈值
black_threshold = (0, 26, -14, 11, -11, 16)
white_threshold=(76, 100, -38, 32, -49, 34)
outter_black_threshold=(0, 11, -78, 79, -42, 48)
outter_white_threshold=(90, 100, -78, 79, -42, 48)
#储存棋盘上棋子的情况
blackcount=[0,0,0,0,0,0,0,0,0]
whitecount=[0,0,0,0,0,0,0,0,0]
totalcount=0
board_last = [0,0,0,0,0,0,0,0,0]
#初始化接收到的指令
command = "NONE"
bwside = "NONE"
location = "NONE"

def find_max_rect(rects):

    """
     返回图像中最大的矩阵，也就是整个棋盘
    """
    
    global max_rect
    rect_max=0
    for rect in rects:
        if rect.w() >rect_max:
            max_rect = rect
            rect_max=rect.w()
    return max_rect

def find_grid_points(corner1, corner2, corner3, corner4):#用棋盘的四个顶点坐标计算出九宫格中间格的四个顶点
    # Determine grid points based on corners
    inner_coener = []
    inner_coener1 =(corner1[0] / 3 * 2 +corner3[0] / 3 * 1 , corner1[1] / 3 * 2 +corner3[1] / 3 * 1)
    inner_coener2 =(corner2[0] / 3 * 2 +corner4[0] / 3 * 1 , corner2[1] / 3 * 2 +corner4[1] / 3 * 1)
    inner_coener3 =(corner1[0] / 3 * 1 +corner3[0] / 3 * 2 , corner1[1] / 3 * 1 +corner3[1] / 3 * 2)
    inner_coener4 =(corner2[0] / 3 * 1 +corner4[0] / 3 * 2 , corner2[1] / 3 * 1 +corner4[1] / 3 * 2)
    inner_coener = [inner_coener1, inner_coener2, inner_coener3, inner_coener4]
    for inner in inner_coener:
        img.draw_cross(tuple(map(round,inner)),color=(0,0,255))
    return inner_coener


while True:
    clock.tick()
    img = sensor.snapshot()
    board_matrix = [[0]*3 for _ in range(3)]  # 初始化代表棋盘的矩阵
    board_now = [0,0,0,0,0,0,0,0,0]
    imgrect = img.copy()
    r = find_max_rect(imgrect.find_rects(threshold=3000))  # threshold是检测矩形的灵敏度，这里是为了找到最大矩形所以threshold不用调
    area = r.magnitude()  # 当前找到的全部最大矩形的面积
    if area > 35000:  # 如果找到的矩形小于这个值说明可能不是代表棋盘的矩形，后续操作都跳过
        img.draw_rectangle(r.rect(), color=(255, 0, 0))  # 在帧缓冲区显示找到的矩形
        for p in r.corners():
            img.draw_circle(p[0], p[1], 5, color=(0, 255, 0))
        corner1=r.corners()[0]
        corner2=r.corners()[1]
        corner3=r.corners()[2]
        corner4=r.corners()[3]  # 得到棋盘矩形四个顶点坐标
        inner_corner = find_grid_points(corner1, corner2, corner3, corner4)
        inner_corner1=inner_corner[0]
        inner_corner2=inner_corner[1]
        inner_corner3=inner_corner[2]
        inner_corner4=inner_corner[3]

        #根据顶点坐标计算各格中心坐标
        cell_0=(int((corner4[0]+inner_corner4[0])/2),int((corner4[1]+inner_corner4[1])/2))
        cell_2=(int((corner3[0]+inner_corner3[0])/2),int((corner3[1]+inner_corner3[1])/2))
        cell_4=(int((inner_corner1[0]+inner_corner3[0])//2),int((inner_corner1[1]+inner_corner3[1])/2))
        cell_6=(int((corner1[0]+inner_corner1[0])/2),int((corner1[1]+inner_corner1[1])/2))
        cell_8=(int((corner2[0]+inner_corner2[0])/2),int((corner2[1]+inner_corner2[1])/2))
        cell_1=(int((cell_0[0]+cell_2[0])/2),int((cell_0[1]+cell_2[1])/2))
        cell_3=(int((cell_0[0]+cell_6[0])/2),int((cell_0[1]+cell_6[1])/2))
        cell_5=(int((cell_2[0]+cell_8[0])/2),int((cell_2[1]+cell_8[1])/2))
        cell_7=(int((cell_6[0]+cell_8[0])/2),int((cell_6[1]+cell_8[1])/2))
        cells = [cell_0, cell_1, cell_2, cell_3, cell_4, cell_5, cell_6, cell_7, cell_8]
        for cell in cells:  # 在各格中心点标出十字
            img.draw_cross(tuple(map(round,cell)),color=(255,0,0),size=5)

        #棋子识别，色块和圆形

        # 通过颜色阈值得到黑色区域的二值图像
        imgb = img.copy()
        imgw = img.copy()
        img_binary_black = imgb.binary([black_threshold])#按之前调的black_threshold二值化图像

        # 在二值图像中寻找圆形目标
        # 原理是在二值化后的图像（也就是调整black_threshold和white_threshold时在阈值编辑器里见到的图像）里找圆形

        for c in img_binary_black.find_circles(roi=r.rect(),threshold=4400, x_margin=5, y_margin=5, r_margin=5,
                                               r_min=5, r_max=70, r_step=2):
            #find_circles函数详情见https://book.openmv.cc/example/09-Feature-Detection/find-circles.html
            #这里最主要调整的参数还是threshold，我的理解是相当于灵敏度，调小了会把一堆噪音识别成棋子，调大了可能识别不到棋子
            area = (c.x()-c.r(), c.y()-c.r(), 2*c.r(), 2*c.r())

            R = c.r()

            #area为识别到的圆的区域，即圆的外接矩形框
            statistics = img.get_statistics(roi=area)#像素颜色统计

            #示例：(0,100,0,120,0,120)是红色的阈值，所以当区域内的众数（也就是最多的颜色），范围在这个阈值内，就说明是红色的圆。
            #l_mode()，a_mode()，b_mode()是L通道，A通道，B通道的众数。
            #将非红色的圆用白色的矩形框出来

            if black_threshold[0]<=statistics.l_mode()<=black_threshold[1] and black_threshold[2]<statistics.a_mode()<black_threshold[3] and black_threshold[4]<statistics.b_mode()<black_threshold[5] and 5<R<15:
                #再加一层识别，识别到的圆圈里必须是相应的颜色且半径符合才能继续，这里颜色的范围就是black_threshold里的值。实际使用中颜色识别感觉效果不明显，半径范围倒是有效果，但是最核心的还是threshold。
                #print(c)
            # 画出圆
                img.draw_circle(c.x(), c.y(), c.r(), color=(255, 0, 0))  # 画出检测到的圆
                c_center = (c.x(),c.y())
                R_error = 8
                #以下是将识别到的黑色棋子存入到棋盘矩阵中，R_error是可接受的误差
                if (c_center[0] > cell_0[0]-R_error and c_center[0] < cell_0[0]+R_error and
                    c_center[1] > cell_0[1]-R_error and c_center[1] < cell_0[1]+R_error):
                    #board_matrix[0][0] = '1'
                    blackcount[0]+=1
                    #print("black in cell_0")
                elif (c_center[0] > cell_1[0]-R_error and c_center[0] < cell_1[0]+R_error and
                      c_center[1] > cell_1[1]-R_error and c_center[1] < cell_1[1]+R_error):
                    #board_matrix[0][1] = '1'
                    blackcount[1]+=1
                    #print("black in cell_1")
                elif (c_center[0] > cell_2[0]-R_error and c_center[0] < cell_2[0]+R_error and
                      c_center[1] > cell_2[1]-R_error and c_center[1] < cell_2[1]+R_error):
                    #board_matrix[0][2] = '1'
                    blackcount[2]+=1
                    #print("black in cell_2")
                elif (c_center[0] > cell_3[0]-R_error and c_center[0] < cell_3[0]+R_error and
                      c_center[1] > cell_3[1]-R_error and c_center[1] < cell_3[1]+R_error):
                    #board_matrix[1][0] = '1'
                    blackcount[3]+=1
                    #print("black in cell_3")
                elif (c_center[0] > cell_4[0]-R_error and c_center[0] < cell_4[0]+R_error and
                      c_center[1] > cell_4[1]-R_error and c_center[1] < cell_4[1]+R_error):
                    #board_matrix[1][1] = '1'
                    blackcount[4]+=1
                    #print("black in cell_4")
                elif (c_center[0] > cell_5[0]-R_error and c_center[0] < cell_5[0]+R_error and
                      c_center[1] > cell_5[1]-R_error and c_center[1] < cell_5[1]+R_error):
                    #board_matrix[1][2] = '1'
                    blackcount[5]+=1
                    #print("black in cell_5")
                elif (c_center[0] > cell_6[0]-R_error and c_center[0] < cell_6[0]+R_error and
                      c_center[1] > cell_6[1]-R_error and c_center[1] < cell_6[1]+R_error):
                    #board_matrix[2][0] = '1'
                    blackcount[6]+=1
                    #print("black in cell_6")
                elif (c_center[0] > cell_7[0]-R_error and c_center[0] < cell_7[0]+R_error and
                      c_center[1] > cell_7[1]-R_error and c_center[1] < cell_7[1]+R_error):
                    #board_matrix[2][1] = '1'
                    blackcount[7]+=1
                    #print("black in cell_7")
                elif (c_center[0] > cell_8[0]-R_error and c_center[0] < cell_8[0]+R_error and
                      c_center[1] > cell_8[1]-R_error and c_center[1] < cell_8[1]+R_error):
                    #board_matrix[2][2] = '1'
                    blackcount[8]+=1
                    #print("black in cell_8")
                else:
                    pass
                    #print("black not in board")
                #print("black Circle detected at:",c_center)  # 输出圆心坐标

        #白棋，操作和识别黑棋一样
        img_binary_white = imgw.binary([white_threshold])

        # 在二值图像中寻找圆形目标

        for c in img_binary_white.find_circles(roi=r.rect(),threshold=4400, x_margin=5, y_margin=5, r_margin=5,
                                               r_min=5, r_max=60, r_step=2):
            area = (c.x()-c.r(), c.y()-c.r(), 2*c.r(), 2*c.r())

            R = c.r()
            #print(c)
            # 画出圆

            #area为识别到的圆的区域，即圆的外接矩形框
            statistics = img.get_statistics(roi=area)#像素颜色统计
            #print(statistics)
            #l_mode()，a_mode()，b_mode()是L通道，A通道，B通道的众数。
                #将非红色的圆用白色的矩形框出来
            if white_threshold[0]<=statistics.l_mode()<=white_threshold[1] and white_threshold[2]<statistics.a_mode()<white_threshold[3] and white_threshold[4]<statistics.b_mode()<white_threshold[5] and 5<R<20:
                img.draw_circle(c.x(), c.y(), c.r(), color=(0, 255, 0))  # 画出检测到的圆
                c_center = (c.x(),c.y())
                R_error = 10
                if (c_center[0] > cell_0[0]-R_error and c_center[0] < cell_0[0]+R_error and
                    c_center[1] > cell_0[1]-R_error and c_center[1] < cell_0[1]+R_error):
                    #board_matrix[0][0] = '-1'
                    whitecount[0]+=1
                    #print("white in cell_0")
                elif (c_center[0] > cell_1[0]-R_error and c_center[0] < cell_1[0]+R_error and
                      c_center[1] > cell_1[1]-R_error and c_center[1] < cell_1[1]+R_error):
                    #board_matrix[0][1] = '-1'
                    whitecount[1]+=1
                    #print("white in cell_1")
                elif (c_center[0] > cell_2[0]-R_error and c_center[0] < cell_2[0]+R_error and
                      c_center[1] > cell_2[1]-R_error and c_center[1] < cell_2[1]+R_error):
                    #board_matrix[0][2] = '-1'
                    whitecount[2]+=1
                    #print("white in cell_2")
                elif (c_center[0] > cell_3[0]-R_error and c_center[0] < cell_3[0]+R_error and
                      c_center[1] > cell_3[1]-R_error and c_center[1] < cell_3[1]+R_error):
                    #board_matrix[1][0] = '-1'
                    whitecount[3]+=1
                    #print("white in cell_3")
                elif (c_center[0] > cell_4[0]-R_error and c_center[0] < cell_4[0]+R_error and
                      c_center[1] > cell_4[1]-R_error and c_center[1] < cell_4[1]+R_error):
                    #board_matrix[1][1] = '-1'
                    whitecount[4]+=1
                    #print("white in cell_4")
                elif (c_center[0] > cell_5[0]-R_error and c_center[0] < cell_5[0]+R_error and
                      c_center[1] > cell_5[1]-R_error and c_center[1] < cell_5[1]+R_error):
                    #board_matrix[1][2] = '-1'
                    whitecount[5]+=1
                    #print("white in cell_5")
                elif (c_center[0] > cell_6[0]-R_error and c_center[0] < cell_6[0]+R_error and
                      c_center[1] > cell_6[1]-R_error and c_center[1] < cell_6[1]+R_error):
                    #board_matrix[2][0] = '-1'
                    whitecount[6]+=1
                    #print("white in cell_6")
                elif (c_center[0] > cell_7[0]-R_error and c_center[0] < cell_7[0]+R_error and
                      c_center[1] > cell_7[1]-R_error and c_center[1] < cell_7[1]+R_error):
                    #board_matrix[2][1] = '-1'
                    whitecount[7]+=1
                    #print("white in cell_7")
                elif (c_center[0] > cell_8[0]-R_error and c_center[0] < cell_8[0]+R_error and
                      c_center[1] > cell_8[1]-R_error and c_center[1] < cell_8[1]+R_error):
                    #board_matrix[2][2] = '-1'
                    whitecount[8]+=1
                    #print("white in cell_8")
                else:
                    pass
                    #print("white not in board")

            #print("white Circle detected at:",c_center)  # 输出圆心坐标
        #平均多次检测结果以增加正确率的机制：totalcount为当前检测的次数，5次一周期，5次中若有2次（countedge）及以上检测到某位置上有棋子，那么则把该位置上的该棋子填入最终的棋盘矩阵
        totalcount += 1
        countedge = 2
        if totalcount >= 5:
            for index, bcount in enumerate(blackcount):
                if bcount >= countedge:
                    board_matrix[index // 3][index % 3] = 1
                    blackcount[index]=0
                else:
                    blackcount[index]=0
            for index,wcount in enumerate(whitecount):
                if wcount >= countedge:
                    board_matrix[index // 3][index % 3] = -1
                    whitecount[index]=0
                else:
                    whitecount[index]=0
            totalcount = 0
            print(board_matrix)
            #转化二维数组到一维数组以进行对弈算法
            for index,element in enumerate(board_now):
                board_now[index] = board_matrix[index // 3][index % 3]
            #print(board_now)
            #下面是接收指令的代码
            if uart.any():                          #判断是否接收到数据
                a = uart.read().decode()           #uart.read()为一个字节串，加.decode() 变成字符串
                command = a
                bwside = a[3]
                location = a[4]
                print(a)                            #在OpenMV的串行终端中打印
                #if a[0:1] == 'mn' and a[5:6] == 'hh':
                if a[0] == 'm' and a[1] == 'n':
                    print("action:")
                    print(a)
                    if a[2] == '0':#自动
                        if a[3] == 'B':
                            side = 1
                            #bwside = "black"
                        elif a[3]=='W':
                            side = 0
                            #bwside = "white"
                        next_move = minimax2.begin(board_now,board_last,side)
                        #uart.write(str(next_move))
                        #print(next_move[0])
                        print("type",type(next_move))
                        if type(next_move) == tuple:#棋盘被移动过的情况
                            print("board has been changed!")
                            buff = f"nn{cells[next_move[0]][0]}f{cells[next_move[0]][1]}m{cells[next_move[1]][0]}b{cells[next_move[1]][1]}h"
                        else:
                            buff = f"mm{cells[next_move][0]},{cells[next_move][1]}h"
                            board_last = board_now
                        uart.write(buff)
                        print("auto")
                        print(buff)

                    elif a[2]=='1':
                        next_move = int(a[4])-1
                        print()
                        print(next_move)
                        buff = f"mm{cells[next_move][0]},{cells[next_move][1]}h"
                        uart.write(buff)
                        print("handmake")
                        print(buff)
            #command_string = "command:%s"%(command)
            #side_string = "side:%s"%(bwside)
            #location_string = "location:%s"%(location)
            #lcdimage = sensor.snapshot().replace(vflip=True,hmirror=False,transpose=True)
        lcdimage = img.copy().replace(vflip=True,hmirror=False,transpose=True)
        lcdimage.draw_string(120,0, "command:%s"%(command), (255,0,0), x_spacing=-1, string_rotation=90)
        lcdimage.draw_string(100,0, "side:%s"%(bwside), (255,0,0), x_spacing=-1, string_rotation=90)
        lcdimage.draw_string(80,0, "location:%s"%(location), (255,0,0), x_spacing=-1, string_rotation=90)
        lcd.write(lcdimage)  # 在屏幕上显示当前画面，包括识别内容和相关说明字符
