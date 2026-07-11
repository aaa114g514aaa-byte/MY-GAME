/**
 * weather.cpp - 命令行天气查询工具
 *
 * 使用 wttr.in 免费 API（无需 API Key）
 * 支持拼音/英文城市名（中文参数需终端支持 UTF-8）
 *
 * 编译:
 *   g++ -o weather weather.cpp -std=c++17
 *
 * 运行:
 *   ./weather beijing
 *   ./weather "New York"
 *   ./weather 北京
 *   ./weather              (默认查询北京)
 *   ./weather -h           (显示帮助)
 *
 * 依赖: Windows 10+ 自带的 curl.exe
 */

#include <iostream>
#include <string>
#include <cstdio>
#include <memory>
#include <array>
#include <regex>
#include <iomanip>
#include <algorithm>
#include <sstream>
#include <clocale>

#ifdef _WIN32
#include <windows.h>
#define POPEN _popen
#define PCLOSE _pclose
#else
#define POPEN popen
#define PCLOSE pclose
#endif

// ============================================================
// 工具函数
// ============================================================

// URL 编码（处理中文等非 ASCII 字符）
static std::string url_encode(const std::string &value) {
    std::ostringstream escaped;
    escaped << std::hex << std::uppercase;
    for (unsigned char c : value) {
        if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            escaped << c;
        } else {
            escaped << '%' << std::setw(2) << static_cast<int>(c);
        }
    }
    return escaped.str();
}

// 去除字符串首尾空白
static std::string trim(const std::string &s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return "";
    size_t end = s.find_last_not_of(" \t\r\n");
    return s.substr(start, end - start + 1);
}

// ============================================================
// HTTP 请求：调用 curl.exe 获取 JSON
// ============================================================

static std::string fetch_json(const std::string &url) {
#ifdef _WIN32
    std::string cmd = "curl.exe -s -m 10 \"" + url + "\" 2>nul";
#else
    std::string cmd = "curl -s -m 10 \"" + url + "\" 2>/dev/null";
#endif

    std::array<char, 4096> buffer;
    std::string result;

    std::unique_ptr<FILE, decltype(&PCLOSE)> pipe(POPEN(cmd.c_str(), "r"), PCLOSE);
    if (!pipe) return "";

    while (fgets(buffer.data(), static_cast<int>(buffer.size()), pipe.get())) {
        result += buffer.data();
    }
    return result;
}

// ============================================================
// JSON 简易提取（不依赖第三方库，只针对已知结构）
// ============================================================

// 从 JSON 中提取指定 key 的字符串值: "key": "value"
// 所有数值在 wttr.in 响应中也带引号，所以统一用这个函数
static std::string json_get_string(const std::string &json, const std::string &key) {
    std::regex pattern("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        return match[1];
    }
    return "";
}

// 从 JSON 中提取指定 key 的整数字符串值
static std::string json_get_int(const std::string &json, const std::string &key) {
    std::string val = json_get_string(json, key);
    // 也支持不带引号的纯数字
    if (val.empty()) {
        std::regex pattern("\"" + key + "\"\\s*:\\s*(\\d+)");
        std::smatch match;
        if (std::regex_search(json, match, pattern)) {
            val = match[1];
        }
    }
    return val;
}

// 提取嵌套 weatherDesc 中的 value（第一个匹配）
static std::string json_get_desc(const std::string &json) {
    std::regex pattern("\"weatherDesc\"\\s*:\\s*\\[\\s*\\{\\s*\"value\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        return match[1];
    }
    return "";
}

// ============================================================
// 天气预报数据解析
// ============================================================

struct DayForecast {
    std::string date;
    std::string max_temp;
    std::string min_temp;
    std::string desc;
};

// Helper: 在 JSON 中找第 N 个 key 的字符串值
static std::string find_nth_value(const std::string &json, const std::string &key, int index) {
    size_t pos = 0;
    for (int i = 0; i <= index; i++) {
        // 找到 "key":  (可能之后有空格)
        std::string search = "\"" + key + "\":";
        size_t found = json.find(search, pos);
        if (found == std::string::npos) return "";
        // 跳过整个 "key": 部分
        pos = found + search.length();
        // 跳过可能的空格
        while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
        // 下一个字符应该是 "
        if (pos >= json.length() || json[pos] != '"') return "";
        pos++; // 跳过 "
    }
    // 读取引号内内容
    size_t end = json.find('"', pos);
    if (end == std::string::npos) return "";
    return json.substr(pos, end - pos);
}

// 从完整的 JSON 中提取第 N 天的预报数据
// day_index: 0=今天, 1=明天, 2=后天
static DayForecast extract_forecast(const std::string &json, int day_index) {
    DayForecast day;
    day.date     = find_nth_value(json, "date", day_index);
    day.max_temp = find_nth_value(json, "maxtempC", day_index);
    day.min_temp = find_nth_value(json, "mintempC", day_index);

    // 对于 description，需要在当天范围内搜索第一个 weatherDesc
    // 先定位到该天的 date 所在位置，然后取到下一个 date 或结尾
    {
        std::string dm = "\"date\":";
        size_t start = 0;
        for (int i = 0; i <= day_index; i++) {
            size_t f = json.find(dm, start);
            if (f == std::string::npos) break;
            start = f + dm.length();
        }
        if (start > 0) {
            // 找到该 date 后面的第一个 weatherDesc
            size_t seg_end = json.find(dm, start);
            if (seg_end == std::string::npos) seg_end = json.length();
            // 从 start-1 到 seg_end
            size_t search_from = (start > 10) ? start - 10 : 0;
            std::string seg = json.substr(search_from, seg_end - search_from);
            day.desc = json_get_desc(seg);
        }
    }

    return day;
}

