"""
KSP1 航天计算机
===============
交互式 CLI 工具，功能：
  1. 输入海拔 → Kerbin 大气稠度（气压、密度）
  2. 输入停车轨道高度 → Kerbin→Mun 霍曼转移（Δv、相位角、转移时间）
  3. 在轨卫星任意圆轨道之间的霍曼转移（Δv、转移时间、交会相位角）
  4. 同轨调相交会：同一轨道上与空间站的角度差缩小（调相轨道 Δv、漂移时间）

KSP1 参考数据:
  - Kerbin μ: 3.5316e12 m³/s², 半径: 600 km
  - 大气标高: 5.6 km, 大气顶: 69.078 km
  - Mun 轨道: 12,000 km (绕 Kerbin)
"""

import math
import sys

# ========== Kerbin 常量 ==========
MU_KERBIN = 3.5316e12          # m³/s²
R_KERBIN = 600_000             # m
ATM_TOP = 69_078               # m
SCALE_HEIGHT = 5_600           # m
P0_KERBIN = 101_325            # Pa
RHO0_KERBIN = 1.225            # kg/m³

# ========== Mun 常量 ==========
R_MUN_ORBIT = 12_000_000       # m
MU_MUN = 6.5138398e10          # m³/s²
R_MUN = 200_000                # m


# ─────────────────────────────────────────────
# 计算函数
# ─────────────────────────────────────────────

def kerbin_pressure(altitude: float) -> float:
    """海拔(米) → 大气压(Pa)"""
    if altitude < 0:
        altitude = 0.0
    if altitude >= ATM_TOP:
        return 0.0
    return P0_KERBIN * math.exp(-altitude / SCALE_HEIGHT)


def kerbin_density(altitude: float) -> float:
    """海拔(米) → 大气密度(kg/m³)"""
    if altitude < 0:
        altitude = 0.0
    if altitude >= ATM_TOP:
        return 0.0
    return RHO0_KERBIN * math.exp(-altitude / SCALE_HEIGHT)


def kerbin_mun_transfer(parking_altitude: float):
    """停车轨道海拔(米) → 霍曼转移参数 dict"""
    r_park = R_KERBIN + parking_altitude
    r_mun = R_MUN_ORBIT

    v_park = math.sqrt(MU_KERBIN / r_park)
    a_trans = (r_park + r_mun) / 2.0
    v_transfer_a = math.sqrt(MU_KERBIN * (2 / r_park - 1 / a_trans))
    v_transfer_b = math.sqrt(MU_KERBIN * (2 / r_mun - 1 / a_trans))
    dv1 = v_transfer_a - v_park

    v_mun_orbit = math.sqrt(MU_KERBIN / r_mun)
    dv2 = v_mun_orbit - v_transfer_b
    dv_total = dv1 + dv2

    transfer_time_s = math.pi * math.sqrt(a_trans**3 / MU_KERBIN)
    omega_mun = math.sqrt(MU_KERBIN / r_mun**3)
    theta_mun = omega_mun * transfer_time_s
    phase_angle_deg = math.degrees(math.pi - theta_mun)
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
        "phase_angle_deg": phase_angle_deg,
        "v_mun": v_mun_orbit,
    }


