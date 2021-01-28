import easygui
import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

#-----------------------------------------------------------------------------------------------------------------------
# SERIJSKA KOMUNIKACIJA ------------------------------------------------------------------------------------------------

def start(ser):
    ser.write('(START)'.encode())

def normal(ser):
    ser.write('(NORMAL)'.encode())
    #ser.write('(TEST)'.encode())

def chs(ser):
    ser.write('(CHs:ON)'.encode())

def stop(ser):
    ser.write('(STOP)'.encode())

ser = serial.Serial(port = 'COM1', baudrate = 921600, timeout = 1, parity = serial.PARITY_NONE, bytesize = serial.EIGHTBITS, rtscts = 1)

normal(ser)
normal_ok = ser.read(11)
print(normal_ok)

chs(ser)
ch_ok = ser.read(11)
print(ch_ok)

start(ser)
start_ok = ser.read(4)
print(start_ok)

global odobrenje

if start_ok != '(OK)'.encode():
    print("Komanda START nije poslata na ispravan nacin")
    odobrenje = False
    exit()
elif normal_ok != '(OK)'.encode():
    print("Komanda NORMAL nije poslata na ispravan nacin")
    odobrenje = False
    exit()
elif ch_ok != '(OK)'.encode():
    print("Komanda CHs:ON nije poslata na ispravan nacin")
    odobrenje = False
    exit()
else:
    odobrenje = True

#-----------------------------------------------------------------------------------------------------------------------
# ANIMACIJA ------------------------------------------------------------------------------------------------------------

animation_end = False

def gen():
    global animation_end
    i = 0
    while animation_end == False:
        i += 1
        yield i

global time
time = 0

def animation_frame(i):
    f = 1 / 500
    global animation_end

    if odobrenje == True:
        for i in range(50):
            ser.reset_output_buffer()
            podaci = ser.read(11)

            if podaci == ''.encode():
                animation_end = True
                easygui.msgbox("Signal je iscrtan do kraja", title="simple gui")
                break

            if podaci[0:1] == '('.encode() and podaci[10:11] == ')'.encode():
                if podaci == ''.encode():
                    print('kraj')

                    animation_end = True
                    break

                global Ch1
                Ch1 = konverzija(podaci)

                emg_signal.append(Ch1)

                global time
                time += f
                t.append(time)
            else:
                exit()

        emg.set_xdata(t)
        emg.set_ydata(emg_signal)

        y_ax_zero_crossing = zero_crossing(emg_signal)
        x_ax_zero_crossing = [x / 10 for x in range(len(y_ax_zero_crossing))]

        zero_cross.set_xdata(x_ax_zero_crossing)
        zero_cross.set_ydata(y_ax_zero_crossing)

        trend1 = izracunavanje_trenda(y_ax_zero_crossing)
        trend.set_xdata(x_ax_zero_crossing)
        trend.set_ydata(trend1)

        return [emg, zero_cross, trend]

#-----------------------------------------------------------------------------------------------------------------------
# FUNKCIJE -------------------------------------------------------------------------------------------------------------

def konverzija(emg_signal):
        C1_first_byte = emg_signal[1]
        C1_second_byte = emg_signal[2]
        C1_third_byte = emg_signal[3]

        Reference_V = 4.5  # A/D converter reference voltage
        Amp_Gain = 24  # gain of the amplifiers

        C1_AD = (C1_first_byte << 16) | (C1_second_byte << 8) | (C1_third_byte)
        # merge all bytes of CHANNEL 1 in one variable

        if C1_AD >= 8388608:
        #most important bit defines sign (0 – positive; 1 - negative)
            C1_AD -= 16777216

        Scale_Factor_uV = 1000000 * ((Reference_V / (8388608 - 1)) / Amp_Gain)
        # scale factor for converting from A/D units to voltage

        Channel_1 = C1_AD * Scale_Factor_uV;

        return Channel_1

def zero_crossing(emg_lista):
    crossings = []
    crossings.append(0)
    cnt_niz = 0
    cnt = 0
    for i in range(1, len(emg_lista)):
        if emg_lista[i - 1] * emg_lista[i] < 0:
            crossings[cnt_niz] += 1
        cnt += 1
        if cnt == 49:
            cnt = 0
            crossings.append(0)
            cnt_niz += 1
    return crossings

def izracunavanje_trenda (crossings):
    tr = []
    for i in range(len(crossings)):
        tr.append(np.mean(crossings[i:i + 100]))
    return tr

#-----------------------------------------------------------------------------------------------------------------------
# ISCRTAVANJE GRAFIKA --------------------------------------------------------------------------------------------------

emg_signal = []
t = []
x_ax_zero_crossing = []
y_ax_zero_crossing = []

fig, axs = plt.subplots(nrows=2, ncols=1,constrained_layout=True)

axs[0].set_title('EMG signal')
axs[0].set_xlabel('vreme [s]')
axs[0].set_ylabel('vrednost [mV]')
emg, = axs[0].plot(t, emg_signal, linewidth = 0.6)
axs[0].axis([0,30,-5,5])

axs[1].set_title('Zero crossings')
axs[1].set_xlabel('vreme [s]')
axs[1].set_ylabel('broj prolazaka')
zero_cross, = axs[1].plot(x_ax_zero_crossing, y_ax_zero_crossing, linewidth = 0.6, label = "Broj prolazaka kroz nulu")
trend, = axs[1].plot(x_ax_zero_crossing, y_ax_zero_crossing, 'r--', linewidth = 1.2, label = 'Analiza zamora misica')
axs[1].axis([0,30,-5,25])
axs[1].legend(loc = "upper left")

#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------

animation = FuncAnimation(fig, func=animation_frame, interval=1, frames=gen, repeat=False)

plt.show()

ser.write('(STOP)'.encode())