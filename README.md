# Jiwon Kim's Blog

Jiwon Kim의 기술 블로그입니다. 백엔드, 클라우드, 아키텍처, 운영, 트러블슈팅 기록을 정리합니다.

## 구성

- `index.html`: 블로그 홈, 포스트 목록, 검색/태그 필터
- `styles.css`: 반응형 UI 스타일
- `script.js`: 포스트 검색과 필터링
- `posts/`: HTML 포스트 원문
- `assets/social-card.svg`: 공유 미리보기 기본 이미지
- `scripts/generate_site.py`: 포스트 HTML에서 홈, RSS, sitemap, llms.txt 자동 생성
- `scripts/validate_site.py`: 포스트 목록과 메타 파일 일관성 검증
- `robots.txt`, `sitemap.xml`, `llms.txt`, `feed.xml`: 검색 엔진과 AI 크롤러를 위한 공개 메타 파일
- `.github/workflows/pages.yml`: GitHub Pages 자동 배포

## 새 글 발행 흐름

포스트 HTML을 `posts/`에 추가하거나 수정한 뒤 아래 명령으로 공개 메타 파일을 갱신합니다.

```bash
python3 scripts/generate_site.py
python3 scripts/validate_site.py
```

`generate_site.py`는 각 포스트의 `og:title`, `description`, `article:published_time`, `article:tag`, 본문 요약을 읽어 `index.html`, `feed.xml`, `sitemap.xml`, `llms.txt`를 다시 생성합니다.

## 방문자 수 체크

`index.html` 하단에 GoatCounter 스크립트를 연결해 두었습니다.

```html
<script
  data-goatcounter="https://jiwonkim-blog.goatcounter.com/count"
  async
  src="https://gc.zgo.at/count.js"
></script>
```

실제로 집계하려면 GoatCounter에서 `jiwonkim-blog` 사이트를 만들고 visitor counter 공개 설정을 켜거나, 원하는 분석 도구의 스크립트로 교체하면 됩니다. 홈 화면의 방문자 표시는 GoatCounter public counter API의 `TOTAL` 값을 사용합니다.

AI 방문은 보통 HTML만 가져가고 JavaScript를 실행하지 않으면 집계되지 않습니다. 반대로 AI 브라우저나 렌더러가 JavaScript를 실행하면 일반 방문처럼 집계될 수 있습니다.

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
