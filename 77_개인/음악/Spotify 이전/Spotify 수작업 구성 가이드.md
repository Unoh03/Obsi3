---
type: troubleshooting
status: active
created: 2026-09-30
topic: Apple Music 원본 순서를 보존하는 Spotify 수작업 구성
parent_moc: "[[77_개인/00_개인_목차]]"
---

# Spotify 수작업 구성 가이드

**앨범·EP를 먼저 묶어 배치하고, 그 사이에 아래 표의 싱글·참여곡만 넣은 뒤, 개인 배치 항목을 마지막에 조정한다.** 기준은 Apple 원본 7개 플레이리스트의 463곡이다. 아래 번호는 모두 **완성 후의 목표 위치**이며 현재 Spotify 위치가 아니다.

## 사용하는 방법

1. 원하는 플레이리스트의 **배치표**를 위에서 아래로 따라간다. 같은 앨범이 다시 나오면 두 번째 앨범을 통째로 넣는 것이 아니라, 그 위치에 지정된 곡만 둔다.
2. 앨범마다 **이번에 가져올 곡 수**와 접힌 **곡별 최종 순서표**를 확인한다. 표의 곡 수는 원본에서 선택한 수이며 해당 앨범의 전체 수록곡 수를 뜻하지 않는다. 통째로 추가했다면 목록에 없는 곡이 함께 들어갔는지 확인한다.
3. 제목이 같은 앨범이 여러 개면 **사용자의 계정에서 재생 가능한 발매본**을 먼저 고른다. 첫 곡·마지막 곡과 필요한 곡의 구성, 원본/재녹음/Remix 표기를 확인한다. 표의 기존 Spotify 표기는 검색 보조이며 그 검색 결과의 판본을 그대로 채택하라는 뜻이 아니다.
4. 싱글·참여곡은 지정된 앞뒤 앨범 사이에 놓는다. 전체 발매일 정렬·제목 정렬을 새로 적용하지 않는다. 이 문서는 발매일을 다시 조사해 만든 순서가 아니라 **현재 Apple에 확정된 순서**를 옮기는 안내다.
5. 각 절의 **개인 배치와 마지막 조정**을 적용한다. CSV만으로 누가 언제 순서를 바꿨는지는 알 수 없으므로, 해당 항목은 의도를 추측하지 않고 원본에서 관측된 배치를 보존한다.
6. 마무리할 때 곡 수뿐 아니라 첫 곡·마지막 곡·앨범 경계·재생 불가 항목·개인 배치를 확인한다. 이후 새 CSV는 전체 순서 대조에 쓰고, 재생 가능 여부는 실제 앱에서 확인한다.

### 같은 앨범 이름이 두 번 보일 때 — strobo

사용자는 Spotify에서 `strobo` 발매본 두 개를 확인했다. 한쪽은 일본어 제목이 많고 `Audio 001`이 재생되지 않으며, 다른 쪽은 영어 표기로 전곡 재생 가능하다고 보고했다. **이는 플레이리스트 안에 동일 트랙 ID가 두 번 있는지와 다른 문제**다. 기존의 ID·ISRC 중복 검사로 이 문제를 배제할 수 없다.

- 이번 작업에서는 사용자가 확인한 **전곡 재생 가능한 strobo 발매본**에서 아래 11곡을 고른다. `Audio 001` / `Audio zero zero one`과 `Audio 002` / `Audio zero zero two`를 특히 확인한다.
- 영어 제목이면 항상 올바른 판본이라는 일반 규칙은 아니다. **현재 재생 가능 여부와 필요한 녹음 버전·곡 구성**을 기준으로 고른다.
- 두 발매본의 정확한 앨범 ID·배급 차이·재생 제한 원인은 이 문서에서 확인하지 않았다. 기존 CSV의 트랙 ID를 일괄 재사용해 같은 문제를 반복하지 않도록 이 가이드는 기존 트랙 링크를 추가 지시로 제공하지 않는다.
- 이미 넣은 곡은 유지할 항목을 정한 뒤 비교한다. 확인 전에 기존 플레이리스트 전체를 지우거나 같은 앨범을 다시 통째로 추가하지 않는다.

### 보존할 선택

- 원본에 없는 새 곡은 추가하지 않는다. Vaundy는 **89곡**이며 과거 목록의 제거곡을 복원하지 않는다.
- 원본/재녹음/Remix/다른 가수 버전을 제목만 보고 합치지 않는다.
- 원본이 특정 싱글 항목을 선택했다면 우선 그 선택을 표에 유지했다. 앨범 우선 규칙과 충돌한다고 임의로 싱글을 없애지 않는다.
- 즛토마요의 `Time Left` / `残機`는 원본의 43번·62번 두 항목을 유지한다.
- 새로 고르는 Instrumental은 제외하되, 원본에 들어 있는 `Audio`·인터루드·OST 곡은 제목만 보고 삭제하지 않는다. 이 문서의 목표는 원본 재현이다.

## 작업 목록

