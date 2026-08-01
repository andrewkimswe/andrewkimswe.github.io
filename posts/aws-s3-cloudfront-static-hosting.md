---
title: "S3와 CloudFront로 정적 블로그 배포하기"
date: "2026-08-31"
tags: ["AWS", "S3", "CloudFront", "Route53"]
---

# S3와 CloudFront로 정적 블로그 배포하기

## 목표

정적 파일로 빌드된 블로그를 S3에 업로드하고 CloudFront로 전 세계에 캐싱해 빠르게 제공한다.

## 아키텍처

- 사용자는 Route 53에 연결된 도메인으로 접속한다.
- CloudFront가 HTTPS와 캐싱을 담당한다.
- S3 버킷은 원본 저장소 역할만 한다.
- ACM 인증서는 CloudFront용으로 `us-east-1` 리전에 만든다.

## 구현 순서

1. S3 버킷을 만들고 정적 파일을 업로드한다.
2. CloudFront 배포를 만들고 S3를 origin으로 연결한다.
3. OAC 또는 OAI로 CloudFront만 S3에 접근하게 제한한다.
4. Route 53에서 도메인 A 레코드를 CloudFront로 연결한다.
5. 캐시 정책과 invalidation 전략을 정한다.

## 체크 포인트

- S3 버킷을 public으로 열지 않는다.
- CloudFront 기본 루트 객체를 `index.html`로 설정한다.
- SPA 라우팅이 필요하면 403/404 응답을 `index.html`로 매핑한다.
- 배포 후 변경 파일만 캐시 무효화할 수 있도록 파일명 해시 전략을 사용한다.

## 배운 점

정적 블로그라도 보안 경계는 S3가 아니라 CloudFront에 두는 편이 운영하기 편하다.
