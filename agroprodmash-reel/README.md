# Агропродмаш 2026 — рилс глазами посетителя

Вертикальный ролик 1080×1920, 59,5 с, 30 fps, с авторской озвучкой и субтитрами по словам.

## Как собран

1. `tools/transcribe.py` — распознаёт дубль 1 из `../озвучка агропродмаш.MOV` моделью GigaAM v2
   и сохраняет таймкоды слов в `assets/vo/take1_words.json`.
2. `tools/voice.py` — собирает озвучку: берёт фразы по номерам слов, вырезает оговорки и длинные паузы,
   ускоряет речь на 12% без изменения тембра, чистит звук. Каждая глава начинается на долю такта.
   Пишет `assets/vo.wav` и таймлайн `assets/timeline.json` / `assets/timeline.js`.
3. `tools/make_music.py` — синтезирует трек 128 BPM под структуру таймлайна (хук → подводка → дроп по главам → финал).
4. `npm run mix` — сводит музыку и голос, музыка автоматически приглушается под речь (`assets/mix.wav`).
5. `tools/cut.py` — нарезка: кадры в каждой главе, ключевые кадры привязаны к словам
   («заходим», «бригада», «конфеты», «шоколад», «мясорубки»…). Пишет `assets/base.mp4` и `assets/shots.js`.
6. `index.html` — композиция HyperFrames: субтитры-караоке, заставка, главы, панчи и whip-переходы, финальный CTA.

## Пересобрать

```bash
npm run voice && npm run music && npm run mix && npm run cut
npm run check
npm run render   # renders/agroprodmash-reel-vo.mp4
```

Нужны Node.js 22+, FFmpeg и Python 3 с numpy, scipy, soundfile (и sherpa-onnx для распознавания).

- Поменять фразы озвучки — `SECTIONS` в `tools/voice.py` (номера слов из `take1_words.json`).
- Поменять кадры — `SHOTS` в `tools/cut.py`.
- Выделение и эмодзи в субтитрах — `EMPH` и `EMOJI` в `index.html`.
