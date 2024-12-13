# 2024秋电子系统设计代码说明
成员：闵鹏升、郭博文、张云飞

1. 代码结构：

```bash
└─tic-tac-toe
    │  README.md
    │
    ├─ESP32
    │      main.py
    │
    └─OpenMV
            minimax2.py
            vis_fullparams.py
```

2. 代码说明

    __main.py__:用于下机位ESP32通过串口接收并解析openMV发送的移动指令，并进行实景映射，控制二维滑台、舵机等机构实现棋子的抓取与放置。

    __minimax2.py__:通过$minimax$博弈算法配合$\alpha\beta$ 减枝算法进行状态搜索和最终决策。 

    __vis_fullparams.py__:视觉部分代码。控制openMV进行棋盘状态检测并依据当前状况进行决策，输出移动指令，通过串口传送至下机位ESP32。