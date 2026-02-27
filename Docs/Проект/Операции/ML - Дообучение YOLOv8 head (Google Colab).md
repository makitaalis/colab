# ML — Дообучение YOLOv8 head (Google Colab)

Цель: запускать обучение/дообучение **из этого репозитория** в Google Colab (GPU), сохраняя:
- код — в GitHub,
- датасет и артефакты прогонов (`runs/`, `best.pt/last.pt`, авто‑логи) — в Google Drive (чтобы не потерять при разрыве сессии).

Эта инструкция опирается на существующие врапперы проекта:
- `scripts/yolo_train_run.sh` — запуск обучения + авто‑документация в `Docs/auto/...`
- `scripts/yolo_train_resume.sh` — корректный resume с `last.pt`
- `scripts/yolo_train_preflight.py` — обязательная проверка датасета/окружения
- `scripts/yolo_antileak_run.sh` — пересборка split без leakage (опционально, но рекомендуется перед “длинными” прогонами)

Рекомендуемый способ в Colab: открыть ноутбук из репозитория:
- `colab/yolo_head_runner.ipynb`

## 0) Датасет: локально на ПК → в Colab

Colab **не видит** локальный путь на ПК вида `/home/alis/Документы/...`. Для обучения датасет нужно положить в место, доступное Colab (обычно Google Drive).

Ниже 2 рабочих варианта.

### Вариант A (просто, но медленнее): загрузить папку датасета в Drive

1) В браузере откройте Google Drive → создайте папку, например:
`MyDrive/OrangePi_passangers_ml/datasets/brainwash.v1i.yolov8/`
2) Загрузите туда содержимое локальной папки:
`/home/alis/Документы/DataSet/brainwash.v1i.yolov8/`

Плюс: просто. Минус: много мелких файлов → Drive/Colab могут работать заметно медленнее.

### Вариант B (рекомендуется): упаковать датасет в архив и распаковывать в `/content`

На ПК (Linux) упаковать:

```bash
cd "/home/alis/Документы/DataSet"
tar -czf brainwash.v1i.yolov8.tgz brainwash.v1i.yolov8
```

Загрузить `brainwash.v1i.yolov8.tgz` в Drive, например в:
`MyDrive/OrangePi_passangers_ml/datasets_archives/brainwash.v1i.yolov8.tgz`

В Colab ноутбук распакует архив в `/content/datasets/...` и будет обучать **с локального диска Colab** (обычно быстрее и стабильнее, чем читать тысячи файлов напрямую из Drive).

## 1) Что нужно заранее (в Google Drive)

### 0.1 Датасет (Roboflow/Ultralytics layout)

Датасет должен лежать в Drive и иметь структуру:

```text
<DATASET_ROOT>/
  train/images  + train/labels
  valid/images  + valid/labels
  test/images   + test/labels
```

Формат меток: YOLO txt (class_id x y w h, нормализованные 0..1).

### 0.2 Где хранить результаты (рекомендуется)

Создайте в Drive папку, например:

```text
/content/drive/MyDrive/OrangePi_passangers_ml/
  datasets/
  artifacts/
```

Дальше в ноутбуке/командах используйте:
- датасет: `/content/drive/MyDrive/OrangePi_passangers_ml/datasets/<dataset_name>`
- артефакты: `/content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/`

## 1) Настройка Colab (точная последовательность)

### 1.1 Включить GPU

`Runtime → Change runtime type → GPU`.

### 1.2 Подключить Google Drive (делаем первым)

```python
from google.colab import drive
drive.mount("/content/drive")
```

### 1.3 Клонировать репозиторий

> Если репозиторий приватный — используйте GitHub Token (PAT) и клонирование по HTTPS.

```bash
%cd /content
!rm -rf OrangePi_passangers
!git clone --depth 1 https://github.com/makitaalis/colab.git OrangePi_passangers
%cd OrangePi_passangers
!git rev-parse --short HEAD
```

### 1.4 Установить зависимости для обучения

В проекте обучение проверено с `ultralytics==8.4.14` (локальная `.venv` в репозитории).
В Colab фиксируем ту же версию (а `torch` берём colab‑овский, чтобы не ломать CUDA‑окружение):

```bash
!python -V
!nvidia-smi -L
!pip -q install ultralytics==8.4.14
!python -c "import torch, ultralytics, numpy as np; print('torch', torch.__version__); print('ultralytics', ultralytics.__version__); print('numpy', np.__version__)"
```

### 1.5 Настроить “персистентные” папки (чтобы не потерять прогоны)

Самое важное: сохранить **и** `Docs/auto/...` (авто‑логи), **и** `ml/yolov8_head_finetune/runs/...` (Ultralytics run dir) в Drive.

Вариант “рекомендуется”: сделать симлинки внутри клон‑репозитория на Drive:

