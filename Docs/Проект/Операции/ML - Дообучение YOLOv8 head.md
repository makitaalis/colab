# ML — Дообучение YOLOv8 head (процесс и контроль)

Цель: воспроизводимо дообучать head-detector (1 класс `head`) и **вести полную статистику** (что делали, стало лучше/хуже, почему).

Эта инструкция описывает процесс обучения на ПК с GPU (не на OPi) и формат фиксации результатов.

## Официальные ссылки (канон)

- Ultralytics Docs (общая): `https://docs.ultralytics.com/`
- Datasets (Detect / `data.yaml`): `https://docs.ultralytics.com/datasets/detect/`
- Training (CLI/args): `https://docs.ultralytics.com/modes/train/`
- YOLO CLI config reference: `https://docs.ultralytics.com/usage/cfg/`

## 0) Где храним всё (структура)

### 0.1 Runbook (канон, в git)

- Этот файл: `Docs/Проект/Операции/ML - Дообучение YOLOv8 head.md`

### 0.2 Авто-логи (локально, не коммитятся)

Логи и результаты каждого прогона складываются в:

- `Docs/auto/ml-training/yolov8-head/<UTC>_<label>/`

Там обязательно должны быть:
- `preflight.json` (проверка окружения + датасета)
- `command.sh` (точная команда запуска)
- `train.log` (если запускали обучение)
- `results/` (копии `results.csv/args.yaml/results.png/confusion_matrix*.png`, `best.pt/last.pt`, `summary.md`)

Дополнительно (сводка всех прогонов):
- `Docs/auto/ml-training/yolov8-head/REPORT.md` (генерируется `scripts/yolo_runs_report.py`)

### 0.3 Рабочая папка обучения (локально)

- `ml/yolov8_head_finetune/` (workspace, см. README)
- Базовые веса для старта складываем в `ml/yolov8_head_finetune/weights/base/` (чтобы исходник в `mvp/models/src/` не трогать).

## 1) Preflight перед обучением (обязателен)

Перед любым запуском:

1) Убедиться, что датасет-конфиг корректный:
- используем `ml/yolov8_head_finetune/data_head.yaml` (с `path:`),
- класс **0 = head**.

2) Выполнить preflight:

```bash
python3 scripts/yolo_train_preflight.py \
  --dataset /home/alis/Документы/DataSet/brainwash.v1i.yolov8 \
  --data-yaml ml/yolov8_head_finetune/data_head.yaml \
  --base-weights ml/yolov8_head_finetune/weights/base/yolov8_head_scut_nano.pt \
  --out /tmp/yolo_preflight.json
```

Если `ok=false` или есть `issues[]` — обучение не начинаем.

## 2) План “безболезненного” дообучения (итерации)

Рекомендуемый порядок:

0) **Smoke**: 1 эпоха, чтобы поймать ошибки окружения/датасета.

1) **Baseline (короткий) @640 на текущих split**: быстрый sanity-check метрик и стабильности обучения.
- `imgsz=640`, `epochs=10`, `batch=auto`, `seed=0`.

2) **Baseline (короткий) @416 на текущих split**: оценить деградацию/выигрыш на “целевом” размере.
- `imgsz=416`, `epochs=10`, `batch=auto`, `seed=0`.

3) **Anti-leak пересборка split** (перед “длинными” прогонами).

4) **Baseline (длинный) на anti-leak**: 1–2 длинных прогона (например, `epochs=80`) и только потом тюнинг.

5) **Сравнение**: сравнивать только по `valid`, `test` использовать 1 раз как “последняя проверка”.

4) **Улучшения** (по одному изменению за итерацию):
- `imgsz` (416↔640),
- размер модели (`yolov8n` → `yolov8s`, если FPS/память позволяют),
- датасет (добавление негативов/сложных сцен, исправление разметки),
- гиперпараметры (только после стабилизации данных).

### 2.1 Anti-leak split (рекомендуется перед “длинными” прогонами)

Если `train/valid/test` получились из видео/серийных кадров, есть риск leakage (почти одинаковые кадры в разных split) → метрики будут завышены.

В проекте есть rebuild-скрипт, который пересобирает split так, чтобы “группа” (числовой префикс имени файла до `_`) не пересекалась между split:

```bash
./scripts/yolo_antileak_run.sh --label brainwash_v1i
```

Результат:
- новый датасет: `/home/alis/Документы/DataSet/brainwash.v1i.yolov8_antileak/`
- YAML для обучения: `/home/alis/Документы/DataSet/brainwash.v1i.yolov8_antileak/data.yaml`
- отчёт: `Docs/auto/ml-training/yolov8-head/antileak/.../report.json`

Дальше для обучения на anti-leak датасете используйте `--dataset` + `--data`:

```bash
./scripts/yolo_train_run.sh \
  --name baseline640_antileak_e10 \
  --dataset /home/alis/Документы/DataSet/brainwash.v1i.yolov8_antileak \
  --data /home/alis/Документы/DataSet/brainwash.v1i.yolov8_antileak/data.yaml \
  --imgsz 640 --epochs 10 --batch auto --execute
```

## 3) Единый способ запуска (с авто-документацией)

