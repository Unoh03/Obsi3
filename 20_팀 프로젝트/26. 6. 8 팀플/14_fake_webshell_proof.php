<?php
/*
 * CARE 악성 파일 업로드 실습용 harmless webshell proof.
 *
 * 목적:
 * - 업로드 필터가 PHP 계열 파일을 차단하지 않는지 확인한다.
 * - 업로드 디렉터리에서 PHP가 실행되는지 확인한다.
 *
 * 주의:
 * - 이 파일은 진짜 웹쉘이 아니다.
 * - 명령 실행, 파일 읽기, DB 접근, 네트워크 요청 기능이 없다.
 * - 실행되면 고정 proof 문자열만 출력한다.
 */

header('Content-Type: text/plain; charset=utf-8');

echo "[CARE_FAKE_WEBSHELL_PROOF]\n";
echo "executed_by_php=true\n";
echo "proof=care-malicious-upload-proof-2026-06-16\n";
echo "note=This is a harmless proof file, not a real web shell.\n";
