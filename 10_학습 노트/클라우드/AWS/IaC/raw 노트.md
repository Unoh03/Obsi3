https://registry.terraform.io/providers/hashicorp/aws/latest

테라폼, 앤서블, 쿠버네티스 등의 개념을 확실하게 잡아야 나중에 안헷갈릴듯.

선언적 언어는 재실행성이 좋다고 해석할 수 있나?
그럼 테라폼은 실행하면 우선 현재 상태를 파악하나?
	terraform state  와 plan 이 딱 내가 말한거인듯?

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}
```
	이거 해석이 필요해.



# 실습? 시작
IAM 검색하고 들어가기 → 왼쪽에 IAM 사용자. → 알잘딱 만들어라 과정 캡쳐 안했다. 나중에 GPT한테 물어봐야지.
액세스 키 만들기. . csv는 격리 된 곳에 두기 {질문: C드라이브가 나을까 D드라이브가 나을까?}

aws cli 설치 → 2차 프로젝트 하면서 이미 설치 됨. 업데이트 하는 명령어 공부 중.

```cmd
aws Configure --profile Terra-user
```




만약 남의 컴에서 cli 과정 했으면 사용자 폴더의 . aws 폴더 날리기.
![[Pasted image 20260706134714.png]]
{질문} 프로필 지정 안했으면 키도 not set 나와야하는거 아닌가?