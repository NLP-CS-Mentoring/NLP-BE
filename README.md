# NLP-BE
> **자기소개서 생성 및 첨삭 AI 기능**을 담당  
> 사용자의 경험을 받고 어투를 적용한 개인 맞춤형 자기소개서 생성기

## 기능
1. 사용자의 경험만 받아 표준 스타일로 자소서를 생성
2. 파일을 포함해 PDF나 TXT 파일을 업로드받아 말투를 분석한 후, 그 스타일로 자소서를 생성

## 버전(파일 캐싱)
1. 프로그램 내부 메모리 사용 캐싱
2. Redis를 이용한 캐싱

## 버전에 따른 실행
1. main.py 실행
2. Redis를 실행하고 main_redis.py 실행

## .env 예시(Docker에서 Redis 실행)
```
OPENAI_API_KEY=SECRETKEY
REDIS_URL=redis://localhost:6379
```

## docker-compose.yml 예시
```
services:
  redis:
    image: redis:8.4.0
    container_name: redis
    ports:
      - "6379:6379"
```
