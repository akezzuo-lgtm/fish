# fish-video

Тестовый ролик на [Remotion](https://www.remotion.dev/): 11 секунд, 1920×1080, 30 fps.

Монтаж описан кодом в `src/FishVideo.tsx`: три сцены (`Sequence`) на таймлайне, переходы — кроссфейды.
Вся анимация считается от номера кадра (`useCurrentFrame`, `interpolate`, `spring`).

```bash
npm install
npm run studio   # редактор с таймлайном в браузере
npm run render   # out/fish.mp4
npm run still    # один кадр в out/frame.png
```
