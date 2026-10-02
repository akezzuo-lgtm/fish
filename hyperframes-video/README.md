# hyperframes-video

Тот же ролик, что в `../video` (Remotion), но на [HyperFrames](https://github.com/heygen-com/hyperframes):
обычный HTML + CSS, анимация на GSAP. 11 секунд, 1920×1080, 30 fps.

Монтаж — в `index.html`: сцены — это элементы с `data-start` / `data-duration`,
движение — один GSAP-таймлайн, который рендерер прокручивает покадрово.
GSAP лежит локально в `assets/`, чтобы рендер не зависел от сети.

```bash
npm run dev      # студия с таймлайном в браузере
npm run check    # линт + проверка рантайма и вёрстки
npm run render   # renders/hyperframes-video.mp4
```

Нужны Node.js 22+ и FFmpeg.
