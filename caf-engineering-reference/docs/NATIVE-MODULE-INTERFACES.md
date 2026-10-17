# Selected native module interfaces

Literal interfaces for modules relevant to AHU-1. Source names, property 3365 port IDs, property 3670 role IDs, property 931 enum sets, property 117 unit enums, and typed property 3113 defaults are preserved. Empty/absent defaults are not interpreted as a runtime zero. Port labels are not guessed from IDs. These records support lookup in the original CAF and CCT Help; they do not establish a successful clone.

## Cooling Proportional Valve w Dehumidification v51

Source: `Output_Control_Modules_1.caf`; object `8-1/575_1.536_10030`; class 536; role 6613; complete subtree 210 objects; 88 internal wires.

Ordered exports: `7000, 7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008, 7009, 7010, 7011, 7012, 7013, 7014, 7015, 7016, 7018, 8000, 8001, 8002, 8003, 32520`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 32520 | output enum | 37 |  | 909 | absent |
| 7000 | input enum | 143 |  | 909 | absent |
| 7001 | input float | 176 | 64 |  | float: 55 |
| 7002 | input float | 190 | 64 |  | float: 55 |
| 7003 | input float | 121 | 29 |  | float: 50 |
| 7004 | input float | 122 | 29 |  | float: 50 |
| 7005 | input enum | 174 |  | 868 | enum: 8 |
| 7006 | input enum | 175 |  | 507 | enum: 64 |
| 7007 | input enum | 65 |  | 868 | enum: 15 |
| 7008 | input float | 126 | 98 |  | float: 100 |
| 7009 | input float | 89 | 98 |  | float: 30 |
| 7010 | input float | 131 | 98 |  | float: 30 |
| 7011 | input float | 103 | 98 |  | float: 100 |
| 7012 | input float | 156 | 64 |  | float: 41 |
| 7013 | input float | 132 | 64 |  | float: 41 |
| 7014 | input float | 130 | 64 |  | float: 4 |
| 8000 | output float | 58 | 98 |  | absent |
| 8001 | output enum | 179 |  |  | absent |
| 8002 | output enum | 53 |  | 351 | absent |
| 7015 | input boolean | 3510 |  |  | absent |
| 7016 | input float | 3511 | 98 |  | absent |
| 7018 | input enum | 3356 |  | 1347 | absent |
| 8003 | output float | 3735 | 98 |  | absent |

## Sideloop Interlock Binary To Analog

Source: `Output_Control_Modules_2.caf`; object `8-1/575_1.536_10086`; class 536; role 1331; complete subtree 54 objects; 20 internal wires.

Ordered exports: `7000, 7001, 7002, 7003, 7004, 7005, 7006, 8001`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input enum | 435 |  |  | absent |
| 7001 | input enum | 143 |  | 1053 | enum: 2 |
| 7002 | input enum | 83 |  | 906 | absent |
| 7003 | input float | 325 | 73 |  | float: 30 |
| 7004 | input float | 316 | 73 |  | float: 30 |
| 8001 | output float | 825 | 98 |  | absent |
| 7005 | input float | 328 | 98 |  | absent |
| 7006 | input float | 327 | 98 |  | float: 100 |

## Sideloop Interlock Binary To Binary

Source: `Output_Control_Modules_2.caf`; object `8-1/575_1.536_10087`; class 536; role 1332; complete subtree 50 objects; 16 internal wires.

Ordered exports: `7000, 7001, 7002, 7003, 7004, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input enum | 435 |  |  | absent |
| 7001 | input enum | 143 |  | 1053 | enum: 2 |
| 7002 | input enum | 83 |  | 906 | absent |
| 7003 | input float | 325 | 73 |  | float: 30 |
| 7004 | input float | 316 | 73 |  | float: 30 |
| 8000 | output enum | 825 |  |  | absent |

## Damper Minimum Position Reset by CO2

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10107`; class 536; role 1118; complete subtree 20 objects; 7 internal wires.

Ordered exports: `7000, 7003, 8000, 7001, 7002, 7004`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 8000 | output float | 825 | 98 |  | absent |
| 7000 | input float | 865 | 96 |  | float: 800 |
| 7001 | input float | 866 | 96 |  | float: 800 |
| 7002 | input float | 867 | 96 |  | float: 1000 |
| 7003 | input float | 868 | 98 |  | absent |
| 7004 | input float | 869 | 98 |  | float: 90 |

## Sideloop Average Inputs

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10384`; class 536; role 1330; complete subtree 8 objects; 3 internal wires.

Ordered exports: `7000, 7001, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input float | 209 |  |  | absent |
| 7001 | input float | 253 |  |  | absent |
| 8000 | output float | 825 |  |  | absent |

## Sideloop Maximum Selector

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10385`; class 536; role 1333; complete subtree 8 objects; 3 internal wires.

Ordered exports: `7000, 7001, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input float | 209 |  |  | absent |
| 7001 | input float | 253 |  |  | absent |
| 8000 | output float | 825 |  |  | absent |

