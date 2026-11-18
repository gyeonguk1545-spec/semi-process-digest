# semi-process-digest — 반도체 공정 기술 주간 다이제스트

반도체 공정 기술 뉴스·논문을 **매일 자동 수집**하고, Claude 로 **분류·요약**해서
**매주 한 편**의 정리 글을 GitHub Pages 블로그에 자동으로 올리는 도구.

**API 키 없이 Claude 구독(Pro/Max)만으로 돌아가게** 설계했다.
수집은 AI 가 필요 없어 GitHub Actions 가 무료로 하고, 요약·글쓰기는 Claude Code 예약 작업이 구독 안에서 한다.

목표는 "자동 요약 모음"이 아니라 **취업 준비용 학습 노트**다.
그래서 주간 글마다 *면접 예상 질문*, *내 연구(CNT 냉음극 멀티빔 전자원)와의 연결*, *내 코멘트* 칸을 둔다.

---

## 전체 흐름

```
① 수집 — GitHub Actions (매일 09:00 KST, 무료, AI 안 씀)
   RSS·arXiv 수집 ─▶ 키워드로 공정 태그 ─▶ 중복 제거 ─▶ data/items.jsonl 커밋

② 요약 — Claude Code 예약 작업 (매주 월요일, 구독 사용량으로)
   이번 주 수집분 읽기 ─▶ 중요도 선별 ─▶ 주간 정리 글 작성 ─▶ site/content/posts/*.md 커밋·푸시

③ 게시 — GitHub Actions
   push 감지 ─▶ Hugo 빌드 ─▶ GitHub Pages 자동 배포
                     (좋은 글만 직접 Tistory 로 옮겨 쓰기)
```

| 부분 | 누가 | 비용 |
|---|---|---|
| 수집 ① · 게시 ③ | GitHub Actions | 무료 (공개 저장소) |
| 요약 ② | Claude Code (내 구독) | 추가 결제 없음 — 구독 사용량 한도를 평소 사용과 공유 |

> Tistory 는 2024년에 Open API 를 종료해서 자동 게시가 안 된다. 그래서 자동 게시는 GitHub Pages 에 하고,
> Tistory 에는 손으로 다듬은 글만 옮긴다.

## 폴더 구조

```
semi-process-digest/
├─ README.md              ← 지금 이 문서 (진행 가이드)
├─ CLAUDE.md              ← Claude Code 가 매번 먼저 읽는 프로젝트 규칙
├─ collector/             ← 수집 파이썬 코드                     (2단계)
├─ config/                ← 수집 출처 목록, 공정 분류 체계(태그)   (2단계)
├─ prompts/               ← 주간 글 작성 지시문 (Claude Code 가 읽음) (3단계)
├─ data/                  ← 수집 기록 items.jsonl (텍스트라 git 으로 변화 추적 가능)
├─ site/                  ← Hugo 블로그. content/posts/ 에 주간 글이 쌓임 (4단계)
└─ .github/workflows/     ← 자동 실행 스케줄(cron)               (5단계)
```

---

## 결과물은 어디에 생기나 (파일 위치 모음)

프로젝트 폴더: `C:\Users\김경욱\Downloads\semi-process-digest`

