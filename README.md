# Andrew Kim SWE AWS Solutions Blog

andrewkimswe의 AWS 솔루션, 아키텍처 노트, 트러블슈팅 기록을 위한 정적 개발 블로그입니다.

## 구성

- `index.html`: 블로그 홈, 포스트 목록, 검색/태그 필터
- `styles.css`: 반응형 UI 스타일
- `script.js`: 포스트 검색과 필터링
- `posts/`: Markdown 포스트 원문
- `.github/workflows/pages.yml`: GitHub Pages 자동 배포

## GitHub에 올리는 방법

```bash
git init
git add .
git commit -m "Create AWS solutions blog"
git branch -M main
git remote add origin https://github.com/andrewkimswe/andrewkimswe.github.io.git
git push -u origin main
```

저장소 이름을 `andrewkimswe.github.io`로 만들면 GitHub Pages 주소는 보통 아래처럼 됩니다.

```text
https://andrewkimswe.github.io
```

다른 저장소 이름을 쓰고 싶다면 `blog` 같은 이름으로 만들고 GitHub Pages 설정에서 `GitHub Actions` 배포를 선택하면 됩니다.
