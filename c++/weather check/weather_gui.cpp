/**
 * weather_gui.cpp - 天气查询工具 (GUI 版)
 *
 * 使用 wttr.in 免费 API（无需 API Key）
 * Win32 原生界面，无需任何第三方库
 *
 * 编译:
 *   g++ -o weather_gui.exe weather_gui.cpp -std=c++17 -static -mwindows
 *
 * 运行:
 *   ./weather_gui.exe
 *
 * 依赖: Windows 自带的 curl.exe + wttr.in API
 *
 * 注意: 源文件必须保存为 UTF-8（带 BOM），否则中文会乱码
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>
#include <array>
#include <sstream>
#include <iomanip>
#include <regex>

// ============================================================
// 常量
// ============================================================

constexpr int ID_EDIT_CITY   = 100;
constexpr int ID_BTN_QUERY   = 101;
constexpr int ID_OUTPUT      = 102;

constexpr UINT WM_WEATHER_DONE = WM_USER + 1;

// ============================================================
// 跨编码字符串辅助：将 UTF-8 字面量转为 wstring
// 避免源文件编码依赖问题
// ============================================================

static std::wstring utf8_to_wstring(const char *utf8) {
    int len = MultiByteToWideChar(CP_UTF8, 0, utf8, -1, nullptr, 0);
    std::wstring w(len, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, utf8, -1, &w[0], len);
    if (!w.empty() && w.back() == L'\0') w.pop_back();
    return w;
}

// ============================================================
// HTTP 请求：调用 curl.exe 获取 JSON（CREATE_NO_WINDOW 防弹窗）
// ============================================================

static std::string fetch_json(const std::string &url) {
    std::string cmdline = "curl.exe -s -m 10 \"" + url + "\"";

    SECURITY_ATTRIBUTES sa = { sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE };
    HANDLE hRead, hWrite;
    if (!CreatePipe(&hRead, &hWrite, &sa, 0)) return "";
    SetHandleInformation(hRead, HANDLE_FLAG_INHERIT, 0);

    PROCESS_INFORMATION pi = {};
    STARTUPINFOA si = { sizeof(STARTUPINFOA) };
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdOutput = hWrite;
    si.hStdError  = hWrite;

    if (!CreateProcessA(nullptr, cmdline.data(), nullptr, nullptr, TRUE,
                        CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi)) {
        CloseHandle(hRead);
        CloseHandle(hWrite);
        return "";
    }

    CloseHandle(hWrite);

    std::string result;
    char buffer[4096];
    DWORD bytesRead;
    while (ReadFile(hRead, buffer, sizeof(buffer) - 1, &bytesRead, nullptr) &&
           bytesRead > 0) {
        buffer[bytesRead] = '\0';
        result.append(buffer, bytesRead);
    }

    CloseHandle(hRead);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return result;
}

// ============================================================
// JSON 简易提取（使用 regex）
// ============================================================

static std::string json_get_string(const std::string &json,
                                   const std::string &key) {
    std::regex pattern("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern))
        return match[1];
    return "";
}

static std::string json_get_desc(const std::string &json) {
    std::regex pattern(
        "\"weatherDesc\"\\s*:\\s*\\[\\s*\\{\\s*\"value\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern))
        return match[1];
    return "";
}

static std::string find_nth_value(const std::string &json,
                                  const std::string &key, int index) {
    size_t pos = 0;
    for (int i = 0; i <= index; i++) {
        std::string search = "\"" + key + "\":";
        size_t found = json.find(search, pos);
        if (found == std::string::npos) return "";
        pos = found + search.length();
        while (pos < json.length() &&
               (json[pos] == ' ' || json[pos] == '\t'))
            pos++;
        if (pos >= json.length() || json[pos] != '"') return "";
        pos++;
    }
    size_t end = json.find('"', pos);
    return (end == std::string::npos) ? "" : json.substr(pos, end - pos);
}

static std::string get_day_desc(const std::string &json, int day_index) {
    std::string dm = "\"date\":";
    size_t start = 0;
    for (int i = 0; i <= day_index; i++) {
        size_t f = json.find(dm, start);
        if (f == std::string::npos) return "";
        start = f + dm.length();
    }
    size_t seg_end = json.find(dm, start);
    if (seg_end == std::string::npos) seg_end = json.length();
    size_t search_from = (start > 10) ? start - 10 : 0;
    return json_get_desc(json.substr(search_from, seg_end - search_from));
}

// ============================================================
// 天气描述中英文翻译表
// ============================================================

static std::string translate_desc(const std::string &en) {
    static const char *table[][2] = {
        // 长/具体匹配在前，短/通用在后
        { "Moderate or heavy rain with thunder", "\u96f7\u66b4\u5927\u96e8" },
        { "Moderate or heavy rain shower",  "\u4e2d\u5230\u5927\u9635\u96e8" },
        { "Moderate or heavy freezing rain","\u4e2d\u5230\u5927\u51bb\u96e8" },
        { "Moderate or heavy sleet",        "\u4e2d\u5230\u5927\u51b0\u96f9" },
        { "Patchy light rain with thunder", "\u96f7\u9635\u96e8" },
        { "Patchy light drizzle",           "\u96f6\u661f\u6bdb\u6bdb\u96e8" },
        { "Patchy light rain",              "\u96f6\u661f\u5c0f\u96e8" },
        { "Patchy moderate snow",           "\u96f6\u661f\u4e2d\u96ea" },
        { "Patchy heavy snow",              "\u96f6\u661f\u5927\u96ea" },
        { "Patchy rain possible",           "\u53ef\u80fd\u6709\u96f6\u661f\u96e8" },
        { "Patchy rain nearby",             "\u9644\u8fd1\u6709\u96e8" },
        { "Torrential rain shower",         "\u7279\u5927\u9635\u96e8" },
        { "Thundery outbreaks possible",    "\u53ef\u80fd\u6709\u96f7\u66b4" },
        { "Light rain shower",              "\u5c0f\u9635\u96e8" },
        { "Light freezing rain",            "\u51bb\u96e8" },
        { "Light drizzle",                  "\u6bdb\u6bdb\u96e8" },
        { "Light rain with thunder",        "\u96f7\u9635\u96e8" },
        { "Moderate rain with thunder",     "\u96f7\u9635\u96e8\u4e2d\u96e8" },
        { "Heavy rain with thunder",        "\u96f7\u9635\u96e8\u5927\u96e8" },
        { "Moderate rain at times",         "\u65f6\u6709\u4e2d\u96e8" },
        { "Heavy rain at times",            "\u65f6\u6709\u5927\u96e8" },
        { "Moderate rain",                  "\u4e2d\u96e8" },
        { "Heavy rain",                     "\u5927\u96e8" },
        { "Light rain",                     "\u5c0f\u96e8" },
        { "Partly cloudy",                  "\u591a\u4e91" },
        { "Freezing fog",                   "\u51bb\u96fe" },
        { "Light snow",                     "\u5c0f\u96ea" },
        { "Moderate snow",                  "\u4e2d\u96ea" },
        { "Heavy snow",                     "\u5927\u96ea" },
        { "Sunny",                          "\u6674" },
        { "Clear ",                         "\u6674 " },
        { "Clear",                          "\u6674" },
        { "Cloudy",                         "\u591a\u4e91" },
        { "Overcast",                       "\u9634" },
        { "Mist",                           "\u8584\u96fe" },
        { "Fog",                            "\u96fe" },
        { "Hail",                           "\u51b0\u96f9" },
    };
    for (auto &pair : table) {
        if (en.find(pair[0]) != std::string::npos)
            return pair[1];
    }
    // 如果已经包含中文字符，说明已经是中文
    for (unsigned char c : en)
        if (c >= 0x80) return en;
    return en;
}

// ============================================================
// URL 编码
// ============================================================

static std::string url_encode(const std::string &value) {
    std::ostringstream escaped;
    escaped << std::hex << std::uppercase;
    for (unsigned char c : value) {
        if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~')
            escaped << c;
        else
            escaped << '%' << std::setw(2) << static_cast<int>(c);
    }
    return escaped.str();
}

// ============================================================
// 获取天气信息并格式化为纯文本
// ============================================================

static std::string format_weather(const std::string &city) {
    std::string url = "https://wttr.in/" + url_encode(city) + "?format=j1&lang=zh";
    std::string json = fetch_json(url);

    if (json.empty()) {
        return reinterpret_cast<const char *>(
            u8"\u9519\u8bef\uff1a\u65e0\u6cd5\u8fde\u63a5\u5230\u5929\u6c14"
            u8"\u670d\u52a1\uff0c\u8bf7\u68c0\u67e5\u7f51\u7edc\u8fde\u63a5\u3002");
    }

    if (json.find("current_condition") == std::string::npos) {
        std::string err = reinterpret_cast<const char *>(
            u8"\u9519\u8bef\uff1a\u672a\u627e\u5230\u57ce\u5e02 \"");
        err += city;
        err += reinterpret_cast<const char *>(
            u8"\" \u7684\u5929\u6c14\u4fe1\u606f\u3002");
        return err;
    }

    std::string temp       = json_get_string(json, "temp_C");
    std::string feels      = json_get_string(json, "FeelsLikeC");
    std::string humidity   = json_get_string(json, "humidity");
    std::string wind_speed = json_get_string(json, "windspeedKmph");
    std::string wind_dir   = json_get_string(json, "winddir16Point");
    std::string desc       = json_get_desc(json);
    std::string visibility = json_get_string(json, "visibility");
    std::string uv         = json_get_string(json, "uvIndex");

    if (desc.empty())
        desc = json_get_string(json, "weatherCode");

    std::ostringstream out;
    out << reinterpret_cast<const char *>(u8"\u57ce\u5e02: ") << city
        << "\r\n";
    if (!desc.empty())
        out << reinterpret_cast<const char *>(u8"\u5929\u6c14: ")
            << translate_desc(desc) << "\r\n";
    out << "\r\n"
        << reinterpret_cast<const char *>(u8"-- \u5b9e\u65f6\u5929\u6c14 --")
        << "\r\n";
    if (!temp.empty())
        out << reinterpret_cast<const char *>(u8"\u6e29\u5ea6    : ")
            << temp << " C\r\n";
    if (!feels.empty())
        out << reinterpret_cast<const char *>(u8"\u4f53\u611f\u6e29\u5ea6: ")
            << feels << " C\r\n";
    if (!humidity.empty())
        out << reinterpret_cast<const char *>(u8"\u6e7f\u5ea6    : ")
            << humidity << "%\r\n";
    if (!wind_speed.empty())
        out << reinterpret_cast<const char *>(u8"\u98ce\u901f    : ")
            << wind_speed << " km/h " << wind_dir << "\r\n";
    if (!visibility.empty())
        out << reinterpret_cast<const char *>(u8"\u80fd\u89c1\u5ea6  : ")
            << visibility << " km\r\n";
    if (!uv.empty())
        out << reinterpret_cast<const char *>(u8"\u7d2b\u5916\u7ebf  : ")
            << uv << "\r\n";

    out << "\r\n"
        << reinterpret_cast<const char *>(
               u8"-- \u672a\u6765 3 \u5929\u9884\u62a5 --")
        << "\r\n";
    for (int i = 0; i < 3; i++) {
        std::string date     = find_nth_value(json, "date", i);
        std::string maxtemp  = find_nth_value(json, "maxtempC", i);
        std::string mintemp  = find_nth_value(json, "mintempC", i);
        std::string day_desc = get_day_desc(json, i);
        if (date.empty()) continue;
        std::string d = (date.length() >= 10) ? date.substr(5) : date;
        out << (i + 1) << ". " << d;
        if (!mintemp.empty() && !maxtemp.empty())
            out << "  " << mintemp << "~" << maxtemp << " C";
        if (!day_desc.empty())
            out << "  " << translate_desc(day_desc);
        out << "\r\n";
    }
    out << "\r\n---\r\n"
        << reinterpret_cast<const char *>(u8"\u6570\u636e\u6765\u6e90: wttr.in");
    return out.str();
}

// ============================================================
// 工作线程
// ============================================================

struct ThreadParam {
    HWND hwnd;
    std::string city;
};

static DWORD WINAPI weather_thread(LPVOID param) {
    auto *tp = static_cast<ThreadParam *>(param);
    std::string result = format_weather(tp->city);
    auto *result_ptr = new std::string(std::move(result));
    PostMessage(tp->hwnd, WM_WEATHER_DONE, 0,
                reinterpret_cast<LPARAM>(result_ptr));
    delete tp;
    return 0;
}

// ============================================================
// 创建系统字体（支持中文的最可靠方式）
// ============================================================

static HFONT CreateSafeFont(int height, const wchar_t *face) {
    LOGFONTW lf = {};
    lf.lfHeight         = height;
    lf.lfWeight         = FW_NORMAL;
    lf.lfCharSet        = DEFAULT_CHARSET;
    lf.lfOutPrecision   = OUT_TT_PRECIS;
    lf.lfClipPrecision  = CLIP_DEFAULT_PRECIS;
    lf.lfQuality        = CLEARTYPE_QUALITY;
    lf.lfPitchAndFamily = DEFAULT_PITCH | FF_DONTCARE;
    if (face && face[0])
        wcscpy_s(lf.lfFaceName, LF_FACESIZE, face);
    else
        lf.lfFaceName[0] = L'\0';
    return CreateFontIndirectW(&lf);
}

// ============================================================
// 窗口过程
// ============================================================

static HFONT g_font_output = nullptr;
static HFONT g_font_ui     = nullptr;

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_CREATE: {
        // 创建字体：用系统已安装的字体，不含具体字体名时 font linking 自动生效
        g_font_ui     = CreateSafeFont(16, L"Microsoft YaHei UI");
        if (!g_font_ui) g_font_ui = CreateSafeFont(16, L"Microsoft YaHei");
        if (!g_font_ui) g_font_ui = CreateSafeFont(16, L"SimSun");
        if (!g_font_ui) g_font_ui = CreateSafeFont(16, nullptr);

        g_font_output = CreateSafeFont(15, L"Consolas");
        if (!g_font_output) g_font_output = CreateSafeFont(15, L"SimSun");
        if (!g_font_output) g_font_output = CreateSafeFont(15, nullptr);

        // 用 UTF-8 字面量初始化中文字符串
        std::wstring label_city = utf8_to_wstring(
            reinterpret_cast<const char *>(u8"\u57ce\u5e02\u540d:"));
        std::wstring btn_query = utf8_to_wstring(
            reinterpret_cast<const char *>(u8"\u67e5\u8be2"));

        HWND hLabel = CreateWindowExW(0, L"STATIC", label_city.c_str(),
                                      WS_CHILD | WS_VISIBLE,
                                      15, 15, 55, 26, hwnd,
                                      nullptr, nullptr, nullptr);

        HWND hEdit = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"beijing",
                                     WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL,
                                     75, 13, 180, 26, hwnd,
                                     (HMENU)ID_EDIT_CITY, nullptr, nullptr);

        HWND hBtn = CreateWindowExW(0, L"BUTTON", btn_query.c_str(),
                                    WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
                                    265, 12, 70, 28, hwnd,
                                    (HMENU)ID_BTN_QUERY, nullptr, nullptr);

        HWND hOutput = CreateWindowExW(
            WS_EX_CLIENTEDGE, L"EDIT", L"",
            WS_CHILD | WS_VISIBLE | ES_MULTILINE |
            ES_READONLY | WS_VSCROLL | ES_AUTOVSCROLL,
            15, 50, 470, 330, hwnd,
            (HMENU)ID_OUTPUT, nullptr, nullptr);

        SendMessageW(hLabel,  WM_SETFONT, (WPARAM)g_font_ui,     TRUE);
        SendMessageW(hEdit,   WM_SETFONT, (WPARAM)g_font_ui,     TRUE);
        SendMessageW(hBtn,    WM_SETFONT, (WPARAM)g_font_ui,     TRUE);
        SendMessageW(hOutput, WM_SETFONT, (WPARAM)g_font_output, TRUE);

        PostMessageW(hwnd, WM_COMMAND, MAKEWPARAM(ID_BTN_QUERY, BN_CLICKED), 0);
        break;
    }
    case WM_COMMAND: {
        if (LOWORD(wParam) == ID_BTN_QUERY && HIWORD(wParam) == BN_CLICKED) {
            HWND hEdit = GetDlgItem(hwnd, ID_EDIT_CITY);
            int len = GetWindowTextLengthW(hEdit);
            if (len == 0) {
                std::wstring msg = utf8_to_wstring(
                    reinterpret_cast<const char *>(
                        u8"\u8bf7\u8f93\u5165\u57ce\u5e02\u540d"));
                std::wstring cap = utf8_to_wstring(
                    reinterpret_cast<const char *>(u8"\u63d0\u793a"));
                MessageBoxW(hwnd, msg.c_str(), cap.c_str(),
                            MB_OK | MB_ICONINFORMATION);
                break;
            }
            std::wstring wbuf(len + 1, L'\0');
            GetWindowTextW(hEdit, wbuf.data(), len + 1);
            wbuf.resize(len);

            int size = WideCharToMultiByte(CP_UTF8, 0, wbuf.data(), len,
                                           nullptr, 0, nullptr, nullptr);
            std::string city(size, '\0');
            WideCharToMultiByte(CP_UTF8, 0, wbuf.data(), len,
                                &city[0], size, nullptr, nullptr);

            EnableWindow(GetDlgItem(hwnd, ID_BTN_QUERY), FALSE);
            std::wstring waiting = utf8_to_wstring(
                reinterpret_cast<const char *>(
                    u8"\u6b63\u5728\u67e5\u8be2\uff0c\u8bf7\u7a0d\u5019..."));
            SetWindowTextW(GetDlgItem(hwnd, ID_OUTPUT), waiting.c_str());

            auto *tp = new ThreadParam{hwnd, std::move(city)};
            CloseHandle(CreateThread(nullptr, 0, weather_thread, tp, 0, nullptr));
        }
        break;
    }
    case WM_WEATHER_DONE: {
        auto *result = reinterpret_cast<std::string *>(lParam);
        if (result) {
            int len = MultiByteToWideChar(CP_UTF8, 0, result->c_str(), -1,
                                          nullptr, 0);
            std::wstring wbuf(len, L'\0');
            MultiByteToWideChar(CP_UTF8, 0, result->c_str(), -1,
                                &wbuf[0], len);
            SetWindowTextW(GetDlgItem(hwnd, ID_OUTPUT), wbuf.data());
            delete result;
        }
        EnableWindow(GetDlgItem(hwnd, ID_BTN_QUERY), TRUE);
        break;
    }
    case WM_SIZE: {
        int w = LOWORD(lParam);
        int h = HIWORD(lParam);
        if (w > 10 && h > 60)
            SetWindowPos(GetDlgItem(hwnd, ID_OUTPUT), nullptr,
                         15, 50, w - 30, h - 65, SWP_NOZORDER);
        break;
    }
    case WM_DESTROY: {
        if (g_font_output) DeleteObject(g_font_output);
        if (g_font_ui)     DeleteObject(g_font_ui);
        PostQuitMessage(0);
        break;
    }
    default:
        return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

// ============================================================
// 入口
// ============================================================

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE, LPSTR, int nCmdShow) {
    HICON hIcon = LoadIcon(hInst, MAKEINTRESOURCE(1));

    WNDCLASS wc = {};
    wc.lpfnWndProc   = WndProc;
    wc.hInstance     = hInst;
    wc.hIcon         = hIcon;
    wc.hCursor       = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = "WeatherApp";

    if (!RegisterClass(&wc)) return 1;

    std::wstring title = utf8_to_wstring(
        reinterpret_cast<const char *>(u8"\u5929\u6c14\u67e5\u8be2\u5de5\u5177"));

    HWND hwnd = CreateWindowEx(
        0, "WeatherApp", "",
        WS_OVERLAPPEDWINDOW & ~WS_MAXIMIZEBOX & ~WS_THICKFRAME,
        CW_USEDEFAULT, CW_USEDEFAULT, 520, 430,
        nullptr, nullptr, hInst, nullptr);

    if (!hwnd) return 1;

    // 设置窗口标题（UTF-8 -> UTF-16）
    SetWindowTextW(hwnd, title.c_str());

    // 显式设置图标（标题栏 + 任务栏）
    SendMessage(hwnd, WM_SETICON, ICON_SMALL, (LPARAM)hIcon);
    SendMessage(hwnd, WM_SETICON, ICON_BIG,  (LPARAM)hIcon);

    // 居中显示
    int sw = GetSystemMetrics(SM_CXSCREEN);
    int sh = GetSystemMetrics(SM_CYSCREEN);
    RECT rc;
    GetWindowRect(hwnd, &rc);
    SetWindowPos(hwnd, nullptr,
                 (sw - (rc.right - rc.left)) / 2,
                 (sh - (rc.bottom - rc.top)) / 3,
                 0, 0, SWP_NOSIZE | SWP_NOZORDER);

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessage(&msg, nullptr, 0, 0)) {
        if (msg.message == WM_KEYDOWN && msg.wParam == VK_RETURN &&
            GetDlgItem(hwnd, ID_EDIT_CITY) == GetFocus()) {
            PostMessage(hwnd, WM_COMMAND,
                        MAKEWPARAM(ID_BTN_QUERY, BN_CLICKED), 0);
            continue;
        }
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}