## Sideloop Minimum Selector

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10386`; class 536; role 1334; complete subtree 8 objects; 3 internal wires.

Ordered exports: `7000, 7001, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input float | 209 |  |  | absent |
| 7001 | input float | 253 |  |  | absent |
| 8000 | output float | 825 |  |  | absent |

## Sideloop Sum Inputs

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10387`; class 536; role 1341; complete subtree 8 objects; 3 internal wires.

Ordered exports: `7000, 7001, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input float | 209 |  |  | absent |
| 7001 | input float | 253 |  |  | absent |
| 8000 | output float | 825 |  |  | absent |

## Unocc Cooling Fan Lockout

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10438`; class 536; role 2700; complete subtree 14 objects; 6 internal wires.

Ordered exports: `7000, 7001, 7003, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input enum | 162 |  | 345 | absent |
| 7001 | input boolean | 54 |  |  | boolean: false |
| 7003 | input boolean | 620 |  |  | boolean: true |
| 8000 | output boolean | 825 |  |  | absent |

## Unocc Heating Fan Lockout

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10440`; class 536; role 2701; complete subtree 19 objects; 8 internal wires.

Ordered exports: `7000, 7001, 7002, 7003, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input enum | 162 |  | 345 | absent |
| 7001 | input boolean | 109 |  |  | boolean: false |
| 7002 | input boolean | 599 |  |  | boolean: false |
| 7003 | input boolean | 619 |  |  | boolean: true |
| 8000 | output boolean | 825 |  |  | absent |

## WarmupCooldown Determination

Source: `Setpoint-Misc_Modules.caf`; object `8-1/575_1.536_10448`; class 536; role 1000; complete subtree 46 objects; 19 internal wires.

Ordered exports: `7001, 7002, 7003, 8000, 7000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 8000 | output enum | 37 |  | 366 | absent |
| 7000 | input float | 226 | 64 |  | float: 15 |
| 7001 | input float | 205 | 64 |  | float: 59 |
| 7002 | input float | 229 | 64 |  | float: 72 |
| 7003 | input enum | 488 |  | 366 | absent |

## Dehumidification Sequencing

Source: `State_Generation_Modules.caf`; object `8-1/575_1.536_10004`; class 536; role 158; complete subtree 22 objects; 9 internal wires.

Ordered exports: `7005, 7000, 7004, 7002, 7001, 7003, 8001, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input float | 290 | 29 |  | float: 50 |
| 7001 | input float | 122 | 29 |  | float: 60 |
| 7002 | input enum | 53 |  | 351 | absent |
| 7003 | input enum | 181 |  | 351 | absent |
| 8000 | output enum | 37 |  | 912 | absent |
| 7004 | input float | 116 | 64 |  | float: 69 |
| 7005 | input float | 59 | 64 |  | float: 73 |
| 8001 | output float | 621 | 64 |  | float: 69 |

## Unit Enable Determination

Source: `State_Generation_Modules.caf`; object `8-1/575_1.536_10122`; class 536; role 117; complete subtree 38 objects; 14 internal wires.

Ordered exports: `7002, 7000, 7001, 7003, 7004, 8000`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input enum | 145 |  | 349 | enum: 1 |
| 7001 | input enum | 106 |  | 349 | enum: 1 |
| 7002 | input boolean | 167 |  |  | absent |
| 7003 | input float | 168 | 73 |  | float: 60 |
| 7004 | input enum | 182 |  | 385 | absent |
| 8000 | output enum | 37 |  | 349 | enum: 1 |

## PID Tuning Reset

Source: `State_Generation_Modules.caf`; object `8-1/575_1.536_10130`; class 536; role 5974; complete subtree 19 objects; 6 internal wires.

Ordered exports: `7000, 8000, 8001`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 7000 | input boolean | 3357 |  |  | absent |
| 8000 | output enum | 3356 |  | 1347 | absent |
| 8001 | output boolean | 37 |  |  | absent |

## WarmupCooldown Sequencing

Source: `State_Generation_Modules.caf`; object `8-1/575_1.536_10141`; class 536; role 1041; complete subtree 40 objects; 17 internal wires.

Ordered exports: `7000, 7003, 7006, 7008, 7009, 7010, 8001, 32520, 7011`.

| Port | Direction / type | Role | Units enum | Enum set | Literal default |
|---:|---|---:|---:|---:|---|
| 32520 | output enum | 37 |  | 885 | absent |
| 7000 | input enum | 143 |  | 366 | absent |
| 7003 | input float | 229 | 64 |  | float: 72 |
| 7006 | input float | 116 | 64 |  | float: 70 |
| 7008 | input enum | 173 |  | 351 | enum: 6 |
| 7009 | input enum | 204 |  | 351 | enum: 6 |
| 7010 | input enum | 46 |  | 351 | enum: 6 |
| 7011 | input enum | 114 |  | 883 | absent |
| 8001 | output enum | 225 |  | 886 | absent |

