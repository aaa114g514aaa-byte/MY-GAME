"""
地球航天计算机
===============
交互式 CLI 工具，功能：
  1. 输入海拔 → 地球大气稠度（气压、密度、温度）
  2. 输入停车轨道高度 → 地球→月球 霍曼转移（Δv、相位角、转移时间）

大气模型: 1976 U.S. Standard Atmosphere (简化版, 0 ~ 84.852 km)
"""

import math
import sys

# ========== 地球常量 ==========
MU_EARTH = 3.986004418e14      # m³/s²
R_EARTH = 6_371_000            # m
G0_EARTH = 9.80665             # m/s²
R_SPECIFIC = 287.058           # J/(kg·K)

# 海平面标准条件
T0 = 288.15                    # K
P0 = 101_325                   # Pa
RHO0 = 1.225                   # kg/m³

# 大气分层 (km): (base_alt, base_temp_K, lapse_rate_K/km)
LAYERS = [
    ( 0.000, 288.15, -6.5),
    (11.000, 216.65,  0.0),
    (20.000, 216.65,  1.0),
    (32.000, 228.65,  2.8),
    (47.000, 270.65,  0.0),
    (51.000, 270.65, -2.8),
    (71.000, 214.65, -2.0),
    (84.852, 186.95,  0.0),
]

# ========== 月球常量 ==========
MOON_ORBIT_R = 384_400_000      # m
MU_MOON = 4.902800e12           # m³/s²
R_MOON = 1_737_400              # m


# ─────────────────────────────────────────────
# 计算函数
# ─────────────────────────────────────────────

def earth_temperature(altitude: float) -> float:
    """海拔(米) → 温度(K)"""
    alt_km = altitude / 1000.0
    if altitude < 0:
        alt_km = 0.0
    if alt_km >= 84.852:
        return 0.0
    for i in range(len(LAYERS)):
        h_base, T_base, lapse = LAYERS[i]
        h_next = LAYERS[i + 1][0] if i + 1 < len(LAYERS) else alt_km
        if alt_km <= h_next:
            return T_base + lapse * (alt_km - h_base)
    return 0.0


def earth_pressure(altitude: float) -> float:
    """海拔(米) → 大气压(Pa), 0 ~ 84.852 km"""
    alt_km = altitude / 1000.0
    if altitude < 0:
        alt_km = 0.0
    if alt_km >= 84.852:
        return 0.0

    P_prev = P0
    for i in range(len(LAYERS)):
        h_base, T_base, lapse = LAYERS[i]
        h_next = LAYERS[i + 1][0] if i + 1 < len(LAYERS) else alt_km
        lapse_per_m = lapse / 1000.0

        if alt_km <= h_next:
            dh_m = (alt_km - h_base) * 1000.0
            if abs(lapse) < 1e-9:
                return P_prev * math.exp(-G0_EARTH * dh_m / (R_SPECIFIC * T_base))
            T_h = T_base + lapse * (alt_km - h_base)
            exponent = -G0_EARTH / (R_SPECIFIC * lapse_per_m)
            return P_prev * (T_h / T_base) ** exponent
        else:
            dh_m = (h_next - h_base) * 1000.0
            if abs(lapse) < 1e-9:
                P_prev = P_prev * math.exp(-G0_EARTH * dh_m / (R_SPECIFIC * T_base))
            else:
                T_next = T_base + lapse * (h_next - h_base)
                exponent = -G0_EARTH / (R_SPECIFIC * lapse_per_m)
                P_prev = P_prev * (T_next / T_base) ** exponent
    return 0.0


def earth_density(altitude: float) -> float:
    """海拔(米) → 大气密度(kg/m³)"""
    P = earth_pressure(altitude)
    if P <= 0:
        return 0.0
    T = earth_temperature(altitude)
    if T <= 0:
        return 0.0
    return P / (R_SPECIFIC * T)