| 이동할 절 | 목표 곡 수 | 먼저 볼 부분 |
|---|---:|---|
| [[#Vaundy — 89곡]] | 89 | strobo 발매본, 참여작, ASH 순서 |
| [[#요루시카 — 117곡]] | 117 | 幻燈 전체, 마지막 あぶく, 잘못된 수록본 |
| [[#kessoku band — 26곡]] | 26 | 마지막 두 커버곡 분리 배치 |
| [[#Wave To Earth — 34곡]] | 34 | daisy. 삽입, 마지막 검은 산 |
| [[#너드커넥션 — 49곡]] | 49 | 앨범 사이 싱글, Losing Myself 수록본 |
| [[#즛토마요 — 70곡]] | 70 | 앨범별 일부 선택과 흩어진 개인 배치 |
| [[#DJMAX — 78곡]] | 78 | OST 일부 선택, 원본 곡별 순서 |


## Vaundy — 89곡

원본 플레이리스트 이름: `Vaundy 본인곡·참여작 — 앨범 우선·발매순 1/4`. 이름 끝의 `1/4`와 관계없이 이번 기준 파일에는 한 목록으로 89곡이 있다.

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1–11 | strobo | 선택 11곡: Audio zero zero one → … → Bye by me |
| □ | 12 | Walpurgis | 地球儀 (with Vaundy) (에메) |
| □ | 13–14 | NEW GRAVITY | Ash (feat. Vaundy) [N-Buna From Yorushika Remix] (Nulbarich) → Ash (feat. Vaundy) (Nulbarich) |
| □ | 15–17 | 裸の勇者 - EP | 二人話 (Vaundy) → HERO (Vaundy) → おもかげ -self cover- (Vaundy) |
| □ | 18 | UTA'S SONGS ONE PIECE FILM RED | Backlight (Ado) |
| □ | 19 | Versus the night | くびったけ (yama) |
| □ | 20 | ELLEGARDEN TRIBUTE | Missing (Vaundy) |
| □ | 21 | mixtape - EP | rose feat. Vaundy (Chilli Beans.) |
| □ | 22–56 | replica | 선택 35곡: Audio 007 → … → トドメの一撃 (feat. Cory Wong) |
| □ | 57–58 | タイムパラドックス - Single | タイムパラドックス (Vaundy) → ココロありがとう (Vaundy) |
| □ | 59 | SPIN | 惑う糸 (스다 마사키) |
| □ | 60 | Zanmu | Ibara (Ado) |
| □ | 61–62 | ホムンクルス / Gift - Single | ホムンクルス (Vaundy) → Gift (Vaundy) |
| □ | 63 | No.Ⅰ | Toumei Ni Naritai (Number_i) |
| □ | 64 | GORILLA SHIBAI - Single | GORILLA SHIBAI (Vaundy) |
| □ | 65 | 風神 - Single | 風神 (Vaundy) |
| □ | 66–67 | 走れSAKAMOTO - Single | 走れSAKAMOTO (Vaundy) → Somebody help us (Vaundy) |
| □ | 68 | Jinsei wa mix nuts no kumiawase - Single | Jinsei wa mix nuts no kumiawase (Vaundy) |
| □ | 69 | 僕にはどうしてわかるんだろう - Single | 僕にはどうしてわかるんだろう (Vaundy) |
| □ | 70 | まじで、サヨナラべぃべぃ - Single | まじで、サヨナラべぃべぃ (Vaundy) |
| □ | 71 | pained - Single | pained (Vaundy) |
| □ | 72 | 再会 - Single | 再会 (Vaundy) |
| □ | 73 | zutto love song - Single | zutto love song (Vaundy) |
| □ | 74 | wasurerumaeni - Single | wasurerumaeni (Vaundy) |
| □ | 75 | 偉生人 - Single | 偉生人 (Vaundy) |
| □ | 76 | Dear Jubilee -RADWIMPS TRIBUTE- | Zenzenzense (Vaundy) |
| □ | 77 | Kiseki - Single | Kiseki (Vaundy) |
| □ | 78 | 呼び声 - Single | 呼び声 (Vaundy) |
| □ | 79 | シンギュラリティ - Single | シンギュラリティ (Vaundy) |
| □ | 80–81 | The SILENCE - Single | Audio 015 (DOME TOUR 2026 ver.) (Vaundy) → The SILENCE (Vaundy) |
| □ | 82–85 | 飛ぶ時 / 飛ぼうよ - Single | 선택 4곡: 飛ぶ時 → … → 飛ぼうよ |
| □ | 86 | イデアが溢れて眠れない - Single | イデアが溢れて眠れない (Vaundy) |
| □ | 87 | kimagure - Single | kimagure (Vaundy) |
| □ | 88 | かげろう - Single | かげろう (Vaundy) |
| □ | 89 | ポップス (Prod. n-buna from ヨルシカ) - Single | ポップス (Prod. n-buna from ヨルシカ) (Jeremy Quartus & n-buna) |

### 개인 배치와 마지막 조정

- **1–11번 strobo:** 전곡 재생 가능한 하나의 발매본에서 구성한다. 원본의 영어 표기 11곡은 아래 상세표를 따른다. 기존 Spotify에 섞인 일본어 표기는 검색 참고만 한다.
- **12–21번은 참여작·EP 구간:** Aimer, Nulbarich, Ado, yama, Chilli Beans. 등의 앨범 전체를 추가하지 말고 표에 지정한 참여곡만 고른다.
- **13 → 14번:** `ASH`는 **n-buna Remix 먼저 → 일반 버전 다음**이다. 둘은 별도 항목으로 유지한다.
- **15–17번 裸の勇者 EP:** `二人話 → HERO → おもかげ -self cover-`만 여기 둔다. `裸の勇者` 곡은 **46번 replica 구간**에 한 번 둔다.
- **20번 Missing:** 원본은 `ELLEGARDEN TRIBUTE`다. 기존 Spotify의 `Boys in Stereo: Asia - Spring`을 목표 앨범으로 삼지 않는다. 원본에 대응하는 발매본의 이용 가능 여부는 앱에서 확인한다.
- **22–56번 replica:** 아래 35곡 순서를 유지한다. `Audio 007`로 시작하고 `トドメの一撃`로 끝난다. `Audio 003`이 오는 곳은 **37번**이다.
- **4번 Kaiju no Hanauta ↔ 34번 怪獣の花唄 - replica -**, **18번 Ado의 Backlight ↔ 31번 Vaundy의 逆光 - replica -**는 원본에서 각각 유지한 항목이다. 제목 대응만 보고 하나를 지우지 않는다.
- **82–85번:** `飛ぶ時(Vaundy) → 飛ぼうよ(yama) → 飛ぶ時(yama) → 飛ぼうよ(Vaundy)`. 같은 제목이라도 아티스트를 확인한다.
- 마지막은 **89번 Jeremy Quartus의 ポップス (Prod. n-buna from ヨルシカ)**다. 그 곡의 수록 이유를 여기서 재판단하거나 새로 빼지 않는다.


> [!example]- Vaundy 곡별 최종 순서표 — 89곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | Audio zero zero one | Audio 001 | Vaundy | strobo |
> | 2 | Tomoshibi | 동일 표기 | Vaundy | strobo |
> | 3 | Tokyo Flash | 東京フラッシュ | Vaundy | strobo |
> | 4 | Kaiju no Hanauta | 동일 표기 | Vaundy | strobo |
> | 5 | life hack | 동일 표기 | Vaundy | strobo |
> | 6 | Fukakoryoku | 동일 표기 | Vaundy | strobo |
> | 7 | soramimi | 동일 표기 | Vaundy | strobo |
> | 8 | Audio zero zero two | Audio 002 | Vaundy | strobo |
> | 9 | napori | 동일 표기 | Vaundy | strobo |
> | 10 | Boku wa kyo mo | 僕は今日も | Vaundy | strobo |
> | 11 | Bye by me | 동일 표기 | Vaundy | strobo |
> | 12 | 地球儀 (with Vaundy) | 地球儀 | 에메 | Walpurgis |
> | 13 | Ash (feat. Vaundy) [N-Buna From Yorushika Remix] | ASH feat. Vaundy (n-buna from YORUSHIKA Remix) | Nulbarich | NEW GRAVITY |
> | 14 | Ash (feat. Vaundy) | ASH feat. Vaundy | Nulbarich | NEW GRAVITY |
> | 15 | 二人話 | 동일 표기 | Vaundy | 裸の勇者 - EP |
> | 16 | HERO | 동일 표기 | Vaundy | 裸の勇者 - EP |
> | 17 | おもかげ -self cover- | 동일 표기 | Vaundy | 裸の勇者 - EP |
> | 18 | Backlight | 동일 표기 | Ado | UTA'S SONGS ONE PIECE FILM RED |
> | 19 | くびったけ | 동일 표기 | yama | Versus the night |
> | 20 | Missing | Missing - Amazon Original | Vaundy | ELLEGARDEN TRIBUTE |
> | 21 | rose feat. Vaundy | rose - feat. Vaundy | Chilli Beans. | mixtape - EP |
> | 22 | Audio 007 | 동일 표기 | Vaundy | replica |
> | 23 | ZERO | 동일 표기 | Vaundy | replica |
> | 24 | 美電球 | 동일 표기 | Vaundy | replica |
> | 25 | カーニバル | 동일 표기 | Vaundy | replica |
> | 26 | 1リッター分の愛をこめて | 동일 표기 | Vaundy | replica |
> | 27 | 常熱 | 동일 표기 | Vaundy | replica |
> | 28 | Audio 006 | 동일 표기 | Vaundy | replica |
> | 29 | 宮 | 동일 표기 | Vaundy | replica |
> | 30 | 黒子 | 동일 표기 | Vaundy | replica |
> | 31 | 逆光 - replica - | 동일 표기 | Vaundy | replica |
> | 32 | NEO JAPAN | 동일 표기 | Vaundy | replica |
> | 33 | 呼吸のように | 동일 표기 | Vaundy | replica |
> | 34 | 怪獣の花唄 - replica - | 동일 표기 | Vaundy | replica |
> | 35 | Audio 008 | 동일 표기 | Vaundy | replica |
> | 36 | replica | 동일 표기 | Vaundy | replica |
> | 37 | Audio 003 | 동일 표기 | Vaundy | replica |
> | 38 | 世界の秘密 | 동일 표기 | Vaundy | replica |
> | 39 | 融解sink | 동일 표기 | Vaundy | replica |
> | 40 | しわあわせ | 동일 표기 | Vaundy | replica |
> | 41 | benefits | 동일 표기 | Vaundy | replica |
> | 42 | 花占い | 동일 표기 | Vaundy | replica |
> | 43 | Tokimeki | 동일 표기 | Vaundy | replica |
> | 44 | 泣き地蔵 | 동일 표기 | Vaundy | replica |
> | 45 | 踊り子 | 동일 표기 | Vaundy | replica |
> | 46 | 裸の勇者 | 동일 표기 | Vaundy | replica |
> | 47 | 恋風邪にのせて | 동일 표기 | Vaundy | replica |
> | 48 | 走馬灯 | 동일 표기 | Vaundy | replica |
> | 49 | mabataki | 동일 표기 | Vaundy | replica |
> | 50 | CHAINSAW BLOOD | 동일 표기 | Vaundy | replica |
> | 51 | 瞳惚れ | 동일 표기 | Vaundy | replica |
> | 52 | 忘れ物 | 동일 표기 | Vaundy | replica |
> | 53 | 置き手紙 | 동일 표기 | Vaundy | replica |
> | 54 | まぶた | 동일 표기 | Vaundy | replica |
> | 55 | そんなbitterな話 | 동일 표기 | Vaundy | replica |
> | 56 | トドメの一撃 (feat. Cory Wong) | トドメの一撃 | Vaundy | replica |
> | 57 | タイムパラドックス | 동일 표기 | Vaundy | タイムパラドックス - Single |
> | 58 | ココロありがとう | 동일 표기 | Vaundy | タイムパラドックス - Single |
> | 59 | 惑う糸 | 동일 표기 | 스다 마사키 | SPIN |
> | 60 | Ibara | 동일 표기 | Ado | Zanmu |
> | 61 | ホムンクルス | 동일 표기 | Vaundy | ホムンクルス / Gift - Single |
> | 62 | Gift | 동일 표기 | Vaundy | ホムンクルス / Gift - Single |
> | 63 | Toumei Ni Naritai | 透明になりたい | Number_i | No.Ⅰ |
> | 64 | GORILLA SHIBAI | 동일 표기 | Vaundy | GORILLA SHIBAI - Single |
> | 65 | 風神 | 동일 표기 | Vaundy | 風神 - Single |
> | 66 | 走れSAKAMOTO | 동일 표기 | Vaundy | 走れSAKAMOTO - Single |
> | 67 | Somebody help us | 동일 표기 | Vaundy | 走れSAKAMOTO - Single |
> | 68 | Jinsei wa mix nuts no kumiawase | 동일 표기 | Vaundy | Jinsei wa mix nuts no kumiawase - Single |
> | 69 | 僕にはどうしてわかるんだろう | 동일 표기 | Vaundy | 僕にはどうしてわかるんだろう - Single |
> | 70 | まじで、サヨナラべぃべぃ | 동일 표기 | Vaundy | まじで、サヨナラべぃべぃ - Single |
> | 71 | pained | 동일 표기 | Vaundy | pained - Single |
> | 72 | 再会 | 동일 표기 | Vaundy | 再会 - Single |
> | 73 | zutto love song | 동일 표기 | Vaundy | zutto love song - Single |
> | 74 | wasurerumaeni | 동일 표기 | Vaundy | wasurerumaeni - Single |
> | 75 | 偉生人 | 동일 표기 | Vaundy | 偉生人 - Single |
> | 76 | Zenzenzense | 前前前世 | Vaundy | Dear Jubilee -RADWIMPS TRIBUTE- |
> | 77 | Kiseki | 동일 표기 | Vaundy | Kiseki - Single |
> | 78 | 呼び声 | 동일 표기 | Vaundy | 呼び声 - Single |
> | 79 | シンギュラリティ | 동일 표기 | Vaundy | シンギュラリティ - Single |
> | 80 | Audio 015 (DOME TOUR 2026 ver.) | Audio 015 - DOME TOUR 2026 ver. | Vaundy | The SILENCE - Single |
> | 81 | The SILENCE | 동일 표기 | Vaundy | The SILENCE - Single |
> | 82 | 飛ぶ時 | 동일 표기 | Vaundy | 飛ぶ時 / 飛ぼうよ - Single |
> | 83 | 飛ぼうよ | 동일 표기 | yama | 飛ぶ時 / 飛ぼうよ - Single |
> | 84 | 飛ぶ時 | 동일 표기 | yama | 飛ぶ時 / 飛ぼうよ - Single |
> | 85 | 飛ぼうよ | 동일 표기 | Vaundy | 飛ぶ時 / 飛ぼうよ - Single |
> | 86 | イデアが溢れて眠れない | 동일 표기 | Vaundy | イデアが溢れて眠れない - Single |
> | 87 | kimagure | 동일 표기 | Vaundy | kimagure - Single |
> | 88 | かげろう | 동일 표기 | Vaundy | かげろう - Single |
> | 89 | ポップス (Prod. n-buna from ヨルシカ) | 동일 표기 | Jeremy Quartus & n-buna | ポップス (Prod. n-buna from ヨルシカ) - Single |

## 요루시카 — 117곡

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1–7 | 夏草が邪魔をする | 선택 7곡: 夏陰、ピアノを弾く → … → 雲と幽霊 |
| □ | 8–16 | 負け犬にアンコールはいらない | 선택 9곡: 前世 → … → 夏、バス停、君を待つ |
| □ | 17–30 | だから僕は音楽を辞めた | 선택 14곡: 8/31 → … → だから僕は音楽を辞めた |
| □ | 31–44 | Elma / エルマ | 선택 14곡: Train Window → … → Nautilus |
| □ | 45 | Inoue Yosui Tribute | Make-up Shadow (요루시카) |
| □ | 46–59 | Plagiarism / 盗作 | 선택 14곡: Confession Of Plagiarist → … → Ghost In A Flower |
| □ | 60–64 | Creation - EP / 創作 | 선택 5곡: Robber And Bouquet → … → Liar |
| □ | 65 | Telepath - Single / テレパス | Telepath (요루시카) |
| □ | 66–90 | Magic Lantern / 幻燈 | 선택 25곡: Portrait of Summer → … → The Tenth Night |
| □ | 91 | Setting Sun - Single / 斜陽 | Setting Sun (요루시카) |
| □ | 92 | Yu, Sansan - Single / 憂、燦々 | Yu, Sansan (요루시카) |
| □ | 93 | Darma Grand Prix - Single / DARMA GRAND PRIX | Darma Grand Prix (요루시카) |
| □ | 94 | Madder - Single / 茜 | Madder (요루시카) |
| □ | 95–116 | second person / 二人称 | 선택 22곡: Early morning, mailbox → … → To the sea |
| □ | 117 | Bubble - Single / あぶく | Bubble (요루시카) |

### 개인 배치와 마지막 조정

- 앨범 뼈대는 `夏草が邪魔をする → 負け犬にアンコールはいらない → だから僕は音楽を辞めた → エルマ → 盗作 → 創作 → 幻燈 → 二人称`이다. 아래 배치표의 참여곡·싱글을 해당 사이에 끼운다.
- **45번 Make-up Shadow**는 `エルマ` 다음, `盗作` 직전이다.
- **65번 テレパス**는 `創作` 다음, `幻燈` 직전이다.
- **66–90번 幻燈 25곡:** `夏の肖像 → 都落ち → ブレーメン → チノカテ`로 시작한다. **79번 左右盲 → 80번 アルジャーノン → 81번 第一夜**를 확인한다. `第十夜`가 90번이다.
- **91–94번:** `斜陽 → 憂、燦々 → DARMA GRAND PRIX → 茜`를 두고, **95–116번 二人称**을 이어 붙인다.
- 마지막 **117번은 あぶく(Bubble)**다. `海へ(To the sea)`가 116번이고 `あぶく` 바로 앞이다.

**기존 118곡 목록을 고친다면:** 새 CSV 기준 `アルジャーノン`은 **96번과 118번**에 같은 ID로 중복되고, `あぶく`는 **108번**에 있다. `アルジャーノン` 하나만 남겨 `左右盲` 뒤·`第一夜` 앞으로 옮기고, `あぶく`를 `海へ` 뒤 마지막으로 옮긴다. 하나를 움직이거나 삭제하면 이후 현재 번호가 변하므로 **곡명과 앞뒤 곡으로 위치를 찾는다.** 직접 작업 후 이 번호는 오래된 정보가 된다.

**수록본 교체 목표 — 아래는 완성 후 번호:**

| 목표 앨범/싱글 | 해당 곡의 최종 위치 |
|---|---|
| エルマ | 34, 37 |
| 盗作 | 48, 58, 59 |
| 創作 | 61, 63, 64 |
| テレパス | 65 |
| 幻燈 | 79 — 左右盲 |
| 斜陽 | 91 |
| 二人称 | 100, 102, 103, 104, 105, 106, 107, 109, 110, 114 |

이 21곡은 새 CSV에도 이전의 다른 싱글·컴필레이션 ID가 남아 있었다. 새로 구성할 때 해당 목표 앨범에서 고르면 된다. `左右盲`의 Apple ISRC는 공란이므로 제목·아티스트·앨범 내 위치까지 확인한다.


> [!example]- 요루시카 곡별 최종 순서표 — 117곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | 夏陰、ピアノを弾く | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 2 | カトレア | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 3 | 言って。 | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 4 | あの夏に咲け | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 5 | 飛行 | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 6 | 靴の花火 | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 7 | 雲と幽霊 | 동일 표기 | 요루시카 | 夏草が邪魔をする |
> | 8 | 前世 | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 9 | 負け犬にアンコールはいらない | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 10 | 爆弾魔 | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 11 | ヒッチコック | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 12 | 落下 | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 13 | 準透明少年 | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 14 | ただ君に晴れ | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 15 | 冬眠 | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 16 | 夏、バス停、君を待つ | 동일 표기 | 요루시카 | 負け犬にアンコールはいらない |
> | 17 | 8/31 | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 18 | 藍二乗 | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 19 | 八月、某、月明かり | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 20 | 詩書きとコーヒー | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 21 | 7/13 | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 22 | 踊ろうぜ | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 23 | 六月は雨上がりの街を書く | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 24 | 五月は花緑青の窓辺から | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 25 | 夜紛い | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 26 | 5/6 | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 27 | パレード | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 28 | エルマ | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 29 | 4/10 | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 30 | だから僕は音楽を辞めた | 동일 표기 | 요루시카 | だから僕は音楽を辞めた |
> | 31 | Train Window | 車窓 | 요루시카 | Elma / エルマ |
> | 32 | Only Sorrow | 憂一乗 | 요루시카 | Elma / エルマ |
> | 33 | Evening Calm, Somewhere, Fireworks | 夕凪、某、花惑い | 요루시카 | Elma / エルマ |
> | 34 | Rain with Cappuccino | 雨とカプチーノ | 요루시카 | Elma / エルマ |
> | 35 | Lakeside Town | 湖の街 | 요루시카 | Elma / エルマ |
> | 36 | Dance of You | 神様のダンス | 요루시카 | Elma / エルマ |
> | 37 | After the Rain | 雨晴るる | 요루시카 | Elma / エルマ |
> | 38 | Walk | 歩く | 요루시카 | Elma / エルマ |
> | 39 | Hole in the Heart | 心に穴が空いた | 요루시카 | Elma / エルマ |
> | 40 | Church in the Forest | 森の教会 | 요루시카 | Elma / エルマ |
> | 41 | Voice | 声 | 요루시카 | Elma / エルマ |
> | 42 | Amy | エイミー | 요루시카 | Elma / エルマ |
> | 43 | Seabed,Moonlight | 海底、月明かり | 요루시카 | Elma / エルマ |
> | 44 | Nautilus | ノーチラス | 요루시카 | Elma / エルマ |
> | 45 | Make-up Shadow | 동일 표기 | 요루시카 | Inoue Yosui Tribute |
> | 46 | Confession Of Plagiarist | 音楽泥棒の自白 | 요루시카 | Plagiarism / 盗作 |
> | 47 | Burglar | 昼鳶 | 요루시카 | Plagiarism / 盗作 |
> | 48 | Prostitution | 春ひさぎ | 요루시카 | Plagiarism / 盗作 |
> | 49 | Bomber (Re-Recording) | 爆弾魔 - Re-Recording | 요루시카 | Plagiarism / 盗作 |
> | 50 | Adolescent, Burglar | 青年期、空き巣 | 요루시카 | Plagiarism / 盗作 |
> | 51 | Replicant | レプリカント | 요루시카 | Plagiarism / 盗作 |
> | 52 | Thoughtcrime | 思想犯 | 요루시카 | Plagiarism / 盗作 |
> | 53 | Flower And Badger Game | 花人局 | 요루시카 | Plagiarism / 盗作 |
> | 54 | Middle Age, Plagiarist | 朱夏期、音楽泥棒 | 요루시카 | Plagiarism / 盗作 |
> | 55 | Plagiarism | 盗作 | 요루시카 | Plagiarism / 盗作 |
> | 56 | Escape | 逃亡 | 요루시카 | Plagiarism / 盗作 |
> | 57 | Childhood, In Memories | 幼年期、思い出の中 | 요루시카 | Plagiarism / 盗作 |
> | 58 | Night Journey | 夜行 | 요루시카 | Plagiarism / 盗作 |
> | 59 | Ghost In A Flower | 花に亡霊 | 요루시카 | Plagiarism / 盗作 |
> | 60 | Robber And Bouquet | 強盗と花束 | 요루시카 | Creation - EP / 創作 |
> | 61 | Spring Thief | 동일 표기 | 요루시카 | Creation - EP / 創作 |
> | 62 | Creation | 創作 | 요루시카 | Creation - EP / 創作 |
> | 63 | Eat the wind | 風を食む | 요루시카 | Creation - EP / 創作 |
> | 64 | Liar | 嘘月 | 요루시카 | Creation - EP / 創作 |
> | 65 | Telepath | テレパス | 요루시카 | Telepath - Single / テレパス |
> | 66 | Portrait of Summer | 夏の肖像 | 요루시카 | Magic Lantern / 幻燈 |
> | 67 | Miyakoochi | 都落ち | 요루시카 | Magic Lantern / 幻燈 |
> | 68 | Bremen | ブレーメン | 요루시카 | Magic Lantern / 幻燈 |
> | 69 | Chinokate | チノカテ | 요루시카 | Magic Lantern / 幻燈 |
> | 70 | Snow Country | 雪国 | 요루시카 | Magic Lantern / 幻燈 |
> | 71 | Howl At The Moon | 月に吠える | 요루시카 | Magic Lantern / 幻燈 |
> | 72 | 451 | 동일 표기 | 요루시카 | Magic Lantern / 幻燈 |
> | 73 | Pas de Deux | パドドゥ | 요루시카 | Magic Lantern / 幻燈 |
> | 74 | Matasaburo | 又三郎 | 요루시카 | Magic Lantern / 幻燈 |
> | 75 | Fireworks of shoes (Re-Recording) | 靴の花火 - Re-Recording | 요루시카 | Magic Lantern / 幻燈 |
> | 76 | The Old Man and the Sea | 老人と海 | 요루시카 | Magic Lantern / 幻燈 |
> | 77 | Goodbye Molten | さよならモルテン | 요루시카 | Magic Lantern / 幻燈 |
> | 78 | Whale | いさな | 요루시카 | Magic Lantern / 幻燈 |
> | 79 | Left-Right Confusion | 左右盲 | 요루시카 | Magic Lantern / 幻燈 |
> | 80 | Algernon | アルジャーノン | 요루시카 | Magic Lantern / 幻燈 |
> | 81 | The First Night | 第一夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 82 | The Second Night | 第二夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 83 | The Third Night | 第三夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 84 | The Fourth Night | 第四夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 85 | The Fifth Night | 第五夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 86 | The Sixth Night | 第六夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 87 | The Seventh Night | 第七夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 88 | The Eighth Night | 第八夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 89 | The Ninth Night | 第九夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 90 | The Tenth Night | 第十夜 | 요루시카 | Magic Lantern / 幻燈 |
> | 91 | Setting Sun | 斜陽 | 요루시카 | Setting Sun - Single / 斜陽 |
> | 92 | Yu, Sansan | 憂、燦々 | 요루시카 | Yu, Sansan - Single / 憂、燦々 |
> | 93 | Darma Grand Prix | DARMA GRAND PRIX | 요루시카 | Darma Grand Prix - Single / DARMA GRAND PRIX |
> | 94 | Madder | 茜 | 요루시카 | Madder - Single / 茜 |
> | 95 | Early morning, mailbox | 早朝、郵便受け | 요루시카 | second person / 二人称 |
> | 96 | Become a cloud | 雲になる | 요루시카 | second person / 二人称 |
> | 97 | The flowers are also noisy | 花も騒めく | 요루시카 | second person / 二人称 |
> | 98 | Plover | 千鳥 | 요루시카 | second person / 二人称 |
> | 99 | Devilishness | 魔性 | 요루시카 | second person / 二人称 |
> | 100 | Play Sick | プレイシック | 요루시카 | second person / 二人称 |
> | 101 | Post spring | ポスト春 | 요루시카 | second person / 二人称 |
> | 102 | Sun | 太陽 | 요루시카 | second person / 二人称 |
> | 103 | Sunny | 晴る | 요루시카 | second person / 二人称 |
> | 104 | Forget it | 忘れてください | 요루시카 | second person / 二人称 |
> | 105 | Shura | 修羅 | 요루시카 | second person / 二人称 |
> | 106 | Martian | 火星人 | 요루시카 | second person / 二人称 |
> | 107 | Rubato | ルバート | 요루시카 | second person / 二人称 |
> | 108 | Cremation | 火葬 | 요루시카 | second person / 二人称 |
> | 109 | Aporia | アポリア | 요루시카 | second person / 二人称 |
> | 110 | Snake | へび | 요루시카 | second person / 二人称 |
> | 111 | Groan | うめき | 요루시카 | second person / 二人称 |
> | 112 | Woodpecker | 啄木鳥 | 요루시카 | second person / 二人称 |
> | 113 | Hitchcock (Re-Recording) | ヒッチコック - Re-Recording | 요루시카 | second person / 二人称 |
> | 114 | Moonbath | 月光浴 | 요루시카 | second person / 二人称 |
> | 115 | Paddle | 櫂 | 요루시카 | second person / 二人称 |
> | 116 | To the sea | 海へ | 요루시카 | second person / 二人称 |
> | 117 | Bubble | あぶく | 요루시카 | Bubble - Single / あぶく |

## kessoku band — 26곡

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1–13 | 結束バンド | 선택 13곡: 青春コンプレックス → … → フラッシュバッカー |
| □ | 14–15 | 光の中へ - EP | 光の中へ (kessoku band) → 青い春と西の空 (kessoku band) |
| □ | 16–20 | Re:結束バンド - EP | 선택 5곡: 月並みに輝け → … → 秒針少女 |
| □ | 21–24 | We will - EP | 선택 4곡: milky way → … → 夢を束ねて |
| □ | 25 | 結束バンド | 転がる岩、君に朝が降る (kessoku band) |
| □ | 26 | Re:結束バンド - EP | Re:Re: (kessoku band) |

### 개인 배치와 마지막 조정

먼저 `結束バンド → 光の中へ → Re:結束バンド → We will` 순으로 필요한 곡을 모은다. 이후 아래 두 곡을 끝으로 빼면 원본 배치가 된다.

1. `転がる岩、君に朝が降る`를 첫 앨범 끝에 두지 않고 **25번**으로 옮긴다.
2. `Re:Re:`를 `Re:結束バンド` 구간에서 빼서 **26번 마지막**으로 옮긴다.

완성 형태는 **첫 앨범 앞 13곡 → 光の中へ 2곡 → Re:結束バンド 앞 5곡 → We will 4곡 → 転がる岩、君に朝が降る → Re:Re:**다. `光の中へ`에서는 원본에 있는 두 곡만 선택하고 Instrumental 등을 추가하지 않는다.


> [!example]- kessoku band 곡별 최종 순서표 — 26곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | 青春コンプレックス | 동일 표기 | kessoku band | 結束バンド |
> | 2 | ひとりぼっち東京 | 동일 표기 | kessoku band | 結束バンド |
> | 3 | Distortion!! | 동일 표기 | kessoku band | 結束バンド |
> | 4 | ひみつ基地 | 동일 표기 | kessoku band | 結束バンド |
> | 5 | ギターと孤独と蒼い惑星 | 동일 표기 | kessoku band | 結束バンド |
> | 6 | ラブソングが歌えない | 동일 표기 | kessoku band | 結束バンド |
> | 7 | あのバンド | 동일 표기 | kessoku band | 結束バンド |
> | 8 | カラカラ | 동일 표기 | kessoku band | 結束バンド |
> | 9 | 小さな海 | 동일 표기 | kessoku band | 結束バンド |
> | 10 | なにが悪い | 동일 표기 | kessoku band | 結束バンド |
> | 11 | 忘れてやらない | 동일 표기 | kessoku band | 結束バンド |
> | 12 | 星座になれたら | 동일 표기 | kessoku band | 結束バンド |
> | 13 | フラッシュバッカー | 동일 표기 | kessoku band | 結束バンド |
> | 14 | 光の中へ | 동일 표기 | kessoku band | 光の中へ - EP |
> | 15 | 青い春と西の空 | 동일 표기 | kessoku band | 光の中へ - EP |
> | 16 | 月並みに輝け | 동일 표기 | kessoku band | Re:結束バンド - EP |
> | 17 | 今、僕、アンダーグラウンドから | 동일 표기 | kessoku band | Re:結束バンド - EP |
> | 18 | ドッペルゲンガー | 동일 표기 | kessoku band | Re:結束バンド - EP |
> | 19 | 僕と三原色 | 동일 표기 | kessoku band | Re:結束バンド - EP |
> | 20 | 秒針少女 | 동일 표기 | kessoku band | Re:結束バンド - EP |
> | 21 | milky way | 동일 표기 | kessoku band | We will - EP |
> | 22 | 惑う星 | 동일 표기 | kessoku band | We will - EP |
> | 23 | UNITE | 동일 표기 | kessoku band | We will - EP |
> | 24 | 夢を束ねて | 동일 표기 | kessoku band | We will - EP |
> | 25 | 転がる岩、君に朝が降る | 동일 표기 | kessoku band | 結束バンド |
> | 26 | Re:Re: | 동일 표기 | kessoku band | Re:結束バンド - EP |

## Wave To Earth — 34곡

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1–6 | wave 0.01 - EP | 선택 6곡: gold → … → purple lake |
| □ | 7–11 | summer flows 0.02 - EP | 선택 5곡: summer flows → … → surf. |
| □ | 12 | daisy. - Single | daisy. (wave to earth) |
| □ | 13–26 | 0.1 flaws and all. | 선택 14곡: bad → … → so real |
| □ | 27–33 | play with earth! 0.03 (Extended Version) | 선택 7곡: are you bored? → … → holyland |
| □ | 34 | Twenty Plenty | 검은 산 (wave to earth) |

### 개인 배치와 마지막 조정

- `wave 0.01`의 **6곡 → summer flows 0.02의 5곡 → daisy. 한 곡 → 0.1 flaws and all.의 14곡 → play with earth! 0.03 (Extended Version)의 7곡 → 검은 산 한 곡** 순이다.
- `daisy.`는 **12번**, 마지막 참여곡 `검은 산`은 **34번**이다. `Twenty Plenty` 전체를 추가하지 않는다.
- **30번 pueblo (remastered 2024)**는 원본이 선택한 리마스터 항목이다. 다른 `pueblo`를 추가하거나 버전 표기를 생략해 고르지 않는다.
- Extended Version이라는 앨범명만 보고 확장판의 모든 곡을 추가하지 않는다. 이번 원본에서 선택한 구간은 `are you bored?`부터 `holyland`까지 **7곡**이다.


> [!example]- Wave To Earth 곡별 최종 순서표 — 34곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | gold | 동일 표기 | wave to earth | wave 0.01 - EP |
> | 2 | bonfire | 동일 표기 | wave to earth | wave 0.01 - EP |
> | 3 | wave | 동일 표기 | wave to earth | wave 0.01 - EP |
> | 4 | light | 동일 표기 | wave to earth | wave 0.01 - EP |
> | 5 | bird | 동일 표기 | wave to earth | wave 0.01 - EP |
> | 6 | purple lake | 동일 표기 | wave to earth | wave 0.01 - EP |
> | 7 | summer flows | 동일 표기 | wave to earth | summer flows 0.02 - EP |
> | 8 | ride | 동일 표기 | wave to earth | summer flows 0.02 - EP |
> | 9 | seasons | 동일 표기 | wave to earth | summer flows 0.02 - EP |
> | 10 | ocean floor | 동일 표기 | wave to earth | summer flows 0.02 - EP |
> | 11 | surf. | 동일 표기 | wave to earth | summer flows 0.02 - EP |
> | 12 | daisy. | 동일 표기 | wave to earth | daisy. - Single |
> | 13 | bad | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 14 | sunny days | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 15 | peach eyes | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 16 | evening glow | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 17 | pink horizon | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 18 | pink | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 19 | calla | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 20 | 사랑으로 | love. | wave to earth | 0.1 flaws and all. |
> | 21 | homesick | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 22 | dried flower | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 23 | sunburn | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 24 | akira | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 25 | nouvelle vague | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 26 | so real | 동일 표기 | wave to earth | 0.1 flaws and all. |
> | 27 | are you bored? | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 28 | play with earth! | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 29 | annie. | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 30 | pueblo (remastered 2024) | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 31 | beck. | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 32 | slow dive | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 33 | holyland | 동일 표기 | wave to earth | play with earth! 0.03 (Extended Version) |
> | 34 | 검은 산 | Black Mountain | wave to earth | Twenty Plenty |

## 너드커넥션 — 49곡

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1 | Hymn of the Birds - Single | Hymn of the Birds (Nerd Connection) |
| □ | 2 | 대나무숲 - Single | 대나무숲 (Nerd Connection) |
| □ | 3–8 | TOO FAST - EP | 선택 6곡: Waterfall → … → Where are we |
| □ | 9 | 좋은 밤 좋은 꿈 - Single | 좋은 밤 좋은 꿈 (Nerd Connection) |
| □ | 10 | Back in Time - Single | Back in Time (Nerd Connection) |
| □ | 11 | 진눈깨비 - Single | 진눈깨비 (Nerd Connection) |
| □ | 12 | 걸어갈래요 - Single | 걸어갈래요 (Nerd Connection) |
| □ | 13 | 두려울뿐야 - Single | 두려울뿐야 (Nerd Connection) |
| □ | 14–25 | New Century Masterpiece Cinema | 선택 12곡: 21st Century Kingdom → … → 조용히 완전히 영원히 |
| □ | 26 | 버들길 - Single | 버들길 (Nerd Connection) |
| □ | 27 | 파블로 - Single | 파블로 (Nerd Connection) |
| □ | 28 | 그 또한 우리 사랑 - Single | 그 또한 우리 사랑 (Nerd Connection) |
| □ | 29 | 그대만 있다면 (영화 '여름날 우리') - Single | 그대만 있다면 (영화 '여름날 우리') (Nerd Connection) |
| □ | 30–34 | 설명하기 어려운 것들 - EP | 선택 5곡: Planet Earth → … → 여전히 이곳에 |
| □ | 35–48 | 그래도 우리는 | 선택 14곡: 그림자 놀이 → … → 딱 네 잔 (Bonus Track) |
| □ | 49 | Cliché - Single | Cliché (Nerd Connection) |

### 개인 배치와 마지막 조정

- 앨범·EP의 뼈대는 **TOO FAST → New Century Masterpiece Cinema → 설명하기 어려운 것들 → 그래도 우리는**다. 앞·사이·끝의 싱글은 배치표대로 넣는다.
- **1–2번** `Hymn of the Birds → 대나무숲` 뒤에 `TOO FAST`를 둔다.
- **9–13번**의 다섯 싱글을 넣은 다음 `New Century Masterpiece Cinema`를 시작한다.
- **26–29번**의 네 싱글·참여곡 다음 `설명하기 어려운 것들`을 둔다.
- **33번 I Robbed a Bank (2023 Remastered ver.)**는 원본의 리마스터를 유지한다.
- **39번 Losing Myself**는 기존 Spotify의 싱글 대신 원본 `그래도 우리는`에 대응하는 앨범 수록본을 고른다.
- `그래도 우리는`의 마지막 선택곡은 **48번 딱 네 잔 (Bonus Track)**이고, 플레이리스트 마지막은 **49번 Cliché**다.


> [!example]- 너드커넥션 곡별 최종 순서표 — 49곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | Hymn of the Birds | 동일 표기 | Nerd Connection | Hymn of the Birds - Single |
> | 2 | 대나무숲 | 동일 표기 | Nerd Connection | 대나무숲 - Single |
> | 3 | Waterfall | 동일 표기 | Nerd Connection | TOO FAST - EP |
> | 4 | Marion | 동일 표기 | Nerd Connection | TOO FAST - EP |
> | 5 | V | 동일 표기 | Nerd Connection | TOO FAST - EP |
> | 6 | Interlude | 동일 표기 | Nerd Connection | TOO FAST - EP |
> | 7 | Castel | 동일 표기 | Nerd Connection | TOO FAST - EP |
> | 8 | Where are we | 동일 표기 | Nerd Connection | TOO FAST - EP |
> | 9 | 좋은 밤 좋은 꿈 | ‎Good Night Good Dream | Nerd Connection | 좋은 밤 좋은 꿈 - Single |
> | 10 | Back in Time | 동일 표기 | Nerd Connection | Back in Time - Single |
> | 11 | 진눈깨비 | Time Falling | Nerd Connection | 진눈깨비 - Single |
> | 12 | 걸어갈래요 | 동일 표기 | Nerd Connection | 걸어갈래요 - Single |
> | 13 | 두려울뿐야 | 동일 표기 | Nerd Connection | 두려울뿐야 - Single |
> | 14 | 21st Century Kingdom | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 15 | Hollywood Movie Star | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 16 | 29 | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 17 | Behind the Trees | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 18 | SUPERNOVA! | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 19 | 항성통신 | Star Communications | Nerd Connection | New Century Masterpiece Cinema |
> | 20 | 우린 노래가 될까 | Will We Be a Melody | Nerd Connection | New Century Masterpiece Cinema |
> | 21 | Snowman in a Bathtub | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 22 | Green Fields | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 23 | Odds | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 24 | Life Dancing | 동일 표기 | Nerd Connection | New Century Masterpiece Cinema |
> | 25 | 조용히 완전히 영원히 | Silently Completely Eternally | Nerd Connection | New Century Masterpiece Cinema |
> | 26 | 버들길 | Beodeul-gil | Nerd Connection | 버들길 - Single |
> | 27 | 파블로 | Pablo | Nerd Connection | 파블로 - Single |
> | 28 | 그 또한 우리 사랑 | That′s also our love | Nerd Connection | 그 또한 우리 사랑 - Single |
> | 29 | 그대만 있다면 (영화 '여름날 우리') | If I have you only (My love X Nerd Connection) | Nerd Connection | 그대만 있다면 (영화 '여름날 우리') - Single |
> | 30 | Planet Earth | 동일 표기 | Nerd Connection | 설명하기 어려운 것들 - EP |
> | 31 | Stand Up | 동일 표기 | Nerd Connection | 설명하기 어려운 것들 - EP |
> | 32 | Hi, Drunk! | 동일 표기 | Nerd Connection | 설명하기 어려운 것들 - EP |
> | 33 | I Robbed a Bank (2023 Remastered ver.) | I Robbed a Bank (Remastered ver.) | Nerd Connection | 설명하기 어려운 것들 - EP |
> | 34 | 여전히 이곳에 | Been This Way | Nerd Connection | 설명하기 어려운 것들 - EP |
> | 35 | 그림자 놀이 | Playing Shadow | Nerd Connection | 그래도 우리는 |
> | 36 | Psychiatric Hospital | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 37 | headshrinker | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 38 | CASH | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 39 | Losing Myself | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 40 | 무너진 땅 위에서 | Forever Only | Nerd Connection | 그래도 우리는 |
> | 41 | 사랑을 닮은 이유로 | You | Nerd Connection | 그래도 우리는 |
> | 42 | 꽉 잡아 | Hold on Tight | Nerd Connection | 그래도 우리는 |
> | 43 | She | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 44 | Freddy | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 45 | Clown | 동일 표기 | Nerd Connection | 그래도 우리는 |
> | 46 | 가장 높은 인연 | The Highest Tie | Nerd Connection | 그래도 우리는 |
> | 47 | 행운을 빌어 | Good Luck | Nerd Connection | 그래도 우리는 |
> | 48 | 딱 네 잔 (Bonus Track) | Just 4 Shots (Bonus Track) | Nerd Connection | 그래도 우리는 |
> | 49 | Cliché | 동일 표기 | Nerd Connection | Cliché - Single |

## 즛토마요 — 70곡

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1 | Byoushinwo Kamu - Single | Byoushinwo Kamu (ZUTOMAYO) |
| □ | 2–4 | Tadashii Itsuwarikarano Kishou - EP | Humanoid (ZUTOMAYO) → Saturn (ZUTOMAYO) → Uni To Kuri (ZUTOMAYO) |
| □ | 5 | Hisohiso Banashi | Nouriueno Cracker (ZUTOMAYO) |
| □ | 6 | Tadashii Itsuwarikarano Kishou - EP | Kimigaite Mizuninaru (ZUTOMAYO) |
| □ | 7 | Imawa Imade Chikaiwa Emide - EP | Kan Saete Kuyashiiwa (ZUTOMAYO) |
| □ | 8 | Seigi - Single | Seigi (ZUTOMAYO) |
| □ | 9–11 | Imawa Imade Chikaiwa Emide - EP | Matane Maboroshi (ZUTOMAYO) → Minority Myakuraku (ZUTOMAYO) → Samayoi Yoi Ondo (ZUTOMAYO) |
| □ | 12 | Mabushii DNA Dake - Single | Mabushii DNA Dake (ZUTOMAYO) |
| □ | 13–19 | Hisohiso Banashi | 선택 7곡: Inemuri Enseitai → … → Yasashiku Last Smile |
| □ | 20 | Hogarakana Hifutote Fufuku - EP | Fastening (ZUTOMAYO) |
| □ | 21 | Obenkyou Shitoiteyo - Single | Obenkyou Shitoiteyo (ZUTOMAYO) |
| □ | 22–25 | Hogarakana Hifutote Fufuku - EP | 선택 4곡: Ham → … → Milabo |
| □ | 26 | Gusare | One's Mind (ZUTOMAYO) |
| □ | 27 | Can't Be Right - Single | Can't Be Right (ZUTOMAYO) |
| □ | 28 | Hunch Gray - Single | Hunch Gray (ZUTOMAYO) |
| □ | 29–30 | Gusare | Have A (ZUTOMAYO) → Engine Oil (ZUTOMAYO) |
| □ | 31 | Darken - Single | Darken (ZUTOMAYO) |
| □ | 32–35 | Gusare | 선택 4곡: Loneliness → … → Inner Heart |
| □ | 36 | Nobi Shigusa Korite Itomagoi - EP | Flow Different (ZUTOMAYO) |
| □ | 37 | 沈香学 | 袖のキルト (ZUTOMAYO) |
| □ | 38 | Inside Joke - Single | Inside Joke (ZUTOMAYO) |
| □ | 39 | Neko Reset - Single | Neko Reset (ZUTOMAYO) |
| □ | 40 | Nobi Shigusa Korite Itomagoi - EP | Kisumi at Midnight (ZUTOMAYO) |
| □ | 41 | Stay Foolish - Single | Stay Foolish (ZUTOMAYO) |
| □ | 42 | 沈香学 | 花一匁 (ZUTOMAYO) |
| □ | 43 | Time Left - Single | Time Left (ZUTOMAYO) |
| □ | 44 | Kira Killer (feat. Mori Calliope) - Single | Kira Killer (feat. Mori Calliope) (ZUTOMAYO) |
| □ | 45–46 | 沈香学 | 馴れ合いサーブ (ZUTOMAYO) → 夏枯れ (ZUTOMAYO) |
| □ | 47 | INTRUSION - Single | INTRUSION (ZUTOMAYO) |
| □ | 48–50 | 沈香学 | 消えてしまいそうです (ZUTOMAYO) → ミラーチューン (ZUTOMAYO) → 上辺の私自身なんだよ (ZUTOMAYO) |
| □ | 51–53 | Koke no ichinen Kaiba ni takusu - EP | KOKE (ZUTOMAYO) → TAIDADA (ZUTOMAYO) → KUZURI (ZUTOMAYO) |
| □ | 54 | Hippocampal Pain - Single | Hippocampal Pain (ZUTOMAYO) |
| □ | 55 | Truth In Lies - Single | Truth In Lies (ZUTOMAYO) |
| □ | 56 | Blues in the Closet - Single | Blues in the Closet (ZUTOMAYO) |
| □ | 57 | SHADE - Single | SHADE (ZUTOMAYO) |
| □ | 58 | Warmthaholic - Single | Warmthaholic (ZUTOMAYO) |
| □ | 59 | CREAM - Single | CREAM (ZUTOMAYO) |
| □ | 60 | Yushinron - Single | Yushinron (ZUTOMAYO) |
| □ | 61 | KEISOUDO | This Planet Feels Fake (ZUTOMAYO) |
| □ | 62 | 沈香学 | 残機 (ZUTOMAYO) |
| □ | 63 | Medianoche - Single | Medianoche (ZUTOMAYO) |
| □ | 64 | KEISOUDO | Kani Shabu Funk (ZUTOMAYO) |
| □ | 65 | Pain Give Form - Single | Pain Give Form (ZUTOMAYO) |
| □ | 66–70 | KEISOUDO | 선택 5곡: ultra soul → … → lowmotion algae |

### 개인 배치와 마지막 조정

이 목록은 같은 앨범의 곡이 여러 위치로 나뉜다. 앨범을 통째로 이어 붙인 것만으로는 원본이 되지 않는다. 앨범에서 필요한 곡을 모은 뒤 **아래 최종 번호대로** 조정한다.

- `Tadashii Itsuwarikarano Kishou`: **2–4, 6번**. 그 사이 **5번 Nouriueno Cracker**는 `Hisohiso Banashi`에서 가져온다.
- `Imawa Imade Chikaiwa Emide`: **7, 9–11번**. **8번 Seigi**를 사이에 넣는다.
- `Hisohiso Banashi`: **5번 외에 13–19번**. 이 구간 앞 **12번 Mabushii DNA Dake**를 유지한다.
- `Hogarakana Hifutote Fufuku`: **20, 22–25번**. **21번 Obenkyou Shitoiteyo**를 사이에 넣는다.
- `Gusare`: **26, 29–30, 32–35번**. 사이 **27번 Can't Be Right, 28번 Hunch Gray, 31번 Darken**을 원본 위치에 둔다.
- `Nobi Shigusa Korite Itomagoi`: **36번 Flow Different, 40번 Kisumi at Midnight** 두 곡만 선택한다.
- `沈香学`: **37, 42, 45–46, 48–50, 62번**으로 나뉜다. 특히 **62번 残機**를 앨범 구간으로 끌어올리지 않는다.
- **43번 Time Left / 62번 残機**는 원본의 동일 ISRC 두 항목이다. 현재 개인 선택을 보존하므로 하나를 자동 제거하지 않는다.
- **61–70번 마지막 구간:** `This Planet Feels Fake → 残機 → Medianoche → Kani Shabu Funk → Pain Give Form → ultra soul → Learning How Not to Break → antimony → yomosugara → lowmotion algae`.
- **37번 袖のキルト, 52번 TAIDADA, 69번 yomosugara**는 원본 앨범을 특히 확인한다. 기존 Spotify의 다른 모음집·싱글 이름을 목표로 삼지 않는다.

원본 싱글 선택과 일반적인 앨범 우선 규칙이 충돌하는 곳은 이번 가이드에서 싱글을 유지했다. 개인 규칙 자체를 바꾸는 정리는 별도 결정이다.


> [!example]- 즛토마요 곡별 최종 순서표 — 70곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | Byoushinwo Kamu | 동일 표기 | ZUTOMAYO | Byoushinwo Kamu - Single |
> | 2 | Humanoid | 동일 표기 | ZUTOMAYO | Tadashii Itsuwarikarano Kishou - EP |
> | 3 | Saturn | サターン | ZUTOMAYO | Tadashii Itsuwarikarano Kishou - EP |
> | 4 | Uni To Kuri | 동일 표기 | ZUTOMAYO | Tadashii Itsuwarikarano Kishou - EP |
> | 5 | Nouriueno Cracker | 동일 표기 | ZUTOMAYO | Hisohiso Banashi |
> | 6 | Kimigaite Mizuninaru | 君がいて水になる | ZUTOMAYO | Tadashii Itsuwarikarano Kishou - EP |
> | 7 | Kan Saete Kuyashiiwa | 동일 표기 | ZUTOMAYO | Imawa Imade Chikaiwa Emide - EP |
> | 8 | Seigi | 동일 표기 | ZUTOMAYO | Seigi - Single |
> | 9 | Matane Maboroshi | またね幻 | ZUTOMAYO | Imawa Imade Chikaiwa Emide - EP |
> | 10 | Minority Myakuraku | 동일 표기 | ZUTOMAYO | Imawa Imade Chikaiwa Emide - EP |
> | 11 | Samayoi Yoi Ondo | 彷徨い酔い温度 | ZUTOMAYO | Imawa Imade Chikaiwa Emide - EP |
> | 12 | Mabushii DNA Dake | 眩しいDNAだけ | ZUTOMAYO | Mabushii DNA Dake - Single |
> | 13 | Inemuri Enseitai | 동일 표기 | ZUTOMAYO | Hisohiso Banashi |
> | 14 | Haze Haseru Haterumade | 동일 표기 | ZUTOMAYO | Hisohiso Banashi |
> | 15 | Kettobashita Moufu | 동일 표기 | ZUTOMAYO | Hisohiso Banashi |
> | 16 | Dear. Mr"F" | Dear Mr「F」 | ZUTOMAYO | Hisohiso Banashi |
> | 17 | Konnakoto Soudou | 동일 표기 | ZUTOMAYO | Hisohiso Banashi |
> | 18 | Glass to Rum Raisin | Glass To Rum Raisin | ZUTOMAYO | Hisohiso Banashi |
> | 19 | Yasashiku Last Smile | 동일 표기 | ZUTOMAYO | Hisohiso Banashi |
> | 20 | Fastening | 동일 표기 | ZUTOMAYO | Hogarakana Hifutote Fufuku - EP |
> | 21 | Obenkyou Shitoiteyo | 동일 표기 | ZUTOMAYO | Obenkyou Shitoiteyo - Single |
> | 22 | Ham | 동일 표기 | ZUTOMAYO | Hogarakana Hifutote Fufuku - EP |
> | 23 | JK Bomber | 동일 표기 | ZUTOMAYO | Hogarakana Hifutote Fufuku - EP |
> | 24 | Marine Blue Garden | 동일 표기 | ZUTOMAYO | Hogarakana Hifutote Fufuku - EP |
> | 25 | Milabo | 동일 표기 | ZUTOMAYO | Hogarakana Hifutote Fufuku - EP |
> | 26 | One's Mind | 동일 표기 | ZUTOMAYO | Gusare |
> | 27 | Can't Be Right | 正しくなれない | ZUTOMAYO | Can't Be Right - Single |
> | 28 | Hunch Gray | 동일 표기 | ZUTOMAYO | Hunch Gray - Single |
> | 29 | Have A | 동일 표기 | ZUTOMAYO | Gusare |
> | 30 | Engine Oil | 機械油 | ZUTOMAYO | Gusare |
> | 31 | Darken | 동일 표기 | ZUTOMAYO | Darken - Single |
> | 32 | Loneliness | ろんりねす | ZUTOMAYO | Gusare |
> | 33 | Crop | 동일 표기 | ZUTOMAYO | Gusare |
> | 34 | Hypersomnia | 동일 표기 | ZUTOMAYO | Gusare |
> | 35 | Inner Heart | 奥底に眠るルーツ | ZUTOMAYO | Gusare |
> | 36 | Flow Different | 동일 표기 | ZUTOMAYO | Nobi Shigusa Korite Itomagoi - EP |
> | 37 | 袖のキルト | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 38 | Inside Joke | 동일 표기 | ZUTOMAYO | Inside Joke - Single |
> | 39 | Neko Reset | 猫リセット | ZUTOMAYO | Neko Reset - Single |
> | 40 | Kisumi at Midnight | 동일 표기 | ZUTOMAYO | Nobi Shigusa Korite Itomagoi - EP |
> | 41 | Stay Foolish | ばかじゃないのに | ZUTOMAYO | Stay Foolish - Single |
> | 42 | 花一匁 | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 43 | Time Left | 残機 | ZUTOMAYO | Time Left - Single |
> | 44 | Kira Killer (feat. Mori Calliope) | Kira Killer | ZUTOMAYO | Kira Killer (feat. Mori Calliope) - Single |
> | 45 | 馴れ合いサーブ | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 46 | 夏枯れ | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 47 | INTRUSION | Intrusion | ZUTOMAYO | INTRUSION - Single |
> | 48 | 消えてしまいそうです | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 49 | ミラーチューン | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 50 | 上辺の私自身なんだよ | Superficial Me | ZUTOMAYO | 沈香学 |
> | 51 | KOKE | 동일 표기 | ZUTOMAYO | Koke no ichinen Kaiba ni takusu - EP |
> | 52 | TAIDADA | 동일 표기 | ZUTOMAYO | Koke no ichinen Kaiba ni takusu - EP |
> | 53 | KUZURI | 동일 표기 | ZUTOMAYO | Koke no ichinen Kaiba ni takusu - EP |
> | 54 | Hippocampal Pain | 海馬成長痛 | ZUTOMAYO | Hippocampal Pain - Single |
> | 55 | Truth In Lies | 동일 표기 | ZUTOMAYO | Truth In Lies - Single |
> | 56 | Blues in the Closet | 동일 표기 | ZUTOMAYO | Blues in the Closet - Single |
> | 57 | SHADE | 동일 표기 | ZUTOMAYO | SHADE - Single |
> | 58 | Warmthaholic | 동일 표기 | ZUTOMAYO | Warmthaholic - Single |
> | 59 | CREAM | クリームで会いにいけますか | ZUTOMAYO | CREAM - Single |
> | 60 | Yushinron | 동일 표기 | ZUTOMAYO | Yushinron - Single |
> | 61 | This Planet Feels Fake | 동일 표기 | ZUTOMAYO | KEISOUDO |
> | 62 | 残機 | 동일 표기 | ZUTOMAYO | 沈香学 |
> | 63 | Medianoche | メディアノーチェ | ZUTOMAYO | Medianoche - Single |
> | 64 | Kani Shabu Funk | 동일 표기 | ZUTOMAYO | KEISOUDO |
> | 65 | Pain Give Form | 동일 표기 | ZUTOMAYO | Pain Give Form - Single |
> | 66 | ultra soul | 동일 표기 | ZUTOMAYO | KEISOUDO |
> | 67 | Learning How Not to Break | 동일 표기 | ZUTOMAYO | KEISOUDO |
> | 68 | antimony | 동일 표기 | ZUTOMAYO | KEISOUDO |
> | 69 | yomosugara | 동일 표기 | ZUTOMAYO | KEISOUDO |
> | 70 | lowmotion algae | 동일 표기 | ZUTOMAYO | KEISOUDO |

## DJMAX — 78곡

### 앨범·싱글 배치표

**표의 순서대로 배치한다.** 범위가 여러 곡이면 아래 접힌 표에서 해당 번호의 곡들을 선택한다.

| 완료 | 최종 위치 | 앨범·EP·싱글 — Apple 기준 / 검색 보조 | 가져올 곡 |
|---|---:|---|---|
| □ | 1–5 | DJMAX RESPECT VERSE.1 | 선택 5곡: glory day (Extended Ver.) → … → Daydream |
| □ | 6 | DMRV 22FW - EP | Tic! Tac! Toe! (Rocky Music) |
| □ | 7–8 | DJMAX RESPECT VERSE.1 | DIE IN (탁 & Sobrem) → glory MAX -나의 최대치로 너와 함께할게- (탁) |
| □ | 9 | DMRV 24SS | Final Hour (Full Ver.) (Pure 100%) |
| □ | 10 | V LIBERTY 2 (Original Soundtrack) | Kakera (CLTH(이태훈)) |
| □ | 11 | V LIBERTY 3 (Original Soundtrack) | Checkmate (feat. Re.may) (ned & PahNic) |
| □ | 12 | V LIBERTY 4 (Original Soundtrack) | The Castle of Báthory (Wicked Frontier) |
| □ | 13 | V LIBERTY (Original Soundtrack) | Break Out (Night Tempo) |
| □ | 14 | DMRV 24SS | 때론, 냉정도 필요해 (Full Ver.) (Mycin.T) |
| □ | 15 | Djmax Best, Vol. 1 (Original Soundtrack) | 별빛정원 (DJMAX) |
| □ | 16 | DMRV23FW | 별빛너머 (Full ver.) (ned) |
| □ | 17 | V LIBERTY 2 (Original Soundtrack) | Mad (feat. WaMi) (ESAI) |
| □ | 18 | V EXTENSION V (Original Soundtrack) | Carrot Carrot (Sobrem) |
| □ | 19 | V LIBERTY (Original Soundtrack) | Away (Sobrem) |
| □ | 20 | V LIBERTY 2 (Original Soundtrack) | 1! 2! 3! 4! Streaming rn CHU! (Sobrem) |
| □ | 21 | V LIBERTY 4 (Original Soundtrack) | Crazy (feat. Yina) (chomin) |
| □ | 22 | V LIBERTY (Original Soundtrack) | 평행고백 (BEXTER) |
| □ | 23–24 | V LIBERTY 3 (Original Soundtrack) | Love, Epilogue (Feat. mill) (최신엽) → DJ조선 (feat. 이오몽, 판다랑) (CLTH(이태훈)) |
| □ | 25 | V LIBERTY (Original Soundtrack) | Final Round (Extended Ver.) (INFX & 머신투더문) |
| □ | 26 | V EXTENSION V (Original Soundtrack) | ECiLA (최신엽) |
| □ | 27 | V LIBERTY 2 (Original Soundtrack) | B!G-BANG CHALLENGE (seatrus) |
| □ | 28 | Dying - Single | Dying (다인) |
| □ | 29 | AWAKE - Single | AWAKE (다인) |
| □ | 30 | AURORA - Single | AURORA (다인) |
| □ | 31 | No Mercy - Single | No Mercy (다인) |
| □ | 32 | Rocket Ride - Single | Rocket Ride (다인) |
| □ | 33 | V LIBERTY 3 (Original Soundtrack) | Summer Fling (Pure 100%) |
| □ | 34 | V EXTENSION III (Original Soundtrack) | KICK IT (HAYAKO) |
| □ | 35 | V EXTENSION V (Original Soundtrack) | Pitter-patter (SOPHI) |
| □ | 36 | mochimochi - Single | mochimochi (탁) |
| □ | 37 | LEMON MELON COOKIE - Single | LEMON MELON COOKIE (탁) |
| □ | 38 | PPPP (feat. 初音ミク & 重音テト) - Single | PPPP (feat. 初音ミク & 重音テト) (탁) |
| □ | 39 | numb numb (feat. Hatsune Miku & Kasane Teto) - Single | numb numb (feat. Hatsune Miku, Kasane Teto) (탁) |
| □ | 40 | Rabbit Hole - Single | Rabbit Hole (DECO*27) |
| □ | 41 | Cherry Pop - Single | Cherry Pop (DECO*27) |
| □ | 42 | Telepathy - Single | Telepathy (DECO*27) |
| □ | 43 | Monitoring (Best Friend Remix) - Single | Monitoring (Best Friend Remix) (DECO*27) |
| □ | 44–48 | 블루 아카이브 1주년 기념 (Original Soundtrack) | 선택 5곡: Constant Moderato → … → Shooting Stars |
| □ | 49 | 블루 아카이브 2주년 기념 (Original Game Soundtrack) | Colorful Mess (KARUT) |
| □ | 50–54 | 블루 아카이브 4주년 기념 (Original Soundtrack) | 선택 5곡: Usagi Flap → … → Action 68 |
| □ | 55–56 | 블루 아카이브 3주년 기념 (Original Soundtrack) | Unwelcome School (ミツキヨ (미츠키요)) → Funky Road (KARUT) |
| □ | 57 | 꿈길 위의 꽃 (블루 아카이브) [Original Soundtrack] [Korean Version] - Single | 꿈길 위의 꽃 (Korean Version) (ミツキヨ (미츠키요)) |
| □ | 58–60 | 블루 아카이브 3.5주년 기념 OST (Original Soundtrack) | Raise the Huddle (Nor) → Shooting Athletes (KARUT) → Goal Wo Nerae! (KARUT) |
| □ | 61–65 | 블루 아카이브 2.5주년 기념 (Original Soundtrack) | 선택 5곡: Midnight Trip → … → Dolce Biblioteca |
| □ | 66 | 블루 아카이브 4주년 기념 (Original Soundtrack) | Takaramonogatari (ミツキヨ (미츠키요)) |
| □ | 67 | Romantic Seaside (블루 아카이브) [Korean Version] - EP | Romantic Seaside (Korean Version) (ミツキヨ (미츠키요)) |
| □ | 68 | 블루 아카이브 2주년 기념 (Original Game Soundtrack) | Bunny Bunny Carrot Carrot (ミツキヨ (미츠키요)) |
| □ | 69 | 블루 아카이브 1주년 기념 (Original Soundtrack) | Mechanical JUNGLE (KARUT) |
| □ | 70 | 블루 아카이브 2주년 기념 (Original Game Soundtrack) | OperationD (Nor) |
| □ | 71 | Love Parade (블루 아카이브) [feat. Dovlvl] - Single | Love Parade (feat. Dovlvl) (ミツキヨ (미츠키요)) |
| □ | 72 | 꽃, 바람, 그대 (블루 아카이브) - Single | 꽃, 바람, 그대 (feat. 새빛) (ミツキヨ (미츠키요)) |
| □ | 73 | 블루 아카이브 4주년 기념 (Original Soundtrack) | Ramune Lagoon (YUC'e) |
| □ | 74–75 | 블루 아카이브 3주년 기념 (Original Soundtrack) | Encroached Sky (KARUT) → Polyphonic (Nor) |
| □ | 76 | 블루 아카이브 2주년 기념 (Original Game Soundtrack) | Oxygen Destroyer (KARUT) |
| □ | 77 | V EXTENSION IV (Original Soundtrack) | Hell'o (PahNic) |
| □ | 78 | V LIBERTY (Original Soundtrack) | O'men (PahNic) |

### 개인 배치와 마지막 조정

이 목록은 DJMAX와 여러 OST·싱글에서 고른 **개인 선곡 78곡**이다. 앨범 발매일순으로 정렬하면 원본 순서가 깨진다. 배치표와 접힌 곡별 표가 최종 순서다.

- **1–5번 DJMAX RESPECT VERSE.1 → 6번 Tic! Tac! Toe! → 7–8번 같은 앨범의 DIE IN, glory MAX** 배치를 유지한다.
- **9–27번**은 여러 DMRV·V LIBERTY·V EXTENSION 앨범의 개별 선곡이다. 각 OST 전체를 넣지 않는다.
- **28–43번**은 별도 싱글과 선곡 구간이며 **43번 Monitoring (Best Friend Remix)**의 Remix 표기를 유지한다.
- **44–76번**은 블루 아카이브 OST·한국어 버전·참여곡 구간이다. 주년 앨범별로 전체를 정렬하지 않는다. **1주년 → 2주년 일부 → 4주년 일부 → 3주년 일부** 등 원본의 연결을 그대로 따른다.
- **57번 꿈길 위의 꽃, 67번 Romantic Seaside**는 원본의 **Korean Version**을 선택한다.
- **40번 Rabbit Hole**은 원본의 싱글 선택을 표에 유지했다. 기존 Spotify의 `TRANSFORM` 수록 항목과 같다고 자동 처리하지 않는다.
- 마지막은 **77번 Hell'o → 78번 O'men**이다. 두 곡을 각각의 OST 구간으로 끌어올리지 않는다.
- `Full Ver.`, `Extended Ver.`, `Remix`는 구분해서 고른다. OST나 제목에 instrumental이라는 단어가 없다는 이유로 임의 분류하거나 기존 원본 곡을 삭제하지 않는다.


> [!example]- DJMAX 곡별 최종 순서표 — 78곡 펼치기
> 검색 보조 표기는 기존 대조표에서 확인한 이름이다. **기존 Spotify의 잘못된 수록본을 추천하는 표가 아니다.** 앨범 선택은 Apple 기준 열과 본문의 안내를 따른다.
>
> | 최종 번호 | 원본 곡명 | Spotify 검색 보조 표기 | 아티스트 | 원본 앨범·EP·싱글 |
> |---:|---|---|---|---|
> | 1 | glory day (Extended Ver.) | glory day - Extended Ver. | BEXTER & Mycin.T | DJMAX RESPECT VERSE.1 |
> | 2 | BlackCat | 동일 표기 | BEXTER | DJMAX RESPECT VERSE.1 |
> | 3 | Boom! | 동일 표기 | BEXTER | DJMAX RESPECT VERSE.1 |
> | 4 | Dream it | 동일 표기 | BEXTER | DJMAX RESPECT VERSE.1 |
> | 5 | Daydream | 동일 표기 | BEXTER & SiNA | DJMAX RESPECT VERSE.1 |
> | 6 | Tic! Tac! Toe! | 동일 표기 | Rocky Music | DMRV 22FW - EP |
> | 7 | DIE IN | 동일 표기 | 탁 & Sobrem | DJMAX RESPECT VERSE.1 |
> | 8 | glory MAX -나의 최대치로 너와 함께할게- | glory MAX -to the MAXimum- | 탁 | DJMAX RESPECT VERSE.1 |
> | 9 | Final Hour (Full Ver.) | Final Hour - Full Ver. | Pure 100% | DMRV 24SS |
> | 10 | Kakera | 동일 표기 | CLTH(이태훈) | V LIBERTY 2 (Original Soundtrack) |
> | 11 | Checkmate (feat. Re.may) | 동일 표기 | ned & PahNic | V LIBERTY 3 (Original Soundtrack) |
> | 12 | The Castle of Báthory | 동일 표기 | Wicked Frontier | V LIBERTY 4 (Original Soundtrack) |
> | 13 | Break Out | 동일 표기 | Night Tempo | V LIBERTY (Original Soundtrack) |
> | 14 | 때론, 냉정도 필요해 (Full Ver.) | Cold Generation - Full Ver. | Mycin.T | DMRV 24SS |
> | 15 | 별빛정원 | Starlight Garden | DJMAX | Djmax Best, Vol. 1 (Original Soundtrack) |
> | 16 | 별빛너머 (Full ver.) | Over the Starlight - Full ver. | ned | DMRV23FW |
> | 17 | Mad (feat. WaMi) | 동일 표기 | ESAI | V LIBERTY 2 (Original Soundtrack) |
> | 18 | Carrot Carrot | 동일 표기 | Sobrem | V EXTENSION V (Original Soundtrack) |
> | 19 | Away | 동일 표기 | Sobrem | V LIBERTY (Original Soundtrack) |
> | 20 | 1! 2! 3! 4! Streaming rn CHU! | 동일 표기 | Sobrem | V LIBERTY 2 (Original Soundtrack) |
> | 21 | Crazy (feat. Yina) | Crazy | chomin | V LIBERTY 4 (Original Soundtrack) |
> | 22 | 평행고백 | Confession in Another World | BEXTER | V LIBERTY (Original Soundtrack) |
> | 23 | Love, Epilogue (Feat. mill) | 동일 표기 | 최신엽 | V LIBERTY 3 (Original Soundtrack) |
> | 24 | DJ조선 (feat. 이오몽, 판다랑) | DJ_Joseon (feat. E_Omong, Pandalang) | CLTH(이태훈) | V LIBERTY 3 (Original Soundtrack) |
> | 25 | Final Round (Extended Ver.) | Final Round - Extended Ver. | INFX & 머신투더문 | V LIBERTY (Original Soundtrack) |
> | 26 | ECiLA | 동일 표기 | 최신엽 | V EXTENSION V (Original Soundtrack) |
> | 27 | B!G-BANG CHALLENGE | 동일 표기 | seatrus | V LIBERTY 2 (Original Soundtrack) |
> | 28 | Dying | 동일 표기 | 다인 | Dying - Single |
> | 29 | AWAKE | 동일 표기 | 다인 | AWAKE - Single |
> | 30 | AURORA | 동일 표기 | 다인 | AURORA - Single |
> | 31 | No Mercy | 동일 표기 | 다인 | No Mercy - Single |
> | 32 | Rocket Ride | 동일 표기 | 다인 | Rocket Ride - Single |
> | 33 | Summer Fling | 동일 표기 | Pure 100% | V LIBERTY 3 (Original Soundtrack) |
> | 34 | KICK IT | 동일 표기 | HAYAKO | V EXTENSION III (Original Soundtrack) |
> | 35 | Pitter-patter | 동일 표기 | SOPHI | V EXTENSION V (Original Soundtrack) |
> | 36 | mochimochi | 동일 표기 | 탁 | mochimochi - Single |
> | 37 | LEMON MELON COOKIE | 동일 표기 | 탁 | LEMON MELON COOKIE - Single |
> | 38 | PPPP (feat. 初音ミク & 重音テト) | PPPP (feat. Hatsune Miku, Kasane Teto) | 탁 | PPPP (feat. 初音ミク & 重音テト) - Single |
> | 39 | numb numb (feat. Hatsune Miku, Kasane Teto) | 동일 표기 | 탁 | numb numb (feat. Hatsune Miku & Kasane Teto) - Single |
> | 40 | Rabbit Hole | ラビットホール | DECO*27 | Rabbit Hole - Single |
> | 41 | Cherry Pop | チェリーポップ | DECO*27 | Cherry Pop - Single |
> | 42 | Telepathy | テレパシ | DECO*27 | Telepathy - Single |
> | 43 | Monitoring (Best Friend Remix) | モニタリング (Best Friend Remix) | DECO*27 | Monitoring (Best Friend Remix) - Single |
> | 44 | Constant Moderato | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 1주년 기념 (Original Soundtrack) |
> | 45 | Signal of Abydos | 동일 표기 | Nor | 블루 아카이브 1주년 기념 (Original Soundtrack) |
> | 46 | Rolling beat | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 1주년 기념 (Original Soundtrack) |
> | 47 | Step by Step | 동일 표기 | KARUT | 블루 아카이브 1주년 기념 (Original Soundtrack) |
> | 48 | Shooting Stars | 동일 표기 | KARUT | 블루 아카이브 1주년 기념 (Original Soundtrack) |
> | 49 | Colorful Mess | 동일 표기 | KARUT | 블루 아카이브 2주년 기념 (Original Game Soundtrack) |
> | 50 | Usagi Flap | 동일 표기 | Nor | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 51 | Up to 21°C | 동일 표기 | Nor | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 52 | Operation☆DOTABATA! | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 53 | Tok9 Train | 동일 표기 | Nor | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 54 | Action 68 | 동일 표기 | KARUT | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 55 | Unwelcome School | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 3주년 기념 (Original Soundtrack) |
> | 56 | Funky Road | 동일 표기 | KARUT | 블루 아카이브 3주년 기념 (Original Soundtrack) |
> | 57 | 꿈길 위의 꽃 (Korean Version) | Yumeji no Hana - Korean Version | ミツキヨ (미츠키요) | 꿈길 위의 꽃 (블루 아카이브) [Original Soundtrack] [Korean Version] - Single |
> | 58 | Raise the Huddle | 동일 표기 | Nor | 블루 아카이브 3.5주년 기념 OST (Original Soundtrack) |
> | 59 | Shooting Athletes | 동일 표기 | KARUT | 블루 아카이브 3.5주년 기념 OST (Original Soundtrack) |
> | 60 | Goal Wo Nerae! | 동일 표기 | KARUT | 블루 아카이브 3.5주년 기념 OST (Original Soundtrack) |
> | 61 | Midnight Trip | 동일 표기 | Nor | 블루 아카이브 2.5주년 기념 (Original Soundtrack) |
> | 62 | Hifumi Daisuki | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 2.5주년 기념 (Original Soundtrack) |
> | 63 | After School Dessert | 동일 표기 | KARUT | 블루 아카이브 2.5주년 기념 (Original Soundtrack) |
> | 64 | FEEEEVER TIME | 동일 표기 | Nor | 블루 아카이브 2.5주년 기념 (Original Soundtrack) |
> | 65 | Dolce Biblioteca | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 2.5주년 기념 (Original Soundtrack) |
> | 66 | Takaramonogatari | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 67 | Romantic Seaside (Korean Version) | Romantic Seaside - Korean Version | ミツキヨ (미츠키요) | Romantic Seaside (블루 아카이브) [Korean Version] - EP |
> | 68 | Bunny Bunny Carrot Carrot | 동일 표기 | ミツキヨ (미츠키요) | 블루 아카이브 2주년 기념 (Original Game Soundtrack) |
> | 69 | Mechanical JUNGLE | 동일 표기 | KARUT | 블루 아카이브 1주년 기념 (Original Soundtrack) |
> | 70 | OperationD | 동일 표기 | Nor | 블루 아카이브 2주년 기념 (Original Game Soundtrack) |
> | 71 | Love Parade (feat. Dovlvl) | Love Parade | ミツキヨ (미츠키요) | Love Parade (블루 아카이브) [feat. Dovlvl] - Single |
> | 72 | 꽃, 바람, 그대 (feat. 새빛) | Flower, Wind, and You | ミツキヨ (미츠키요) | 꽃, 바람, 그대 (블루 아카이브) - Single |
> | 73 | Ramune Lagoon | 동일 표기 | YUC'e | 블루 아카이브 4주년 기념 (Original Soundtrack) |
> | 74 | Encroached Sky | 동일 표기 | KARUT | 블루 아카이브 3주년 기념 (Original Soundtrack) |
> | 75 | Polyphonic | 동일 표기 | Nor | 블루 아카이브 3주년 기념 (Original Soundtrack) |
> | 76 | Oxygen Destroyer | 동일 표기 | KARUT | 블루 아카이브 2주년 기념 (Original Game Soundtrack) |
> | 77 | Hell'o | 동일 표기 | PahNic | V EXTENSION IV (Original Soundtrack) |
> | 78 | O'men | 동일 표기 | PahNic | V LIBERTY (Original Soundtrack) |

## 마무리 확인

- [ ] 플레이리스트별 목표 곡 수가 맞는다: 89 / 117 / 26 / 34 / 49 / 70 / 78 = **463곡**.
- [ ] 같은 이름의 앨범을 두 번 추가하지 않았고, 선택한 발매본에서 필요한 곡을 실제로 재생할 수 있다.
- [ ] 각 목록의 첫 곡·마지막 곡과 앨범 사이 싱글·참여곡이 표의 위치에 있다.
- [ ] kessoku band 마지막 두 곡, 즛토마요 흩어진 배치, DJMAX 마지막 두 곡을 조정했다.
- [ ] 요루시카 `アルジャーノン`은 한 번만 80번에, `あぶく`는 117번에 있다.
- [ ] 원본의 재녹음·Remix·다른 가수 버전과 `残機` 예외를 제목만 보고 삭제하지 않았다.
- [ ] 새 Spotify CSV로 463개 항목의 순서를 대조한다. CSV 대조와 실제 재생 확인은 별도로 완료한다.

## 근거와 확인 범위

- **1번류 — 직접 읽은 로컬 자료:** [[77_개인/음악/Spotify 이전/My Apple Music Library.csv|Apple 원본 CSV]]의 463행이 목표 곡·아티스트·수록본·최종 순서 기준이다. 각 플레이리스트의 행 순서를 그대로 사용했다.
- [[77_개인/음악/Spotify 이전/spotify_migration_repair_checklist_extracted.txt|기존 검수표]]의 전수대조 463행은 Apple ID·플레이리스트가 원본과 일치함을 확인하고 **검색 표기 보조**에 사용했다. 기존 검수표를 재생 가능 여부의 증거로 쓰지 않았다.
- 현재 상태 참고: `C:/Users/Unoh/Downloads/My Spotify Library (1).csv`. 직접 파싱한 결과 7개·464행이고 요루시카는118행이다. 현재 번호는 이 스냅샷에 한정된다. 이 파일을 원본의 목표 순서로 삼지 않았다.
- [[77_개인/음악/Spotify 이전/HANDOFF_AppleMusic_to_Spotify_2026-09-30|기존 인수인계]]의 89곡 유지·원본 중복 예외를 반영했다. 이후 실제 작업 상태는 새 CSV가 우선한다.
- **사용자 관찰:** strobo 두 발매본의 제목 표기와 재생 차이. 에이전트가 두 앨범 전체의 재생을 독립적으로 검증한 결과는 아니다.
- **미확인:** 전체 Spotify 카탈로그의 대체 발매본, 현재 계정의 전곡 재생 가능 여부, 서로 다른 ISRC 사이의 실제 음원 동일성, 사용자가 과거에 순서를 바꾼 이유. 본문은 이 부분을 추측으로 채우지 않는다.

이 문서 작성 과정에서는 Spotify의 곡 추가·삭제·교체·재정렬을 수행하지 않았다.
