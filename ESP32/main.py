from machine import UART, Pin, PWM
import time
import array
yanse = 'B' #表示装置所持棋子的颜色（W为白，B为黑）
num = 0 #表示棋盘格子的计数（1-9）
en = 0 #表示发送标志位，表示手动自动区分标志位
buffer = "mm000hh" #
data=""

ifled = 0
ifmov = 0
delay_time = 1000 # 这个时间不能设置太小，否则电机来不及响应

getx=0
gety=0
#location_now = [73,-8]
location_now = [0,0]
sign_moved = 0#判断棋子是否非法移动

#控制像素位置与实际位置的映射变换系数
apix = 0.145
axpix = 0.130
aypix = 0.120
xpix=0
ypix=0

#显示当前对应黑棋白棋的数目
BI=5
WI=5

#步进电机引脚接线
ax = Pin(15, Pin.OUT)
bx = Pin(4, Pin.OUT)
cx = Pin(2, Pin.OUT)
dx = Pin(22, Pin.OUT)

ay = Pin(5, Pin.OUT)
by = Pin(19, Pin.OUT)
cy = Pin(18, Pin.OUT)
dy = Pin(21, Pin.OUT)

# 定义LED引脚
led0 = Pin(25, Pin.OUT)
# 定义IO口中断引脚
pinWB = Pin(33, Pin.IN, pull=Pin.PULL_UP)
pinCHOICE = Pin(32, Pin.IN, pull=Pin.PULL_UP)
pinEN = Pin(23, Pin.IN, pull=Pin.PULL_UP)
help(Pin)

# 初始化 UART
uart = UART(2, baudrate=115200, tx=17, rx=16)

# 这里假设SG90的信号线连接到GPIO2引脚
servo_pin = Pin(12)
pwm = PWM(servo_pin, freq=50)  # SG90典型的PWM频率是50Hz

# 定义中断处理函数，接受一个参数event
def WB_interrupt(event):
    global buffer
    global en
    global yanse
    global num
    time.sleep_ms(5)
    if pinWB.value()==0:
        if yanse == "W":
            yanse = "B"
        elif yanse == "B":
            yanse = "W"
        else:
            yanse = "B"
        buffer = "mm"+str(en)+ str(yanse)+ str(num)+ "hh"
        uart.write(str(buffer) + "\n")
        print("状态:",buffer)
    while pinWB.value()==0:
        pass
    return 0
def CHOICE_interrupt(event):
    global buffer
    global en
    global yanse
    global num
    time.sleep_ms(5)
    if pinCHOICE.value()==0:
        if num>8:
            num = 0
            en = 0
        else:
            num +=1
            en = 1
        buffer = "mm"+str(en)+ str(yanse)+ str(num)+ "hh"
        uart.write(str(buffer) + "\n")
        print("状态:",buffer)
        # 在这里编写中断处理逻辑
    while pinCHOICE.value()==0:
        pass
    return 0
def EN_interrupt(event):
    global buffer
    global en
    global yanse
    global num
    global ifled
    global ifmov
    time.sleep_ms(5)
    if pinEN.value()==0:
        if en==1: #装置手动放棋子
            ifmov = 1
            #print()
        elif en==0:           #自动下棋
            ifmov = 2
            # 发送字符串信息到 OpenMV
        buffer = "mn"+str(en)+ str(yanse)+ str(num)+ "hh"
        uart.write(str(buffer) + "\n")
        print("状态:",buffer)
    while pinEN.value()==0:
        pass
    return 0
# 配置IO口中断，触发条件为下降沿触发
pinWB.irq(trigger=Pin.IRQ_FALLING, handler=WB_interrupt)
pinCHOICE.irq(trigger=Pin.IRQ_FALLING, handler=CHOICE_interrupt)
pinEN.irq(trigger=Pin.IRQ_FALLING, handler=EN_interrupt)