def earth_moon_transfer(parking_altitude: float):
    """停车轨道海拔(米) → 地球→月球 霍曼转移参数 dict"""
    r_park = R_EARTH + parking_altitude
    r_moon = MOON_ORBIT_R

    v_park = math.sqrt(MU_EARTH / r_park)
    a_trans = (r_park + r_moon) / 2.0
    v_transfer_a = math.sqrt(MU_EARTH * (2 / r_park - 1 / a_trans))
    v_transfer_b = math.sqrt(MU_EARTH * (2 / r_moon - 1 / a_trans))
    dv1 = v_transfer_a - v_park

    v_moon_orbit = math.sqrt(MU_EARTH / r_moon)
    dv2 = v_moon_orbit - v_transfer_b
    dv_total = dv1 + dv2

    transfer_time_s = math.pi * math.sqrt(a_trans**3 / MU_EARTH)
    omega_moon = math.sqrt(MU_EARTH / r_moon**3)
    theta_moon = omega_moon * transfer_time_s
    phase_angle_deg = math.degrees(math.pi - theta_moon)
    if phase_angle_deg < 0:
        phase_angle_deg += 360

    return {
        "r_park": r_park,
        "v_park": v_park,
        "v_transfer_a": v_transfer_a,
        "v_transfer_b": v_transfer_b,
        "dv1": dv1,
        "dv2": dv2,
        "dv_total": dv_total,
        "transfer_time_s": transfer_time_s,
        "transfer_time_h": transfer_time_s / 3600,
        "transfer_time_d": transfer_time_s / 86400,
        "phase_angle_deg": phase_angle_deg,
        "v_moon": v_moon_orbit,
    }


# ─────────────────────────────────────────────
# 交互界面函数
# ─────────────────────────────────────────────

def input_float(prompt: str, default: float = None) -> float:
    """带默认值的数字输入。"""
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            return float(raw)
        except ValueError:
            print("  输入无效，请输入数字。")


def calc_atmo():
    """大气稠度计算交互"""
    print("\n" + "=" * 55)
    print("  地球大气稠度计算 (1976 标准大气)")
    print("=" * 55)
    km = input_float("  输入海拔 (km) [例如 10]: ")
    h = km * 1000.0

    T = earth_temperature(h)
    P = earth_pressure(h)
    rho = earth_density(h)
    ratio = (rho / RHO0 * 100) if rho > 0 else 0.0

    print(f"\n  海拔:         {km:.3f} km")
    if P <= 0:
        print("  结果:         已超出模型范围 (>84.852 km)")
        print("  温度:         N/A")
        print("  气压:         0 Pa")
        print("  密度:         0 kg/m³")
    else:
        print(f"  温度:         {T:.2f} K ({T - 273.15:.1f}°C)")
        print(f"  大气压:       {P:.2f} Pa")
        print(f"  大气密度:     {rho:.6e} kg/m³")
        print(f"  相对海平面:   {ratio:.2f}%")


def calc_transfer():
    """霍曼转移计算交互"""
    print("\n" + "=" * 55)
    print("  地球 → 月球  霍曼转移")
    print("=" * 55)
    km = input_float("  输入停车轨道海拔 (km) [默认 200]: ", 200.0)
    h = km * 1000.0

    r = earth_moon_transfer(h)

    print(f"\n  停车轨道:     {km:.1f} km (r = {r['r_park']/1000:.1f} km)")
    print(f"  轨道速度:     {r['v_park']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  Δv₁ 加速:     {r['dv1']:.2f} m/s   (进入转移轨道)")
    print(f"  Δv₂ 捕获:     {r['dv2']:.2f} m/s   (月球轨道注入)")
    print(f"  总 Δv:        {r['dv_total']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  转移时间:     {r['transfer_time_s']:.0f} s")
    print(f"                ≈ {r['transfer_time_h']:.2f} h")
    print(f"                ≈ {r['transfer_time_d']:.2f} d")
    print(f"  ─────────────────────────────")
    print(f"  发射相位角:   {r['phase_angle_deg']:.2f}°")
    print(f"                (月球应超前航天器的角度)")


def main():
    """主菜单循环"""
    while True:
        print("\n" + "=" * 55)
        print("  地球航天计算机")
        print("=" * 55)
        print("  1. 大气稠度计算")
        print("  2. 地球 → 月球 转移")
        print("  0. 退出")
        print("-" * 55)
        choice = input("  请选择 [1/2/0]: ").strip()

        if choice == "1":
            calc_atmo()
        elif choice == "2":
            calc_transfer()
        elif choice == "0":
            print("  再见!")
            break
        else:
            print("  无效选择，请重试。")

        input("\n  按 Enter 继续...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  再见!")
        sys.exit(0)
