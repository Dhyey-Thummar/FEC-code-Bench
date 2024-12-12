import matplotlib.pyplot as plt
import csv

def extract_hsc_times(csv_filename):
    y15 = []
    y25 = []
    y35 = []
    avg_time_15 = {"0.002": 0, "0.004": 0, "0.006": 0, "0.008": 0, "0.01": 0,}
    avg_time_25 = {"0.002": 0, "0.004": 0, "0.006": 0, "0.008": 0, "0.01": 0,}
    avg_time_35 = {"0.002": 0, "0.004": 0, "0.006": 0, "0.008": 0, "0.01": 0,}
    with open(csv_filename, newline="") as csv_file:
        lines = csv.reader(csv_file)
        for line in lines:
            if line[2] == "0.002":
                if line[3] != 3:
                    if line[1] == "15":
                       avg_time_15["0.002"] = avg_time_15["0.002"] + float(line[5])
                    elif line[1] == "25":
                        avg_time_25["0.002"] = avg_time_25["0.002"] + float(line[5])
                    elif line[1] == "35":
                        avg_time_35["0.002"] = avg_time_35["0.002"] + float(line[5])
            elif line[2] == "0.004":
                if line[3] != 3:
                    if line[1] == "15":
                       avg_time_15["0.004"] = avg_time_15["0.004"] + float(line[5])
                    elif line[1] == "25":
                        avg_time_25["0.004"] = avg_time_25["0.004"] + float(line[5])
                    elif line[1] == "35":
                        avg_time_35["0.004"] = avg_time_35["0.004"] + float(line[5])
            elif line[2] == "0.006":
                if line[3] != 3:
                    if line[1] == "15":
                       avg_time_15["0.006"] = avg_time_15["0.006"] + float(line[5])
                    elif line[1] == "25":
                        avg_time_25["0.006"] = avg_time_25["0.006"] + float(line[5])
                    elif line[1] == "35":
                        avg_time_35["0.006"] = avg_time_35["0.006"] + float(line[5])
            elif line[2] == "0.008":
                if line[3] != 3:
                    if line[1] == "15":
                       avg_time_15["0.008"] = avg_time_15["0.008"] + float(line[5])
                    elif line[1] == "25":
                        avg_time_25["0.008"] = avg_time_25["0.008"] + float(line[5])
                    elif line[1] == "35":
                        avg_time_35["0.008"] = avg_time_35["0.008"] + float(line[5])
            elif line[2] == "0.01":
                if line[3] != 3:
                    if line[1] == "15":
                       avg_time_15["0.01"] = avg_time_15["0.01"] + float(line[5])
                    elif line[1] == "25":
                        avg_time_25["0.01"] = avg_time_25["0.01"] + float(line[5])
                    elif line[1] == "35":
                        avg_time_35["0.01"] = avg_time_35["0.01"] + float(line[5])
    
    for k1, k2, k3 in zip(avg_time_15, avg_time_25, avg_time_35):
        avg_time_15[k1] = avg_time_15[k1] / 3
        y15.append(avg_time_15[k1])
        avg_time_25[k2] = avg_time_25[k2] / 3
        y25.append(avg_time_25[k2])
        avg_time_35[k3] = avg_time_35[k3] / 3
        y35.append(avg_time_35[k3])
    
    return y15, y25, y35
    


x = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
y = [0.050, 0.0379, 0.0302, 0.0250, 0.0216, 0.0189, 0.0168, 0.0151, 0.0137, 0.0126, 0.0116]
# y15 = [99, 98, 94, 96, 92]
# y25 = [95, 91, 86, 85, 81]
# y35 = [87, 84, 83, 81, 81]

plt.title("FPS vs Threshold (HSC Ratio = 0.758)")
plt.plot(x, y)
plt.xlabel("FPS (F)")
plt.ylabel("Threshold (t)")
plt.xlim(15, 70)
plt.ylim(0, 0.05)
plt.show()