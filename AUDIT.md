# Technical Blog Audit and Redesign

Audit date: 2026-09-05

## Executive Summary

기존 사이트는 글의 양과 프로젝트 근거는 충분했지만, 홈에 모든 항목을 노출하고 긴 글의 탐색 장치가 부족해 포트폴리오와 기술 문서 양쪽의 강점이 흐려졌습니다. 이번 개선은 사이트를 "운영 노트에 가까운 편집형 기술 출판물"로 정의하고 정보 구조, article UX, 검증 자동화를 함께 정리했습니다.

## P0 Findings

- 긴 한글 제목이 첫 화면을 대부분 차지해 글의 요약과 본문 진입이 늦었습니다.
- 자격증 문제 풀이 문구와 `실시간` 같은 표현이 실제 운영 글의 신뢰도를 낮췄습니다.
- 검색 결과 수, empty state, clear action이 없어 필터 상태를 파악하기 어려웠습니다.
- 생성 파일의 누락과 SEO·fragment·asset 오류를 CI에서 충분히 잡지 못했습니다.

## P1 Findings

- 홈의 전체 글과 프로젝트가 긴 내부 스크롤 영역에 묶여 있었습니다.
- 긴 글에 읽기 시간, 고정 목차, heading anchor, 코드 복사, 이전·다음 글, 관련 글이 없었습니다.
- 프로젝트 설명에서 구현 범위, 검증 결과, 미완료 범위의 구분이 약했습니다.
- 오류 페이지와 전체 글 전용 페이지가 없었습니다.

## Implemented

- 홈을 추천 글, 최신 7개, 대표 프로젝트, 프로필 중심으로 재구성
- 전체 글 archive와 정적 검색·주제 필터·empty state 추가
- 프로젝트 사례 페이지에서 Problem, Implemented, Measured, Validated, Boundary 분리
- article typography, 740px 본문 폭, sticky TOC, anchor, code copy, table overflow 개선
- 읽기 시간, 이전·다음 글, 관련 글을 생성기에 추가
- 404, canonical, Open Graph, Twitter metadata, RSS self link, sitemap coverage 보강
- AWS 운영 제약과 전달 보장에 대한 공식 문서 근거 추가
- 링크, fragment, ID, H1, meta, image alt, TOC, RSS, sitemap 검증 확대
- GitHub Pages 기본 배포와 겹치던 custom deploy를 validation-only workflow로 정리

## Deliberate Non-Goals

- Hosted search: 현재 콘텐츠 규모에서는 정적 검색으로 충분합니다.
- CMS 또는 SPA 전환: 배포와 유지보수 복잡도를 늘릴 이유가 없습니다.
- Dark mode: 핵심 탐색과 article UX보다 우선순위가 낮습니다.
- 무거운 syntax highlighter: 현재 코드 양에서는 언어 표기와 copy control이 더 직접적입니다.
- 확인할 수 없는 성과 수치: 프로젝트에 존재하는 측정값과 실제 사용 범위만 표시합니다.

## Remaining Risks

- 정적 HTML 원문은 구조 변경 시 generator 의존도가 높습니다.
- Mermaid와 GoatCounter는 외부 CDN·API 장애 또는 차단기의 영향을 받습니다.
- 브라우저 검색은 한국어 형태소와 의미 기반 검색을 지원하지 않습니다.
- 기술 글의 모든 AWS 설정은 계정별 정책과 최신 공식 문서를 배포 전에 다시 확인해야 합니다.

## Verification

- Site validator: 30 posts and 3 indexable pages passed
- Long-form article UI: 16 TOC links matched 16 article headings
- Code controls: 20 code blocks matched 20 copy buttons
- Mermaid: 36 of 36 diagrams rendered without fallback errors in the longest RAG article
- Layout: no horizontal document overflow on audited desktop and mobile pages
- Project media: all six lazy-loaded images completed with valid natural dimensions

## Next Priorities

1. 실제 CloudOps RAG 저장소의 benchmark artifact와 블로그 수치를 자동으로 연결합니다.
2. 프로젝트별 ADR, 운영 runbook, 실패 사례를 공개 가능한 범위에서 보강합니다.
3. 콘텐츠가 100개 이상으로 늘면 build-time search index 또는 hosted search를 재평가합니다.
