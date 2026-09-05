# Jiwon Kim Engineering Notes

백엔드 시스템, AWS 인프라, RAG 평가, 아키텍처 의사결정을 구현과 운영의 관점에서 기록하는 정적 기술 블로그입니다.

## Information Architecture

- `index.html`: 관점, 추천 글, 최근 글, 대표 프로젝트를 보여주는 홈
- `articles.html`: 전체 글의 정적 검색 및 주제 필터
- `projects.html`: 구현 범위, 검증 결과, 한계를 구분한 프로젝트 사례
- `posts/`: HTML 포스트 원문
- `404.html`: GitHub Pages용 오류 화면
- `styles.css`: 공통 레이아웃, article typography, 반응형 스타일
- `script.js`: 검색, 필터, TOC, 코드 복사, Mermaid, 방문 통계
- `scripts/generate_site.py`: 목록, TOC, 읽기 시간, 글 이동, 관련 글, RSS, sitemap, `llms.txt` 생성
- `scripts/validate_site.py`: HTML 구조, SEO, 내부 링크, 접근성 기본값, 생성 결과 일관성 검증

## Design Principles

1. 운영 노트에 가까운 편집형 기술 출판물로 보이게 한다.
2. 홈은 모든 콘텐츠를 쌓지 않고, 추천과 최신 항목에서 전용 목록으로 연결한다.
3. 긴 글은 740px 안팎의 읽기 폭, 고정 목차, 명확한 코드와 다이어그램 계층을 유지한다.
4. 프로젝트는 문제, 구현, 측정, 검증, 한계를 분리하고 확인되지 않은 성과를 만들지 않는다.
5. 장식보다 탐색, 비교, 출처 확인, 다음 글 이동 같은 반복 작업을 우선한다.

## Content Contract

새 포스트는 `posts/*.html`에 추가하며 다음 정보를 포함해야 합니다.

- 정확히 하나의 `h1`
- `description`, canonical, Open Graph, Twitter metadata
- `article:published_time`, `article:modified_time`, `article:tag`
- `.article-body` 안의 의미 있는 `h2` 구조
- 이미지의 설명 가능한 `alt` 텍스트
- 구현 근거와 검증 방법, 필요한 경우 공식 문서 링크

글 목록, 목차, 읽기 시간, 이전·다음 글, 관련 글은 직접 편집하지 않고 생성기로 갱신합니다.

```bash
python3 scripts/generate_site.py
python3 scripts/validate_site.py
node --check script.js
git diff --check
```

생성기는 날짜와 slug를 함께 사용해 순서를 결정하므로 같은 날짜의 글도 매번 동일하게 정렬됩니다. 홈에는 최신 7개만 두고 전체 글은 `articles.html`에서 찾습니다.

## Search Decision

현재 30개 글 규모에서는 외부 검색 서비스나 CMS보다 브라우저 내 정적 검색이 적절합니다. 제목, 요약, 태그를 대상으로 즉시 필터링하며 네트워크 의존성과 별도 인덱싱 작업이 없습니다.

## Analytics

GoatCounter 스크립트와 public counter API를 사용합니다. 설정에서 visitor counter 공개가 허용되어야 숫자가 표시되며, 차단기나 JavaScript 비활성화 환경에서는 집계 또는 화면 표시가 누락될 수 있습니다. JavaScript를 실행하지 않는 AI crawler는 일반적으로 이 카운터에 포함되지 않습니다.

## Publishing

`main` push 시 GitHub Pages의 branch 배포가 정적 파일을 게시합니다. `.github/workflows/pages.yml`은 별도 배포를 중복 실행하지 않고, 생성기를 다시 실행한 뒤 diff가 없는지와 validator, JavaScript syntax를 확인합니다.

## Known Limits

- 포스트 원문이 HTML이라 공통 article chrome은 생성기로 동기화합니다.
- Mermaid renderer는 CDN에 의존하므로 차단 환경에서는 원문 다이어그램 코드를 fallback으로 보여줍니다.
- 검색은 substring 기반이며 형태소 분석, 오타 교정, 랭킹 모델은 없습니다.
- GoatCounter 표시는 제3자 script와 public API 가용성에 영향을 받습니다.
- 별도 CMS, dark mode, client-side router는 현재 규모에서 운영 복잡도 대비 이득이 작아 두지 않았습니다.
