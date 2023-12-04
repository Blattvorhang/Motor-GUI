# Motor GUI
并励直流电动机工作特性测定实验，基于[zz-f-g/MotorGUI](https://github.com/zz-f-g/MotorGUI)进行修改。

使用人机交互界面完成。

## 依赖环境
- Python $\ge$ 3.9
- Numpy $\ge$ 1.21.5
- Matplotlib $\ge$ 3.5.2
- PyYAML
- tkinter

## 文件说明
```shell
.
├── dc-motor.py # 程序源码
├── images
│   ├── motor.ico # UI 图标
│   └── schematic.png # 电机电路图
├── motor-config.yaml # 电机模型参数配置文件
└── README.md # 项目说明
```

## 操作说明
初始界面

![](./images/default.png)

记录数据

![](./images/scatter.png)

最小二乘法，使用`np.linalg.lstsq`

![](./images/fit.png)

多组数据描点

![](./images/R_changed_scatter.png)

改变电枢串联电阻$R_{\Omega}$

![](./images/R_changed_fit.png)

改变励磁回路电阻$R_{\text{f}}$

![](./images/Rf_changed_fit.png)

改变输入电压$U$

![](./images/U_changed_fit.png)

电机YAML配置文件

![](./images/yaml.png)