def kerbin_orbit_transfer(start_altitude: float, target_altitude: float):
    """任意两个 Kerbin 圆轨道之间的霍曼转移
    参数均为海拔(米)，返回 dict 包含 Δv、转移时间等。
    """
    r1 = R_KERBIN + start_altitude
    r2 = R_KERBIN + target_altitude

    # 两圆轨道速度
    v1 = math.sqrt(MU_KERBIN / r1)
    v2 = math.sqrt(MU_KERBIN / r2)

    # 转移轨道半长轴
    a_trans = (r1 + r2) / 2.0
    v_trans_a = math.sqrt(MU_KERBIN * (2 / r1 - 1 / a_trans))
    v_trans_b = math.sqrt(MU_KERBIN * (2 / r2 - 1 / a_trans))

    # Δv（带符号，负值表示减速/反推）
    dv1 = v_trans_a - v1
    dv2 = v2 - v_trans_b
    dv_total = abs(dv1) + abs(dv2)

    transfer_time_s = math.pi * math.sqrt(a_trans**3 / MU_KERBIN)

    # 轨道周期
    period1 = 2 * math.pi * math.sqrt(r1**3 / MU_KERBIN)
    period2 = 2 * math.pi * math.sqrt(r2**3 / MU_KERBIN)

    # 交会相位角：出发时目标卫星应在的位置（与出发点的夹角）
    # 航天器沿转移轨道飞行 180°，目标在目标轨道上飞行 ω₂ × t_transfer
    # 交会条件：θ₀ + ω₂ × t_transfer = 180° → θ₀ = 180° - ω₂ × t_transfer
    omega_target = math.sqrt(MU_KERBIN / r2**3)
    theta_target = omega_target * transfer_time_s
    phase_angle_deg = math.degrees(math.pi - theta_target)
    if phase_angle_deg < 0:
        phase_angle_deg += 360

    return {
        "r_start": r1,
        "r_target": r2,
        "h_start": start_altitude,
        "h_target": target_altitude,
        "v_start": v1,
        "v_target": v2,
        "v_trans_a": v_trans_a,
        "v_trans_b": v_trans_b,
        "dv1": dv1,
        "dv2": dv2,
        "dv_total": dv_total,
        "transfer_time_s": transfer_time_s,
        "transfer_time_h": transfer_time_s / 3600,
        "transfer_time_min": transfer_time_s / 60,
        "phase_angle_deg": phase_angle_deg,
        "period_start": period1,
        "period_start_min": period1 / 60,
        "period_target": period2,
        "period_target_min": period2 / 60,
        "going_outward": target_altitude > start_altitude,
    }


def kerbin_phasing_orbit(altitude: float, angle_deg: float, station_ahead: bool, num_orbits: int = 1):
    """同轨调相：同一圆轨道上，通过改变轨道高度来缩小与空间站的角度差。

    参数:
        altitude:    当前轨道海拔(米)
        angle_deg:   与空间站的角度差(度)，0~360
        station_ahead: True=空间站在前方需追赶, False=空间站在后方等它追
        num_orbits:  漂移圈数

    返回 dict。
    """
    r = R_KERBIN + altitude
    v = math.sqrt(MU_KERBIN / r)
    T = 2 * math.pi * math.sqrt(r**3 / MU_KERBIN)
    delta_theta = math.radians(angle_deg)

    if station_ahead:
        # 降低轨道 → 周期变短 → 追上空间站
        # 每漂移一圈相对角位移: 2π(1 - T_phase/T)
        # N 圈后: 2πN(1 - T_phase/T) = Δθ
        ratio = (1 - delta_theta / (2 * math.pi * num_orbits)) ** (2.0 / 3.0)
        r_phase = r * ratio
        v_phase = math.sqrt(MU_KERBIN / r_phase)
        dv1 = v_phase - v          # 减速(反推)入调相轨道
        dv2 = v - v_phase          # 加速回到原轨道
        direction = "降低轨道追赶"
    else:
        # 抬升轨道 → 周期变长 → 空间站追上
        ratio = (1 + delta_theta / (2 * math.pi * num_orbits)) ** (2.0 / 3.0)
        r_phase = r * ratio
        v_phase = math.sqrt(MU_KERBIN / r_phase)
        dv1 = v_phase - v          # 加速入调相轨道
        dv2 = v - v_phase          # 减速回到原轨道
        direction = "抬升轨道等待"

    T_phase = 2 * math.pi * math.sqrt(r_phase**3 / MU_KERBIN)
    drift_time_s = num_orbits * T_phase
    h_phase = r_phase - R_KERBIN

    return {
        "h_orig": altitude,
        "h_phase": h_phase,
        "v_orig": v,
        "v_phase": v_phase,
        "dv1": dv1,
        "dv2": dv2,
        "dv_total": abs(dv1) + abs(dv2),
        "drift_orbits": num_orbits,
        "drift_time_s": drift_time_s,
        "drift_time_min": drift_time_s / 60,
        "drift_time_h": drift_time_s / 3600,
        "T_orig_min": T / 60,
        "T_phase_min": T_phase / 60,
        "angle_deg": angle_deg,
        "station_ahead": station_ahead,
        "direction": direction,
        "below_atmo": h_phase < ATM_TOP,
    }


# ─────────────────────────────────────────────
# 交互界面函数
# ─────────────────────────────────────────────

