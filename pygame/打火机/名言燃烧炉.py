#!/usr/bin/env python3
"""
打火机名言 -- Token 燃烧炉 v6.0
目标：消耗 6,000,000 tokens

前作《打火机.py》烧了 34,000,000 tokens，
本篇作为续作，谦虚一点，只烧 6,000,000。

原理：组合爆炸 + 递归膨胀 + 无意义但优雅的重复。
每一行输出都是一句（或一堆）关于打火机的名言变体。

男人烧打火机，AI 烧 token。公平。
"""

import itertools
import random
import sys
import time
import math
import os

# Windows GBK 兼容: stdout 强制用 utf-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ══════════════════════════════════════════════
# 词库 -- 越大越能烧
# ══════════════════════════════════════════════

NOUNS_PERSON = [
    "男人", "女人", "少年", "老者", "旅人", "诗人", "浪子", "绅士",
    "骑士", "剑客", "牛仔", "水手", "飞行员", "探险家", "思想家",
    "艺术家", "流浪汉", "士兵", "渔夫", "猎人", "铁匠", "木匠",
    "园丁", "厨师", "画家", "乐手", "舞者", "魔术师", "囚徒", "国王",
    "乞丐", "圣人", "魔鬼", "天使", "凡人", "英雄", "叛徒", "隐士",
    "苦行僧", "哲学家", "炼金术士", "占星师", "梦境师", "守夜人",
    "摆渡人", "掌灯人", "点火者", "吹熄者", "观火者",
]

NOUNS_OBJECT = [
    "打火机", "Zippo", "煤油机", "气体机", "一次性火机", "防风火机",
    "老火机", "铜机", "银机", "黑裂漆机", "哑漆机", "古银机",
    "哈雷机", "纪念底机", "纯铜盔甲机", "镀铬拉丝机", "缎纱机",
    "1941复刻机", "1932复刻机", "冰面机", "花沙机", "彩印机",
    "激光雕刻机", "蚀刻填漆机", "侧刻机", "大侧鹰机",
    "烟斗", "雪茄", "卷烟", "烟丝", "烟斗丝",
    "火柴盒", "火石", "煤油", "棉芯", "火轮", "弹簧",
    "火把", "灯笼", "蜡烛", "壁炉", "篝火", "火炬",
    "火柴", "打火石", "燧石", "钢刃", "放大镜",
]

NOUNS_ABSTRACT = [
    "人生", "命运", "爱情", "梦想", "希望", "孤独", "自由", "信仰",
    "时间", "记忆", "青春", "岁月", "伤痕", "荣耀", "沉默", "声音",
    "光明", "黑暗", "温度", "寒冷", "风", "雨", "雪", "雾",
    "烟", "灰烬", "火焰", "光", "影子", "回声", "余烬",
    "远方", "故乡", "路", "归途", "起点", "终点", "彼岸",
    "灵魂", "欲望", "恐惧", "勇气", "温柔", "暴烈", "平静",
]

ADJECTIVES = [
    "温暖", "冰冷", "明亮", "昏暗", "炽热", "温和", "暴烈", "安静",
    "漫长", "短暂", "永恒", "瞬间", "古老", "崭新", "破旧", "完美",
    "粗糙", "精致", "沉重", "轻盈", "坚硬", "柔软", "锋利", "圆润",
    "危险", "安全", "野性", "驯服", "自由", "禁锢", "纯洁", "污浊",
    "明亮", "模糊", "清晰", "朦胧", "直接", "曲折", "简单", "复杂",
    "廉价", "昂贵", "普通", "特别", "虚假", "真实", "肤浅", "深刻",
    "锋利", "迟钝", "干燥", "湿润", "饥饿", "饱足", "清醒", "沉醉",
    "孤独", "热闹", "寂静", "喧嚣", "愤怒", "温柔", "绝望", "希望",
    "疲惫", "精力充沛", "老旧", "时髦", "笨拙", "灵巧",
    "华丽", "朴素", "张扬", "内敛", "疏离", "亲密",
]

VERBS_ACTION = [
    "点燃", "熄灭", "把玩", "抚摸", "凝视", "倾听", "等待", "追寻",
    "守护", "放弃", "拥抱", "推开", "创造", "毁灭", "记住", "遗忘",
    "出发", "归来", "沉默", "诉说", "燃烧", "熄灭", "升起", "坠落",
    "打开", "合上", "转动", "按下", "摩擦", "碰撞", "摇晃", "静止",
    "呼吸", "屏息", "颤抖", "坚定", "徘徊", "前行", "回头",
    "生火", "取暖", "照明", "信号", "献祭", "供奉", "仪式",
    "淬炼", "锻造", "熔铸", "打磨", "雕刻", "烙印", "封存",
]

