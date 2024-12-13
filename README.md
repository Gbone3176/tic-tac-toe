#代码说明

    **main.py**:用于下机位ESP32通过串口接收并解析openMV发送的移动指令，并进行实景映射，控制二维滑台、舵机等机构实现棋子的抓取与放置。

    **minimax2.py**:通过$minimax$博弈算法配合$\alpha\beta$ 减枝算法进行状态搜索和最终决策。 

    **vis_fullparams.py**:视觉部分代码。控制openMV进行棋盘状态检测并依据当前状况进行决策，输出移动指令，通过串口传送至下机位ESP32。
