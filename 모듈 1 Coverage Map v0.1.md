# 모듈 1 Coverage Map v0.1

## 구간 요약

|구간|교재 쪽|핵심 역할|변환 방향|
|---|--:|---|---|
|도입|p.27~31|확인 질문, 모듈 개요, CTO 요청|Source Digest 보존|
|AWS 서비스|p.32~34|AWS 이점, 이전 이유, 서비스 범주|핵심 개념화|
|AWS 인프라|p.35~44|데이터 센터, AZ, Region, Local Zones, Edge Location|핵심 개념화 + 비교표|
|Well-Architected|p.45~51|아키텍트 역할, 6개 pillar, Well-Architected Tool, 솔루션 제시|핵심 개념화|
|지식 확인|p.52~63|문제 1~5, 정답, 해설|Quiz Appendix 후보|
|실습 1|p.64~67|Console, CLI, SDK, API, S3 실습 안내|Lab Note 후보|

---

## Coverage Map

|파일 p.|교재 p.|내용|처리 방식|이미지 처리|분리 후보|상태|
|--:|--:|---|---|---|---|---|
|1|27|모듈 1 표지: 아키텍팅 기본 사항, 실습 1 표시|제목/메타데이터로 보존|표지 이미지 생략|없음|preserved|
|2|28|확인 질문: 조직의 AWS 클라우드 이전 진행 단계|문제/보기 보존|퀴즈 화면 생략|Quiz Appendix|preserved|
|3|29|모듈 개요|모듈 전체 목차로 보존|단순 슬라이드 생략|Source Digest 구조 기준|preserved|
|4|30|CTO 비즈니스 요청: AWS 이점, 글로벌 인프라 구성, 모범 사례 기반 구축|비즈니스 요청 섹션으로 보존|인물 아이콘 생략|핵심 프레임|preserved|
|5|31|AWS 서비스 섹션 표지|섹션 마커로 처리|표지 이미지 생략|없음|preserved|
|6|32|Amazon Web Services 개요: 글로벌 데이터 센터, 200개 이상 서비스, 보안/안정성, 비용 절감/혁신|핵심 bullet로 보존|세계 지도는 장식성 높음, 텍스트화|Concept 후보|concept-note-candidate|
|7|33|고객이 AWS로 이전하는 이유: 민첩성, 출시 시간 단축, 혁신, 크기 조정, 비용 최적화, 보안 위험 감소, 관리 감소|핵심 개념으로 보존|이점 도식은 목록화|Concept 후보|concept-note-candidate|
|8|34|AWS 서비스 범주: 서버리스, 네트워킹 및 콘텐츠 전송, 데이터베이스, 보안/자격 증명/규정 준수, 관리 및 거버넌스, 스토리지, AWS 비용 관리, 컴퓨팅, 컨테이너 등|강조된 서비스 범주만 표로 보존|전체 아이콘 이미지는 생략, 표로 변환|Concept 후보|preserved|
|9|35|AWS 인프라 섹션 표지|섹션 마커로 처리|표지 이미지 생략|없음|preserved|
|10|36|AWS 인프라 관련 주제: 데이터 센터, 가용 영역, 리전, AWS Local Zones, 엣지 로케이션|계층 구조로 보존|도식은 텍스트 계층으로 변환|Concept 후보|preserved|
|11|37|AWS 데이터 센터: AWS 서비스가 데이터 센터에서 작동, 보안, 전원, 네트워킹, 접근 통제|핵심 설명 보존|건물 도식은 설명으로 대체|Concept 후보|summarized|
|12|38|가용 영역: 하나 이상의 데이터 센터 그룹, 독립 전력/네트워크, 리전 내부의 격리 단위|핵심 개념 보존|AZ-리전 관계 도식은 텍스트화|Concept 후보|concept-note-candidate|
|13|39|AWS 리전: 지리적 영역, 복수 AZ 포함, 격리, 리전 간 통신/복제 가능|핵심 개념 보존|지도는 생략 가능, 리전-AZ 관계만 보존|Concept 후보|concept-note-candidate|
|14|40|리전 선택 요인: 거버넌스/법적 요구, 지연 시간, 서비스 가용성, 비용|반드시 표로 보존|4분면 아이콘은 표로 대체|Concept 후보|preserved|
|15|41|AWS Local Zones: 10ms 미만 지연 요구, 미디어/게임/금융/HPC 등 사용 사례|Local Zones 설명과 사용 사례 보존|사용 사례 아이콘은 목록화|Concept 후보|concept-note-candidate|
|16|42|엣지 로케이션: CloudFront, Route 53, AWS WAF 관련, 콘텐츠 캐시/전송|Edge Location 설명 보존|지도는 생략, 기능 목록화|Concept 후보|concept-note-candidate|
|17|43|엣지 로케이션 사용 사례: S3 오리진 → CloudFront → 사용자 근접 캐시|흐름 설명 보존|간단한 Mermaid 후보|Concept 후보|image-preserve-needed|
|18|44|AWS Local Zones 및 엣지 로케이션 기능 비교|비교표로 변환|원본 도식은 표로 대체 가능|Concept 후보|preserved|
|19|45|AWS Well-Architected Framework 섹션 표지|섹션 마커로 처리|표지 이미지 생략|없음|preserved|
|20|46|AWS 아키텍트의 역할: 계획, 조사, 구축|역할 표로 보존|3열 도식은 표로 변환|Concept 후보|preserved|
|21|47|Well-Architected Framework 핵심 요소 6개: 보안, 비용 최적화, 안정성, 성능 효율성, 운영 우수성, 지속 가능성|반드시 표로 보존|6개 pillar 도식은 표로 대체 가능|Concept 후보|preserved|
|22|48|지속 가능성 설명 및 Well-Architected 관련 참고 링크|본문 보존, 링크 목록화|이미지 없음|Concept 후보|preserved|
|23|49|AWS Well-Architected Tool: 워크로드 문서화, 검토, 우수 사례 제안, 개선 계획|도구 흐름으로 보존|흐름도는 Mermaid 후보|Concept 후보|concept-note-candidate|
|24|50|검토 섹션 표지|섹션 마커로 처리|표지 이미지 생략|없음|preserved|
|25|51|솔루션 제시: CTO 질문에 대한 답변 정리|모듈 결론으로 보존|인물 아이콘 생략|핵심 결론|preserved|
|26|52|모듈 복습: AWS 서비스, AWS 인프라, Well-Architected Framework|복습 체크리스트로 보존|아이콘 생략|Quiz Appendix 앞머리|preserved|
|27|53|지식 확인 표지|섹션 마커로 처리|표지 이미지 생략|Quiz Appendix|preserved|
|28|54|지식 확인 문제 1: AWS 아키텍트의 역할|문제/보기 보존|퀴즈 화면 텍스트화|Quiz Appendix|preserved|
|29|55|문제 1 정답: 비즈니스 요구 사항과 기술 요구 사항을 위한 솔루션 분석|정답/해설 보존|화면 생략|Quiz Appendix|preserved|
|30|56|지식 확인 문제 2: 지연 시간 영향 최소화 위치 선택|문제/보기 보존|화면 텍스트화|Quiz Appendix|preserved|
|31|57|문제 2 정답: 가용 영역|정답/해설 보존|화면 생략|Quiz Appendix|preserved|
|32|58|지식 확인 문제 3: AWS 리전 선택 시 고려 요소 2개|문제/보기 보존|화면 텍스트화|Quiz Appendix|preserved|
|33|59|문제 3 정답: 현지 데이터 관련 규정, 최종 사용자 지역 시간|정답/해설 보존|화면 생략|Quiz Appendix|preserved|
|34|60|지식 확인 문제 4: 여러 AZ 애플리케이션 배포 이유|문제/보기 보존|화면 텍스트화|Quiz Appendix|preserved|
|35|61|문제 4 정답: 리소스의 고가용성 보장|정답/해설 보존|화면 생략|Quiz Appendix|preserved|
|36|62|지식 확인 문제 5: 최소 권한 원칙이 속하는 Well-Architected pillar|문제/보기 보존|화면 텍스트화|Quiz Appendix|preserved|
|37|63|문제 5 정답: 보안|정답/해설 보존|화면 생략|Quiz Appendix|preserved|
|38|64|실습 1 표지: AWS 관리 콘솔 및 AWS CLI 살펴보기 및 상호작용|실습 섹션 마커로 보존|표지 이미지 생략|Lab Note 후보|preserved|
|39|65|AWS 서비스에 연결: Console, CLI, SDK → AWS API → AWS 서비스|흐름도 + 설명 보존|Mermaid 변환 권장|Lab Note 후보|image-preserve-needed|
|40|66|실습 과제: 콘솔 구성, S3 버킷 생성, 객체 업로드, CLI로 버킷 생성/업로드|체크리스트로 변환|단계 도식은 체크리스트화|Lab Note 후보|preserved|
|41|67|모듈 1 완료|종료 마커로 보존|표지 이미지 생략|없음|preserved|