```bash
!mkdir -p /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head
!mkdir -p /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/Docs_auto
!mkdir -p /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/runs

!rm -rf Docs/auto
!ln -s /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/Docs_auto Docs/auto

!rm -rf ml/yolov8_head_finetune/runs
!mkdir -p ml/yolov8_head_finetune
!ln -s /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/runs ml/yolov8_head_finetune/runs
```

## 2) Запуск обучения (через враппер проекта)

### 2.1 Подготовить корректный `data.yaml` для Colab

В репозитории есть `ml/yolov8_head_finetune/data_head.yaml`, но в нём локальный путь (`/home/alis/...`) — для Colab он **не подходит**.

Создайте отдельный YAML в Drive (или в `/content`) с правильным `path:`:

```python
from pathlib import Path

DATASET_ROOT = Path("/content/drive/MyDrive/OrangePi_passangers_ml/datasets/brainwash.v1i.yolov8")  # <-- поменяй
DATA_YAML = Path("/content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/data_head_colab.yaml")

DATA_YAML.write_text(
    "\n".join(
        [
            "path: " + str(DATASET_ROOT),
            "train: train/images",
            "val: valid/images",
            "test: test/images",
            "",
            "names:",
            "  0: head",
            "",
        ]
    ),
    encoding="utf-8",
)
print("Wrote:", DATA_YAML)
```

### 2.2 Smoke‑run (1 эпоха)

```bash
!bash scripts/yolo_train_run.sh \
  --name smoke_colab_e1_640 \
  --dataset /content/drive/MyDrive/OrangePi_passangers_ml/datasets/brainwash.v1i.yolov8 \
  --data /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/data_head_colab.yaml \
  --model ml/yolov8_head_finetune/weights/base/yolov8_head_scut_nano.pt \
  --imgsz 640 --epochs 1 --batch auto --device 0 --workers 2 \
  --execute
```

После выполнения:
- Ultralytics run dir (в Drive): `.../artifacts/yolov8-head/runs/<UTC>_smoke_colab_e1_640/`
- Авто‑лог (в Drive): `.../artifacts/yolov8-head/Docs_auto/ml-training/yolov8-head/<UTC>_smoke_colab_e1_640/`

ID последнего прогона:

```bash
!cat Docs/auto/ml-training/yolov8-head/_latest.txt
```

### 2.3 Длинный прогон

```bash
!bash scripts/yolo_train_run.sh \
  --name long_colab_e80_640 \
  --dataset /content/drive/MyDrive/OrangePi_passangers_ml/datasets/brainwash.v1i.yolov8 \
  --data /content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/data_head_colab.yaml \
  --model ml/yolov8_head_finetune/weights/base/yolov8_head_scut_nano.pt \
  --imgsz 640 --epochs 80 --batch auto --device 0 --workers 2 \
  --execute
```

### 2.4 Resume после разрыва сессии

1) Узнайте ID (например, из `Docs/auto/.../_latest.txt` или по папке в Drive).
2) Запустите:

```bash
!bash scripts/yolo_train_resume.sh --id <UTC>_<label> --device 0
```

Важно: `resume=True` продолжает *тот же* run (берёт параметры из `args.yaml`). Если хотите менять `imgsz/датасет/гиперы` — делайте **новый** прогон от `best.pt`.

## 3) Anti‑leak split (опционально, но рекомендуется перед “длинными” прогонами)

Суть: если кадры из одного видео попали в разные split, метрики будут завышены.

В Colab используйте режим `copy` (hardlink в Drive может не работать/быть неэффективным):

```bash
!bash scripts/yolo_antileak_run.sh \
  --label brainwash_colab \
  --src /content/drive/MyDrive/OrangePi_passangers_ml/datasets/brainwash.v1i.yolov8 \
  --dst /content/drive/MyDrive/OrangePi_passangers_ml/datasets/brainwash.v1i.yolov8_antileak \
  --mode copy
```

Дальше обучайте на `.../brainwash.v1i.yolov8_antileak/data.yaml` (он будет создан скриптом).

## 4) Экспорт для деплоя (что можно/нельзя в Colab)

### 4.1 Можно в Colab: экспорт `best.pt -> onnx`

```python
from ultralytics import YOLO
model = YOLO("/content/drive/MyDrive/OrangePi_passangers_ml/artifacts/yolov8-head/runs/<RUN_ID>/weights/best.pt")
out = model.export(format="onnx", imgsz=416, dynamic=False, opset=18)
print("Exported:", out)
```

### 4.2 Нельзя “как есть” в Colab: сборка `*.rvc2.tar.xz` через Docker ModelConverter

В проекте конвертация в Luxonis NNArchive сделана через Docker:
- `scripts/model_convert_yolov8_to_rvc2_nnarchive.sh`

Обычно в Colab **нет рабочего Docker‑рантайма**, поэтому этот шаг выполняйте на машине/сервере с Docker (локально или удалённый ПК).
