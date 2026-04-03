from app.services.email_parser import normalize_email


def test_zoho_parsing():
    # Имитация "сырых" байтов письма с ZOHO-номером в теле
    raw_email = b"""From: test@example.com
Subject: Test Email
Message-ID: <123@example.com>

#3965 test 101

This is the main body of the email.
-- 
Signature
"""

    # В реальном коде mail-parser парсит из байтов, здесь мы просто передаем байты
    # Примечание: mail-parser требует корректный формат email.
    # Для теста добавим заголовки в байтовую строку.
    raw_email_full = b"From: test@example.com\nSubject: Test Email\nMessage-ID: <123@example.com>\n\n#3965 test 101\n\nThis is the main body of the email.\n-- \nSignature"

    result = normalize_email(raw_email_full)

    print(f"Extracted subject: {result['subject']}")

    expected_subject = "#3965 test 101"
    if result["subject"] == expected_subject:
        print("✅ Success: Zoho ticket ID and subject correctly extracted.")
    else:
        print(f"❌ Error: Expected '{expected_subject}', but got '{result['subject']}'")


if __name__ == "__main__":
    test_zoho_parsing()