Подготовить run (без запуска):

```bash
./scripts/yolo_train_run.sh --name baseline640 --imgsz 640 --epochs 80
```

Запустить обучение:

```bash
./scripts/yolo_train_run.sh --name baseline640 --imgsz 640 --epochs 80 --execute
```

Все артефакты и статистика складываются автоматически в `Docs/auto/ml-training/yolov8-head/...`.

### 3.1 Пауза и продолжение (resume)

“Пауза” как в IDE отсутствует, но обучение можно **безопасно остановить** и потом **продолжить** с `last.pt`.

- Остановка: в терминале с обучением нажать `Ctrl+C` (SIGINT). Желательно дождаться конца текущей эпохи/итерации (чтобы `last.pt` точно успел сохраниться).
- Продолжение: запуск с `resume=True` и указанием `model=<.../weights/last.pt>`.

Как найти `last.pt`:
- `ml/yolov8_head_finetune/runs/<run_name>/weights/last.pt`
- либо копия в `Docs/auto/ml-training/yolov8-head/<...>/results/last.pt`

Пример (продолжить конкретный прогон):

```bash
.venv/bin/yolo detect train resume=True \
  model=ml/yolov8_head_finetune/runs/<run_name>/weights/last.pt \
  device=0
```

Или в проекте есть удобный враппер, который:
- использует `systemd-inhibit` (если доступно), чтобы ПК не ушёл в сон,
- дописывает лог в `Docs/auto/.../train.log`,
- после завершения собирает артефакты в `Docs/auto/.../results/`:

```bash
./scripts/yolo_train_resume.sh --id <UTC>_<label>
```

Важно:
- Не останавливать через `kill -9` (можно повредить чекпоинт).
- При `resume=True` параметры берутся из `args.yaml` того же run — это хорошо для воспроизводимости, но **если хотите поменять imgsz/датасет/гиперы**, делайте новый прогон от `best.pt` (не resume).

## 4) Подводные камни (и как избегать)

1) **Неверные пути в исходном Roboflow `data.yaml`**  
Roboflow часто пишет `train: ../train/images` — это ломает запуск, если `data.yaml` лежит в корне датасета.  
Решение: используем `ml/yolov8_head_finetune/data_head.yaml` с `path:`.

2) **Leakage между train/valid/test (кадры из одного видео в разных split)**  
Даёт завышенные метрики и провалы на реальном транспорте.  
Решение: держать split “группами” (по видео/сцене/временному диапазону).  
Preflight выводит предупреждение по пересечению числовых префиксов имён.

3) **Негативные примеры**  
Если в датасете почти нет кадров “без голов”, модель может давать много ложных.  
Решение: добавить часть пустых label-файлов (изображения без объектов) или отдельный negative split.

4) **Мелкие объекты**  
При `imgsz=416` голова может быть слишком маленькой → ухудшение recall.  
Решение: A/B `416 vs 640` и сравнение на реальных сценах.

5) **Сравнение прогонов “на глаз”**  
Решение: сравнивать только по авто-логам: `preflight.json` + `results.csv` + `summary.md`.

6) **Лицензия датасета/весов**  
Перед использованием в проде всегда фиксировать лицензию источников (датасет/веса/код) и совместимость с коммерческим использованием.

7) **Совместимость зависимостей (NumPy 2.x)**  
Если `yolo train` падает на этапе валидации с ошибкой про `numpy.trapz`, значит версия Ultralytics несовместима с NumPy 2.x.  
Решение: обновить Ultralytics в `.venv` (или альтернативно закрепить NumPy `<2`), затем повторить smoke-run.

## 5) Что нужно для более качественного обучения (влияние по убыванию)

1) **Данные “как в проде”**  
Для задачи “пассажиры круглый год” обязательно покрыть условия:
- зима: капюшоны/шапки, шарфы, сильные окклюзии,
- ночь/сумерки/контровой свет, блики, дождь/снег,
- разные камеры/ракурсы/высоты/экспозиции (если есть).

2) **Чёткое правило разметки**  
Например: “капюшон без лица = `head`” → такие объекты **всегда размечаем как `head`** по одному правилу bbox.  
Если правила нет — модель будет “учиться” противоречиям.

3) **Негативные примеры (пустые кадры)**  
Если в `train` нет пустых label-файлов (`empty_labels=0`), в проде обычно растут ложные срабатывания.  
Добавляйте кадры без голов как изображения с пустым `.txt` (и соблюдайте anti-leak принципы при split).

4) **Hard negatives / hard positives (итеративно)**  
Собирайте ошибки с реального пайплайна (FP на сиденьях/поручнях/плакатах, FN на капюшонах/поворотах головы), размечайте и добавляйте в train.

5) **Честная оценка (anti-leak + тематические eval-наборы)**  
Длинные прогоны и финальные решения делайте только на anti-leak split.  
Дополнительно держите отдельные “winter/night” eval-наборы без пересечений с train (по видео/серии/сцене).

6) **Только потом — тюнинг гиперпараметров**  
Сначала стабилизировать данные/сплиты/правило разметки, затем уже менять `imgsz`, `epochs`, модель (`n/s`) и прочее.
