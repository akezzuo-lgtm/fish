# Короткие ролики и посты из видео с Агропродмаша

| Папка | Что это | Готовый файл |
|---|---|---|
| `asmr/` | №4: залипательный ролик без слов, 21,5 с, зациклен | `final/agroprodmash-asmr-1080p.mp4` |
| `tips/` | №7: «Как ходить на выставку, чтобы не зря», 5 советов, 32 с | `final/agroprodmash-tips-1080p.mp4` |
| `robot-vs-human/` | №1: сценарий под озвучку, нужны ваши цифры | `robot-vs-human/script.md` |
| `threads/` | №8: 5 постов для Threads с картинками 4:5 | `threads/posts.md`, `threads/post1-5.jpg` |

Пересобрать ролик (пример для asmr):

```bash
python3 tools/cut_edl.py asmr                     # нарезка по asmr/edl.json -> asmr/assets/base.mp4
python3 tools/music.py asmr/assets/music.wav 21.5 chill
cd asmr && npx --yes hyperframes@0.8.111 render --sdr -o renders/asmr.mp4
```
