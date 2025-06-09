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