---

## 분리 후보 정리

아직 물리 파일로 쪼개지는 말고, `Source Digest` 안에서 아래처럼 후보만 표시하는 게 맞다.

```markdown
## 분리 후보

| 후보 노트 | 근거 페이지 | 분리 시점 |
|---|---:|---|
| Concept - AWS 서비스와 클라우드 이전 이유 | p.32~34 | 모듈 1 Source Digest 완성 후 |
| Concept - AWS 글로벌 인프라 | p.35~44 | Region/AZ/Local Zones/Edge Location 정리 필요 시 |
| Concept - AWS Well-Architected Framework | p.45~51 | 6개 pillar와 Tool 정리 필요 시 |
| Appendix - 모듈 1 지식 확인 | p.52~63 | 문제/정답/해설이 길어질 때 |
| Lab - AWS Console과 AWS CLI로 S3 조작하기 | p.64~67 | 실제 실습 로그/스크린샷 추가 시 |
```

## 이미지 보존 후보

원본 이미지 placeholder를 남길 만한 건 많지 않다. 우선순위는 이 정도다.

|교재 p.|이미지|보존 판단|
|--:|---|---|
|p.43|S3 오리진 → 엣지 로케이션 → 사용자 흐름|`image-preserve-needed` 또는 Mermaid 변환|
|p.47|Well-Architected 6개 pillar 도식|표로 충분하지만, 원본 참조도 가능|
|p.49|AWS Well-Architected Tool 흐름|Mermaid 변환 권장|
|p.65|Console / CLI / SDK → AWS API → AWS 서비스|실습 이해에 중요, Mermaid 변환 권장|