ADVERBS = [
    "轻轻地", "重重地", "慢慢地", "飞快地", "安静地", "喧嚣地",
    "温柔地", "粗暴地", "坚定地", "犹豫地", "自由地", "禁锢地",
    "孤独地", "热闹地", "沉默地", "大声地", "优雅地", "笨拙地",
    "漫不经心地", "郑重其事地", "无可奈仍地", "义无反顾地",
    "小心翼翼地", "肆无忌惮地", "心不在焉地", "全神贯注地",
    "似懂非懂地", "恍然大悟地", "漫无目的地", "一往无前地",
    "不自觉地", "下意识地", "本能地", "刻意地", "随性地",
]

PREPOSITIONS = [
    "在", "于", "从", "向", "沿着", "穿过", "越过", "抵达",
    "远离", "靠近", "围绕", "进入", "离开", "经过", "通往",
]

CONJUNCTIONS = [
    "如同", "仿佛", "像是", "正如", "恰如", "好比", "犹如",
    "宛若", "好似", "堪比", "不输于", "胜似", "不如",
]

SEASONS = [
    "春天", "夏天", "秋天", "冬天",
    "清晨", "午后", "黄昏", "深夜",
    "雨天", "雪天", "雾天", "晴天",
    "黎明", "傍晚", "午夜", "拂晓",
    "春日", "夏夜", "秋晨", "冬暮",
]

# 将所有词库按类型分组建表
ALL_BANKS = {
    "p": NOUNS_PERSON,
    "o": NOUNS_OBJECT,
    "n": NOUNS_ABSTRACT,
    "adj": ADJECTIVES,
    "v": VERBS_ACTION,
    "adv": ADVERBS,
    "prep": PREPOSITIONS,
    "conj": CONJUNCTIONS,
    "season": SEASONS,
}

# ══════════════════════════════════════════════
# 模板 -- 组合爆炸的核心
# ══════════════════════════════════════════════

TEMPLATES_SINGLE = [
    "{p}玩{o}，就像{p}玩{n}一样，是一种{adj}的{v}。",
    "每一个{o}里都住着一团{adj}的{n}，等待着被{v}。",
    "{o}是{p}的{n}。",
    "{adj}的{o}，也许能{v}一支{n}，却{v}不了{n}的路。",
    "{o}虽小，却能{v}{adj}的{n}。",
    "{p}与{o}，就像是{n}与{n}，{adv}{v}着彼此。",
    "{o}在{p}手中{adv}{v}，发出{adj}的{n}。",
    "一个{adj}的{o}，比任何{n}都{adj}。",
    "每一次{v}{o}，都是一次{adj}的{n}。",
    "{o}是{adj}的{n}，它让{n}变得{adj}而{adj}。",
    "当你需要{n}的时候，一个{o}比任何{p}都{adj}。",
    "{n}就像{o}，不{v}永远不知道能{v}多久。",
    "{o}的{n}虽然{adj}，却足以{v}{adj}的{n}。",
    "拥有一个{o}，你就拥有了一个可以{adv}{v}的{n}。",
    "{o}——把{n}{v}在手中的人。",
    "{o}在{v}中{v}的声音，是{p}为数不多的{n}。",
    "一个{o}陪了你十年，它就不再是{n}，是{n}。",
    "有些人用{o}{v}{n}，有些人用{o}{v}{n}。",
    "{o}是最{adj}的{n}——你总在手里{adv}{v}。",
    "别小看一个{o}，它掌管着{n}最{adj}的{n}。",
    "送一个{o}给{p}，意思是：我这儿永远有{adj}的{n}。",
    "每一次{v}上盖子的声音，都是一次{adj}的{n}。",
    "{o}在{p}的口袋里{adv}{v}，等待着{adj}的{n}。",
    "{adj}的{n}从{o}中升起，{v}了整片{adj}的天空。",
    "{p}的{o}里，装着{adj}的{n}和{adj}的{n}。",
    "那是一个{adj}的{season}，{p}{adv}{v}着他的{o}。",
    "{o}的火焰{adv}{v}着，像是{n}在{adv}{v}。",
    "{p}把{o}{v}在{n}上，{n}开始{adv}{v}。",
    "{o}见证了{p}所有的{n}——{n}、{n}和{n}。",
    "当{o}的{n}耗尽了，{p}才{adv}{v}到{n}的{adj}。",
    "{n}。{o}。{n}。{adj}的{n}在{adv}{v}。",
    "{p}说：给我一个{o}，我可以{v}整个{n}。",
    "{o}不是用来{v}{n}的，是用来{v}{n}的。",
    "在{adj}的{n}里，{o}是唯一{adj}的{n}。",
    "如果{n}是{o}，那{n}就是{n}，{adj}地{v}着。",
    "——你的{o}{adv}{v}着，{adj}。\n——因为我的{n}还在{adv}{v}。",
    "——借个{o}。\n——{n}可以借，{n}要自己找。",
    "——为什么总{v}着那个{o}？\n——因为{n}太{adj}了。",
    "{adv}{v}一盏{o}，{v}{adj}的{n}。",
    "{o}不明，{n}不灭，{p}在{n}外{adv}{v}。",
    "一壶{n}，一个{o}，{adj}的{n}里{adv}{v}。",
    "{o}映{n}，{n}照{p}，{adj}的{n}在{adv}{v}。",
    "此{o}可待成{n}，只是当时已{adj}。",
]

