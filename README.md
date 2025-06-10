# <span style="color:orange">本说明文件分为<u>英文</u>和<u>中文</u>两部分</span>。

# Real-time Japanese Subtitle Transcription System (with Keyword Functionality)

## 🧩 Introduction

This program is a **multilingual real-time speech transcription and translation system** based on the GPT-4o-transcribe API, featuring a modern and visually appealing graphical user interface. Users only need to connect a microphone and click "Start Recording" to obtain real-time text from Japanese (or other languages) speech. It supports translation into English, Chinese, and other languages, and displays the results in a floating subtitle window.

Ideal for meeting documentation, language learning, subtitle assistance, and more.

---

## 🚀 How to Use

### 1. Preparation

Make sure the folder contains the following two files:

- `RealTime_Jp2txt.exe`: The packaged executable program

- `API_Key.txt`: A text file containing your personal OpenAI API Key (supports GPT-4o)

### 2. Configure the API Key

In the `API_Key.txt` file located in the same directory as `RealTime_Jp2txt.exe`, enter a valid API Key obtained from the OpenAI website, like this:

```
sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> ⚠️ **Do not upload this file to a public repository or share it with others!**

### 3. Launch the Program

- Double-click `RealTime_Jp2txt.exe` to start the program.

- A graphical interface will appear—no command-line operations required.

### 4. Interface Operation Guide

- **Keyword Input Box**: Optional input for keywords related to the current topic. Helps the model better understand the context.

- **Transcription Language Selection**: Dropdown menu with options including:
  
  - `ja – 日本語 (Japanese)`
  
  - `en – English`
  
  - `zh – 中文 (Chinese)`
  
  - `ko – 한국어 (Korean)`
  
  - `es – Español`
  
  - `fr – Français`
  
  - `de – Deutsch`
  
  - `ru – Русский`
  
  - `auto – 自動検出 (Auto-detect)`

Selecting "auto" lets the model detect the language automatically; selecting other options will pass the corresponding language code to the API for forced recognition.

- **🎙️ Start Recording**: Begins capturing audio from the microphone. Audio chunks of 4 seconds (with 0.8-second overlap) are sent to the GPT-4o Transcribe API and displayed in real time.

- **⏹️ Stop Recording**: Stops current recording and transcription. Previously obtained subtitles are retained and can be resumed anytime.

- **🖥️ Floating Subtitle**: Displays a semi-transparent, frameless floating window at the bottom of the screen, showing the latest two subtitle lines without timestamps. Supports dragging and resizing.

- **Audio Level Progress Bar**: Displays the current audio input volume, updating in real time.

- **Subtitle Display Area**: A scrollable text box that automatically appends subtitles in the format `[HH:MM:SS] content`, auto-scrolling to the bottom.

### 5. Exit the Program

- Click the close button on the top right of the main window to exit.

- If the floating window is enabled, it is recommended to close it first before exiting the main window. The program will automatically terminate threads and release microphone resources.

---

## 🧠 Feature Overview

### ✅ Real-time Audio Capture & Chunked Transcription

- Uses PyAudio to capture microphone input in real time and slices it into chunks of "4 seconds + 0.8 seconds overlap" for GPT-4o-transcribe;

- Overlapping helps maintain context continuity and improves accuracy.

### ✅ Keyword-based Context Prompting

- Keywords provided by the user are included as prompts in the initial request to help set the context;

- Subsequent requests automatically concatenate previous results to maintain semantic coherence.

### ✅ Multilingual Support

- Supports `ja – Japanese`, `en – English`, `zh – Chinese`, `ko – Korean`, `es – Spanish`, `fr – French`, `de – German`, `ru – Russian`, and `auto – Auto-detect`;

- Language code can be manually specified or automatically detected by the model.

### ✅ Visual Graphical Interface

- **Main Window**:
  
  - Provides keyword input, language selection, and recording control buttons;
  
  - Displays audio levels, debug info, and real-time subtitles.

- **Floating Subtitle Window**:
  
  - Frameless, semi-transparent, draggable, and resizable;
  
  - Supports font size adjustments (A-/A+), displays the two most recent subtitle lines;
  
  - Suitable for staying on top of other application windows.

### ✅ Multithreaded Asynchronous Processing

- **Audio Thread**: Handles audio input and chunking;

- **Transcription Thread**: Sends audio to the transcription API;

- **Main Thread**: Handles GUI updates and subtitle display only—no lag or freezing;

- Ensures real-time, stable, and smooth system performance.

---

## 📂 Configuration Files

Inside the `Transcription` folder, there are two files:

| Filename              | Description                                                  |
| --------------------- | ------------------------------------------------------------ |
| `RealTime_Jp2txt.exe` | Main program, double-click to run (no installation required) |
| `API_Key.txt`         | Text file containing the OpenAI API Key                      |

Python source code is located in the `Pycode` folder.

---

📧 For any questions or issues, please contact the author:**heu_xuyouyan@outlook.com**

---

# 实时日语字幕转写系统（附带关键词功能）

## 🧩 简介

本程序是一款基于 GPT-4o-transcribe API 的**多语种实时语音转写与翻译系统**，具有美观现代的图形界面。用户只需连接麦克风并点击“Start Recording”，即可实时获取日语（或其他语言）语音的文字版本，支持翻译为英语、中文等多种语言，并通过浮动字幕窗口进行即时展示。

适用于会议记录、语言学习、字幕辅助等场景。

---

## 🚀 使用方法

### 1. 准备工作

- 确保文件夹中存在两个文件：
  
  - `RealTime_Jp2txt.exe`：已打包好的可执行程序
  
  - `API_Key.txt`：存放你自己的 OpenAI API Key（GPT-4o 版本支持）

### 2. 配置 API Key

- 在与 `RealTime_Jp2txt.exe` 同级的目录中的文件 `API_Key.txt`，中输入从OpenAI网站获取的一行有效的 API Key，形如：
  
  ```
  sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```

> ⚠️ **请勿将该文件上传至公共仓库或与他人共享！**

### 3. 启动程序

- 双击 `RealTime_Jp2txt.exe` 启动程序。

- 程序启动后将出现图形界面，无需任何命令行操作。

### 4. 界面操作说明

- **关键词输入框**：填写当前语音主题关键词（可选），用于提高模型理解上下文的能力。

- **转写语言选择**：下拉框提供多种选项，包括：
  
  - `ja – 日本語 (Japanese)`
  
  - `en – English`
  
  - `zh – 中文 (Chinese)`
  
  - `ko – 한국어 (Korean)`
  
  - `es – Español`
  
  - `fr – Français`
  
  - `de – Deutsch`
  
  - `ru – Русский`
  
  - `auto – 自動検出 (Auto-detect)`
  
  - 选择 "auto" 时由模型自动检测语言；选择其他语言时将对应语言代码传给 API 强制指定。

- **🎙️ 开始录音**：点击后程序开始采集麦克风音频，每段 4 秒（含 0.8 秒重叠）上传至 GPT-4o Transcribe API 并实时显示文字结果。

- **⏹️ 停止录音**：停止当前录音与转写，已获取字幕保留，可随时重新开始。

- **🖥️ 浮动字幕**：点击可在屏幕底部弹出一个半透明的无边框窗口（悬浮窗），实时显示最近两条无时间戳字幕，支持拖动与缩放。

- **音频电平进度条**：界面中显示当前音频输入强度，实时更新。

- **字幕显示区域**：带滚动条的文本框，自动追加 `[HH:MM:SS] 文字内容` 格式的字幕，自动滚动到底部。

### 5. 关闭程序

- 点击主窗口右上角的关闭按钮即可退出。

- 若开启了悬浮窗，建议先关闭浮窗，再关闭主界面。程序会自动终止线程并释放麦克风资源。

---

## 🧠 功能概览

### ✅ 实时音频采集与分段转写

- 使用 PyAudio 实时采集麦克风音频，按“4 秒 + 0.8 秒重叠”切分为片段发送至 GPT-4o-transcribe；

- 重叠部分帮助上下文衔接，提升连续性和准确性。

### ✅ 关键词上下文提示

- 用户填写的关键词将在首次请求中以 Prompt 形式提供给模型，用于设定语境；

- 后续请求自动拼接前几条结果作为上下文，确保语义连贯。

### ✅ 多语种支持

- 支持 `ja – 日语`、`en – 英语`、`zh – 中文`、`ko – 韩语`、`es – 西班牙语`、`fr – 法语`、`de – 德语`、`ru – 俄语` 及 `auto – 自动检测`；

- 可指定语言代码或交由模型自动识别。

### ✅ 可视化图形界面

- **主窗口**：
  
  - 提供关键词输入、语言选择、录音控制等按钮；
  
  - 显示音频电平、调试信息和实时字幕；

- **悬浮字幕窗口**：
  
  - 无边框、半透明、可拖动和缩放；
  
  - 支持字体大小调整（A-/A+），最多显示最近两句字幕；
  
  - 适合在其他应用窗口上层持续查看。

### ✅ 多线程异步处理

- **音频线程**：处理音频输入和切片；

- **转写线程**：发送音频并调用转写 API；

- **主线程**：仅处理 GUI 和字幕刷新，不卡顿、不卡界面；

- 保证系统响应实时、稳定、流畅。

---

## 📂 配置文件说明

在`Transcription`文件夹下有两个文件:

| 文件名                   | 用途说明                    |
| --------------------- | ----------------------- |
| `RealTime_Jp2txt.exe` | 主程序，双击运行（无需安装）          |
| `API_Key.txt`         | 存放 OpenAI API Key 的文本文件 |

python源码在`Pycode`文件夹中

---

📧 如有任何问题，请联系作者：**heu_xuyouyan@outlook.com**
