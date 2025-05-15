import threading

import numpy as np
import pygame
import time
from pymycobot import MercurySocket

# 初始化机械臂,IP和端口号需根据实际进行修改
mc = MercurySocket('192.168.1.4', 9001)

# 检测机械臂是否上电
if mc.is_power_on() != 1:
    mc.power_on()

# 设置夹爪透传模式
mc.set_gripper_mode(0)

THRESHOLD = 0.5  # 鼠标轴触发运动的阈值
DEAD_ZONE = 0.05  # 归零判断阈值

# jog 坐标运动速度
jog_speed = 20

# 夹爪速度
gripper_speed = 80

# 初始点运动速度
home_speed = 10

# 夹爪状态（默认张开）
gripper_state = True

# 模式状态
is_speed_mode = False
led_flash = False

# 6D 轴映射关系，鼠标轴 -> 机械臂坐标ID映射
AXIS_MAPPING = {
    0: 2,
    1: 1,
    2: 3,
    3: 5,
    4: 4,
    5: 6
}

# 轴运动方向映射
DIRECTION_MAPPING = {
    0: (-1, 1),  # 轴0 (Y) -> 负向 -1，正向 1
    1: (-1, 1),  # 轴1 (X) -> 负向 -1，正向 1
    2: (-1, 1),  # 轴2 (Z) -> 负向 -1，正向 1
    3: (-1, 1),  # 轴3 (RX) -> 负向 -1，正向 1
    4: (-1, 1),  # 轴4 (RY) -> 负向 1，正向 -1
    5: (-1, 1)  # 轴5 (RZ) -> 负向 1，正向 -1
}


# def led_flash_loop():
#     """LED灯闪烁提示速度调节模式"""
#     global led_flash
#     while True:
#         if led_flash:
#             mc.set_color(255, 0, 0)  # 红色
#             time.sleep(0.5)
#             mc.set_color(0, 0, 0)    # 熄灭
#             time.sleep(0.5)
#         else:
#             time.sleep(1)
def led_flash_loop():
    """LED灯闪烁提示速度调节模式"""
    last_led_state = None
    while True:
        if led_flash:
            mc.set_color(128, 0, 128)  # 红色
            time.sleep(0.5)
            if not led_flash:  # 防止在 sleep 期间被切换模式
                continue
            mc.set_color(0, 0, 0)  # 熄灭
            time.sleep(0.5)
        else:
            if last_led_state != "green":
                mc.set_color(0, 255, 0)  # 绿色常亮
                last_led_state = "green"
            time.sleep(0.1)


