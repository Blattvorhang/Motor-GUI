from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import yaml
import tkinter as tk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")


class DCMotor:
    def __init__(self):
        self.Ce = 0.05770058507
        self.CT = 60 * self.Ce / (2 * np.pi)
        self.T0 = 4.503348408
        self.Ra = 0.114
        self.Rf = 181.5
        self.U = 220
        self.T2 = 17000 / (3000 * 2 * np.pi / 60)
        self.error_sigma = 1
        self.R_Omega = 0
        with open(sys.path[0] + '/motor-config.yaml', 'r') as config:
            data = yaml.safe_load(config)
            self.Ce = (
                data['Rf'] / (data['nN'])
                    * (1 + data['Ra'] / data['Rf'] - data['IN'] * data['Ra'] / data['UN'])
            )
            self.CT = 60 * self.Ce / (2 * np.pi)
            self.T0 = (
                60 / (2 * np.pi * data['nN'])
                    * (data['UN'] * (data['IN'] - data['UN'] / data['Rf'])
                    * (1 + data['Ra'] / data['Rf'] - data['IN'] * data['Ra'] / data['UN'])
                    - data['PN'])
            )
            self.Ra = data['Ra']
            self.Rf = data['Rf']
            self.U = data['UN']
            self.T2 = data['PN'] / (data['nN'] * 2 * np.pi / 60)
            self.error_sigma = data['error_sigma']

    # the total resistance of the armature circuit
    @property
    def R(self) -> float:
        return self.Ra + self.R_Omega

    @property
    def n(self) -> float:
        return self.Rf / self.Ce \
            - self.R * self.Rf**2 / (self.Ce * self.CT * self.U**2) \
            * (self.T2 + self.T0)

    @property
    def If(self) -> float:
        return self.U / self.Rf

    @property
    def Ia(self) -> float:
        # Gaussian noise
        noise = np.random.normal(0, self.error_sigma)
        return (self.U - self.Ce * self.If * self.n) / self.R + noise