# 电机向内侧移动，即向距离马达近的一端移动
def movin(a,b,c,d,langin):#3.1cm-----256
    xi=langin*256/3.1
    global delay_time
    #print("单四拍模式")
    for i in range (int(xi)):  # 顺时针转动180度
        a.value(1)
        b.value(0)
        c.value(0)
        d.value(0)
        time.sleep_us(delay_time)
        a.value(0)
        b.value(1)
        c.value(0)
        d.value(0)
        time.sleep_us(delay_time)
        a.value(0)
        b.value(0)
        c.value(1)
        d.value(0)
        time.sleep_us(delay_time)
        a.value(0)
        b.value(0)
        c.value(0)
        d.value(1)
        time.sleep_us(delay_time)
    # 步进电机停止后需要使四个相位引脚都为低电平，否则步进电机会发热
    a.value(0)
    b.value(0)
    c.value(0)
    d.value(0)
    return 0

# 电机向外侧移动，即向距离马达远的一端移动
def movout(a,b,c,d,langout):#3.1cm-----256
    xo=langout*256/3.1
    global delay_time
    
    # 改变脉冲的顺序， 可以方便的改变转动的方向
    for i in range (int(xo)):  # 逆时针转动转动180度
        a.value(0)
        b.value(0)
        c.value(0)
        d.value(1)
        time.sleep_us(delay_time)
        a.value(0)
        b.value(0)
        c.value(1)
        d.value(0)
        time.sleep_us(delay_time)
        a.value(0)
        b.value(1)
        c.value(0)
        d.value(0)
        time.sleep_us(delay_time)
        a.value(1)
        b.value(0)
        c.value(0)
        d.value(0)
        time.sleep_us(delay_time)
    # 步进电机停止后需要使四个相位引脚都为低电平，否则步进电机会发热
    a.value(0)
    b.value(0)
    c.value(0)
    d.value(0)
    return 0

#获取需要移动的数据
def getxy(dat):
    x_finish=0
    y_finish=0

    for index,dat_index_search in enumerate(dat):
        if dat_index_search == ',':
            x_finish = index
        elif dat_index_search == 'h':
            y_finish = index
   
    x = int(dat[2:x_finish])
    y = int(dat[x_finish+1:y_finish])

    return x,y
#获取移动过的数据，以便滑台返回初始位置
def getxy_moved(dat):
    x1_finish=0
    y1_finish=0
    x2_finish=0
    y2_finish=0

    for index,dat_index_search in enumerate(dat):
        if dat_index_search == 'f':
            x1_finish = index
        elif dat_index_search == 'm':
            y1_finish = index
        elif dat_index_search == 'b':
            x2_finish = index
        elif dat_index_search == 'h':
            y2_finish = index
    x1 = int(dat[2:x1_finish])
    y1 = int(dat[x1_finish+1:y1_finish])
    x2 = int(dat[y1_finish+1:x2_finish])
    y2 = int(dat[x2_finish+1:y2_finish])

    return x1,y1,x2,y2


#从（px1，py1）移动到（px2，py2）
def move_from_to(px1,py1,px2,py2):#1像素为0.115cm，
    global location_now
    global apix
    global axpix
    global aypix
    global xpix
    global ypix
    #像素位置与实际位置的映射变换
    x1=(px1+xpix)*axpix
    y1=(py1+ypix)*aypix
    x2=(px2+xpix)*axpix
    y2=(py2+ypix)*aypix
    if x1-x2<0 and y1-y2<0:
        movout(ay,by,cy,dy,y2-y1)
        movout(ax,bx,cx,dx,x2-x1)
    elif x1-x2<0 and y2-y1<=0:
        movin(ay,by,cy,dy,y1-y2)
        movout(ax,bx,cx,dx,x2-x1)
    elif x2-x1<=0 and y1-y2<0:
        movout(ay,by,cy,dy,y2-y1)
        movin(ax,bx,cx,dx,x1-x2)
    elif x2-x1<=0 and y2-y1<=0:
        movin(ay,by,cy,dy,y1-y2)
        movin(ax,bx,cx,dx,x1-x2)
    #更新当前位置
    location_now=[px2,py2]
    return 0

#控制抓取舵机的旋转角度，影响抓取装置的高度
def set_angle(angle):
    # 将角度转换为对应的PWM占空比
    # 根据SG90舵机的PWM信号标准，占空比在0.5ms到2.5ms之间，对应0到180度
    # 占空比 = 0.5ms + (角度/180) * 2ms
    duty = int(40 + (angle / 180) * 115)  # duty在40到155之间，根据具体舵机调整
    pwm.duty(duty)
    return 0

