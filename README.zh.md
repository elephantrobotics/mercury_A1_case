# mercury_A1_case

# 6D 鼠标控制

**使用设备：** 3Dconnexion SpaceMouse Wireless 蓝牙无线版、蓝牙USB接收器。

**适用机型：** Mercury A1。

**末端执行器：** MyCobot Pro 自适应夹爪、myGripper F100 力控夹爪

## 摆放位置

将 6D 鼠标的 `3Dconnexion` 标志面朝向使用者，并按如下方式摆放：

![6D mouse](./res/6d_mouse.jpg)

## 按键功能对应

![6D mouse on_off0](./res/6d_mouse_on_off.png)

控制器帽是 SpaceMouse Wireless 的核心。它的 Six-Degrees-of-Freedom (6DoF)传感器允许您推、拉、旋转或倾斜以平移、缩放和旋转。

![6D mouse control](./res/6d_mouse_control.jpg)
![6D mouse control](./res/6d_mouse_button_control.png)

**1:** 前后平移；控制机械臂的X轴坐标，向前平移控制X轴正方向，向后平移控制X轴负方向。

![6D mouse](./res/forward_backward.gif)

**2:** 左右平移；控制机械臂的Y轴坐标，左平移控制Y轴正方向，右平移控制Y轴负方向。

![6D mouse](./res/left_right.gif)

**3:** 上拉下压；控制机械臂的Z轴坐标，向上拉控制Z轴正方向，向下压控制Z轴负方向

![6D mouse](./res/up_down.gif)

**4:** 左右倾斜；控制机械臂的翻滚角。

![6D mouse](./res/roll.gif)

**5:** 前后倾斜；控制机械臂的俯仰角。

![6D mouse](./res/pitch.gif)

**6:** 左右旋转；控制机械臂的偏航角。

![6D mouse](./res/yaw.gif)

- **按钮1：** 左侧按钮，长按按钮，机械臂移动到初始点位，松开按钮停止机械臂移动。
  
- **按钮2：** 右侧按钮，点击按钮，控制夹爪的张开或者闭合。


## 脚本说明

**非轨迹融合模式脚本:**

  - 6D_mouse_serial_serial_port_control.py
  - 6D_mouse_serial_socket_control.py
  - serial_port_control_gripper_f100.py
  - socket_control_gripper_f100.py
  
**轨迹融合模式脚本（支持多维方向同时运动）:**

  - 6D_mouse_serial_serial_port_control_fusion.py
  - 6D_mouse_socket_control_fusion.py

## 按钮速度切换

程序启动后

**进入速度切换模式：** 长按 右侧按钮（**按钮2**） `1`秒松开，进入速度切换模式，此时末端LED灯板闪烁紫色。加速请点击 右侧按钮（**按钮2**），减速请点击 左侧按钮（**按钮1**）； 考虑到鼠标操作灵敏度较高，为降低高速运动引发机械臂碰撞的风险，非轨迹融合模式下最大切换速度设为 50，轨迹融合模式下则限制为 30

**退出速度切换模式：** 长按 右侧按钮（**按钮2**） `1`秒松开，退出速度切换模式，此时末端LED灯板变回绿色。


## 使用方式

>> 注意：使用之前，请打开鼠标的电源开关。

### 安装依赖

```python
pip install pygame
```

**注意：** 若使用**轨迹融合模式**程序，需烧录 `MouseControl_v1.0.42.bin` 固件、安装`mercury_A1_case`文件夹下的pymycobot库版本 `pip install pymycobot-3.9.8b1-py3-none-any.whl`

下载代码: https://github.com/elephantrobotics/mercury_A1_case

**这里使用机械臂的通信方式有串口控制和socket控制两种，将鼠标的蓝牙接收器连接到电脑或者机器系统。**

### 方式1：串口控制

打开终端，切换路径到 `mercury_A1_case` 文件夹，运行程序即可：

- 非轨迹融合-自适应夹爪

```python
python3 6D_mouse_serial_port_control.py
```

- 非轨迹融合-力控夹爪

```python
python3 serial_port_control_gripper_f100.py
```

- 轨迹融合-自适应夹爪

```python
python3 6D_mouse_serial_port_control_fusion.py
```


**注意：程序启动后，首先要长按左侧按钮（按钮1）将机械臂移动到预设的初始点位，然后再进行其他操作。**

### 方式2：Socket控制

>> 注意： raspberryPi版本 仅支持python3 使用此类前提的机械臂有服务器，并且已经开启服务。


#### 启动服务端

使用socket控制之前，需要注意：

- 机械臂系统和控制端（客户端）需要在同一网络。

- 需要先在机械臂系统里执行服务器文件，开启服务端。

- 服务器文件执行后，提示“Binding succeeded” 和 “waiting connect” 表示开启成功。

打开终端， 切换路径到`mercury_A1_case` 文件夹，运行程序即可：

```python
python3 server_A1_close_loop.py
```

#### 客户端

**修改IP地址和端口号**

在PC电脑端，切换路径到 `mercury_A1_case` 文件夹，编辑6D_mouse_serial_socket_control.py文件：

根据服务端真实的IP和端口号进行修改即可。

```bash
import pygame
import time
from pymycobot import MercurySocket

# 初始化机械臂,IP和端口号需根据实际进行修改
mc = MercurySocket('192.168.1.4', 9000)

···
```

然后运行程序即可。

- 非轨迹融合-自适应夹爪

```python
python3 6D_mouse_socket_control.py
```

- 非轨迹融合-力控夹爪

```python
python3 socket_control_gripper_f100.py
```

 - 轨迹融合-自适应夹爪

```python
python3 6D_mouse_socket_control_fusion.py
```


**注意：程序启动后，首先要长按左侧按钮（按钮1）将机械臂移动到预设的初始点位，然后再进行其他操作。**

### 脚本修改速度

可根据需要自行修改机械臂的JOG坐标运动速度、夹爪的速度和初始点运动速度。在文件的开头进行修改，具体如下：

```bash
···
# jog 坐标运动速度
jog_speed = 20

# 夹爪速度
gripper_speed = 70

# 初始点运动速度
home_speed = 10
···
```

## 注意事项

当 SpaceMouse Wireless 的状态 LED 变为红色时，说明它的电池电量不足 10%，此时应该给它
充电。使用随附的 USB cable将 SpaceMouse 连接到计算机的充电端口。当 SpaceMouse Wireless 正
在充电时，状态 LED 就会呈绿色并闪烁，充满电后则会变成长亮的绿色。 