// ============================================================
// 显示天气信息
// ============================================================

static void display_weather(const std::string &city, const std::string &json) {
    if (json.empty()) {
        std::cerr << "\n  [错误] 无法连接到天气服务，请检查网络连接。\n\n";
        return;
    }

    // 检查是否有 current_condition
    if (json.find("current_condition") == std::string::npos) {
        std::cerr << "\n  [错误] 未找到城市 \"" << city << "\" 的天气信息。\n"
                  << "  请检查城市名是否正确（建议使用拼音或英文名）。\n\n";
        return;
    }

    // --- 解析实时天气 ---
    std::string temp       = json_get_int(json, "temp_C");
    std::string feels      = json_get_int(json, "FeelsLikeC");
    std::string humidity   = json_get_int(json, "humidity");
    std::string wind_speed = json_get_int(json, "windspeedKmph");
    std::string wind_dir   = json_get_string(json, "winddir16Point");
    std::string desc       = json_get_desc(json);
    std::string visibility = json_get_int(json, "visibility");
    std::string uv_index   = json_get_int(json, "uvIndex");

    // --- 解析未来3天预报 ---
    DayForecast days[3];
    for (int i = 0; i < 3; i++) {
        days[i] = extract_forecast(json, i);
    }

    // ============================================================
    // --- 输出 ---
    // ============================================================

    // 标题
    std::cout << "\n";
    std::cout << "  +------------------------------------------+\n";
    std::cout << "  |           实时天气查询                    |\n";
    std::cout << "  +------------------------------------------+\n";
    std::cout << "\n";
    std::cout << "  城市: " << city << "\n";
    if (!desc.empty()) {
        std::cout << "  天气: " << desc << "\n";
    }
    std::cout << "\n";

    // 实时数据
    std::cout << "  --- 实时天气 ---\n";
    if (!temp.empty())       std::cout << "  温度    : " << temp << " C\n";
    if (!feels.empty())      std::cout << "  体感温度: " << feels << " C\n";
    if (!humidity.empty())   std::cout << "  湿度    : " << humidity << "%\n";
    if (!wind_speed.empty()) std::cout << "  风速    : " << wind_speed << " km/h " << wind_dir << "\n";
    if (!visibility.empty()) std::cout << "  能见度  : " << visibility << " km\n";
    if (!uv_index.empty())   std::cout << "  紫外线  : " << uv_index << "\n";
    std::cout << "\n";

    // 未来3天预报
    std::cout << "  --- 未来 3 天预报 ---\n";
    for (int i = 0; i < 3; i++) {
        if (days[i].date.empty()) continue;

        // 只显示 MM-DD
        std::string date_short = (days[i].date.length() >= 10)
            ? days[i].date.substr(5) : days[i].date;

        std::cout << "  " << (i + 1) << ". " << date_short;
        if (!days[i].min_temp.empty() && !days[i].max_temp.empty()) {
            std::cout << "  " << days[i].min_temp << "~" << days[i].max_temp << " C";
        }
        if (!days[i].desc.empty()) {
            std::cout << "  " << days[i].desc;
        }
        std::cout << "\n";
    }
    std::cout << "\n";

    std::cout << "  ---\n";
    std::cout << "  数据: wttr.in\n";
    std::cout << "\n";
}

// ============================================================
// 帮助信息
// ============================================================

static void print_help(const char *prog_name) {
    std::cout << "\n";
    std::cout << "  天气查询工具\n";
    std::cout << "\n";
    std::cout << "  用法: " << prog_name << " [城市名]\n";
    std::cout << "\n";
    std::cout << "  参数:\n";
    std::cout << "    城市名    要查询的城市（支持拼音、英文）\n";
    std::cout << "             不指定则默认查询北京\n";
    std::cout << "    -h        显示本帮助信息\n";
    std::cout << "\n";
    std::cout << "  示例:\n";
    std::cout << "    " << prog_name << " beijing\n";
    std::cout << "    " << prog_name << " shanghai\n";
    std::cout << "    " << prog_name << " \"New York\"\n";
    std::cout << "    " << prog_name << " london\n";
    std::cout << "\n";
}

// ============================================================
// 主函数
// ============================================================

int main(int argc, char *argv[]) {
    // 设置本地化以支持中文输出
    std::setlocale(LC_ALL, "");

#ifdef _WIN32
    // Windows 下设置控制台 UTF-8 编码以支持中文
    SetConsoleOutputCP(CP_UTF8);
#endif

    std::string city;

    if (argc > 1) {
        city = argv[1];
        if (city == "-h" || city == "--help") {
            print_help(argv[0]);
            return 0;
        }
    }

    city = trim(city);
    if (city.empty()) {
        city = "beijing";
    }

    // 构建 API URL
    std::string url = "https://wttr.in/" + url_encode(city) + "?format=j1";
    std::string json = fetch_json(url);

    display_weather(city, json);

    return 0;
}
