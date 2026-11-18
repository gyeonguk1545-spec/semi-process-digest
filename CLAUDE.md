# CLAUDE.md — semi-process-digest

반도체 공정 기술 뉴스·논문을 매일 수집하고 매주 정리 글을 GitHub Pages(Hugo)에 자동 게시하는 도구.
사용자는 반도체 취업 준비 중인 대학원생(CNT 냉음극 멀티빔 전자원 연구)이며 **Claude Code 초보**다.
사용자와는 **한국어**로 대화한다.

## 진행 방식
- `README.md` 의 단계(0–6)를 따른다. 사용자가 "N단계 해줘"라고 하면 그 단계만 한다.
- 한 단계가 끝나면 README 의 "진행 상황" 체크박스를 갱신하고, 무엇을 만들었는지·사용자가 직접 할 일을 쉬운 말로 설명한다.
- 초보자이므로 명령어를 줄 때는 무엇을 하는지 한 줄 설명을 붙인다.

## 구조 (구독 방식 — API 키 없음)
- 수집: `collector/collect.py` 를 GitHub Actions 가 매일 실행. AI 미사용, 키워드 태그. 결과는 `data/items.jsonl`.
- 요약: Claude Code 예약 작업이 매주 `prompts/weekly_digest.md` 를 따라 주간 글 작성 → `site/content/posts/`. 사용자 구독 사용량을 쓴다.
- 게시: push 시 GitHub Actions 가 Hugo 빌드 → Pages.
- Anthropic API 키·`anthropic` SDK 를 쓰지 않는다. API 방식으로 바꾸려면 사용자에게 별도 결제임을 알리고 확인받는다.

- 기초 강의: Claude Code 예약 작업이 매주 화·목요일 `prompts/study_lesson.md` 를 따라 `site/data/curriculum.yaml` 의 다음 강의를 `site/content/study/<번호>-<slug>/` 에 쓴다.

## 규칙
1. **토큰·비밀번호를 채팅으로 받지 않는다.** 코드·커밋에 비밀 정보를 넣지 않는다.
2. 수집 출처 URL 은 실제로 접속해 확인한 것만 `config/sources.yaml` 에 넣는다. 추측한 URL 금지.
3. 블로그 글에는 원문을 복사하지 않는다. 요약 + 원문 링크만 (저작권).
4. 주간 글 형식·배경 지식·그림 규칙은 `prompts/weekly_digest.md` 를 따른다. 글은 `site/content/posts/<주차>/index.md` (그림과 같은 폴더).
4-1. 그림은 직접 그린 SVG 또는 자유 라이선스(CC·PD) 자료만. 뉴스·기업 자료 그림은 가져오지 않는다. 모든 그림에 출처·라이선스 표기.
5. 주간 글 작업은 구독 사용량을 쓰므로, 수집분이 많으면 제목·요약만 먼저 훑고 상위 항목만 원문 링크를 연다.
6. `git push`, 저장소 생성, GitHub 설정 변경 전에는 사용자 확인을 받는다.
7. 연구실 실험 데이터·사진은 이 저장소에 넣지 않는다.
8. 스케줄(cron)은 UTC 기준. KST 09:00 = UTC 00:00.

## 의존성
python ≥3.10 · feedparser · requests · pyyaml · matplotlib · Hugo(4단계) · Git
로컬 가상환경: `.venv` (`.venv\Scripts\python`), 패키지 목록: `requirements.txt`