def input_float(prompt: str, default: float = None) -> float:
    """带默认值的数字输入，单位统一为 km 输入，返回米。"""
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
    print("\n" + "=" * 50)
    print("  Kerbin 大气稠度计算")
    print("=" * 50)
    km = input_float("  输入海拔 (km) [例如 10]: ")
    h = km * 1000.0

    P = kerbin_pressure(h)
    rho = kerbin_density(h)
    ratio = (rho / RHO0_KERBIN * 100) if rho > 0 else 0.0

    print(f"\n  海拔:         {km:.3f} km")
    if P <= 0:
        print("  结果:         已超出大气层 (atm_top = 69.078 km)")
        print("  气压:         0 Pa")
        print("  密度:         0 kg/m³")
    else:
        print(f"  大气压:       {P:.2f} Pa")
        print(f"  大气密度:     {rho:.6e} kg/m³")
        print(f"  相对海平面:   {ratio:.2f}%")


def calc_transfer():
    """霍曼转移计算交互"""
    print("\n" + "=" * 50)
    print("  Kerbin → Mun  霍曼转移")
    print("=" * 50)
    km = input_float("  输入停车轨道海拔 (km) [默认 80]: ", 80.0)
    h = km * 1000.0

    r = kerbin_mun_transfer(h)

    print(f"\n  停车轨道:     {km:.1f} km (r = {r['r_park']/1000:.1f} km)")
    print(f"  轨道速度:     {r['v_park']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  Δv₁ 加速:     {r['dv1']:.2f} m/s   (进入转移轨道)")
    print(f"  Δv₂ 捕获:     {r['dv2']:.2f} m/s   (Mun 轨道注入)")
    print(f"  总 Δv:        {r['dv_total']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  转移时间:     {r['transfer_time_s']:.0f} s")
    print(f"                ≈ {r['transfer_time_h']:.2f} h")
    print(f"  ─────────────────────────────")
    print(f"  发射相位角:   {r['phase_angle_deg']:.2f}°")
    print(f"                (Mun 应超前航天器的角度)")


def calc_orbit_transfer():
    """任意轨道转移计算交互"""
    print("\n" + "=" * 50)
    print("  Kerbin 在轨卫星 — 任意轨道转移")
    print("=" * 50)
    print("  说明: 计算两颗圆轨道之间的霍曼转移参数。")
    print()
    s_km = input_float("  起始轨道海拔 (km) [默认 80]: ", 80.0)
    t_km = input_float("  目标轨道海拔 (km) [默认 200]: ", 200.0)

    h_start = s_km * 1000.0
    h_target = t_km * 1000.0

    if abs(h_start - h_target) < 1:
        print("\n  起始与目标轨道相同，无需转移。")
        return

    r = kerbin_orbit_transfer(h_start, h_target)
    outward = r["going_outward"]
    direction = "升轨 ↑" if outward else "降轨 ↓"

    dv1_label = "加速 (推进)" if outward else "减速 (反推)"
    dv2_label = "加速 (推进)" if not outward else "减速 (反推)"

    print(f"\n  起始轨道:     {s_km:.1f} km (r = {r['r_start']/1000:.1f} km)")
    print(f"  目标轨道:     {t_km:.1f} km (r = {r['r_target']/1000:.1f} km)")
    print(f"  转移方向:     {direction}")
    print(f"  ─────────────────────────────")
    print(f"  起始轨道速度: {r['v_start']:.2f} m/s")
    print(f"  目标轨道速度: {r['v_target']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  Δv1 {dv1_label}: {abs(r['dv1']):.2f} m/s   (进入转移轨道)")
    print(f"  Δv2 {dv2_label}: {abs(r['dv2']):.2f} m/s   (目标轨道注入)")
    print(f"  总 Δv:        {r['dv_total']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  转移时间:     {r['transfer_time_s']:.0f} s")
    print(f"                ≈ {r['transfer_time_min']:.1f} min")
    print(f"                ≈ {r['transfer_time_h']:.3f} h")
    print(f"  ─────────────────────────────")
    print(f"  起始轨道周期: {r['period_start_min']:.2f} min")
    print(f"  目标轨道周期: {r['period_target_min']:.2f} min")
    print(f"  ─────────────────────────────")
    print(f"  转移转角:     180° (霍曼转移半椭圆)")
    print(f"  交会相位角:   {r['phase_angle_deg']:.2f}°")
    if outward:
        print(f"                (出发时目标卫星应超前航天器 {r['phase_angle_deg']:.1f}°)")
    else:
        behind = 360 - r['phase_angle_deg']
        print(f"                (出发时目标卫星应落后航天器 {behind:.1f}°)")
    print()
    print("  [提示] 在 KSP 地图视角观察目标的角度位置，")
    print("        当相位角等于上述数值时执行变轨即可交会。")