| 무엇 | 위치 | 언제 생기나 |
|---|---|---|
| **주간 정리 글 (읽을 것)** | `site\content\posts\<주차>\index.md` (예: `2026-W47\index.md`) | 매주 |
| 그 주 글의 그림 | 같은 폴더 `site\content\posts\<주차>\` (*.svg, *.jpg, 출처 기록 `figures_sources.json`) | 매주 |
| 블로그 미리보기 (내 PC) | http://localhost:1313/semi-process-digest/ (아래 4단계 명령 실행 중일 때만) | — |
| 블로그 디자인 | `site\layouts\` (HTML 틀), `site\static\css\main.css` (스타일) | — |
| 주간 글 입력 목록 | `data\weekly\<주차>_input.md` | 매주, 글 쓰기 직전 |
| 수집 원본 데이터 | `data\items\<연-월>.jsonl` (예: `2026-11.jsonl`) | 매일 |
| 수집 출처 목록 (편집 가능) | `config\sources.yaml` | — |
| 공정 태그·키워드 (편집 가능) | `config\taxonomy.yaml` | — |
| 주간 글 작성 지시문 (편집 가능) | `prompts\weekly_digest.md` | — |
| **블로그 주소** | https://gyeonguk1545-spec.github.io/semi-process-digest/ | 글이 push 되면 1~2분 뒤 반영 |

주차는 ISO 기준(월요일 시작). 예: 2026-11-17 은 `2026-W47`.

---

## 처음 해보는 사람을 위한 단계별 가이드

각 단계는 **"내가 할 일"** 과 **"Claude 에게 이렇게 말하기"** 로 나눴다.
한 단계가 끝나면 아래 체크박스에 표시하자.

### 0단계 — Claude Code 사용법 (5분)

Claude Code 는 **대화로 코딩을 시키는 도구**다. 지금 쓰고 있는 Claude 데스크톱 앱의 **Code 탭**이 바로 그것이다.

1. **폴더 열기**: 새 세션을 시작할 때 작업 폴더로 `Downloads\semi-process-digest` 를 고른다.
   그러면 Claude 가 이 폴더의 `CLAUDE.md` 를 자동으로 읽고 프로젝트 맥락을 이해한다.
2. **말로 요청하기**: "2단계 해줘"처럼 한국어로 말하면 된다. 이 README 의 단계 번호를 말하면 가장 정확하다.
3. **승인하기**: Claude 가 파일을 만들거나 명령을 실행하기 전에 허락을 묻는 창이 뜬다.
   내용을 읽어보고 괜찮으면 허용한다. 모르겠으면 "이게 뭐하는 거야?"라고 물어보면 된다.
4. **확인하기**: 만들어진 파일은 왼쪽 파일 창에서 열어볼 수 있다. 결과가 이상하면 그대로 말하면 고쳐준다.
5. **팁**
   - 한 번에 한 단계씩 시키는 게 좋다. 한꺼번에 시키면 확인하기 어렵다.
   - 비밀번호·토큰은 **채팅창에 붙여넣지 말 것.**
   - 세션의 작업 폴더를 `semi-process-digest` 로 열어야 `CLAUDE.md` 가 자동으로 읽힌다.
     상위 폴더(`Downloads`)로 열어도 작업은 되지만, 그때는 "semi-process-digest 작업 이어서 해줘"라고 말해주자.

### 1단계 — 준비물 설치·가입 (내가 직접, 20분)

- [x] **Python** — 설치되어 있음 (3.12)
- [x] **Git** — 설치됨 (2.56)
- [x] **GitHub 계정** — https://github.com
- [x] **Claude 구독** — 이미 사용 중. **API 키는 필요 없다.**
  (나중에 PC 를 켜두지 않고 완전 자동으로 돌리고 싶어지면 그때 API 방식으로 바꿀 수 있다. 그건 별도 결제.)

### 2단계 — 수집기 만들기 (Claude 가 작업)

- 수집 출처 목록 `config/sources.yaml` (RSS 주소는 Claude 가 실제로 접속해서 확인한 것만 넣음)
- 공정 분류 체계 `config/taxonomy.yaml`
  (노광 EUV·High-NA / 식각·증착 ALE·ALD·ASD / 배선 Mo·Ru·BSPDN / 트랜지스터 GAA·CFET /
  메모리 3D NAND·HBM / 패키징 하이브리드 본딩 / 계측·검사 / CMP)
- `collector/collect.py` — RSS·arXiv 수집, SQLite 에 저장, 중복 제거

👉 Claude 에게: **"2단계 해줘"**

AI 를 쓰지 않는 단계라 비용이 없다. 태그는 `taxonomy.yaml` 의 키워드로 붙인다. 수집 결과를 보고 출처·키워드를 넣고 빼면 된다.

실행 (직접 해볼 때):
```bash
.venv\Scripts\python collector\collect.py
```

### 3단계 — 주간 글 작성 지시문 만들기 (Claude 가 작업)

- `collector/week_input.py` — 지난 7일 수집분을 태그별 짧은 목록(`data/weekly/<주차>_input.md`)으로 정리 (Claude 가 읽을 양을 줄임)
- `prompts/weekly_digest.md` — Claude Code 가 매주 읽고 따라 할 지시문
  - 이번 주 `data/items.jsonl` 에서 중요한 것 선별
  - 형식: 핵심 기술 3개(원리·장점·난제) / 면접 예상 질문 / 내 연구와의 연결 / 원문 링크 / 내 코멘트(빈칸)
  - 원문은 복사하지 않고 **요약 + 링크**만 (저작권)
- 처음엔 손으로 한 번 실행해서 결과를 보고 형식을 같이 다듬는다.

👉 Claude 에게: **"3단계 해줘"** → 첫 주간 글을 읽어보고 "면접 질문 더 어렵게" 같은 식으로 고쳐달라고 하면 된다.

### 4단계 — 블로그 만들기 (Claude 가 작업)

- `site/` 에 Hugo 블로그 (외부 테마 없이 직접 만든 단순한 디자인, 다크 모드 지원)
- 글마다 그림: 직접 그린 개념도(SVG) + 자유 라이선스 그림(Wikimedia Commons) + 태그 통계 차트. 그림 아래에 출처·라이선스 자동 표기
- 배경 지식 상자(초록), 접는 면접 질문, 용어 정리 표

내 PC 에서 미리보기 (끄려면 Ctrl+C):
```bash
cd site; hugo server
```
→ 브라우저에서 http://localhost:1313/semi-process-digest/

👉 Claude 에게: **"블로그 미리보기 띄워줘"** 라고 해도 된다.

### 5단계 — GitHub 에 올리고 자동화 (같이 작업)

1. **내가 할 일**: GitHub 에서 새 저장소(repository) `semi-process-digest` 를 만든다 (Public 이어야 Pages 무료).
   - https://github.com/new → Repository name: `semi-process-digest` → **Public** → README·.gitignore·license 는 **추가하지 않음**(빈 저장소) → Create repository
2. Claude 에게 **"5단계 해줘. 저장소 주소는 https://github.com/<내아이디>/semi-process-digest"** 라고 말한다.
   Claude 가 `git` 초기화, 첫 커밋, `.github/workflows/` 자동 실행 파일(매일 수집 + 블로그 배포)을 만들고, 올리기(push) 전에 확인을 받는다.
   처음 push 할 때 GitHub 로그인 창이 뜨면 **내가 직접** 로그인한다.
3. **내가 할 일**: 저장소 **Settings → Pages → Source: GitHub Actions** 로 설정.
4. Actions 탭에서 수동으로 한 번 실행(Run workflow) → 블로그 주소(`https://<내아이디>.github.io/semi-process-digest/`)가 뜨면 완료.
5. **주간 요약 예약**: Claude 에게 **"매주 월요일 오전 9시에 주간 글 쓰는 예약 작업 만들어줘"** 라고 말한다.
   - 내 PC 에서 도는 예약 작업이면 그 시간에 PC 가 켜져 있고 Claude 앱에 로그인돼 있어야 한다. 놓치면 켰을 때 "이번 주 글 써줘"로 수동 실행하면 된다.
   - 클라우드에서 도는 방식도 가능한지 이 단계에서 같이 확인한다.