#抓取
def catch():
    set_angle(25)
    time.sleep(0.5)
    set_angle(100)
    print("catching...")
    return 0
#放下
def put():
    #set_angle(-10)
    #time.sleep(0.5)
    print("puting...")
    set_angle(130)
    return 0 
#按照顺序抓取黑棋
def getblack(i):
    global location_now
    if i>0 and i<6:
        move_from_to(location_now[0],location_now[1],0+(i-1)*25,25)
        catch()
#按照顺序抓取白棋
def getwhite(i):
    global location_now
    if i>0 and i<6:
        move_from_to(location_now[0],location_now[1],0+(i-1)*25,160)
        catch()
#将棋子放到（x，y）位置
def puttopix(x,y):
    global location_now
    move_from_to(location_now[0],location_now[1],x,y)
    put()
    move_from_to(location_now[0],location_now[1],0,0)

#主程序
while True:
    
    # 从 OpenMV 读取数据，并进行对应的数据整理
    data = ''    
    if uart.any():
        #将获取到的串口信息进行相应的变换，以便阅读
        data_o= uart.readline()
        data0 = data_o.decode('utf-8')
        data +=data0
        while data0[-1]!='h':
            data_o= uart.readline()
            data0 = data_o.decode('utf-8')
            data +=data0
        print("here",data)
        if len(data)<20:
            #将从openmv上获取的数据显示出来
            print("Received from OpenMV:", data)
            #判断如果是正常移动棋子
            if data[0] == "m" and data[1]=="m":
                print("here",data)
                getx,gety=getxy(data)
                print("x=",getx)
                print("y=",gety)
                #对获取到的像素位置进行原点变换，以便与滑台适配
                getx=150-getx
                gety=160-gety
            #判断如果检测出作弊行为
            elif data[0] == "n" and data[1] == "n":
                sign_moved = 1
                getx1,gety1,getx2,gety2=getxy_moved(data)
                getx1=150-getx1
                gety1=160-gety1
                getx2=150-getx2
                gety2=160-gety2
        
    #控制滑台下棋程序
        #指定下棋
        if ifmov == 1:
            print("ifm==1")
            if yanse =="B":
                if BI>0:
                    getblack(6-BI)
                    puttopix(getx,gety)
                    BI -= 1
                else:
                    print("NO BLACK")
            elif yanse =="W":
                if WI>0:
                    getwhite(6-WI)
                    puttopix(getx,gety)
                    WI -= 1
                else:
                    print("NO WHITE")
            ifmov = 0
            ifled=1
        #自动下棋
        elif ifmov ==2:
            print("ifm==2")
            print(sign_moved)
            #判断作弊
            if sign_moved == 1:
                sign_moved = 0
                print("getx1",getx1)
                print("gety1",gety1)
                print("getx2",getx2)
                print("gety2",gety2)
                move_from_to(location_now[0],location_now[1],getx1,gety1)
                catch()
                move_from_to(location_now[0],location_now[1],getx2,gety2)
                put()
                move_from_to(location_now[0],location_now[1],0,0)
            #判断没有作弊
            elif sign_moved == 0:
                if yanse =="B":
                    if BI>0:
                        getblack(6-BI)
                        puttopix(getx,gety)
                        BI -= 1
                    else:
                        print("NO BLACK")
                elif yanse =="W":
                    if WI>0:
                        getwhite(6-WI)
                        puttopix(getx,gety)
                        WI -= 1
                    else:
                        print("NO WHITE")
            ifmov = 0  
            ifled=1
    #下完棋子后指示灯进行3次闪烁
    if ifled == 1:
        ifled=0
        led0.value(1)
        time.sleep_ms(300)
        led0.value(0)
        time.sleep_ms(300)
        led0.value(1)
        time.sleep_ms(300)
        led0.value(0)
        time.sleep_ms(300)
        led0.value(1)
        time.sleep_ms(300)
        led0.value(0)

    
