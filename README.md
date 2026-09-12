# BellenneRelay

Local real-time English ↔ Russian speech translation for Windows.

BellenneRelay captures system audio through WASAPI Loopback, microphone audio, or
both sources at the same time. It detects completed speech phrases, transcribes
them with Whisper, translates them locally, and displays the result in the main
window and an optional always-on-top subtitle overlay.

The packaged build includes Whisper Turbo, both OPUS-MT translation models, and
the CUDA runtime required by faster-whisper. It does not require Python, a virtual
environment, CUDA Toolkit, cuDNN, or an internet connection.

> Русская версия документации находится в разделе [Русский](#русский).

## English

### Features

- English → Russian and Russian → English translation;
- system audio capture through Windows WASAPI Loopback;
- separate microphone capture or simultaneous System + Microphone mode;
- local speech recognition with faster-whisper and Whisper Turbo;
- local translation with OPUS-MT/Marian models;
- automatic NVIDIA CUDA acceleration with CPU `int8` fallback;
- input-language filtering for the selected translation direction;
- movable, resizable, always-on-top subtitle overlay;
- configurable overlay font size, opacity, line count, original text, and
  mouse click-through;
- live source level meters, component states, and latency information;
- translation history and structured application logs;
- global keyboard shortcuts and Windows system tray controls;
- offline operation with all default models bundled in the distribution.

### Included models

The standard build contains:

| Purpose | Model |
| --- | --- |
| Speech recognition | Whisper Turbo (`faster-whisper-large-v3-turbo`) |
| English → Russian | `Helsinki-NLP/opus-mt-en-ru` |
| Russian → English | `Helsinki-NLP/opus-mt-ru-en` |

The models are stored in `BellenneRelay\models` next to the executable and are
loaded directly from disk. If a different Whisper model is selected, the model
setup screen downloads it into the user data directory.

### System requirements

- Windows 10 or Windows 11 x64;
- a working WASAPI output device and/or microphone;
- approximately 5.1 GiB of free disk space for the packaged folder;
- optional NVIDIA GPU for accelerated recognition.

An NVIDIA GPU is not required. When CUDA initialization or warm-up fails, the
application automatically switches Whisper to CPU `int8`. The packaged CUDA
libraries are used only for speech recognition; the translation models run on
the available PyTorch device.

### Running the packaged application

1. Keep the entire `dist\BellenneRelay` folder together. The executable cannot be
   moved out of the folder by itself.
2. Run `dist\BellenneRelay\BellenneRelay.exe`.
3. Open **Settings** and confirm the audio source, output device, microphone,
   translation direction, Whisper model, and compute device.
4. Press **Start Translation**.
5. Use **Overlay** when translated subtitles should appear above other windows.

The default configuration uses:

- System + Microphone audio;
- `Maono PD200W Mic USB` as the microphone;
- English → Russian;
- Whisper Turbo;
- automatic CUDA/CPU selection;
- input-language filtering enabled.

Using headphones in System + Microphone mode is recommended to prevent the
microphone from capturing the system audio again.

### Translation direction and language filter

The direction selector controls both the expected speech language and the output
translation language:

- **English → Russian** expects English speech and produces Russian text;
- **Russian → English** expects Russian speech and produces English text.

**Settings → Input filter → Ignore other languages** is enabled by default.
Whisper detects the dominant language before full decoding. A phrase confidently
detected as a language other than the selected input language is discarded and
does not appear in translation history or the overlay.

The default confidence threshold is 65%. Ambiguous short words, names, and
abbreviations are allowed through to reduce false rejections. Filtering is
phrase-level rather than word-level: a mixed-language phrase is handled according
to its dominant detected language.

### Application pages

- **Main** — live original/translated feed, audio levels, latency, and Start/Stop;
- **Overlay** — subtitle appearance, visibility, click-through, and position reset;
- **History** — translations produced during the current application session;
- **Logs** — structured runtime events and component status;
- **Settings drawer** — audio devices, direction, language filter, Whisper model,
  and compute device.

Closing the main window minimizes the application to the system tray by default.
Use **Exit** in the tray menu to stop audio streams, model workers, hotkeys, and
the application completely.

### Global shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+Alt+T` | Start or stop translation |
| `Ctrl+Alt+S` | Show or hide the subtitle overlay |
| `Ctrl+Alt+O` | Enable or disable overlay editing |

If another application has already registered one of these shortcuts,
BellenneRelay reports the registration error in its logs.

### Data and privacy

Default speech recognition and translation run locally. Captured audio is
processed in memory by the GUI pipeline and is not saved as WAV files or uploaded
to a translation service.

Runtime files are stored in:

```text
%LOCALAPPDATA%\BellenneRelay\
├── config.json
├── logs\app.log
└── models\              # only models downloaded after packaging
```

Bundled models remain in `BellenneRelay\models`. Internet access is needed only
when the selected model is not included in the distribution.

### Performance profile

The pipeline uses Silero VAD to submit completed phrases. The default end-of-phrase
silence is 350 ms. Whisper uses `beam_size=1`, a single deterministic temperature,
no timestamp sampling, and eight CPU threads when CPU fallback is active.

Measured on the development machine with an AMD Ryzen 7 5700X and an NVIDIA RTX
3060 12 GB, using the same 10.15-second test phrase:

| Model/device | Recognition time |
| --- | ---: |
| Whisper Medium, CPU `int8` | 3.86 s |
| Whisper Medium, RTX 3060 | 0.44–0.45 s |
| Whisper Turbo, RTX 3060 | 0.34–0.36 s |

Actual latency depends on phrase length, audio quality, background noise, GPU
load, and the time required to detect the end of speech.

### Troubleshooting

#### The application appears to close

Check the Windows system tray. Closing the main window minimizes BellenneRelay by
default. Select **Open BellenneRelay** or **Exit** from its tray menu.

#### System audio is not detected

- confirm that audio is currently playing through the selected Windows output;
- refresh the device list and select the physical output device, not a recording
  input;
- verify that the **System** level meter moves while audio is playing.

#### The wrong microphone is used

Open **Settings**, refresh devices, and select the microphone by name. Device names
are saved in `config.json`; temporary PortAudio indexes are not persisted.

#### Recognition runs on CPU

Leave **Compute** set to **Auto**. BellenneRelay performs a real CUDA warm-up before
audio capture starts. If CUDA cannot be initialized, it logs the failure and uses
CPU `int8` instead.

#### Expected speech is being ignored

Disable **Ignore other languages** to test mixed-language or very short speech.
The filter threshold can also be changed through `language_filter_threshold` in
`config.json`.

#### The model setup window appears

The current configuration requests a model that is not present in the packaged
`models` directory. Restore Whisper `turbo`, keep the complete distribution folder,
or allow the application to download the selected model.

### Development setup

Development uses Python 3.11 or 3.12 x64 and the project-local `.venv`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Python 3.14 is not supported by this project configuration. All development,
diagnostic, test, and build commands should use `.venv\Scripts\python.exe`.

Run the application from source:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

### Tests and code quality

```powershell
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
```

### Building the Windows distribution

The project uses a PyInstaller one-directory build. This format is more reliable
for Qt and native ML libraries than a single self-extracting executable.

Before building, install Git LFS and fetch the versioned files in `model_assets`.
Then run:

```powershell
git lfs install
git lfs pull
.\scripts\build.ps1
```

The script:

1. runs the test suite;
2. creates `dist\BellenneRelay` with PyInstaller;
3. copies the default configuration;
4. copies Whisper Turbo and both translation models from `model_assets` into the
   distribution.

Build output:

```text
dist\BellenneRelay\
├── BellenneRelay.exe
├── config.json
├── models\
│   ├── whisper\turbo\
│   └── translation\
│       ├── en-ru\
│       └── ru-en\
└── _internal\
```

Distribute the complete `BellenneRelay` directory.

### Technical overview

```text
WASAPI system audio / microphone
              │
              ▼
   resample to mono 16 kHz float32
              │
              ▼
          Silero VAD
              │
              ▼
 input-language detection and filtering
              │
              ▼
 faster-whisper Turbo (CUDA or CPU int8)
              │
              ▼
     OPUS-MT EN↔RU translation
              │
              ▼
 main feed / history / subtitle overlay
```

System and microphone sources use separate capture streams and VAD buffers. A
bounded transcription queue prevents unlimited latency growth if inference falls
behind live audio.

---

## Русский

### О проекте

BellenneRelay — Windows-приложение для локального перевода речи между английским
и русским языками в реальном времени. Оно захватывает системный звук через WASAPI
Loopback, микрофон или оба источника одновременно, выделяет законченные речевые
фразы, распознаёт их с помощью Whisper и отображает локальный перевод в основном
окне и поверх других приложений.

Готовая сборка уже содержит Whisper Turbo, обе модели перевода и CUDA-библиотеки
для faster-whisper. Для запуска не нужны Python, `.venv`, CUDA Toolkit, cuDNN или
подключение к интернету.

### Возможности

- перевод English → Russian и Russian → English;
- захват системного звука через Windows WASAPI Loopback;
- отдельный захват микрофона и совместный режим System + Microphone;
- локальное распознавание через faster-whisper и Whisper Turbo;
- локальный перевод через OPUS-MT/Marian;
- автоматическое ускорение на NVIDIA CUDA и fallback на CPU `int8`;
- фильтрация речи, не совпадающей с выбранным входным языком;
- перемещаемый и масштабируемый overlay субтитров поверх окон;
- настройка шрифта, прозрачности, количества строк, исходного текста и
  mouse click-through;
- индикаторы System/Mic, статусы компонентов и отображение задержки;
- история переводов и структурированные логи;
- глобальные горячие клавиши и управление через System Tray;
- полностью офлайн-работа со стандартным комплектом моделей.

### Встроенные модели

| Назначение | Модель |
| --- | --- |
| Распознавание речи | Whisper Turbo (`faster-whisper-large-v3-turbo`) |
| English → Russian | `Helsinki-NLP/opus-mt-en-ru` |
| Russian → English | `Helsinki-NLP/opus-mt-ru-en` |

Модели находятся в `BellenneRelay\models` рядом с EXE и загружаются напрямую с
диска. Если выбрать другую модель Whisper, приложение покажет экран подготовки и
скачает её в пользовательское хранилище.

### Системные требования

- Windows 10 или Windows 11 x64;
- рабочее устройство вывода WASAPI и/или микрофон;
- около 5,1 ГиБ свободного места для готовой папки приложения;
- опционально — видеокарта NVIDIA для ускоренного распознавания.

Видеокарта NVIDIA не обязательна. Если инициализация или прогрев CUDA завершаются
ошибкой, Whisper автоматически переключается на CPU `int8`.

### Запуск готовой сборки

1. Сохраняйте папку `dist\BellenneRelay` целиком. Один EXE без соседних файлов не
   запустится.
2. Откройте `dist\BellenneRelay\BellenneRelay.exe`.
3. В **Settings** проверьте источник звука, устройство вывода, микрофон, направление
   перевода, модель Whisper и Compute.
4. Нажмите **Start Translation**.
5. Включите **Overlay**, если перевод должен отображаться поверх других окон.

Настройки по умолчанию:

- System + Microphone;
- микрофон `Maono PD200W Mic USB`;
- English → Russian;
- Whisper Turbo;
- автоматический выбор CUDA/CPU;
- включённый фильтр входного языка.

В совместном режиме рекомендуется использовать наушники, чтобы микрофон повторно
не захватывал системный звук.

### Направление перевода и фильтр языка

Направление задаёт ожидаемый язык речи и язык результата:

- **English → Russian** принимает английскую речь и выводит русский перевод;
- **Russian → English** принимает русскую речь и выводит английский перевод.

Параметр **Settings → Input filter → Ignore other languages** включён по умолчанию.
Перед полным декодированием Whisper определяет преобладающий язык фразы. Если он
уверенно не совпадает с выбранным входным языком, фраза отбрасывается и не попадает
в перевод, историю или overlay.

Порог уверенности по умолчанию — 65%. Неоднозначные короткие слова, имена и
аббревиатуры пропускаются, чтобы уменьшить ложные блокировки. Фильтрация работает
на уровне целой фразы, а не отдельных слов: смешанная фраза обрабатывается по её
преобладающему языку.

### Разделы приложения

- **Main** — лента оригинала и перевода, уровни звука, задержка и Start/Stop;
- **Overlay** — вид субтитров, отображение, click-through и сброс позиции;
- **History** — переводы текущего сеанса приложения;
- **Logs** — события работы и состояния компонентов;
- **Settings drawer** — аудиоустройства, направление, фильтр языка, Whisper и
  устройство вычисления.

По умолчанию закрытие главного окна сворачивает приложение в System Tray. Для
полной остановки потоков, моделей и горячих клавиш используйте **Exit** в tray-меню.

### Глобальные горячие клавиши

| Клавиши | Действие |
| --- | --- |
| `Ctrl+Alt+T` | Запустить или остановить перевод |
| `Ctrl+Alt+S` | Показать или скрыть overlay субтитров |
| `Ctrl+Alt+O` | Включить или выключить редактирование overlay |

Если сочетание уже занято другой программой, ошибка регистрации появится в логах
BellenneRelay.

### Данные и приватность

Стандартное распознавание и перевод выполняются локально. Рабочий GUI обрабатывает
захваченный звук в памяти, не записывает его в WAV и не отправляет в облачный
сервис перевода.

Пользовательские данные находятся здесь:

```text
%LOCALAPPDATA%\BellenneRelay\
├── config.json
├── logs\app.log
└── models\              # только модели, скачанные после сборки
```

Встроенные модели остаются в `BellenneRelay\models`. Интернет требуется только
при выборе модели, которой нет в комплекте.

### Производительность

Silero VAD отправляет в обработку законченные фразы. Стандартное ожидание тишины в
конце фразы — 350 мс. Whisper использует `beam_size=1`, детерминированную
температуру, декодирование без timestamps и восемь потоков при CPU fallback.

Замеры на AMD Ryzen 7 5700X и NVIDIA RTX 3060 12 ГБ для одного фрагмента длиной
10,15 с:

| Модель и устройство | Время распознавания |
| --- | ---: |
| Whisper Medium, CPU `int8` | 3,86 с |
| Whisper Medium, RTX 3060 | 0,44–0,45 с |
| Whisper Turbo, RTX 3060 | 0,34–0,36 с |

Реальная задержка зависит от длины фразы, качества записи, фонового шума, загрузки
GPU и времени определения конца речи.

### Решение проблем

#### Приложение будто бы закрылось

Проверьте System Tray. Главное окно по умолчанию сворачивается туда. Для полного
выхода используйте **Exit** в tray-меню.

#### Не захватывается системный звук

- запустите воспроизведение через выбранное Windows-устройство;
- обновите список устройств и выберите физический выход;
- проверьте, двигается ли индикатор **System**.

#### Используется неправильный микрофон

Откройте **Settings**, обновите устройства и выберите микрофон по имени. В
`config.json` сохраняется имя, а не временный индекс PortAudio.

#### Распознавание работает на CPU

Оставьте **Compute → Auto**. Перед запуском захвата выполняется реальный прогрев
CUDA. Если он завершается ошибкой, приложение записывает причину в лог и включает
CPU `int8`.

#### Нужная речь отбрасывается

Отключите **Ignore other languages** для смешанной или очень короткой речи. Порог
также можно изменить через `language_filter_threshold` в `config.json`.

#### Появился экран загрузки моделей

В конфигурации выбрана модель, которой нет в папке `models`, либо папка сборки
перенесена не целиком. Верните Whisper `turbo`, восстановите полный дистрибутив или
разрешите приложению скачать выбранную модель.

### Настройка среды разработки

Для разработки используются Python 3.11/3.12 x64 и локальное окружение `.venv`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Python 3.14 текущей конфигурацией не поддерживается. Все команды разработки,
диагностики, тестирования и сборки следует выполнять через
`.venv\Scripts\python.exe`.

Запуск из исходников:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

### Тесты и качество кода

```powershell
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
```

### Сборка Windows-дистрибутива

Проект использует PyInstaller one-directory. Для Qt и нативных ML-библиотек этот
формат надёжнее одного самораспаковывающегося EXE.

Перед сборкой установите Git LFS и получите версионируемые файлы из
`model_assets`. Затем выполните:

```powershell
git lfs install
git lfs pull
.\scripts\build.ps1
```

Скрипт:

1. запускает тесты;
2. создаёт `dist\BellenneRelay` через PyInstaller;
3. копирует стандартную конфигурацию;
4. копирует Whisper Turbo и две модели перевода из `model_assets` внутрь
   дистрибутива.

Структура результата:

```text
dist\BellenneRelay\
├── BellenneRelay.exe
├── config.json
├── models\
│   ├── whisper\turbo\
│   └── translation\
│       ├── en-ru\
│       └── ru-en\
└── _internal\
```

Распространять необходимо всю папку `BellenneRelay`.

### Техническая схема

```text
WASAPI system audio / microphone
              │
              ▼
   mono 16 kHz float32 resampling
              │
              ▼
          Silero VAD
              │
              ▼
  определение и фильтрация языка
              │
              ▼
 faster-whisper Turbo (CUDA / CPU int8)
              │
              ▼
      OPUS-MT EN↔RU перевод
              │
              ▼
 основная лента / история / overlay
```

Для системного звука и микрофона используются отдельные capture streams и буферы
VAD. Ограниченная очередь распознавания не позволяет задержке бесконечно расти,
если обработка временно отстаёт от живого звука.