def calc_phasing():
    """同轨调相计算交互"""
    print("\n" + "=" * 50)
    print("  Kerbin 同轨调相交会")
    print("=" * 50)
    print("  说明: 与空间站同在一个圆轨道时，通过")
    print("  改变轨道高度产生周期差来缩小间距。")
    print()
    km = input_float("  当前轨道海拔 (km) [默认 200]: ", 200.0)
    angle = input_float("  空间站的角度差 (度) [默认 45]: ", 45.0)

    if angle < 0:
        angle = -angle
        ahead = False
    else:
        ahead = True

    # 把角度归一化到 0~360
    angle = angle % 360
    if angle == 0:
        print("\n  角度差为 0，已在同一位置。")
        return

    print()
    print("  空间站位置: ", end="")
    if angle <= 180:
        print(f"航天器前方 {angle:.1f}°")
        ahead = True
        close_angle = angle
    else:
        behind = 360 - angle
        print(f"航天器后方 {behind:.1f}°")
        ahead = False
        close_angle = behind

    n_str = input("  调相圈数 (默认自动推荐): ").strip()
    if n_str:
        try:
            n = max(1, int(n_str))
        except ValueError:
            n = None
    else:
        n = None

    h = km * 1000.0
    r_orig = R_KERBIN + h

    # 尝试 1~50 圈，找推荐方案
    if n is not None:
        trials = [n]
    else:
        trials = list(range(1, 51))

    best = None
    for orb in trials:
        rr = kerbin_phasing_orbit(h, close_angle, ahead, orb)
        if not rr["below_atmo"]:
            # 自动模式：选圈数最少（最快）的方案
            if n is None and (best is None or orb < best["drift_orbits"]):
                best = rr
            elif n is not None:
                best = rr
                break

    if best is None:
        best = kerbin_phasing_orbit(h, close_angle, ahead, max(trials))

    print(f"\n  调相策略:   {best['direction']}")
    print(f"  原轨道:     {km:.1f} km (r = {r_orig/1000:.1f} km)")
    print(f"  调相轨道:   {best['h_phase']/1000:.1f} km (r = {best['h_phase']/1000 + 600:.1f} km)")
    if best["below_atmo"]:
        print(f"  ⚠ 警告: 调相轨道低于大气层顶 ({ATM_TOP/1000:.3f} km)!")
        rec = False
        for orb in range(1, 101):
            rr = kerbin_phasing_orbit(h, close_angle, ahead, orb)
            if not rr["below_atmo"]:
                rec_km = (rr["h_phase"] - R_KERBIN) / 1000
                print(f"  建议增至 {orb} 圈可避免进入大气。")
                rec = True
                break
        if not rec:
            print("  无法避免进入大气，请选择更高的起始轨道。")
    print(f"  ─────────────────────────────")
    print(f"  Δv1: {abs(best['dv1']):.2f} m/s   (进入调相轨道)")
    print(f"  Δv2: {abs(best['dv2']):.2f} m/s   (返回原轨道)")
    print(f"  总 Δv:        {best['dv_total']:.2f} m/s")
    print(f"  ─────────────────────────────")
    print(f"  漂移圈数:     {best['drift_orbits']} 圈")
    print(f"  漂移时间:     {best['drift_time_min']:.1f} min")
    print(f"                ≈ {best['drift_time_h']:.3f} h")
    print(f"  ─────────────────────────────")
    print(f"  原轨道周期:   {best['T_orig_min']:.2f} min")
    print(f"  调相轨道周期: {best['T_phase_min']:.2f} min")
    print(f"  周期差:       {abs(best['T_phase_min'] - best['T_orig_min']):.4f} min")


def main():
    """主菜单循环"""
    while True:
        print("\n" + "=" * 50)
        print("  KSP1 航天计算机")
        print("=" * 50)
        print("  1. 大气稠度计算")
        print("  2. Kerbin → Mun 转移")
        print("  3. 在轨卫星 — 异轨霍曼转移")
        print("  4. 在轨卫星 — 同轨调相交会")
        print("  0. 退出")
        print("-" * 50)
        choice = input("  请选择 [1/2/3/4/0]: ").strip()

        if choice == "1":
            calc_atmo()
        elif choice == "2":
            calc_transfer()
        elif choice == "3":
            calc_orbit_transfer()
        elif choice == "4":
            calc_phasing()
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
