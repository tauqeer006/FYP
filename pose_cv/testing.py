import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import yaml

# ---------------- Load YAML ----------------
with open("new_exercise.yml") as f:
    exercises = yaml.safe_load(f)

exercise_names = [ex["name"] for ex in exercises["shoulder_rehab_exercises"]]

# Ask user for exercise
print("Available exercises:")
for name in exercise_names:
    print("-", name)

choice = input("Enter exercise name: ").strip().lower()
exercise = next((ex for ex in exercises["shoulder_rehab_exercises"] if ex["name"].strip().lower()==choice), None)
if not exercise:
    print("Exercise not found!")
    exit()

# ---------------- 3D Skeleton Setup ----------------
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(-200, 200)
ax.set_ylim(-200, 200)
ax.set_zlim(-200, 200)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
ax.set_title(f"3D Skeleton - {exercise['name']}")

# Skeleton points: shoulder, elbow, wrist
def get_arm_coords(shoulder_angle, elbow_angle, side='left'):
    shoulder = np.array([0, 0, 0])
    elbow = np.array([np.sin(np.radians(shoulder_angle))*100,
                      np.cos(np.radians(shoulder_angle))*100,
                      0])
    wrist = np.array([elbow[0] + np.sin(np.radians(elbow_angle))*80,
                      elbow[1] - np.cos(np.radians(elbow_angle))*80,
                      0])
    return np.array([shoulder, elbow, wrist])

ref_left = get_arm_coords(exercise['left_arm']['shoulder_angle'], exercise['left_arm']['elbow_angle'])
ref_right = get_arm_coords(exercise['right_arm']['shoulder_angle'], exercise['right_arm']['elbow_angle'])

line_left, = ax.plot([], [], [], lw=4, c='blue', label='Left Arm')
line_right, = ax.plot([], [], [], lw=4, c='green', label='Right Arm')

# Animation function
def animate(i):
    # For simplicity, do a smooth oscillation around angles to simulate movement
    factor = np.sin(i * 0.05)  # oscillation
    shoulder_left = exercise['left_arm']['shoulder_angle'] + factor*15
    elbow_left = exercise['left_arm']['elbow_angle'] + factor*10
    shoulder_right = exercise['right_arm']['shoulder_angle'] + factor*15
    elbow_right = exercise['right_arm']['elbow_angle'] + factor*10

    left_coords = get_arm_coords(shoulder_left, elbow_left)
    right_coords = get_arm_coords(shoulder_right, elbow_right)

    line_left.set_data(left_coords[:,0], left_coords[:,1])
    line_left.set_3d_properties(left_coords[:,2])
    line_right.set_data(right_coords[:,0], right_coords[:,1])
    line_right.set_3d_properties(right_coords[:,2])
    return line_left, line_right

ani = FuncAnimation(fig, animate, frames=200, interval=50, blit=True)
plt.legend()
plt.show()
