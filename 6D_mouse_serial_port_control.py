import threading

import pygame
import time
from pymycobot.mercury import Mercury

# 初始化机械臂
mc = Mercury('/dev/ttyAMA1', 115200)

# 检测机械臂是否上电
if mc.is_power_on() != 1:
    mc.power_on()

# 设置夹爪透传模式
mc.set_gripper_mode(0)

THRESHOLD = 0.7  # 鼠标轴触发运动的阈值
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
    3: 4,
    4: 5,
    5: 6
}

# 轴运动方向映射
DIRECTION_MAPPING = {
    0: (-1, 1),  # 轴0 (Y) -> 负向 -1，正向 1
    1: (-1, 1),  # 轴1 (X) -> 负向 -1，正向 1
    2: (-1, 1),  # 轴2 (Z) -> 负向 -1，正向 1
    3: (-1, 1),  # 轴3 (RX) -> 负向 -1，正向 1
    4: (1, -1),  # 轴4 (RY) -> 负向 1，正向 -1
    5: (1, -1)  # 轴5 (RZ) -> 负向 1，正向 -1
}


def led_flash_loop():
    """LED灯闪烁提示速度调节模式"""
    last_led_state = None
    while True:
        if led_flash:
            mc.set_color(128, 0, 128)  # 紫色
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

    global jog_speed

    try:
        while True:
            for event in pygame.event.get():
                # 处理轴运动
                if event.type == pygame.JOYAXISMOTION:
                    axis_id = event.axis
                    value = event.value

                    if axis_id in AXIS_MAPPING:
                        coord_id = AXIS_MAPPING[axis_id]
                        pos_dir, neg_dir = DIRECTION_MAPPING[axis_id]

                        if value > THRESHOLD and active_axes.get(axis_id) != 1:
                            jog_callback(coord_id, pos_dir)
                            active_axes[axis_id] = 1

                        elif value < -THRESHOLD and active_axes.get(axis_id) != -1:
                            jog_callback(coord_id, neg_dir)
                            active_axes[axis_id] = -1

                        elif -DEAD_ZONE < value < DEAD_ZONE and axis_id in active_axes:
                            stop_callback(coord_id)
                            del active_axes[axis_id]

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
                        else:
                            if in_speed_mode:
                                jog_speed = min(50, jog_speed + 10)
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
def jog_callback(coord_id, direction):
    """触发机械臂JOG坐标运动"""
    print(f"机械臂 {coord_id} 方向 {'正向' if direction == 1 else '负向'} 运动 - 速度: {jog_speed}")
    if direction != 1:
        direction = 0
    if coord_id in [1, 2, 3]:
        mc.jog_coord(coord_id, direction, jog_speed, _async=True)
    else:
        model = [2, 1, 3]
        model_dir = [0, 1, 1]
        model_id = model[coord_id - 4]
        model_dire = direction ^ model_dir[coord_id - 4]
        mc.jog_rpy(model_id, model_dire, jog_speed, _async=True)


def stop_callback(coord_id):
    """停止机械臂运动"""
    mc.stop(1)
    print("停止运动")


def gripper_callback():
    """控制夹爪开合"""
    global gripper_state
    gripper_state = not gripper_state
    flag = 1 if gripper_state else 0
    # print(f"夹爪 {'关闭' if flag else '打开'}")
    mc.set_gripper_state(flag, gripper_speed)


def home_callback():
    """回到初始点"""
    mc.send_angles([0, 0, 0, -90, 0, 90, 0], home_speed, _async=True)


def home_stop_callback():
    """停止回到初始点"""
    mc.stop(1)
    print("停止运动")


if __name__ == '__main__':
    threading.Thread(target=led_flash_loop, daemon=True).start()
    # 启动监听
    handle_mouse_event(jog_callback, stop_callback, gripper_callback)
