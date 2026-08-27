# Verified Working — Bring-up Log

Record of the hardware bring-up tests performed on this setup, in order. Useful as a reference if wiring or software gets touched later and something needs re-verifying.

## Environment
- Ubuntu 22.04, ROS2 Humble
- 2x PCAN-USB Pro FD adapters (can0 = right arm, can1 = left arm)
- openarm-can-utils / libopenarm-can-dev 1.3.4-1.ubuntu22.04.1 (via `ppa:openarm/main`)

## 1. CAN interface bring-up
```
$ ip -details link show can0
can <FD> state ERROR-ACTIVE (berr-counter tx 0 rx 0)
bitrate 1000000 dbitrate 5000000
```
✅ Zero bus errors, correct FD bitrate on both can0 and can1.

## 2. Motor discovery (can0, right arm)
```
$ sudo openarm-can-cli -i can0 discover
DISCOVERY SUMMARY (Total: 8 motors found)
Send ID     Recv ID     Internal Baudrate Setting
0x01        0x11        5 Mbps (FD)
0x02        0x12        5 Mbps (FD)
0x03        0x13        5 Mbps (FD)
0x04        0x14        5 Mbps (FD)
0x05        0x15        5 Mbps (FD)
0x06        0x16        5 Mbps (FD)
0x07        0x17        5 Mbps (FD)
0x08        0x18        5 Mbps (FD)
```
✅ All 8 motors respond on both can0 and can1.

## 3. Motor parameters
```
$ sudo openarm-can-cli -i can0 show_param
```
✅ Control Mode = MIT on all motors, no fault states, sane factory limits (PMAX/VMAX/TMAX).

## 4. Encoder feedback (manual movement)
```
$ sudo openarm-can-cli -i can0 monitor -t 60000
```
✅ All 8 joints on both arms tracked manual movement smoothly — no jumps, dropouts, or sign flips.

## 5. Closed-loop torque control (joint 1)
Custom test script (`tests/test_joint1_hold.py`) — enables joint 1 only, holds current position with MIT control (kp=10, kd=1.5), logs live torque while manually nudging the joint.

Result: torque climbed from ~0.1 Nm to ~0.6 Nm in response to manual push, confirming the full control loop (position error → commanded torque → CAN frame → motor output) is working end-to-end.

## 6. ROS2 / MoveIt2 — simulation
```
$ ros2 launch openarm_bimanual_moveit_config demo.launch.py
```
✅ Both arms load correctly in RViz, `/joint_states` publishes 16 joints, planning + execution work in fake hardware mode.

## 7. ROS2 / MoveIt2 — real hardware
```
$ ros2 launch openarm_bimanual_moveit_config demo.launch.py use_fake_hardware:=false
```
✅ `/joint_states` reflects real arm positions. Arm trajectory planning + execution confirmed on both arms.

⚠️ Gripper execution initially failed (`GripperCommand` action mismatch) — see main README's [Fixes](README.md#fixes-made) section. Confirmed working after config fix.

## 8. Gripper control (post-fix)
✅ Both grippers plan and execute successfully via MoveIt2 after the `moveit_controllers.yaml` fix.