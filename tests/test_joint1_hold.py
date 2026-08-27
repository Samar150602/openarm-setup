#!/usr/bin/env python3
"""
Safe single-joint low-gain MIT hold test for OpenArm.
Targets ONLY joint 1 (send_can_id=0x01, recv_can_id=0x11).
Reads the current position, then holds there with low gains.
Ctrl+C or normal exit always disables the motor.
"""
import time
import sys
from openarm_can import (
    OpenArm,
    MotorType,
    ControlMode,
    MITParam,
)

CAN_INTERFACE = "can0"
SEND_ID = 0x01
RECV_ID = 0x11
# Best-guess motor type for joint 1 (largest/shoulder motor).
# Kept here only for CAN-frame scaling; actual safety limits are enforced
# by the motor's own firmware (already confirmed: TMAX=10Nm, VMAX=30rad/s).
MOTOR_TYPE = MotorType.DM8009

# Higher gains for a clearer resistance test - still well under the
# motor's own firmware TMAX=10Nm safety limit confirmed earlier.
KP = 10.0
KD = 1.5
DURATION_S = 20.0

def main():
    arm = OpenArm(CAN_INTERFACE, True)  # CAN-FD enabled
    arm.init_arm_motors(
        [MOTOR_TYPE],
        [SEND_ID],
        [RECV_ID],
        [ControlMode.MIT],
    )
    arm_component = arm.get_arm()

    try:
        print(">>> Enabling joint 1 only...")
        arm_component.enable_all()  # only 1 motor is known to this ArmComponent
        time.sleep(0.2)

        # Read current position to hold in place (not move to a new target)
        arm_component.refresh_all()
        motor = arm_component.get_motors()[0]
        current_pos = motor.get_position()
        print(f">>> Current position: {current_pos:.4f} rad")
        print(f">>> Holding at this position with kp={KP}, kd={KD} for {DURATION_S}s")
        print(">>> Try gently nudging the joint - it should resist softly. Ctrl+C to stop early.")

        start = time.time()
        while time.time() - start < DURATION_S:
            mit_param = MITParam(KP, KD, current_pos, 0.0, 0.0)  # kp, kd, q, dq, tau
            arm_component.mit_control_one(0, mit_param)
            arm.recv_all(500)
            m = arm_component.get_motors()[0]
            print(f"pos={m.get_position():.4f}  vel={m.get_velocity():.4f}  "
                  f"torque={m.get_torque():.4f}  tmos={m.get_state_tmos()}C", end="\r")
            time.sleep(0.02)
        print()

    except KeyboardInterrupt:
        print("\n>>> Interrupted by user.")
    finally:
        print(">>> Disabling joint 1...")
        arm_component.disable_all()
        print(">>> Done. Motor disarmed.")

if __name__ == "__main__":
    main()