TEMPLATES_CHAIN = [
    "{p}{adv}{v}着{o}，{n}在{adj}中{adv}{v}。",
    "{o}说：{n}。{n}说：{n}。{p}什么也没说。",
    "第一个{o}用来{v}{n}，第二个用来{v}{n}，第三个用来{v}{n}。",
    "{o}、{n}和{n}，是{p}最{adj}的三样{n}。",
    "从{adj}的{n}到{adj}的{n}，中间只隔着一个{o}的距离。",
]

TEMPLATES_STORY = [
    "从前有一个{adj}的{p}，他有一个{adj}的{o}。\n"
    "他每天{adv}{v}着它，{n}也{adv}{v}着他。\n"
    "直到有一天，{o}说：{n}。\n"
    "{p}{adv}{v}了，{v}起{o}，{adv}走向{adj}的{n}。",

    "{p}问{o}：你{adj}吗？\n"
    "{o}回答：我{adj}，因为我的{n}在{adv}{v}。\n"
    "{p}{adv}{v}了{o}，{n}从此{adv}{v}。",

    "在{adj}的{n}里，有一个{adj}的{o}。\n"
    "它{adv}躺在{n}上，{n}满了{adj}的{n}。\n"
    "{p}把它{adv}{v}起来，{v}了{v}。\n"
    "{n}{adv}{v}，{n}{adv}{v}，{n}也{adv}{v}。",
]

TEMPLATES_POEM = [
    "{o}\n"
    "{adv}{v}，{adv}{v}\n"
    "{adj}的{n}，{adj}的{n}\n"
    "在{n}中{adv}{v}\n"
    "{n}",

    "《{n}》\n"
    "{p}啊{p}\n"
    "你的{o}{adj}地{v}着\n"
    "像{adj}的{n}在{adv}{v}\n"
    "又像{n}在{adv}{v}\n"
    "{adj}啊{adj}",
]

# 合并所有模板用于地狱火模式
ALL_TEMPLATES = (
    TEMPLATES_SINGLE * 3 +
    TEMPLATES_CHAIN * 2 +
    TEMPLATES_STORY * 1 +
    TEMPLATES_POEM * 1
)


def fill(template, banks):
    """填充模板中的占位符"""
    result = template
    while True:
        remaining = [k for k in ("p", "o", "n", "adj", "v", "adv", "season")
                     if "{" + k + "}" in result]
        if not remaining:
            break
        key = random.choice(remaining)
        words = banks.get(key, ["???"])
        word = random.choice(words)
        result = result.replace("{" + key + "}", word, 1)
    return result


# ══════════════════════════════════════════════
# Token 燃烧炉
# ══════════════════════════════════════════════