def handle_mouse_event(jog_callback, stop_callback, gripper_callback):
    """
    监听 6D 鼠标事件，并调用传入的回调函数控制机械臂
    :param jog_callback: 运动回调函数 (coord_id, direction)
    :param stop_callback: 停止运动回调函数 (coord_id)
    :param gripper_callback: 夹爪开合回调函数 ()
    """
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到 6D 鼠标设备！")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"已连接 6D 鼠标: {joystick.get_name()}")

    active_axes = {}  # 记录当前运动状态
    home_active = False  # 记录初始点运动状态
    in_speed_mode = False
    btn1_press_time = None
    speed_mode_hold_time = 1  # 长按1秒进入速度调节模式

    axis = [0, 0, 0, 0, 0, 0]
    dir = [0, 0, 0, 0, 0, 0]

    global jog_speed

    try:
        while True:
            for event in pygame.event.get():
                # 处理轴运动
                if event.type == pygame.JOYAXISMOTION:
                    axis_id = event.axis
                    value = event.value
                    # print('axis_id:', axis_id)
                    # print('value:', value)

                    if axis_id in AXIS_MAPPING:
                        coord_id = AXIS_MAPPING[axis_id]
                        pos_dir, neg_dir = DIRECTION_MAPPING[axis_id]

                        if abs(value) > THRESHOLD and active_axes.get(axis_id) != 1:
                            axis[coord_id - 1] = 1
                            if (pos_dir * np.sign(value)) > 0:
                                dir[coord_id - 1] = 1
                            else:
                                dir[coord_id - 1] = 0

                            # print("axis_id", coord_id, value, pos_dir)
                            print(axis)
                            print(dir)

                            jog_callback(axis, dir)
                            active_axes[axis_id] = 1

                        elif -DEAD_ZONE < value < DEAD_ZONE and axis_id in active_axes:
                            axis[coord_id - 1] = 0
                            if np.sum(axis) == 0:
                                print("stop")
                                stop_callback(coord_id)
                                axis = [0, 0, 0, 0, 0, 0]
                                dir = [0, 0, 0, 0, 0, 0]
                                del active_axes[axis_id]
                        # if value > THRESHOLD and active_axes.get(axis_id) != 1:
                        #     jog_callback(coord_id, pos_dir)
                        #     active_axes[axis_id] = 1
                        #     print('axis_id000:', axis_id)
                        #     print('value000:', value)
                        #
                        # elif value < -THRESHOLD and active_axes.get(axis_id) != -1:
                        #     jog_callback(coord_id, neg_dir)
                        #     active_axes[axis_id] = -1
                        #     print('axis_id111:', axis_id)
                        #     print('value111:', value)
                        #
                        # elif -DEAD_ZONE < value < DEAD_ZONE and axis_id in active_axes:
                        #     stop_callback(coord_id)
                        #     del active_axes[axis_id]
                        #     print('axis_id222:', axis_id)
                        #     print('value222:', value)

                # 处理按键（按钮 0 回到初始点，按钮 1 控制夹爪）
                # elif event.type == pygame.JOYBUTTONDOWN:
                #     if event.button == 0:  # 按下按钮 0，回到初始点
                #         home_callback()
                #         home_active = True
                #     elif event.button == 1:  # 按下按钮 1，切换夹爪状态
                #         gripper_callback()
                #
                # elif event.type == pygame.JOYBUTTONUP:
                #     if event.button == 0 and home_active:  # 松开按钮 0，停止初始点运动
                #         home_stop_callback()
                #         home_active = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 1:  # 按下按钮 1，记录时间
                        btn1_press_time = time.time()
                    elif event.button == 0:  # 按下按钮 0
                        if in_speed_mode:
                            jog_speed = max(1, jog_speed - 10)
                            print(f"减速，当前速度：{jog_speed}")
                        else:
                            home_callback()
                            home_active = True

                elif event.type == pygame.JOYBUTTONUP:
                    global led_flash
                    if event.button == 1:
                        held_time = time.time() - btn1_press_time if btn1_press_time else 0
                        btn1_press_time = None
                        if held_time >= speed_mode_hold_time:
                            in_speed_mode = not in_speed_mode
                            led_flash = in_speed_mode
                            if in_speed_mode:
                                print(">>> 进入速度调节模式 <<<")
                            else:
                                print(">>> 退出速度调节模式 <<<")
                                mc.set_color(0, 255, 0)  # 恢复绿色常亮
                            # print(">>> 进入速度调节模式 <<<" if in_speed_mode else ">>> 退出速度调节模式 <<<")
                        else:
                            if in_speed_mode:
                                jog_speed = min(30, jog_speed + 10)
                                print(f"加速，当前速度：{jog_speed}")
                            else:
                                gripper_callback()
                    elif event.button == 0 and home_active:
                        home_stop_callback()
                        home_active = False

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("监听结束")
        pygame.quit()


# 定义回调函数
def jog_callback(axis, dir):
    """触发机械臂JOG坐标运动"""
    global jog_speed
    print("jog_speed", jog_speed, 'axis', axis, 'dir', dir)
    mc.jog_coord_fusion(axis, dir, jog_speed)

def stop_callback(coord_id):
    """停止机械臂运动"""
    mc.stop(1)
    print("停止运动")


def gripper_callback():
    """控制夹爪开合"""
    global gripper_state
    gripper_state = not gripper_state
    flag = 1 if gripper_state else 0
    print(f"夹爪 {'关闭' if flag else '打开'}")
    mc.set_gripper_state(flag, gripper_speed)
    # if gripper_state:
    #     mc.set_pro_gripper_open(14)
    # else:
    #     mc.set_pro_gripper_close(14)


def home_callback():
    """回到初始点"""
    mc.send_angles([0, 0, 0, -90, 0, 90, 40], home_speed, _async=True)


def home_stop_callback():
    """停止回到初始点"""
    mc.stop(1)
    print("停止运动")

#鼠标控制线程
def mouse():
    handle_mouse_event(jog_callback, stop_callback, gripper_callback)


if __name__ == '__main__':
    threading.Thread(target=led_flash_loop, daemon=True).start()
    # 启动监听
    # handle_mouse_event(jog_callback, stop_callback, gripper_callback)
    mouse_thread = threading.Thread(target=mouse)
    mouse_thread.start()