### 6단계 — 운영 (매주 10~20분)

- [ ] 월요일에 올라온 주간 글 읽기
- [ ] **내 코멘트** 칸 채우기 → 이게 자소서·면접 소재가 된다
- [ ] 좋은 글은 다듬어서 Tistory 에 직접 옮기기
- [ ] 읽고 싶은 논문은 GitHub **Issues** 에 등록해서 읽을거리 목록으로 관리
- [ ] 한 달에 한 번: 출처·태그 정리 ("요즘 패키징 기사가 너무 많아, 필터 강화해줘")

---

## 비용·주의

- **GitHub Actions / Pages**: 공개 저장소는 무료.
- **Claude**: 구독 안에서 사용. 추가 결제 없음. 다만 주간 글 작성이 구독 사용량 한도를 평소 사용과 같이 쓴다
  (주 1회라 부담은 작다). API 키는 쓰지 않는다.
- **저작권**: 기사·논문 원문을 블로그에 복사하지 않는다. 요약 + 출처 링크만.
- **연구실 자료**: CNT 실험 데이터·사진은 이 저장소에 올리지 않는다. 연구 연결 칸에는 공개된 개념 수준만 쓴다.

## 진행 상황

- [x] 0. 폴더·README 생성
- [x] 1. 준비물 (Git, GitHub, 구독)
- [x] 2. 수집기 (2026-11-17 첫 수집 64건)
- [x] 3. 주간 글 지시문 (첫 글: `site/content/posts/2026-W47.md`)
- [x] 4. 블로그 (Hugo, 그림·배경 지식 포함 첫 글)
- [x] 5. GitHub 자동화 (저장소 gyeonguk1545-spec/semi-process-digest, 매일 09:00 수집, 매주 월 09:30 경 주간 글 예약 작업)
- [x] 6. 운영 시작 (2026-11-18 블로그 공개)