class TokenFurnace:
    """Token 燃烧炉——核心引擎"""

    CHARS_PER_TOKEN = 1.8

    def __init__(self, target_tokens=6_000_000):
        self.target_tokens = target_tokens
        self.target_chars = int(target_tokens * self.CHARS_PER_TOKEN)
        self.total_chars = 0
        self.total_lines = 0
        self.start_time = time.time()
        self.last_report = 0
        self.banks = ALL_BANKS
        self.templates = ALL_TEMPLATES

    def progress_pct(self):
        return min(100, self.total_chars / self.target_chars * 100)

    def elapsed(self):
        return time.time() - self.start_time

    def speed(self):
        e = self.elapsed()
        return self.total_chars / e if e > 0 else 0

    def eta(self):
        s = self.speed()
        if s <= 0:
            return float("inf")
        return (self.target_chars - self.total_chars) / s

    def tokens_burned(self):
        return int(self.total_chars / self.CHARS_PER_TOKEN)

    # 四种生成模式

    def gen_single(self):
        """文火：一句一句地烧"""
        tpl = random.choice(TEMPLATES_SINGLE)
        return "  「" + fill(tpl, self.banks) + "」\n"

    def gen_chain(self):
        """中火：三句连锁"""
        tpl = random.choice(TEMPLATES_CHAIN)
        return "  " + fill(tpl, self.banks) + "\n"

    def gen_story(self):
        """大火：微型故事"""
        tpl = random.choice(TEMPLATES_STORY)
        lines = fill(tpl, self.banks)
        formatted = "\n".join("    " + l for l in lines.split("\n") if l.strip())
        return "  [故事]\n" + formatted + "\n\n"

    def gen_poem(self):
        """烈火：现代诗"""
        tpl = random.choice(TEMPLATES_POEM)
        poem = fill(tpl, self.banks)
        formatted = "\n".join("    " + l for l in poem.split("\n") if l.strip())
        return "  [诗]\n" + formatted + "\n\n"

    def gen_maximus(self):
        """地狱火：一次性生成大量变体"""
        batch_size = random.randint(10, 30)
        lines = []
        for _ in range(batch_size):
            tpl = random.choice(self.templates)
            lines.append("    " + fill(tpl, self.banks))
        return "  [MAXIMUS BURN]\n" + "\n".join(lines) + "\n\n"

    def generate(self):
        """主循环——一直烧到目标"""
        generators = [
            (self.gen_single, 30),
            (self.gen_chain, 20),
            (self.gen_story, 10),
            (self.gen_poem, 10),
            (self.gen_maximus, 30),
        ]
        gen_list = [g for g, w in generators for _ in range(w)]

        while self.total_chars < self.target_chars:
            gen = random.choice(gen_list)
            output = gen()
            self.total_chars += len(output)
            self.total_lines += output.count("\n")

            sys.stdout.write(output)
            sys.stdout.flush()

            progress = self.progress_pct()
            if progress - self.last_report >= 2 or progress >= 100:
                self.last_report = int(progress // 2) * 2
                self.report(progress)

        self.report(100, final=True)

    def report(self, progress, final=False):
        pct = "{:.1f}%".format(progress)
        token_s = "{:,}".format(self.tokens_burned())
        lines_s = "{:,}".format(self.total_lines)
        speed_s = "{:.0f}".format(self.speed() / self.CHARS_PER_TOKEN)
        eta_s = "{:.0f}s".format(self.eta()) if self.eta() < float("inf") else "INF"

        report = (
            "\n+-----" + "-" * 55 + "+\n"
            "| BURN: " + pct.rjust(7) + "\n"
            "| TOKEN: " + token_s.rjust(13) + " / " + str(self.target_tokens) + "\n"
            "| LINES: " + lines_s.rjust(11) + "\n"
            "| SPEED: " + speed_s.rjust(9) + " tok/s\n"
            "| TIME: " + "{:.0f}".format(self.elapsed()).rjust(4) + "s  ETA: " + eta_s.rjust(6) + "\n"
            "+-----" + "-" * 55 + "+\n"
        )
        # 用 stderr 输出进度，不影响 stdout 的名言流
        sys.stderr.write("\r\033[K" + report)
        sys.stderr.flush()


def main():
    target = 6_000_000
    separator = "=" * 70

    print()
    print(separator)
    print("  打火机名言 . Token 燃烧炉 v6.0")
    print(separator)
    print()
    print("  目标: {:,} tokens (约 {:,} 万字符)".format(target, int(target * 1.8 / 10000)))
    print("  前作《打火机.py》会话消耗: 34,000,000 tokens")
    print("  本作谦虚一些, 只烧 6,000,000.")
    print("  理论名言产量: 约 100,000 ~ 200,000 句")
    print()
    print("  原理: 组合爆炸 + 递归膨胀 + 无意义但优雅的重复")
    print("  每一行输出都是一句关于打火机的名言变体。")
    print("  男人烧打火机, AI 烧 token。公平。")
    print()
    print(separator)
    print("  燃烧开始...")
    print(separator)
    print()

    furnace = TokenFurnace(target_tokens=target)
    furnace.generate()

    elapsed = furnace.elapsed()
    print()
    print(separator)
    print("  [完成] 燃烧结束!")
    print("  [统计]")
    print("    目标: {:,} tokens".format(target))
    print("    实际: {:,} tokens ({:,} 字符)".format(furnace.tokens_burned(), furnace.total_chars))
    print("    名言: {:,} 行".format(furnace.total_lines))
    print("    用时: {:.1f} 秒".format(elapsed))
    print("    速率: {:.0f} token/s".format(furnace.tokens_burned() / elapsed))
    print(separator)
    print()
    print("  前作《打火机.py》: 34,000,000 tokens")
    print("  本作《名言燃烧炉》: 6,000,000+ tokens")
    print("  合计: 40,000,000+ tokens  完美闭环")
    print()


if __name__ == "__main__":
    main()