class MotorUI:
    def __init__(self) -> None:
        self.motor = DCMotor()

        # one set of data
        self.data = {}
        self.data['n'] = np.array([])
        self.data['Ia'] = np.array([])
        
        # all sets of data
        self.n_set = []
        self.Ia_set = []

        self.root = tk.Tk()
        self.root.title('直流电动机工作特性测定')
        self.root.iconbitmap('./images/motor.ico')
        # self.root.configure(background='#ffffff')

        self.canvas_sch = tk.Canvas(
            self.root,
            width=500,
            height=300,
            bg='#ffffff'
        )
        self.schematic = tk.PhotoImage(file='./images/schematic.png')
        self.canvas_sch.create_image(250, 150, image=self.schematic)
        self.canvas_sch.grid(columnspan=4)

        self.nstr = tk.StringVar()
        self.nstr.set('电机转速n：\n%.0f r/min' % (self.motor.n))
        self.msg_n = tk.Message(
            self.root,
            textvariable=self.nstr,
            width=150
        )
        self.msg_n.grid(row=1, column=2, rowspan=2)

        self.Iastr = tk.StringVar()
        self.Iastr.set('电枢电流Ia：\n%.2f A' % (self.motor.Ia))
        self.msg_Ia = tk.Message(
            self.root,
            textvariable=self.Iastr,
            width=150
        )
        self.msg_Ia.grid(row=1, column=3, rowspan=2)

        self.scale_RF = tk.Scale(
            self.root,
            label='负载转矩 T2',
            from_=30,
            to=100,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=True,
            command=self.updateT2
        )
        self.scale_RF.set(self.motor.T2)
        self.scale_RF.grid(row=1, column=0, columnspan=2, padx=10, pady=3)
        
        self.scale_R_Omega = tk.Scale(
            self.root,
            label='电枢串联电阻 RΩ（调速）',
            from_=0,
            to=0.8,
            resolution=0.001,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=True,
            command=self.updateROmega
        )
        self.scale_R_Omega.set(self.motor.R_Omega)
        self.scale_R_Omega.grid(row=2, column=0, columnspan=2, padx=10, pady=3)
        
        self.scale_Rf = tk.Scale(
            self.root,
            label='励磁回路电阻 Rf（弱磁）',
            from_=160,
            to=210,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=True,
            command=self.updateRf
        )
        self.scale_Rf.set(self.motor.Rf)
        self.scale_Rf.grid(row=3, column=0, columnspan=2, padx=10, pady=3)
        
        self.scale_U = tk.Scale(
            self.root,
            label='输入电压 U（调速）',
            from_=150,
            to=300,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=True,
            command=self.updateU
        )
        self.scale_U.set(self.motor.U)
        self.scale_U.grid(row=4, column=0, columnspan=2, padx=10, pady=3)

        self.btn_sample = tk.Button(
            self.root,
            text='记录数据',
            command=self.sample,
            width=8
        )
        self.btn_sample.grid(row=3, column=2, pady=10)

        self.btn_fit = tk.Button(
            self.root,
            text='绘制曲线',
            command=self.fit,
            width=8
        )
        self.btn_fit.grid(row=3, column=3, pady=10)

        self.btn_clear = tk.Button(
            self.root,
            text='清除',
            command=self.clear,
            width=8
        )
        self.btn_clear.grid(row=4, column=2, columnspan=2, pady=10)

        self.create_figure()
        self.root.mainloop()

    # refresh armature current and speed
    def refresh(self) -> None:
        self.nstr.set('电机转速n：\n%.0f r/min' % (self.motor.n))
        self.Iastr.set('电枢电流Ia：\n%.2f A' % (self.motor.Ia))

    def new_set(self) -> None:
        # check if data is empty
        if len(self.data['n']) != 0:
            self.n_set.append(self.data['n'])
            self.Ia_set.append(self.data['Ia'])
            self.data['n'] = np.array([])
            self.data['Ia'] = np.array([])

    # update the motor parameters
    # called when the scale is moved
    def updateT2(self, value) -> None:
        self.motor.T2 = float(value)
        self.refresh()
    
    # once R_Omega, Rf or U is changed, a new set of data is created
    def updateROmega(self, value) -> None:
        self.motor.R_Omega = float(value)
        self.new_set()
        self.refresh()
        
    def updateRf(self, value) -> None:
        self.motor.Rf = float(value)
        self.new_set()
        self.refresh()
        
    def updateU(self, value) -> None:
        self.motor.U = float(value)
        self.new_set()
        self.refresh()

    # measure the characteristics of the motor
    def sample(self) -> None:
        self.data['n'] = np.append(self.data['n'], self.motor.n)
        self.data['Ia'] = np.append(self.data['Ia'], self.motor.Ia)
        self.plot_point()

    def create_figure(self) -> None:
        self.figure = Figure((6, 6))
        self.draw = self.figure.add_subplot(111)
        self.draw.set_xlim((0, 200))
        self.draw.set_ylim((1600, 3800))
        self.draw.set_xlabel(r'$I_a$ / A')
        self.draw.set_ylabel(r'$n$ / (r/min)')
        self.canvas_plot = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas_plot.get_tk_widget().grid(row=0, column=4, rowspan=5)

    def plot_point(self) -> None:
        self.create_figure()
             
        # combine set and data
        n_set = self.n_set.copy()
        n_set.append(self.data['n'])
        Ia_set = self.Ia_set.copy()
        Ia_set.append(self.data['Ia'])
        
        # plot all sets of data
        for i in range(len(n_set)):
            self.draw.scatter(Ia_set[i], n_set[i])
        
        self.canvas_plot = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas_plot.get_tk_widget().grid(row=0, column=4, rowspan=5)

    # fit the data using linear regression
    def fit(self) -> None:
        # combine set and data
        n_set = self.n_set.copy()
        n_set.append(self.data['n'])
        Ia_set = self.Ia_set.copy()
        Ia_set.append(self.data['Ia'])
        
        # fit all sets of data
        for i in range(len(n_set)):
            A = np.vstack(
                [Ia_set[i], np.ones(len(Ia_set[i]))]
            ).T
            # n = a * Ia + b
            a, b = np.linalg.lstsq(A, n_set[i], rcond=None)[0]
            x = np.linspace(0, 200, 201)
            label = r'$n = %.2f \cdot I_a + %.2f$' % (a, b)
            self.draw.plot(x, x * a + b, label=label)
        
        self.draw.legend(loc='best')
        self.canvas_plot = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas_plot.get_tk_widget().grid(row=0, column=4, rowspan=5)

    # clear the data and refresh the plot
    def clear(self) -> None:
        self.n_set = []
        self.Ia_set = []
        self.data['n'] = np.array([])
        self.data['Ia'] = np.array([])
        self.create_figure()


if __name__ == '__main__':
    app = MotorUI()
