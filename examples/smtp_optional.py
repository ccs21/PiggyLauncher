"""선택적인 SMTP 학습 예제. 기본값은 전송하지 않으며 실제 계정은 포함하지 않는다."""

import argparse
from email.message import EmailMessage
import os
import smtplib
import ssl


def make_message():
    message = EmailMessage()
    message["Subject"] = "Launcher Lab example"
    message["From"] = os.environ.get("LAB_SMTP_USER", "")
    message["To"] = os.environ.get("LAB_SMTP_TO", "")
    message.set_content(
        "가상 실습 메시지입니다. 장치 정보나 개인 설정을 첨부하지 않습니다."
    )
    return message


def send_example():
    host = os.environ.get("LAB_SMTP_HOST", "")
    user = os.environ.get("LAB_SMTP_USER", "")
    password = os.environ.get("LAB_SMTP_PASSWORD", "")
    recipient = os.environ.get("LAB_SMTP_TO", "")
    if not all((host, user, password, recipient)):
        raise ValueError("자신의 실습 SMTP 설정을 먼저 입력하세요.")
    with smtplib.SMTP_SSL(
        host, 465, timeout=10, context=ssl.create_default_context()
    ) as server:
        server.login(user, password)
        server.send_message(make_message())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--send", action="store_true", help="자신이 지정한 수신자에게 실습 메시지 전송"
    )
    args = parser.parse_args()
    if args.send:
        send_example()
    else:
        print("전송하지 않았습니다. 사용법은 examples/README.md를 확인하세요.")
