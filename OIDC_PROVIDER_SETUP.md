# AWS IAM OIDC Provider 설정 가이드 (GitHub Actions)

GitHub Actions가 AWS에 접속하려면 **"자격 증명 공급자 (Identity Provider)"**가 먼저 존재해야 합니다.
현재 이 설정이 빠져 있어서 `<No OpenIDConnect provider found>` 에러가 발생하는 것입니다.

### 🚀 해결 방법: 공급자 생성 (1분 소요)

1.  [AWS IAM 콘솔 > 자격 증명 공급자 (Identity providers)](https://console.aws.amazon.com/iamv2/home#/identity_providers) 로 이동
2.  우측 상단 **"공급자 추가 (Add provider)"** 버튼 클릭
3.  설정 값 입력:
    *   **공급자 유형 (Provider type)**: `OpenID Connect` 선택
    *   **공급자 URL (Provider URL)**: `https://token.actions.githubusercontent.com`
        *   (입력 후 **"지문 가져오기 (Get thumbprint)"** 버튼을 꼭 눌러야 합니다!)
    *   **대상 (Audience)**: `sts.amazonaws.com`
4.  **"공급자 추가 (Add provider)"** 완료

---

이제 다시 GitHub Actions에서 **"Re-run jobs"**를 누르면 정상적으로 작동할 것입니다! 🎉
