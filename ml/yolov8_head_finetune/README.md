# YOLOv8 head — дообучение (рабочая папка)

Эта папка — локальный workspace для обучения/дообучения YOLOv8 head detector.

Цели:
- изолировать обучение от `mvp/` (чтобы не ломать продовые артефакты);
- фиксировать воспроизводимые команды и результаты;
- складывать “тяжёлые” артефакты (runs/weights) локально (обычно не коммитятся).

Связанные документы:
- Runbook: `Docs/Проект/Операции/ML - Дообучение YOLOv8 head.md`
- Авто-логи прогонов (локально): `Docs/auto/ml-training/yolov8-head/`

Содержимое:
- `data_head.yaml` — датасет-конфиг для Ultralytics (с `path:`).
- `weights/` — локальные веса (base/best/last и т.п.).
- `runs/` — вывод Ultralytics (`project=...` направляем сюда).

Colab:
- Runbook: `Docs/Проект/Операции/ML - Дообучение YOLOv8 head (Google Colab).md`
- Notebook: `colab/yolo_head_runner.ipynb`
