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
// 跨平台 UTF-8 输出
// Linux/Mac: 直接 cout
// Windows:   WriteConsoleW 绕过编码问题
// ============================================================

#ifdef _WIN32
static void print_u8(const std::string &s) {
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD mode;
    // 真实控制台用 WriteConsoleW（绕开代码页问题）
    // 管道/文件重定向时退回到 cout
    if (h && h != INVALID_HANDLE_VALUE && GetConsoleMode(h, &mode)) {
        int len = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), (int)s.size(),
                                      nullptr, 0);
        std::wstring w(len, L'\0');
        MultiByteToWideChar(CP_UTF8, 0, s.c_str(), (int)s.size(),
                            &w[0], len);
        DWORD written;
        WriteConsoleW(h, w.data(), (DWORD)w.size(), &written, nullptr);
    } else {
        std::cout << s;
    }
}
#else
static void print_u8(const std::string &s) { std::cout << s; }
#endif

// ============================================================
// 工具函数
// ============================================================

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
// JSON 简易提取
// ============================================================

static std::string json_get_string(const std::string &json, const std::string &key) {
    std::regex pattern("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern))
        return match[1];
    return "";
}

static std::string json_get_int(const std::string &json, const std::string &key) {
    std::string val = json_get_string(json, key);
    if (val.empty()) {
        std::regex pattern("\"" + key + "\"\\s*:\\s*(\\d+)");
        std::smatch match;
        if (std::regex_search(json, match, pattern))
            val = match[1];
    }
    return val;
}

static std::string json_get_desc(const std::string &json) {
    std::regex pattern(
        "\"weatherDesc\"\\s*:\\s*\\[\\s*\\{\\s*\"value\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern))
        return match[1];
    return "";
}

// ============================================================
// 天气描述中英文翻译表
// ============================================================

static std::string translate_desc(const std::string &en) {
    static const char *table[][2] = {
        { "Moderate or heavy rain with thunder", u8"\u96f7\u66b4\u5927\u96e8" },
        { "Moderate or heavy rain shower",       u8"\u4e2d\u5230\u5927\u9635\u96e8" },
        { "Moderate or heavy freezing rain",     u8"\u4e2d\u5230\u5927\u51bb\u96e8" },
        { "Moderate or heavy sleet",             u8"\u4e2d\u5230\u5927\u51b0\u96f9" },
        { "Patchy light rain with thunder",      u8"\u96f7\u9635\u96e8" },
        { "Patchy light drizzle",                u8"\u96f6\u661f\u6bdb\u6bdb\u96e8" },
        { "Patchy light rain",                   u8"\u96f6\u661f\u5c0f\u96e8" },
        { "Patchy moderate snow",                u8"\u96f6\u661f\u4e2d\u96ea" },
        { "Patchy heavy snow",                   u8"\u96f6\u661f\u5927\u96ea" },
        { "Patchy rain possible",                u8"\u53ef\u80fd\u6709\u96f6\u661f\u96e8" },
        { "Patchy rain nearby",                  u8"\u9644\u8fd1\u6709\u96e8" },
        { "Torrential rain shower",              u8"\u7279\u5927\u9635\u96e8" },
        { "Thundery outbreaks possible",         u8"\u53ef\u80fd\u6709\u96f7\u66b4" },
        { "Light rain shower",                   u8"\u5c0f\u9635\u96e8" },
        { "Light freezing rain",                 u8"\u51bb\u96e8" },
        { "Light drizzle",                       u8"\u6bdb\u6bdb\u96e8" },
        { "Light rain with thunder",             u8"\u96f7\u9635\u96e8" },
        { "Moderate rain with thunder",          u8"\u96f7\u9635\u96e8\u4e2d\u96e8" },
        { "Heavy rain with thunder",             u8"\u96f7\u9635\u96e8\u5927\u96e8" },
        { "Moderate rain at times",              u8"\u65f6\u6709\u4e2d\u96e8" },
        { "Heavy rain at times",                 u8"\u65f6\u6709\u5927\u96e8" },
        { "Moderate rain",                       u8"\u4e2d\u96e8" },
        { "Heavy rain",                          u8"\u5927\u96e8" },
        { "Light rain",                          u8"\u5c0f\u96e8" },
        { "Partly cloudy",                       u8"\u591a\u4e91" },
        { "Freezing fog",                        u8"\u51bb\u96fe" },
        { "Light snow",                          u8"\u5c0f\u96ea" },
        { "Moderate snow",                       u8"\u4e2d\u96ea" },
        { "Heavy snow",                          u8"\u5927\u96ea" },
        { "Sunny",                               u8"\u6674" },
        { "Clear ",                              u8"\u6674 " },
        { "Clear",                               u8"\u6674" },
        { "Cloudy",                              u8"\u591a\u4e91" },
        { "Overcast",                            u8"\u9634" },
        { "Mist",                                u8"\u8584\u96fe" },
        { "Fog",                                 u8"\u96fe" },
        { "Hail",                                u8"\u51b0\u96f9" },
    };
    for (auto &pair : table)
        if (en.find(pair[0]) != std::string::npos)
            return pair[1];
    for (unsigned char c : en)
        if (c >= 0x80) return en;
    return en;
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

static std::string find_nth_value(const std::string &json,
                                  const std::string &key, int index) {
    size_t pos = 0;
    for (int i = 0; i <= index; i++) {
        std::string search = "\"" + key + "\":";
        size_t found = json.find(search, pos);
        if (found == std::string::npos) return "";
        pos = found + search.length();
        while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t'))
            pos++;
        if (pos >= json.length() || json[pos] != '"') return "";
        pos++;
    }
    size_t end = json.find('"', pos);
    return (end == std::string::npos) ? "" : json.substr(pos, end - pos);
}

static DayForecast extract_forecast(const std::string &json, int day_index) {
    DayForecast day;
    day.date     = find_nth_value(json, "date", day_index);
    day.max_temp = find_nth_value(json, "maxtempC", day_index);
    day.min_temp = find_nth_value(json, "mintempC", day_index);

    {
        std::string dm = "\"date\":";
        size_t start = 0;
        for (int i = 0; i <= day_index; i++) {
            size_t f = json.find(dm, start);
            if (f == std::string::npos) break;
            start = f + dm.length();
        }
        if (start > 0) {
            size_t seg_end = json.find(dm, start);
            if (seg_end == std::string::npos) seg_end = json.length();
            size_t search_from = (start > 10) ? start - 10 : 0;
            day.desc = json_get_desc(
                json.substr(search_from, seg_end - search_from));
        }
    }
    return day;
}

// ============================================================
// 输出构建（先用 UTF-8 拼装，再一次性输出）
// ============================================================

static void display_weather(const std::string &city, const std::string &json) {
    std::ostringstream out;  // 全部用 UTF-8 拼装

    if (json.empty()) {
        out << u8"\n  [\u9519\u8bef] \u65e0\u6cd5\u8fde\u63a5\u5230"
               u8"\u5929\u6c14\u670d\u52a1\uff0c\u8bf7\u68c0\u67e5"
               u8"\u7f51\u7edc\u8fde\u63a5\u3002\n\n";
        print_u8(out.str());
        return;
    }

    if (json.find("current_condition") == std::string::npos) {
        out << u8"\n  [\u9519\u8bef] \u672a\u627e\u5230\u57ce\u5e02 \""
            << city
            << u8"\" \u7684\u5929\u6c14\u4fe1\u606f\u3002\n"
               u8"  \u8bf7\u68c0\u67e5\u57ce\u5e02\u540d\u662f\u5426\u6b63\u786e"
               u8"\uff08\u5efa\u8bae\u4f7f\u7528\u62fc\u97f3\u6216\u82f1\u6587\u540d\uff09\u3002\n\n";
        print_u8(out.str());
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
    for (int i = 0; i < 3; i++)
        days[i] = extract_forecast(json, i);

    // --- 拼装输出 ---
    out << u8"\n"
           u8"  +------------------------------------------+\n"
           u8"  |            \u5b9e\u65f6\u5929\u6c14\u67e5\u8be2                    |\n"
           u8"  +------------------------------------------+\n"
           u8"\n"
           u8"  \u57ce\u5e02: " << city << "\n";

    if (!desc.empty())
        out << u8"  \u5929\u6c14: " << translate_desc(desc) << "\n";

    out << u8"\n"
           u8"  --- \u5b9e\u65f6\u5929\u6c14 ---\n";
    if (!temp.empty())
        out << u8"  \u6e29\u5ea6    : " << temp << " C\n";
    if (!feels.empty())
        out << u8"  \u4f53\u611f\u6e29\u5ea6: " << feels << " C\n";
    if (!humidity.empty())
        out << u8"  \u6e7f\u5ea6    : " << humidity << "%\n";
    if (!wind_speed.empty())
        out << u8"  \u98ce\u901f    : " << wind_speed << " km/h " << wind_dir << "\n";
    if (!visibility.empty())
        out << u8"  \u80fd\u89c1\u5ea6  : " << visibility << " km\n";
    if (!uv_index.empty())
        out << u8"  \u7d2b\u5916\u7ebf  : " << uv_index << "\n";

    out << u8"\n"
           u8"  --- \u672a\u6765 3 \u5929\u9884\u62a5 ---\n";
    for (int i = 0; i < 3; i++) {
        if (days[i].date.empty()) continue;
        std::string d = (days[i].date.length() >= 10)
                            ? days[i].date.substr(5) : days[i].date;
        out << "  " << (i + 1) << ". " << d;
        if (!days[i].min_temp.empty() && !days[i].max_temp.empty())
            out << "  " << days[i].min_temp << "~" << days[i].max_temp << " C";
        if (!days[i].desc.empty())
            out << "  " << translate_desc(days[i].desc);
        out << "\n";
    }

    out << u8"\n"
           u8"  ---\n"
           u8"  \u6570\u636e: wttr.in\n"
           u8"\n";

    print_u8(out.str());
}

// ============================================================
// 帮助信息
// ============================================================

static void print_help(const char *prog_name) {
    std::ostringstream out;
    out << u8"\n"
           u8"  \u5929\u6c14\u67e5\u8be2\u5de5\u5177\n"
           u8"\n"
           u8"  \u7528\u6cd5: " << prog_name
        << u8" [\u57ce\u5e02\u540d]\n"
           u8"\n"
           u8"  \u53c2\u6570:\n"
           u8"    \u57ce\u5e02\u540d    "
           u8"\u8981\u67e5\u8be2\u7684\u57ce\u5e02\uff08\u652f\u6301\u62fc\u97f3\u3001\u82f1\u6587\uff09\n"
           u8"             "
           u8"\u4e0d\u6307\u5b9a\u5219\u9ed8\u8ba4\u67e5\u8be2\u5317\u4eac\n"
           u8"    -h        \u663e\u793a\u672c\u5e2e\u52a9\u4fe1\u606f\n"
           u8"\n"
           u8"  \u793a\u4f8b:\n"
           u8"    " << prog_name << " beijing\n"
        << u8"    " << prog_name << " shanghai\n"
        << u8"    " << prog_name << " \"New York\"\n"
        << u8"    " << prog_name << " london\n"
        << u8"\n";
    print_u8(out.str());
}

// ============================================================
// 主函数
// ============================================================

int main(int argc, char *argv[]) {
    std::setlocale(LC_ALL, "");

#ifdef _WIN32
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
    if (city.empty())
        city = "beijing";

    std::string url = "https://wttr.in/" + url_encode(city) + "?format=j1&lang=zh";
    std::string json = fetch_json(url);

    display_weather(city, json);

    return 0;
}
